# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
# Copyright (C) 2025 Front Matter.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Crossref DOI Provider."""

import io
import json
import warnings
from collections import ChainMap
from json import JSONDecodeError
from time import time

import requests
from commonmeta import (
    CrossrefError,
    CrossrefNoContentError,
    CrossrefServerError,
    validate_prefix,
)
from flask import current_app
from idutils import is_doi
from invenio_i18n import lazy_gettext as _
from invenio_pidstore.errors import PIDAlreadyExists, PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from requests_toolbelt.multipart.encoder import MultipartEncoder

from ....resources.serializers import CrossrefXMLSerializer
from ....utils import ChainObject
from .base import PIDProvider


class CrossrefClient:
    """Crossref Client."""

    def __init__(self, name, config_prefix=None, config_overrides=None, **kwargs):
        """Constructor."""
        self.name = name
        self._config_prefix = config_prefix or "CROSSREF"
        self._config_overrides = config_overrides or {}

        # Set values from kwargs or use defaults (don't access config yet)
        self.timeout = kwargs.get("timeout", 30)
        self.test_mode = kwargs.get("test_mode", False)
        self.prefixes = kwargs.get("prefixes", [])

        # Ensure prefixes are strings
        if self.prefixes:
            self.prefixes = [str(prefix) for prefix in self.prefixes]

        # Set API URL based on test mode
        if self.test_mode:
            self.api_url = "https://test.crossref.org/servlet/deposit"
        else:
            self.api_url = "https://doi.crossref.org/servlet/deposit"

    def cfgkey(self, key):
        """Generate a configuration key."""
        return f"{self._config_prefix}_{key.upper()}"

    def cfg(self, key, default=None):
        """Get a application config value."""
        config = ChainMap(self._config_overrides, current_app.config)
        return config.get(self.cfgkey(key), default)

    def check_credentials(self, **kwargs):
        """Check if the client has the credentials properly set up.

        :returns: True if credentials are properly configured, False otherwise.
        """
        username = self.cfg("username")
        password = self.cfg("password")
        prefixes = self.cfg("prefixes", [])

        current_app.logger.error(
            f"CrossrefClient.check_credentials: username={'***' if username else None}, "
            f"password={'***' if password else None}, prefixes={prefixes}"
        )

        if not username or not password or not prefixes:
            current_app.logger.error(
                f"CrossrefClient configuration incomplete: missing credentials or prefixes. "
                f"Required: {self.cfgkey('username')}, {self.cfgkey('password')}, {self.cfgkey('prefixes')}"
            )
            warnings.warn(
                f"The {self.__class__.__name__} is misconfigured. Please "
                f"set {self.cfgkey('username')}, {self.cfgkey('password')}"
                f" and {self.cfgkey('prefixes')} in your configuration.",
                UserWarning,
            )
            return False

        current_app.logger.error("CrossrefClient credentials check passed successfully")
        return True

    def generate_doi(self, record):
        """Generate a DOI.

        :param record: The record for which to generate a DOI.
        :returns: Generated DOI string.
        :raises RuntimeError: If credentials or prefixes are not configured.
        """
        current_app.logger.error(
            f"CrossrefClient.generate_doi: Starting DOI generation for record"
        )

        if not self.check_credentials():
            current_app.logger.error(
                "CrossrefClient.generate_doi: Failed - credentials not configured"
            )
            raise RuntimeError("Crossref client credentials not properly configured.")

        prefixes = self.cfg("prefixes", [])
        if not prefixes:
            current_app.logger.error(
                "CrossrefClient.generate_doi: Failed - no prefixes configured"
            )
            raise RuntimeError("Invalid DOI prefixes configured.")

        # Use the first prefix for generation
        prefix = str(prefixes[0]) if prefixes else None
        if not prefix:
            current_app.logger.error(
                "CrossrefClient.generate_doi: Failed - invalid prefix"
            )
            raise RuntimeError("Invalid DOI prefix configured.")

        current_app.logger.error(f"CrossrefClient.generate_doi: Using prefix {prefix}")

        doi_format = self.cfg("format", "{prefix}/{id}")
        current_app.logger.error(
            f"CrossrefClient.generate_doi: DOI format: {doi_format}"
        )

        if callable(doi_format):
            result = doi_format(prefix, record)
            current_app.logger.error(
                f"CrossrefClient.generate_doi: Generated DOI using callable: {result}"
            )
            return result
        else:
            # Ensure we have a valid record ID
            record_id = getattr(record, "pid", None)
            if record_id and hasattr(record_id, "pid_value"):
                result = doi_format.format(prefix=prefix, id=record_id.pid_value)
                current_app.logger.error(
                    f"CrossrefClient.generate_doi: Generated DOI from record.pid.pid_value: {result}"
                )
                return result
            elif hasattr(record, "id"):
                result = doi_format.format(prefix=prefix, id=record.id)
                current_app.logger.error(
                    f"CrossrefClient.generate_doi: Generated DOI from record.id: {result}"
                )
                return result
            else:
                current_app.logger.error(
                    "CrossrefClient.generate_doi: Failed - record has no valid ID"
                )
                raise (
                    RuntimeError("Cannot generate DOI: record has no valid ID.")
                    @ property
                )

    def username(self):
        """Get the Crossref username."""
        return self.cfg("username")

    @property
    def password(self):
        """Get the Crossref password."""
        return self.cfg("password")

    def deposit(self, input_xml):
        """Upload metadata for a new or existing DOI.

        :param input_xml: XML metadata following the Crossref Metadata Schema (str or bytes).
        :return: Status string ('SUCCESS' or 'ERROR' on failure).
        :raises RuntimeError: If credentials are not configured.
        """
        current_app.logger.error("CrossrefClient.deposit: Starting metadata deposit")

        if not self.check_credentials():
            current_app.logger.error(
                "CrossrefClient.deposit: Failed - credentials not configured"
            )
            raise RuntimeError("Crossref client credentials not properly configured.")

        try:
            # Convert string to bytes if necessary
            if isinstance(input_xml, str):
                xml_size = len(input_xml)
                input_xml = input_xml.encode("utf-8")
                current_app.logger.error(
                    f"CrossrefClient.deposit: Converted string XML to bytes ({xml_size} chars)"
                )
            elif not isinstance(input_xml, bytes):
                current_app.logger.error(
                    f"CrossrefClient.deposit: Invalid input type: {type(input_xml)}"
                )
                raise ValueError("input_xml must be string or bytes")
            else:
                current_app.logger.error(
                    f"CrossrefClient.deposit: Using bytes XML ({len(input_xml)} bytes)"
                )

            # The filename displayed in the Crossref admin interface
            filename = f"crossref_deposit_{int(time())}.xml"
            current_app.logger.error(
                f"CrossrefClient.deposit: Using filename: {filename}"
            )

            multipart_data = MultipartEncoder(
                fields={
                    "fname": (filename, io.BytesIO(input_xml), "application/xml"),
                    "operation": "doMDUpload",
                    "login_id": self.username,
                    "login_passwd": self.password,
                }
            )
            current_app.logger.error(
                f"CrossrefClient.deposit: Created multipart data, content-type: {multipart_data.content_type}"
            )

            headers = {"Content-Type": multipart_data.content_type}

            # Log the request (without sensitive data)
            current_app.logger.error(
                f"CrossrefClient.deposit: Submitting to {self.api_url} with timeout {self.timeout}s"
            )

            # Make the request
            resp = requests.post(
                self.api_url, data=multipart_data, headers=headers, timeout=self.timeout
            )

            # Check for HTTP errors
            resp.raise_for_status()

            # Log response details
            current_app.logger.error(
                f"CrossrefClient.deposit: HTTP response status: {resp.status_code}"
            )
            current_app.logger.error(
                f"CrossrefClient.deposit: Response content: {resp.text}"
            )

            # Parse response to check for success/failure
            response_text = resp.text.strip()
            if "SUCCESS" in response_text:
                current_app.logger.error(
                    "CrossrefClient.deposit: Deposit successful - SUCCESS found in response"
                )
                return "SUCCESS"
            else:
                current_app.logger.error(
                    f"CrossrefClient.deposit: Deposit may have failed - no SUCCESS in response: {response_text}"
                )
                return "ERROR"

        except requests.Timeout as e:
            current_app.logger.error(
                f"CrossrefClient.deposit: Timeout error after {self.timeout}s",
                exc_info=e,
            )
            return "ERROR"
        except requests.RequestException as e:
            current_app.logger.error(
                f"CrossrefClient.deposit: Request error - {type(e).__name__}: {str(e)}",
                exc_info=e,
            )
            return "ERROR"
        except ValueError as e:
            current_app.logger.error(
                f"CrossrefClient.deposit: Input validation error: {e}"
            )
            return "ERROR"
        except Exception as e:
            current_app.logger.error(
                f"CrossrefClient.deposit: Unexpected error - {type(e).__name__}: {str(e)}",
                exc_info=e,
            )
            return "ERROR"

    def validate_doi(self, doi):
        """Validate if a DOI is valid and uses an allowed prefix.

        :param doi: DOI string to validate.
        :returns: True if valid, False otherwise.
        """
        current_app.logger.error(f"CrossrefClient.validate_doi: Validating DOI: {doi}")

        if not doi or not is_doi(doi):
            current_app.logger.error(
                f"CrossrefClient.validate_doi: DOI format invalid or empty: {doi}"
            )
            return False

        try:
            doi_prefix = validate_prefix(doi)
            prefixes = self.cfg("prefixes", [])

            current_app.logger.error(
                f"CrossrefClient.validate_doi: DOI prefix: {doi_prefix}, allowed prefixes: {prefixes}"
            )

            result = doi_prefix in [str(p) for p in prefixes]
            current_app.logger.error(
                f"CrossrefClient.validate_doi: Validation result: {result}"
            )
            return result
        except Exception as e:
            current_app.logger.error(
                f"CrossrefClient.validate_doi: Exception during validation: {type(e).__name__}: {str(e)}"
            )
            return False


class CrossrefPIDProvider(PIDProvider):
    """Crossref Provider class.

    Note that Crossref is only contacted when a DOI is registered, or any action
    posterior to it. Its creation happens only at the PIDStore level.
    """

    def __init__(
        self,
        id_,
        client=None,
        serializer=None,
        pid_type="doi",
        default_status=PIDStatus.NEW,
        **kwargs,
    ):
        """Constructor."""
        # Note: Cannot use current_app.logger here as Flask context may not be available during module import
        # Logging will occur in methods when Flask context is available

        super().__init__(
            id_,
            client=(client or CrossrefClient("crossref", config_prefix="CROSSREF")),
            pid_type=pid_type,
            default_status=default_status,
        )
        self.serializer = serializer or CrossrefXMLSerializer()

    @staticmethod
    def _log_errors(exception):
        """Log errors from CrossrefError class."""
        # CrossrefError will have the response msg as first arg
        ex_txt = exception.args[0] or ""
        if isinstance(exception, CrossrefNoContentError):
            current_app.logger.error("Crossref no content error", exc_info=exception)
        elif isinstance(exception, CrossrefServerError):
            current_app.logger.error(
                "Crossref internal server error", exc_info=exception
            )
        else:
            # Client error 4xx status code
            try:
                ex_json = json.loads(ex_txt)
            except JSONDecodeError:
                current_app.logger.error("Unknown Crossref error", exc_info=exception)
                return

            # the `errors` field is only available when a 4xx error happened (not 500)
            for error in ex_json.get("errors", []):
                current_app.logger.error(
                    "Crossref error (field: %(field)s): %(reason)s",
                    {"field": error.get("source"), "reason": error.get("title")},
                    exc_info=exception,
                )

    def create(self, record, pid_value=None, status=None, **kwargs):
        """Get or create the PID with given value for the given record.

        :param record: the record to create the PID for.
        :param pid_value: the PID value.
        :returns: A :class:`invenio_pidstore.models.base.PersistentIdentifier`
            instance.
        """
        current_app.logger.error(
            f"CrossrefPIDProvider.create: Creating PID with value={pid_value}, status={status}"
        )

        if pid_value is None:
            current_app.logger.error(
                "CrossrefPIDProvider.create: Failed - no PID value provided"
            )
            raise ValueError(_("You must provide a pid value."))

        try:
            pid = self.get(pid_value)
            current_app.logger.error(
                f"CrossrefPIDProvider.create: Found existing PID: {pid.pid_value}, status={pid.status}"
            )
        except PIDDoesNotExistError:
            # not existing, create a new one
            current_app.logger.error(
                "CrossrefPIDProvider.create: PID not found, creating new one"
            )
            pid = PersistentIdentifier.create(
                self.pid_type,
                pid_value,
                pid_provider=self.name,
                object_type="rec",
                object_uuid=record.id,
                status=status or self.default_status,
            )
            current_app.logger.error(
                f"CrossrefPIDProvider.create: Created new PID: {pid.pid_value}, status={pid.status}"
            )
            return pid

        # re-activate if previously deleted
        if pid.is_deleted():
            current_app.logger.error(
                f"CrossrefPIDProvider.create: Reactivating deleted PID: {pid.pid_value}"
            )
            pid.sync_status(PIDStatus.NEW)
            return pid
        else:
            current_app.logger.error(
                f"CrossrefPIDProvider.create: PID already exists: {pid.pid_value}"
            )
            raise PIDAlreadyExists(self.pid_type, pid_value)

    def generate_id(self, record, **kwargs):
        """Generate a unique DOI."""
        current_app.logger.error(
            "CrossrefPIDProvider.generate_id: Delegating to client for DOI generation"
        )
        # Delegate to client
        doi = self.client.generate_doi(record)
        current_app.logger.error(
            f"CrossrefPIDProvider.generate_id: Generated DOI: {doi}"
        )
        return doi

    @classmethod
    def is_enabled(cls, app):
        """Determine if crossref is enabled or not."""
        return app.config.get("CROSSREF_ENABLED", False)

    def is_managed(self):
        """Determine if the PID is managed by Crossref.

        This initial version expects the PID value to be provided by the user.
        """
        return False

    def can_modify(self, pid, **kwargs):
        """Checks if the PID can be modified."""
        return not pid.is_registered()

    def register(self, pid, record, **kwargs):
        """Register metadata with the Crossref XML API.

        :param pid: the PID to register.
        :param record: the record metadata for the DOI.
        :returns: `True` if is registered successfully.
        """
        current_app.logger.error(
            f"CrossrefPIDProvider.register: Starting registration for DOI: {pid.pid_value}"
        )
        current_app.logger.error(
            f"CrossrefPIDProvider.register: PID status before registration: {pid.status}"
        )

        local_success = super().register(pid)
        current_app.logger.error(
            f"CrossrefPIDProvider.register: Local registration success: {local_success}"
        )
        if not local_success:
            current_app.logger.error(
                "CrossrefPIDProvider.register: Failed at local registration step"
            )
            return False

        try:
            current_app.logger.error(
                "CrossrefPIDProvider.register: Serializing record to XML"
            )
            doc = self.serializer.dump_obj(record)
            current_app.logger.error(
                f"CrossrefPIDProvider.register: XML serialization successful, size: {len(doc) if doc else 0} chars"
            )

            current_app.logger.error(
                f"CrossrefPIDProvider.register: Calling client.deposit for DOI: {pid.pid_value}"
            )
            self.client.deposit(doc)
            current_app.logger.error(
                f"CrossrefPIDProvider.register: Successfully registered DOI: {pid.pid_value}"
            )
            return True
        except CrossrefError as e:
            current_app.logger.error(
                f"CrossrefPIDProvider.register: Crossref API error when registering DOI {pid.pid_value}: {type(e).__name__}: {str(e)}"
            )
            self._log_errors(e)
            return False
        except Exception as e:
            current_app.logger.error(
                f"CrossrefPIDProvider.register: Unexpected error when registering DOI {pid.pid_value}: {type(e).__name__}: {str(e)}",
                exc_info=e,
            )
            return False

    def update(self, pid, record, url=None, **kwargs):
        """Update metadata with the Crossref XML API.

        :param pid: the PID to update.
        :param record: the record metadata for the DOI.
        :returns: `True` if is updated successfully.
        """
        current_app.logger.error(
            f"CrossrefPIDProvider.update: Starting update for DOI: {pid.pid_value}"
        )

        # Check if record is restricted
        if isinstance(record, ChainObject):
            access_level = record._child["access"]["record"]
        else:
            access_level = record["access"]["record"]

        current_app.logger.error(
            f"CrossrefPIDProvider.update: Record access level: {access_level}"
        )

        if access_level == "restricted":
            current_app.logger.error(
                "CrossrefPIDProvider.update: Skipping update - record is restricted"
            )
            return False

        try:
            current_app.logger.error(
                "CrossrefPIDProvider.update: Serializing record to XML"
            )
            doc = self.serializer.dump_obj(record)
            current_app.logger.error(
                f"CrossrefPIDProvider.update: XML serialization successful, size: {len(doc) if doc else 0} chars"
            )

            current_app.logger.error(
                f"CrossrefPIDProvider.update: Calling client.deposit for DOI: {pid.pid_value}"
            )
            self.client.deposit(doc)
            current_app.logger.error(
                f"CrossrefPIDProvider.update: Successfully updated DOI: {pid.pid_value}"
            )
            return True
        except CrossrefError as e:
            current_app.logger.error(
                f"CrossrefPIDProvider.update: Crossref API error when updating DOI {pid.pid_value}: {type(e).__name__}: {str(e)}"
            )
            self._log_errors(e)
            return False
        except Exception as e:
            current_app.logger.error(
                f"CrossrefPIDProvider.update: Unexpected error when updating DOI {pid.pid_value}: {type(e).__name__}: {str(e)}",
                exc_info=e,
            )
            return False

    def delete(self, pid, **kwargs):
        """Delete/unregister a registered DOI.

        If the PID has not been reserved then it's deleted only locally.
        Otherwise, also it's deleted also remotely.
        :returns: `True` if is deleted successfully.
        """
        current_app.logger.error(
            f"CrossrefPIDProvider.delete: Starting deletion for DOI: {pid.pid_value}"
        )
        current_app.logger.error(
            f"CrossrefPIDProvider.delete: PID status: {pid.status}"
        )

        try:
            if pid.is_reserved():  # Delete only works for draft DOIs
                current_app.logger.error(
                    f"CrossrefPIDProvider.delete: Not implemented - deleting reserved DOI {pid.pid_value}"
                )
            elif pid.is_registered():
                current_app.logger.error(
                    f"CrossrefPIDProvider.delete: Not implemented - deleting registered DOI {pid.pid_value}"
                )
        except CrossrefError as e:
            current_app.logger.error(
                f"CrossrefPIDProvider.delete: Crossref API error when deleting DOI {pid.pid_value}: {type(e).__name__}: {str(e)}"
            )
            self._log_errors(e)
            return False
        except Exception as e:
            current_app.logger.error(
                f"CrossrefPIDProvider.delete: Unexpected error when deleting DOI {pid.pid_value}: {type(e).__name__}: {str(e)}",
                exc_info=e,
            )
            return False

        result = super().delete(pid, **kwargs)
        current_app.logger.error(
            f"CrossrefPIDProvider.delete: Local deletion result for {pid.pid_value}: {result}"
        )
        return result

    def validate(self, record, identifier=None, provider=None, **kwargs):
        """Validate the attributes of the identifier.

        :returns: A tuple (success, errors). `success` is a bool that specifies
                  if the validation was successful. `errors` is a list of
                  error dicts of the form:
                  `{"field": <field>, "messages: ["<msgA1>", ...]}`.
        """
        current_app.logger.error(
            f"CrossrefPIDProvider.validate: Starting validation for record ID: {getattr(record, 'id', 'unknown')}"
        )
        current_app.logger.error(
            f"CrossrefPIDProvider.validate: Identifier: {identifier}, Provider: {provider}"
        )

        errors = []

        try:
            # Validate DOI. Should be a valid DOI with an enabled prefix.
            current_app.logger.error(
                f"CrossrefPIDProvider.validate: Validating DOI format and prefix for: {identifier}"
            )

            if not identifier:
                current_app.logger.error(
                    "CrossrefPIDProvider.validate: No identifier provided"
                )
            elif not is_doi(identifier):
                current_app.logger.error(
                    f"CrossrefPIDProvider.validate: Invalid DOI format: {identifier}"
                )
            elif validate_prefix(identifier) not in self.client.cfg("prefixes"):
                current_app.logger.error(
                    f"CrossrefPIDProvider.validate: DOI prefix not in allowed prefixes: {validate_prefix(identifier)}"
                )
                current_app.logger.error(
                    f"CrossrefPIDProvider.validate: Allowed prefixes: {self.client.cfg('prefixes')}"
                )

            if (
                not identifier
                or not is_doi(identifier)
                or validate_prefix(identifier) not in self.client.cfg("prefixes")
            ):
                errors.append(
                    {
                        "field": "pids.identifier.doi",
                        "messages": [_("Missing or invalid DOI for registration.")],
                    }
                )

            # Validate URL
            # url = record.get("links", {}).get("self_html", None)
            # if not url or not is_url(url):
            #     errors.append(
            #         {
            #             "field": "links.self_html",
            #             "messages": [_("Missing or invalid URL for registration.")],
            #         }
            #     )

            success = errors == []
            current_app.logger.error(
                f"CrossrefPIDProvider.validate: Validation completed - Success: {success}, Errors: {len(errors)}"
            )
            if errors:
                current_app.logger.error(
                    f"CrossrefPIDProvider.validate: Validation errors: {errors}"
                )

            return success, errors

        except Exception as e:
            current_app.logger.error(
                f"CrossrefPIDProvider.validate: Unexpected error during validation: {type(e).__name__}: {str(e)}",
                exc_info=e,
            )
            return False, [
                {"field": "general", "messages": ["Validation error occurred"]}
            ]
