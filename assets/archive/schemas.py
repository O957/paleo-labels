"""
Label type schemas for the paleontological labeling system.
Defines mandatory and optional fields for each label type.
"""

LabelField = dict[str, str | list[str] | bool]


LOCALE_SCHEMA: dict[str, LabelField] = {
    "location": {
        "aliases": ["place", "locale", "site"],
        "required": True,
        "description": "Geographic location name",
    },
    "country": {
        "aliases": ["nation"],
        "required": True,
        "description": "Country where locale is situated",
    },
    "state_province": {
        "aliases": ["state", "province", "region"],
        "required": False,
        "description": "State or province",
    },
    "county": {
        "aliases": ["county_parish", "parish"],
        "required": False,
        "description": "County or parish",
    },
    "coordinates": {
        "aliases": ["lat_long", "gps", "coords"],
        "required": False,
        "description": "GPS coordinates",
    },
    "elevation": {
        "aliases": ["altitude"],
        "required": False,
        "description": "Elevation above sea level",
    },
    "geological_formation": {
        "aliases": ["formation", "fm"],
        "required": False,
        "description": "Geological formation name",
    },
    "geological_age": {
        "aliases": ["age", "period", "epoch"],
        "required": False,
        "description": "Geological time period",
    },
    "description": {
        "aliases": ["notes", "details"],
        "required": False,
        "description": "Additional locale details",
    },
}

COLLECTION_SCHEMA: dict[str, LabelField] = {
    "collection_name": {
        "aliases": ["name", "title"],
        "required": True,
        "description": "Name of the collection",
    },
    "institution": {
        "aliases": ["museum", "repository"],
        "required": True,
        "description": "Institution housing collection",
    },
    "collection_code": {
        "aliases": ["code", "accession"],
        "required": False,
        "description": "Institution collection code",
    },
    "curator": {
        "aliases": ["manager", "keeper"],
        "required": False,
        "description": "Collection curator name",
    },
    "locality": {
        "aliases": ["location", "site"],
        "required": False,
        "description": "Associated locality",
    },
    "date_established": {
        "aliases": ["established", "created"],
        "required": False,
        "description": "Date collection was established",
    },
    "purpose": {
        "aliases": ["research_focus", "scope"],
        "required": False,
        "description": "Collection purpose or scope",
    },
    "access_restrictions": {
        "aliases": ["restrictions", "permissions"],
        "required": False,
        "description": "Access limitations",
    },
}

SPECIMEN_SCHEMA: dict[str, LabelField] = {
    "specimen_number": {
        "aliases": ["catalog_number", "accession_number", "number"],
        "required": True,
        "description": "Unique specimen identifier",
    },
    "scientific_name": {
        "aliases": ["species", "taxon", "name"],
        "required": True,
        "description": "Scientific taxonomic name",
    },
    "locality": {
        "aliases": ["location", "site", "place"],
        "required": False,
        "description": "Collection locality",
    },
    "formation": {
        "aliases": ["geological_formation", "fm"],
        "required": False,
        "description": "Geological formation",
    },
    "age": {
        "aliases": ["geological_age", "period"],
        "required": False,
        "description": "Geological age",
    },
    "collector": {
        "aliases": ["collected_by", "finder"],
        "required": False,
        "description": "Person who collected specimen",
    },
    "collection_date": {
        "aliases": ["date_collected", "date"],
        "required": False,
        "description": "Date of collection",
    },
    "preparation": {
        "aliases": ["prep", "preparation_method"],
        "required": False,
        "description": "Preparation technique used",
    },
    "preservation": {
        "aliases": ["preservation_type", "fossilization"],
        "required": False,
        "description": "Type of preservation",
    },
    "field_notes": {
        "aliases": ["notes", "remarks", "comments"],
        "required": False,
        "description": "Field collection notes",
    },
}

TAXONOMY_SCHEMA: dict[str, LabelField] = {
    "scientific_name": {
        "aliases": ["species", "binomial", "name"],
        "required": True,
        "description": "Full scientific name",
    },
    "kingdom": {
        "aliases": [],
        "required": False,
        "description": "Taxonomic kingdom",
    },
    "phylum": {
        "aliases": [],
        "required": False,
        "description": "Taxonomic phylum",
    },
    "class": {
        "aliases": ["class_name"],
        "required": False,
        "description": "Taxonomic class",
    },
    "order": {
        "aliases": [],
        "required": False,
        "description": "Taxonomic order",
    },
    "family": {
        "aliases": [],
        "required": False,
        "description": "Taxonomic family",
    },
    "genus": {
        "aliases": [],
        "required": False,
        "description": "Taxonomic genus",
    },
    "species": {
        "aliases": ["specific_epithet"],
        "required": False,
        "description": "Species name",
    },
    "subspecies": {
        "aliases": ["variety", "form"],
        "required": False,
        "description": "Subspecies or variety",
    },
    "author": {
        "aliases": ["author_year", "authority"],
        "required": False,
        "description": "Taxonomic authority",
    },
    "year": {
        "aliases": ["year_described"],
        "required": False,
        "description": "Year species was described",
    },
    "common_name": {
        "aliases": ["vernacular", "common"],
        "required": False,
        "description": "Common or vernacular name",
    },
    "original_publication": {
        "aliases": ["publication", "reference"],
        "required": False,
        "description": "Original description reference",
    },
}

EXPEDITION_SCHEMA: dict[str, LabelField] = {
    "expedition_name": {
        "aliases": ["name", "title", "project"],
        "required": True,
        "description": "Name of expedition or fieldwork",
    },
    "location": {
        "aliases": ["place", "locale", "area"],
        "required": True,
        "description": "Geographic area of expedition",
    },
    "start_date": {
        "aliases": ["begin_date", "commenced"],
        "required": False,
        "description": "Expedition start date",
    },
    "end_date": {
        "aliases": ["finish_date", "completed"],
        "required": False,
        "description": "Expedition end date",
    },
    "leader": {
        "aliases": ["expedition_leader", "principal_investigator"],
        "required": False,
        "description": "Expedition leader name",
    },
    "participants": {
        "aliases": ["team", "members", "crew"],
        "required": False,
        "description": "Team member names",
    },
    "institution": {
        "aliases": ["sponsor", "organization"],
        "required": False,
        "description": "Sponsoring institution",
    },
    "permit": {
        "aliases": ["permit_number", "authorization"],
        "required": False,
        "description": "Collection permit details",
    },
    "objectives": {
        "aliases": ["goals", "purpose"],
        "required": False,
        "description": "Expedition objectives",
    },
    "weather": {
        "aliases": ["conditions"],
        "required": False,
        "description": "Weather conditions",
    },
    "notes": {
        "aliases": ["remarks", "summary"],
        "required": False,
        "description": "Additional expedition notes",
    },
}

SPECIMENS_SCHEMA: dict[str, LabelField] = {
    "specimen_range": {
        "aliases": ["numbers", "range", "catalog_range"],
        "required": True,
        "description": "Range of specimen numbers",
    },
    "count": {
        "aliases": ["total", "quantity"],
        "required": True,
        "description": "Total number of specimens",
    },
    "scientific_name": {
        "aliases": ["species", "taxon", "name"],
        "required": False,
        "description": "Scientific taxonomic name",
    },
    "locality": {
        "aliases": ["location", "site", "place"],
        "required": False,
        "description": "Collection locality",
    },
    "formation": {
        "aliases": ["geological_formation", "fm"],
        "required": False,
        "description": "Geological formation",
    },
    "age": {
        "aliases": ["geological_age", "period"],
        "required": False,
        "description": "Geological age",
    },
    "collector": {
        "aliases": ["collected_by", "finder"],
        "required": False,
        "description": "Person who collected specimens",
    },
    "collection_date": {
        "aliases": ["date_collected", "date"],
        "required": False,
        "description": "Date of collection",
    },
    "preparation": {
        "aliases": ["prep", "preparation_method"],
        "required": False,
        "description": "Preparation technique used",
    },
    "storage": {
        "aliases": ["storage_location", "repository"],
        "required": False,
        "description": "Where specimens are stored",
    },
}

GENERAL_SCHEMA: dict[str, LabelField] = {}


LABEL_SCHEMAS = {
    "General": GENERAL_SCHEMA,
    "Locale": LOCALE_SCHEMA,
    "Collection": COLLECTION_SCHEMA,
    "Specimen": SPECIMEN_SCHEMA,
    "Taxonomy": TAXONOMY_SCHEMA,
    "Expedition": EXPEDITION_SCHEMA,
    "Specimens": SPECIMENS_SCHEMA,
}


def get_schema_for_label_type(label_type: str) -> dict[str, LabelField]:
    return LABEL_SCHEMAS.get(label_type, GENERAL_SCHEMA)


def get_required_fields(label_type: str) -> list[str]:
    schema = get_schema_for_label_type(label_type)
    return [
        field for field, config in schema.items() if config.get("required")
    ]


def get_all_fields(label_type: str) -> list[str]:
    """Get all fields (required + optional) for a label type."""
    schema = get_schema_for_label_type(label_type)
    return list(schema.keys())


def get_optional_fields(label_type: str) -> list[str]:
    schema = get_schema_for_label_type(label_type)
    return [
        field for field, config in schema.items() if not config.get("required")
    ]


def get_field_aliases(label_type: str, field: str) -> list[str]:
    schema = get_schema_for_label_type(label_type)
    if field in schema:
        return schema[field].get("aliases", [])
    return []


def validate_label_data(
    label_type: str, data: dict[str, str]
) -> dict[str, list[str]]:
    schema = get_schema_for_label_type(label_type)
    errors = {"missing_required": [], "unknown_fields": []}

    if label_type == "General":
        return errors

    required_fields = get_required_fields(label_type)
    provided_fields = set(data.keys())

    all_valid_fields = set()
    for field, config in schema.items():
        all_valid_fields.add(field)
        all_valid_fields.update(config.get("aliases", []))

    for required_field in required_fields:
        field_aliases = [required_field] + get_field_aliases(
            label_type, required_field
        )
        if not any(alias in provided_fields for alias in field_aliases):
            errors["missing_required"].append(required_field)

    for field in provided_fields:
        if field not in all_valid_fields:
            errors["unknown_fields"].append(field)

    return errors


def normalize_field_name(label_type: str, field: str) -> str | None:
    schema = get_schema_for_label_type(label_type)

    if field in schema:
        return field

    for canonical_field, config in schema.items():
        if field in config.get("aliases", []):
            return canonical_field

    return field if label_type == "General" else None


def format_field_name(field_name: str) -> str:
    """Convert field names to human-readable format."""
    return field_name.replace("_", " ").title()
