# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
# Copyright (C) 2025 Front Matter.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Crossref DOI Provider."""

import json
import warnings
from collections import ChainMap
from json import JSONDecodeError

from commonmeta import (
    CrossrefError,
    CrossrefNoContentError,
    CrossrefNotFoundError,
    CrossrefServerError,
    CrossrefXMLClient,
)
from flask import current_app
from invenio_i18n import lazy_gettext as _
from invenio_pidstore.models import PIDStatus

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
        self._api = None

    def cfgkey(self, key):
        """Generate a configuration key."""
        return f"{self._config_prefix}_{key.upper()}"

    def cfg(self, key, default=None):
        """Get a application config value."""
        config = ChainMap(self._config_overrides, current_app.config)
        return config.get(self.cfgkey(key), default)

    def generate_doi(self, record):
        """Generate a DOI."""
        self.check_credentials()
        prefix = self.cfg("prefix")
        if not prefix:
            raise RuntimeError("Invalid DOI prefix configured.")
        doi_format = self.cfg("format", "{prefix}/{id}")
        if callable(doi_format):
            return doi_format(prefix, record)
        else:
            return doi_format.format(prefix=prefix, id=record.pid.pid_value)

    def check_credentials(self, **kwargs):
        """Returns if the client has the credentials properly set up.

        If the client is running on test mode the credentials are not required.
        """
        if not (self.cfg("username") and self.cfg("password") and self.cfg("prefix")):
            warnings.warn(
                f"The {self.__class__.__name__} is misconfigured. Please "
                f"set {self.cfgkey('username')}, {self.cfgkey('password')}"
                f" and {self.cfgkey('prefix')} in your configuration.",
                UserWarning,
            )

    @property
    def api(self):
        """Crossref XML API client instance."""
        if self._api is None:
            self.check_credentials()
            self._api = CrossrefXMLClient(
                self.cfg("username"),
                self.cfg("password"),
                self.cfg("prefix"),
                self.cfg("test_mode", True),
            )
        return self._api


class CrossrefPIDProvider(PIDProvider):
    """Crossref Provider class.

    Note that Crossref is only contacted when a DOI is reserved or
    registered, or any action posterior to it. Its creation happens
    only at PIDStore level.
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

    def generate_id(self, record, **kwargs):
        """Generate a unique DOI."""
        # Delegate to client
        return self.client.generate_doi(record)

    @classmethod
    def is_enabled(cls, app):
        """Determine if crossref is enabled or not."""
        return app.config.get("CROSSREF_ENABLED", False)

    def can_modify(self, pid, **kwargs):
        """Checks if the PID can be modified."""
        return not pid.is_registered() and not pid.is_reserved()

    def register(self, pid, record, **kwargs):
        """Register a DOI via the Crossref XML API.

        :param pid: the PID to register.
        :param record: the record metadata for the DOI.
        :returns: `True` if is registered successfully.
        """
        if isinstance(record, ChainObject):
            if record._child["access"]["record"] == "restricted":
                return False
        elif record["access"]["record"] == "restricted":
            return False

        local_success = super().register(pid)
        if not local_success:
            return False

        try:
            doc = self.serializer.dump_obj(record)
            url = kwargs["url"]
            self.client.api.public_doi(metadata=doc, url=url, doi=pid.pid_value)
            return True
        except CrossrefError as e:
            current_app.logger.warning(
                f"Crossref provider error when registering DOI for {pid.pid_value}"
            )
            self._log_errors(e)

            return False

    def update(self, pid, record, url=None, **kwargs):
        """Update metadata associated with a DOI.

        This can be called before/after a DOI is registered.
        :param pid: the PID to register.
        :param record: the record metadata for the DOI.
        :returns: `True` if is updated successfully.
        """
        hide = False
        if isinstance(record, ChainObject):
            if record._child["access"]["record"] == "restricted":
                hide = True
        elif record["access"]["record"] == "restricted":
            hide = True

        try:
            if hide:
                self.client.api.hide_doi(doi=pid.pid_value)
            else:
                doc = self.serializer.dump_obj(record)
                self.client.api.update_doi(metadata=doc, doi=pid.pid_value, url=url)
        except CrossrefError as e:
            current_app.logger.warning(
                f"Crossref provider error when updating DOI for {pid.pid_value}"
            )
            self._log_errors(e)

            return False

        if pid.is_deleted():
            return pid.sync_status(PIDStatus.REGISTERED)

        return True

    def restore(self, pid, **kwargs):
        """Restore previously deactivated DOI."""
        try:
            self.client.api.show_doi(pid.pid_value)
        except CrossrefNotFoundError as e:
            if not current_app.config["CROSSREF_TEST_MODE"]:
                raise e

    def delete(self, pid, **kwargs):
        """Delete/unregister a registered DOI.

        If the PID has not been reserved then it's deleted only locally.
        Otherwise, also it's deleted also remotely.
        :returns: `True` if is deleted successfully.
        """
        try:
            if pid.is_reserved():  # Delete only works for draft DOIs
                self.client.api.delete_doi(pid.pid_value)
            elif pid.is_registered():
                self.client.api.hide_doi(pid.pid_value)
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
        # success is unused, but naming it _ would interfere with lazy_gettext as _
        success, errors = super().validate(record, identifier, provider, **kwargs)

        # Validate identifier
        # Checking if the identifier is not None is crucial because not all records at
        # this point will have a DOI identifier (and that is fine in the case of initial
        # creation)
        if identifier is not None:
            # Format check
            try:
                self.client.api.check_doi(identifier)
            except ValueError as e:
                # modifies the error in errors in-place
                self._insert_pid_type_error_msg(errors, str(e))

        # Validate record
        if not record.get("metadata", {}).get("publisher"):
            errors.append(
                {
                    "field": "metadata.publisher",
                    "messages": [
                        _("Missing publisher field required for DOI registration.")
                    ],
                }
            )

        return not bool(errors), errors

    def validate_restriction_level(self, record, identifier=None, **kwargs):
        """Remove the DOI if the record is restricted."""
        if identifier and record["access"]["record"] == "restricted":
            pid = self.get(identifier)
            if pid.status in [PIDStatus.NEW]:
                self.delete(pid)
                del record["pids"][self.pid_type]

    def create_and_reserve(self, record, **kwargs):
        """Create and reserve a DOI for the given record, and update the record with the reserved DOI."""
        if "doi" not in record.pids:
            pid = self.create(record)
            self.reserve(pid, record=record)
            pid_attrs = {"identifier": pid.pid_value, "provider": self.name}
            if self.client:
                pid_attrs["client"] = self.client.name
            record.pids["doi"] = pid_attrs
