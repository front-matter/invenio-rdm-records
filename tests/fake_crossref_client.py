# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 Northwestern University.
# Copyright (C) 2025 Front Matter.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Crossref DOI Client."""

from typing import Union
from unittest.mock import Mock

from invenio_rdm_records.services.pids import providers


class FakeCrossrefClient(providers.CrossrefClient):
    """Fake Crossref Client."""

    def __init__(self, name, config_prefix=None, config_overrides=None, **kwargs):
        """Constructor."""
        self.name = name
        self._config_prefix = config_prefix or "CROSSREF"
        self._config_overrides = config_overrides or {}
        self.timeout = kwargs.get("timeout", 30)
        self.test_mode = kwargs.get("test_mode", False)
        self.prefixes = [str(prefix) for prefix in kwargs.get("prefixes", [])]

        if self.test_mode:
            self.api_url = "https://test.crossref.org/servlet/deposit"
        else:
            self.api_url = "https://doi.crossref.org/servlet/deposit"
        """Initialize the Crossref client.

        :param username: Crossref username.
        :param password: Crossref password.
        :param prefixes: DOI prefixes (or CFG_CROSSREF_DOI_PREFIXES).
        :param test_mode: use test URL when True
        :param timeout: Connect and read timeout in seconds. Specify a tuple
            (connect, read) to specify each timeout individually.
        """

    def deposit(self, input_xml):
        """Deposit metadata.

        :param input_xml: metadata in Crossref XML format.
        :return:
        """
        return Mock()
