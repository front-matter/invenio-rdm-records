# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
# Copyright (C) 2025 Front Matter.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Crossref Serializers for Invenio RDM Records."""

import logging

from commonmeta import (
    MARSHMALLOW_MAP,
    CrossrefXMLSchema,
    Metadata,
    convert_crossref_xml,
    unparse_xml,
)
from flask import current_app
from flask_resources import BaseListSchema, MarshmallowSerializer
from flask_resources.serializers import SimpleSerializer

from ....utils import ChainObject


class CrossrefXMLSerializer(MarshmallowSerializer):
    """JSON based Crossref XML serializer for records."""

    def __init__(self, **options):
        """Constructor."""
        super().__init__(
            format_serializer_cls=SimpleSerializer,
            object_schema_cls=CrossrefXMLSchema,
            list_schema_cls=BaseListSchema,
            encoder=self.crossref_xml_tostring,
            **options,
        )

    def dump_obj(self, record):
        """Dump a single record.

        Uses config variables for Crossref XML head elements.

        :param record: Record instance.
        """
        if isinstance(record, ChainObject):
            meta = record._child
            parent = record._parent
            current_app.logger.error(
                f"Record parent: {parent.id} with pids {parent.pids} for record {meta.id} with pids {meta.pids}"
            )
        else:
            meta = record

        depositor = current_app.config.get("CROSSREF_DEPOSITOR", None)
        email = current_app.config.get("CROSSREF_EMAIL", None)
        registrant = current_app.config.get("CROSSREF_REGISTRANT", None)

        # Convert the metadata to crossref_xml format
        # Reasons for failing to convert to Crossref XML include missing required metadata
        # and type not supported by Crossref.
        metadata = Metadata(
            meta,
            via="inveniordm",
            depositor=depositor,
            email=email,
            registrant=registrant,
        )
        data = convert_crossref_xml(metadata)
        if data is None:
            current_app.logger.error(
                f"Could not convert metadata to Crossref XML: {metadata.id}"
            )
            return ""

        # Use the marshmallow schema to dump the data
        schema = CrossrefXMLSchema()
        crossref_xml = schema.dump(data)

        # Ensure consistent field ordering through the defined mapping
        field_order = [MARSHMALLOW_MAP.get(k, k) for k in list(data.keys())]
        crossref_xml = {k: crossref_xml[k] for k in field_order if k in crossref_xml}

        head = {
            "depositor": metadata.depositor,
            "email": metadata.email,
            "registrant": metadata.registrant,
        }

        # Convert the dict to Crossref XML
        return unparse_xml(crossref_xml, dialect="crossref", head=head)

    @classmethod
    def crossref_xml_tostring(cls, record):
        """Stringify a Crossref XML record."""
        return record
