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

from invenio_rdm_records.resources.serializers import CrossrefXMLSerializer


@pytest.fixture(scope="function")
def minimal_record(minimal_record, parent_record):
    """Minimal record metadata with added parent metadata."""
    minimal_record["access"]["status"] = "open"
    minimal_record["parent"] = parent_record
    minimal_record["links"] = dict(self_html="https://self-link.com")
    return minimal_record


@pytest.fixture
def full_modified_record(full_record_to_dict):
    full_record_to_dict["pids"]["unknown-scheme"] = {
        "identifier": "unknown-1234",
        "provider": "unknown",
        "client": "unknown",
    }

    full_record_to_dict["metadata"]["identifiers"] = [
        {"identifier": "unknown-1234-a", "scheme": "unknown-scheme"}
    ]

    full_record_to_dict["metadata"]["related_identifiers"] = [
        {
            "identifier": "unknown-1234-b",
            "scheme": "unknown-scheme",
            "relation_type": {"id": "iscitedby", "title": {"en": "Is cited by"}},
        }
    ]

    full_record_to_dict["metadata"]["creators"][0]["person_or_org"]["identifiers"] = [
        {"identifier": "unknown-2345", "scheme": "unknown-scheme"}
    ]

    return full_record_to_dict


@pytest.fixture
def full_modified_date_record(full_record_to_dict):
    full_record_to_dict["updated"] = "2022-12-12T22:50:10.573125+00:00"
    return full_record_to_dict


def test_crossref_xml_serializer(running_app, full_record_to_dict):
    expected_data = (
        "<?xml version='1.0' encoding='utf-8'?>\n"
        '<resource xmlns="http://datacite.org/schema/kernel-4" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://datacite.org/schema/kernel-4 '
        'http://schema.datacite.org/meta/kernel-4.3/metadata.xsd">\n'
        '  <identifier identifierType="DOI">10.1234/12345-abcde</identifier>\n'
        "  <alternateIdentifiers>\n"
        "    <alternateIdentifier "
        'alternateIdentifierType="URL">https://127.0.0.1:5000/records/12345-abcde</alternateIdentifier>\n'
        "    <alternateIdentifier "
        'alternateIdentifierType="oai">oai:invenio-rdm.com:12345-abcde</alternateIdentifier>\n'
        "    <alternateIdentifier "
        'alternateIdentifierType="bibcode">1924MNRAS..84..308E</alternateIdentifier>\n'
        "  </alternateIdentifiers>\n"
        "  <creators>\n"
        "    <creator>\n"
        '      <creatorName nameType="Personal">Nielsen, Lars Holm</creatorName>\n'
        "      <givenName>Lars Holm</givenName>\n"
        "      <familyName>Nielsen</familyName>\n"
        "      <nameIdentifier "
        'nameIdentifierScheme="ORCID">0000-0001-8135-3489</nameIdentifier>\n'
        "      <affiliation>CERN</affiliation>\n"
        "      <affiliation>free-text</affiliation>\n"
        "    </creator>\n"
        "    <creator>\n"
        '      <creatorName nameType="Personal">Tom, Blabin</creatorName>\n'
        "      <givenName>Blabin</givenName>\n"
        "      <familyName>Tom</familyName>\n"
        "    </creator>\n"
        "  </creators>\n"
        "  <titles>\n"
        "    <title>InvenioRDM</title>\n"
        '    <title xml:lang="eng" titleType="Subtitle">a research data management '
        "platform</title>\n"
        "  </titles>\n"
        "  <publisher>InvenioRDM</publisher>\n"
        "  <publicationYear>2018</publicationYear>\n"
        "  <subjects>\n"
        '    <subject subjectScheme="MeSH">Abdominal Injuries</subject>\n'
        "    <subject>custom</subject>\n"
        "  </subjects>\n"
        "  <contributors>\n"
        '    <contributor contributorType="Other">\n'
        '      <contributorName nameType="Personal">Nielsen, Lars '
        "Holm</contributorName>\n"
        "      <givenName>Lars Holm</givenName>\n"
        "      <familyName>Nielsen</familyName>\n"
        "      <nameIdentifier "
        'nameIdentifierScheme="ORCID">0000-0001-8135-3489</nameIdentifier>\n'
        "      <affiliation>CERN</affiliation>\n"
        "      <affiliation>TU Wien</affiliation>\n"
        "    </contributor>\n"
        '    <contributor contributorType="Other">\n'
        '      <contributorName nameType="Personal">Dirk, Dirkin</contributorName>\n'
        "      <givenName>Dirkin</givenName>\n"
        "      <familyName>Dirk</familyName>\n"
        "    </contributor>\n"
        "  </contributors>\n"
        "  <dates>\n"
        '    <date dateType="Issued">2018/2020-09</date>\n'
        '    <date dateType="Other" dateInformation="A date">1939/1945</date>\n'
        '    <date dateType="Updated">2023-11-14</date>\n'
        "  </dates>\n"
        "  <language>dan</language>\n"
        '  <resourceType resourceTypeGeneral="Image">Photo</resourceType>\n'
        "  <relatedIdentifiers>\n"
        '    <relatedIdentifier relatedIdentifierType="DOI" relationType="IsCitedBy" '
        'resourceTypeGeneral="Dataset">10.1234/foo.bar</relatedIdentifier>\n'
        '    <relatedIdentifier relatedIdentifierType="DOI" '
        'relationType="IsVersionOf">10.1234/pgfpj-at058</relatedIdentifier>\n'
        "  </relatedIdentifiers>\n"
        "  <sizes>\n"
        "    <size>11 pages</size>\n"
        "  </sizes>\n"
        "  <formats>\n"
        "    <format>application/pdf</format>\n"
        "  </formats>\n"
        "  <version>v1.0</version>\n"
        "  <rightsList>\n"
        '    <rights rightsURI="https://customlicense.org/licenses/by/4.0/">A custom '
        "license</rights>\n"
        "    <rights "
        'rightsURI="https://creativecommons.org/licenses/by/4.0/legalcode" '
        'rightsIdentifierScheme="spdx" rightsIdentifier="cc-by-4.0">Creative Commons '
        "Attribution 4.0 International</rights>\n"
        "  </rightsList>\n"
        "  <descriptions>\n"
        '    <description descriptionType="Abstract">A description \n'
        "with HTML tags</description>\n"
        '    <description descriptionType="Methods" xml:lang="eng">Bla bla '
        "bla</description>\n"
        "  </descriptions>\n"
        "  <geoLocations>\n"
        "    <geoLocation>\n"
        "      <geoLocationPlace>test location place</geoLocationPlace>\n"
        "      <geoLocationPoint>\n"
        "        <pointLongitude>-32.94682</pointLongitude>\n"
        "        <pointLatitude>-60.63932</pointLatitude>\n"
        "      </geoLocationPoint>\n"
        "    </geoLocation>\n"
        "  </geoLocations>\n"
        "  <fundingReferences>\n"
        "    <fundingReference>\n"
        "      <funderName>European Commission</funderName>\n"
        "      <awardNumber>111023</awardNumber>\n"
        "      <awardTitle>Launching of the research program on meaning "
        "processing</awardTitle>\n"
        "    </fundingReference>\n"
        "  </fundingReferences>\n"
        "</resource>\n"
    )

    serializer = CrossrefXMLSerializer()
    serialized_record = serializer.serialize_object(full_record_to_dict)

    assert serialized_record == expected_data


def test_crossref_xml_identifiers(running_app, minimal_record):
    """Test serialization of records with DOI alternate identifiers"""
    # Mimic user putting DOI in alternate identifier field
    minimal_record["metadata"]["identifiers"] = [
        {"identifier": "10.1234/inveniordm.1234", "scheme": "doi"}
    ]

    serializer = CrossrefXMLSerializer()
    serialized_record = serializer.dump_obj(minimal_record)

    assert len(serialized_record["identifiers"]) == 1

    minimal_record["pids"] = {
        "doi": {
            "identifier": "10.1234/inveniordm.1234",
            "provider": "datacite",
            "client": "inveniordm",
        }
    }

    serialized_record = serializer.dump_obj(minimal_record)
    assert len(serialized_record["identifiers"]) == 2
    identifier = serialized_record["identifiers"][0]["identifier"]
    assert identifier == "https://self-link.com"
    identifier = serialized_record["identifiers"][1]["identifier"]
    assert identifier == "10.1234/inveniordm.1234"


def test_crossref_xml_access_right(
    running_app, minimal_record, set_app_config_fn_scoped
):
    """Test serialization of records with access right config."""
    serializer = CrossrefXMLSerializer()

    # Test with access rights dumping disabled (i.e. the default)
    serialized_record = serializer.dump_obj(minimal_record)
    assert "rightsList" not in serialized_record

    # Test with access rights dumping enabled
    set_app_config_fn_scoped({"RDM_DATACITE_DUMP_OPENAIRE_ACCESS_RIGHTS": True})
    serialized_record = serializer.dump_obj(minimal_record)
    rights_list = serialized_record["rightsList"]
    assert {"rightsUri": "info:eu-repo/semantics/openAccess"} in rights_list


def test_crossref_xml_serializer_with_unknown_id_schemes(
    running_app, full_modified_record
):
    """Test if the Crossref XML serializer can handle unknown schemes."""
    serializer = CrossrefXMLSerializer()
    serialized_record = serializer.serialize_object(full_modified_record)
    expected_pid_id = '<alternateIdentifier alternateIdentifierType="unknown-scheme">unknown-1234</alternateIdentifier>'  # noqa
    expected_pid_id_2 = '<alternateIdentifier alternateIdentifierType="unknown-scheme">unknown-1234-a</alternateIdentifier>'  # noqa
    expected_related_id = '<relatedIdentifier relatedIdentifierType="unknown-scheme" relationType="IsCitedBy">unknown-1234-b</relatedIdentifier>'  # noqa
    expected_creator_id = '<nameIdentifier nameIdentifierScheme="unknown-scheme">unknown-2345</nameIdentifier>'  # noqa

    assert expected_pid_id in serialized_record
    assert expected_pid_id_2 in serialized_record
    assert expected_related_id not in serialized_record
    assert expected_creator_id in serialized_record


def test_crossref_serializer_empty_record(running_app, empty_record):
    """Test if the Crossref XML serializer handles an empty record."""

    expected_data = {"schemaVersion": "http://datacite.org/schema/kernel-4"}

    serializer = CrossrefXMLSerializer()
    serialized_record = serializer.dump_obj(empty_record)

    assert serialized_record == expected_data


def test_serialize_publication_conferencepaper(running_app, updated_minimal_record):
    """Test Crossref XML serializer for conference papers."""
    updated_minimal_record["metadata"]["resource_type"]["id"] = (
        "publication-conferencepaper"
    )

    # Force serialization into 'inproceedings'
    updated_minimal_record.update(
        {"custom_fields": {"imprint:imprint": {"title": "book title"}}}
    )
    serializer = CrossrefXMLSerializer()
    serialized_record = serializer.serialize_object(updated_minimal_record)

    expected_data = ""

    assert serialized_record == expected_data

    # Force serialization into 'misc'
    del updated_minimal_record["custom_fields"]["imprint:imprint"]
    serialized_record = serializer.serialize_object(updated_minimal_record)

    expected_data = ""

    assert serialized_record == expected_data


def test_serialize_publication_conferenceproceeding(
    running_app, updated_minimal_record
):
    """Test Crossref XML serializer for conference proceedings."""
    updated_minimal_record["metadata"]["resource_type"]["id"] = (
        "publication-conferenceproceeding"
    )

    serializer = CrossrefXMLSerializer()
    serialized_record = serializer.serialize_object(updated_minimal_record)

    expected_data = ""

    assert serialized_record == expected_data


def test_serialize_publication_booksection(running_app, updated_minimal_record):
    """Test bibtex formatter for a section of a book."""
    updated_minimal_record["metadata"]["resource_type"]["id"] = "publication-section"

    # Force serialization into 'incollection'
    updated_minimal_record.update(
        {"custom_fields": {"imprint:imprint": {"title": "book title", "pages": "1-5"}}}
    )

    serializer = CrossrefXMLSerializer()
    serialized_record = serializer.serialize_object(updated_minimal_record)

    expected_data = ""

    assert serialized_record == expected_data

    # Force serialization into 'inbook' (no book title)
    del updated_minimal_record["custom_fields"]["imprint:imprint"]["title"]
    serialized_record = serializer.serialize_object(updated_minimal_record)

    expected_data = ""

    assert serialized_record == expected_data

    # Force serialization into 'misc' (no pages)
    del updated_minimal_record["custom_fields"]["imprint:imprint"]["pages"]
    serialized_record = serializer.serialize_object(updated_minimal_record)

    expected_data = ""

    assert serialized_record == expected_data


def test_serialize_publication_book(running_app, updated_minimal_record):
    """Test Crossref XML serializer for books."""
    updated_minimal_record["metadata"]["resource_type"]["id"] = "publication-book"

    serializer = CrossrefXMLSerializer()
    serialized_record = serializer.serialize_object(updated_minimal_record)

    expected_data = ""

    assert serialized_record == expected_data

    # Force serialization into 'booklet'
    del updated_minimal_record["metadata"]["publisher"]
    serialized_record = serializer.serialize_object(updated_minimal_record)

    expected_data = ""

    assert serialized_record == expected_data


def test_serialize_publication_article(running_app, updated_minimal_record):
    """Test Crossref XML serializer for articles."""
    updated_minimal_record["metadata"]["resource_type"]["id"] = "publication-article"

    updated_minimal_record.update(
        {"custom_fields": {"journal:journal": {"title": "journal title"}}}
    )

    serializer = CrossrefXMLSerializer()
    serialized_record = serializer.serialize_object(updated_minimal_record)

    expected_data = ""

    assert serialized_record == expected_data


def test_serialize_publication_preprint(running_app, updated_minimal_record):
    """Test Crossref XML serializer for preprints."""
    updated_minimal_record["metadata"]["resource_type"]["id"] = "publication-preprint"

    updated_minimal_record.update(
        {
            "additional_descriptions": [
                {"type": {"id": "other"}, "description": "a description"}
            ]
        }
    )

    serializer = CrossrefXMLSerializer()
    serialized_record = serializer.serialize_object(updated_minimal_record)

    expected_data = ""

    assert serialized_record == expected_data


def test_serialize_publication_thesis(running_app, updated_minimal_record):
    """Test crossref xml serializer for thesis.

    It serializes into 'phdthesis'.
    """
    updated_minimal_record["metadata"]["resource_type"]["id"] = "publication-thesis"

    updated_minimal_record.update(
        {"custom_fields": {"thesis:university": "A university"}}
    )

    serializer = CrossrefXMLSerializer()
    serialized_record = serializer.serialize_object(updated_minimal_record)

    expected_data = ""

    assert serialized_record == expected_data
