# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
# Copyright (C) 2023 Northwestern University.
# Copyright (C) 2025 Front Matter.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Crossref provider tests."""

import pytest
from commonmeta import CrossrefError
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from invenio_rdm_records.proxies import current_rdm_records
from invenio_rdm_records.records import RDMDraft, RDMRecord
from invenio_rdm_records.services.pids.providers import (
    CrossrefClient,
    CrossrefPIDProvider,
)


@pytest.fixture()
def crossref_provider(mocker):
    mocker.patch("invenio_rdm_records.services.pids.providers.crossref.CrossrefClient")

    return CrossrefPIDProvider("crossref", client=CrossrefClient("crossref"))


@pytest.fixture(scope="function")
def record(location):
    """Creates an empty record."""
    draft = RDMDraft.create({})
    record = RDMRecord.publish(draft)

    return record


@pytest.fixture(scope="function")
def record_w_links(running_app, minimal_record):
    """Creates an empty record."""
    service = current_rdm_records.records_service
    draft = service.create(system_identity, minimal_record)
    record = service.publish(system_identity, draft.id)

    return record.to_dict()


def test_crossref_provider_create(record, crossref_provider):
    created_pid = crossref_provider.create(record, pid_value="10.5678/5678")
    db_pid = PersistentIdentifier.get(pid_value=created_pid.pid_value, pid_type="doi")

    assert created_pid == db_pid
    assert created_pid.pid_value
    assert created_pid.pid_type == "doi"
    assert created_pid.status == PIDStatus.NEW


def test_crossref_provider_register(record_w_links, crossref_provider, mocker):
    mocker.patch(
        "invenio_rdm_records.services.pids.providers.crossref."
        + "CrossrefXMLSerializer"
    )
    created_pid = crossref_provider.get(record_w_links["pids"]["doi"]["identifier"])
    assert crossref_provider.register(
        pid=created_pid,
        record=record_w_links,
        url=record_w_links["links"]["self_html"],
    )

    db_pid = PersistentIdentifier.get(pid_value=created_pid.pid_value, pid_type="doi")

    assert created_pid == db_pid
    assert db_pid.pid_value
    assert db_pid.pid_type == "doi"
    assert db_pid.status == PIDStatus.REGISTERED


def test_crossref_provider_update(record_w_links, crossref_provider, mocker):
    mocker.patch(
        "invenio_rdm_records.services.pids.providers.crossref."
        + "CrossrefXMLSerializer"
    )
    record_w_links["metadata"]["resource_type"]["id"] = "publication-preprint"
    created_pid = crossref_provider.get(record_w_links["pids"]["doi"]["identifier"])
    assert crossref_provider.update(
        pid=created_pid, record=record_w_links, url=record_w_links["links"]["self_html"]
    )
    assert crossref_provider.update(pid=created_pid, record=record_w_links, url=None)

    db_pid = PersistentIdentifier.get(pid_value=created_pid.pid_value, pid_type="doi")

    assert created_pid == db_pid
    assert db_pid.pid_value
    assert db_pid.pid_type == "doi"
    assert db_pid.status == PIDStatus.REGISTERED


def test_crossref_provider_configuration(record, mocker):
    def custom_format_func(*args):
        return "10.123/custom.func"

    client = CrossrefClient("crossref")

    # check with default func
    crossref_provider = CrossrefPIDProvider("crossref", client=client)
    expected_result = crossref_provider.generate_id(record)
    assert (
        crossref_provider.create(record, pid_value="10.5678/5678").pid_value
        == expected_result
    )

    # check id generation from env func
    current_app.config["CROSSREF_FORMAT"] = custom_format_func
    crossref_provider = CrossrefPIDProvider("crossref", client=client)
    assert crossref_provider.create(record).pid_value == "10.123/custom.func"

    # check id generation from env f-string
    current_app.config["CROSSREF_FORMAT"] = "{prefix}/crossref2.{id}"  # noqa
    crossref_provider = CrossrefPIDProvider("crossref", client=client)
    expected_result = crossref_provider.generate_id(record)
    assert crossref_provider.create(record).pid_value == expected_result


def test_crossref_provider_validation(record_w_links):
    current_app.config["CROSSREF_PREFIXES"] = ["10.5555"]
    client = CrossrefClient("crossref")
    crossref_provider = CrossrefPIDProvider("crossref", client=client)
    record_w_links["metadata"]["resource_type"]["id"] = "publication-preprint"

    # Case - Valid identifier (doi) + record
    success, errors = crossref_provider.validate(
        record=record_w_links, identifier="10.5555/valid.1234", provider="crossref"
    )
    assert success
    assert [] == errors

    # Case - Wrong identifier (doi) prefix
    success, errors = crossref_provider.validate(
        record=record_w_links, identifier="10.2000/invalid.1234", provider="crossref"
    )
    assert not success
    expected = [
        {
            "field": "pids.identifier.doi",
            "messages": ["Missing or invalid DOI for registration."],
        }
    ]
    assert expected == errors
