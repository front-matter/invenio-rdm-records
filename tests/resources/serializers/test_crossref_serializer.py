# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2025 CERN.
# Copyright (C) 2021-2024 Caltech.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2025 Front Matter.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resources serializers tests."""

import pytest
import xmltodict

from invenio_rdm_records.resources.serializers import CrossrefXMLSerializer


@pytest.fixture(scope="function")
def minimal_record(minimal_record, parent_record):
    """Minimal record metadata with added parent metadata."""
    minimal_record["metadata"]["resource_type"]["id"] = "publication-preprint"
    minimal_record["access"]["status"] = "open"
    minimal_record["parent"] = parent_record
    minimal_record["links"] = dict(self_html="https://doi.org/10.5555/12345-abcde")
    return minimal_record


def test_serialize_publication_preprint(running_app, minimal_record):
    """Test Crossref XML serializer for preprints."""
    minimal_record["metadata"]["resource_type"]["id"] = "publication-preprint"

    serializer = CrossrefXMLSerializer()
    serialized_record = serializer.dump_obj(minimal_record)
    dict_record = xmltodict.parse(serialized_record)

    expected_data = {"month": "6", "day": "1", "year": "2020"}
    assert (
        dict_record["doi_batch"]["body"]["posted_content"]["posted_date"]
        == expected_data
    )


def test_serialize_publication_article(running_app, minimal_record):
    """Test Crossref XML serializer for articles."""
    minimal_record["metadata"]["resource_type"]["id"] = "publication-article"
    minimal_record["pids"] = {
        "doi": {
            "identifier": "10.1234/inveniordm.1234",
            "provider": "crossref",
            "client": "inveniordm",
        }
    }

    serializer = CrossrefXMLSerializer()
    serialized_record = serializer.dump_obj(minimal_record)
    dict_record = xmltodict.parse(serialized_record)

    expected_data = "A Romans story"
    assert (
        dict_record["doi_batch"]["body"]["journal"]["journal_article"]["titles"][
            "title"
        ]
        == expected_data
    )


def test_crossref_serializer_empty_record(running_app, empty_record):
    """Test if the Crossref XML serializer handles an empty record."""

    expected_data = ""

    serializer = CrossrefXMLSerializer()
    serialized_record = serializer.dump_obj(empty_record)

    assert serialized_record == expected_data
