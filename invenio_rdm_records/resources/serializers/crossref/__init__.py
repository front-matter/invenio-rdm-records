# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
# Copyright (C) 2025 Front Matter.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Crossref Serializers for Invenio RDM Records."""

from flask_resources import BaseListSchema, MarshmallowSerializer
from flask_resources.serializers import SimpleSerializer

from ....contrib.journal.processors import JournalCrossrefDumper
from commonmeta import CrossrefXMLSchema


class CrossrefXMLSerializer(MarshmallowSerializer):
    """JSON based Crossref XML serializer for records."""

    def __init__(self, **options):
        """Constructor."""
        super().__init__(
            format_serializer_cls=SimpleSerializer,
            object_schema_cls=CrossrefXMLSchema,
            list_schema_cls=BaseListSchema,
            schema_kwargs={"dumpers": [JournalCrossrefDumper()]},  # Order matters
            encoder=self.crossref_xml_tostring,
            **options,
        )

    @classmethod
    def crossref_xml_tostring(cls, record):
        """Stringify a Crossref XML record."""
        return record
