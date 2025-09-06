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


class FakeDataCrossrefXMLClient:
    """Crossref XML API client wrapper."""

    def __init__(
        self,
        username,
        password,
        prefixes: list[str] = ["10.5555"],
        test_mode=False,
        timeout: int = 30,
    ):
        """Initialize the XML client wrapper.

        :param username: Crossref username.
        :param password: Crossref password.
        :param prefixes: DOI prefixes (or CFG_CROSSREF_DOI_PREFIXES).
        :param test_mode: use test URL when True
        :param timeout: Connect and read timeout in seconds. Specify a tuple
            (connect, read) to specify each timeout individually.
        """
        self.username = str(username)
        self.password = str(password)
        self.prefixes = [str(prefix) for prefix in prefixes]

        if test_mode:
            self.api_url = "https://test.crossref.org/servlet/deposit"
        else:
            self.api_url = "https://doi.crossref.org/servlet/deposit"

        self.timeout = timeout

    def post(self, input_xml: Union[str, bytes]) -> str:
        """Register or update metadata.

        :param input_xml: XML format of the metadata.
        :return:
        """
        return Mock()


class FakeCrossrefClient(providers.CrossrefClient):
    """Fake Crossref Client."""

    @property
    def api(self):
        """Crossref XML API client instance."""
        if self._api is None:
            self.check_credentials()
            self._api = FakeCrossrefClient(
                self.cfg("username"),
                self.cfg("password"),
                self.cfg("prefixes"),
                self.cfg("test_mode", True),
            )
        return self._api
