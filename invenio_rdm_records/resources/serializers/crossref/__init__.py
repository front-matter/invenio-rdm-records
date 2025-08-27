# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
# Copyright (C) 2025 Front Matter.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Crossref Serializers for Invenio RDM Records."""

import logging
import os
from flask_resources import BaseListSchema, MarshmallowSerializer
from flask_resources.serializers import SimpleSerializer

from commonmeta import CrossrefXMLSchema, Metadata, unparse_xml, convert_crossref_xml

MARSHMALLOW_MAP = {
    "abstracts": "jats:abstract",
    "license": "ai:program",
    "funding_references": "fr:program",
    "relations": "rel:program",
    "references": "citation_list",
}

logger = logging.getLogger(__name__)
# Set debug level from environment variable or default to INFO
log_level = os.getenv("CROSSREF_SERIALIZER_LOG_LEVEL", "INFO").upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))


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

    def serialize_object(self, record):
        """Serialize a single record.

        :param record: Record instance.
        """

        logger.debug("Processing record for Crossref XML: %s", record.get("id"))

        metadata = Metadata(record, via="inveniordm")
        data = convert_crossref_xml(metadata)
        if data is None:
            logger.error(f"Could not convert metadata to Crossref XML: {metadata.id}")
            return None

        # Use the marshmallow schema to dump the data
        schema = CrossrefXMLSchema()
        crossref_xml = schema.dump(data)

        # Ensure consistent field ordering through the defined mapping
        field_order = [MARSHMALLOW_MAP.get(k, k) for k in list(data.keys())]
        crossref_xml = {k: crossref_xml[k] for k in field_order if k in crossref_xml}
        return unparse_xml(crossref_xml, dialect="crossref")

    @classmethod
    def crossref_xml_tostring(cls, record):
        """Serialize dict to a Crossref XML record."""
        logger.debug("Converting record to XML string: %s", record.get("id", "unknown"))

        try:
            return unparse_xml(record, dialect="crossref")
        except Exception as e:
            logger.error("Failed to convert record to XML string: %s", str(e))
            raise
