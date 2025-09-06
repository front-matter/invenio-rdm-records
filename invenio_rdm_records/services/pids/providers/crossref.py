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

        if not username or not password or not prefixes:
            warnings.warn(
                f"The {self.__class__.__name__} is misconfigured. Please "
                f"set {self.cfgkey('username')}, {self.cfgkey('password')}"
                f" and {self.cfgkey('prefixes')} in your configuration.",
                UserWarning,
            )
            return False
        return True

    def generate_doi(self, record):
        """Generate a DOI.

        :param record: The record for which to generate a DOI.
        :returns: Generated DOI string.
        :raises RuntimeError: If credentials or prefixes are not configured.
        """
        if not self.check_credentials():
            raise RuntimeError("Crossref client credentials not properly configured.")

        prefixes = self.cfg("prefixes", [])
        if not prefixes:
            raise RuntimeError("Invalid DOI prefixes configured.")

        # Use the first prefix for generation
        prefix = str(prefixes[0]) if prefixes else None
        if not prefix:
            raise RuntimeError("Invalid DOI prefix configured.")

        doi_format = self.cfg("format", "{prefix}/{id}")
        if callable(doi_format):
            return doi_format(prefix, record)
        else:
            # Ensure we have a valid record ID
            record_id = getattr(record, "pid", None)
            if record_id and hasattr(record_id, "pid_value"):
                return doi_format.format(prefix=prefix, id=record_id.pid_value)
            elif hasattr(record, "id"):
                return doi_format.format(prefix=prefix, id=record.id)
            else:
                raise RuntimeError("Cannot generate DOI: record has no valid ID.")

    @property
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
        if not self.check_credentials():
            raise RuntimeError("Crossref client credentials not properly configured.")

        try:
            # Convert string to bytes if necessary
            if isinstance(input_xml, str):
                input_xml = input_xml.encode("utf-8")
            elif not isinstance(input_xml, bytes):
                raise ValueError("input_xml must be string or bytes")

            # The filename displayed in the Crossref admin interface
            filename = f"{int(time())}"

            multipart_data = MultipartEncoder(
                fields={
                    "fname": (filename, io.BytesIO(input_xml), "application/xml"),
                    "operation": "doMDUpload",
                    "login_id": self.username,
                    "login_passwd": self.password,
                }
            )

            headers = {"Content-Type": multipart_data.content_type}

            # Log the request (without sensitive data)
            current_app.logger.info(f"Submitting Crossref deposit to {self.api_url}")

            # Make the request
            resp = requests.post(
                self.api_url, data=multipart_data, headers=headers, timeout=self.timeout
            )

            # Check for HTTP errors
            resp.raise_for_status()

            # Log response details
            current_app.logger.error(f"Crossref response status: {resp.status_code}")
            current_app.logger.error(f"Crossref response: {resp.text}")

            # Parse response to check for success/failure
            response_text = resp.text.strip()
            if "SUCCESS" in response_text:
                current_app.logger.error("Crossref deposit successful")
                return "SUCCESS"
            else:
                current_app.logger.error(
                    f"Crossref deposit may have failed: {response_text}"
                )
                return "ERROR"

        except requests.Timeout as e:
            current_app.logger.error(
                f"Crossref deposit timeout after {self.timeout}s", exc_info=e
            )
            return "ERROR"
        except requests.RequestException as e:
            current_app.logger.error("Crossref deposit request error", exc_info=e)
            return "ERROR"
        except ValueError as e:
            current_app.logger.error(f"Crossref deposit input error: {e}")
            return "ERROR"
        except Exception as e:
            current_app.logger.error(
                "Unexpected error during Crossref deposit", exc_info=e
            )
            return "ERROR"

    def validate_doi(self, doi):
        """Validate if a DOI is valid and uses an allowed prefix.

        :param doi: DOI string to validate.
        :returns: True if valid, False otherwise.
        """
        if not doi or not is_doi(doi):
            return False

        try:
            doi_prefix = validate_prefix(doi)
            prefixes = self.cfg("prefixes", [])
            return doi_prefix in [str(p) for p in prefixes]
        except Exception:
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
        if pid_value is None:
            raise ValueError(_("You must provide a pid value."))

        try:
            pid = self.get(pid_value)
        except PIDDoesNotExistError:
            # not existing, create a new one
            return PersistentIdentifier.create(
                self.pid_type,
                pid_value,
                pid_provider=self.name,
                object_type="rec",
                object_uuid=record.id,
                status=status or self.default_status,
            )

        # re-activate if previously deleted
        if pid.is_deleted():
            pid.sync_status(PIDStatus.NEW)
            return pid
        else:
            raise PIDAlreadyExists(self.pid_type, pid_value)

    def generate_id(self, record, **kwargs):
        """Generate a unique DOI."""
        # Delegate to client
        doi = self.client.generate_doi(record)
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
        local_success = super().register(pid)
        current_app.logger.error(f"Local success registering DOI {local_success}")
        if not local_success:
            return False

        try:
            doc = self.serializer.dump_obj(record)
            current_app.logger.error(f"Registering DOI for {pid.pid_value}")
            self.client.deposit(doc)
            current_app.logger.error(f"Registered DOI for {pid.pid_value}")
            return True
        except CrossrefError as e:
            current_app.logger.warning(
                f"Crossref provider error when registering DOI for {pid.pid_value}"
            )
            self._log_errors(e)

            return False

    def update(self, pid, record, url=None, **kwargs):
        """Update metadata with the Crossref XML API.

        :param pid: the PID to update.
        :param record: the record metadata for the DOI.
        :returns: `True` if is updated successfully.
        """
        if isinstance(record, ChainObject):
            if record._child["access"]["record"] == "restricted":
                return False
        elif record["access"]["record"] == "restricted":
            return False

        try:
            doc = self.serializer.dump_obj(record)
            current_app.logger.info(f"Updating DOI for {pid.pid_value}")
            self.client.deposit(doc)
            current_app.logger.info(f"Updated DOI for {pid.pid_value}")
            return True
        except CrossrefError as e:
            current_app.logger.warning(
                f"Crossref provider error when updating DOI for {pid.pid_value}"
            )
            self._log_errors(e)

            return False

    def delete(self, pid, **kwargs):
        """Delete/unregister a registered DOI.

        If the PID has not been reserved then it's deleted only locally.
        Otherwise, also it's deleted also remotely.
        :returns: `True` if is deleted successfully.
        """
        try:
            if pid.is_reserved():  # Delete only works for draft DOIs
                current_app.logger.info(
                    f"Not implemented: Deleting reserved DOI {pid.pid_value}"
                )
            elif pid.is_registered():
                current_app.logger.info(
                    f"Not implemented: Deleting registered DOI {pid.pid_value}"
                )
        except CrossrefError as e:
            current_app.logger.warning(
                f"Crossref provider error when deleting DOI for {pid.pid_value}"
            )
            self._log_errors(e)

            return False

        return super().delete(pid, **kwargs)

    def validate(self, record, identifier=None, provider=None, **kwargs):
        """Validate the attributes of the identifier.

        :returns: A tuple (success, errors). `success` is a bool that specifies
                  if the validation was successful. `errors` is a list of
                  error dicts of the form:
                  `{"field": <field>, "messages: ["<msgA1>", ...]}`.
        """
        errors = []

        # Validate DOI. Should be a valid DOI with an enabled prefix.
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
        return errors == [], errors
