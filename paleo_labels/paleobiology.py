"""
Paleobiology database integration for taxonomic information lookup.
Handles local parquet file reading and taxonomic data caching.
"""

import pathlib

try:
    import polars as pl
except ImportError:
    pl = None


class PaleobiologyDatabase:
    def __init__(self, data_path: pathlib.Path | None = None):
        if data_path is None:
            data_path = (
                pathlib.Path(__file__).parent.parent
                / "assets"
                / "data"
                / "lc_nacp_all.parquet"
            )

        self.data_path = data_path
        self._data = None
        self._taxonomic_cache = {}
        self._locality_cache = {}

    def _load_data(self):
        if self._data is None:
            if pl is None:
                self._data = None
                return None
            if self.data_path.exists():
                self._data = pl.read_parquet(self.data_path)
            else:
                self._data = pl.DataFrame()
        return self._data

    def is_available(self) -> bool:
        return pl is not None and self.data_path.exists()

    def get_species_list(self) -> list[str]:
        data = self._load_data()
        if (
            data is None
            or (hasattr(data, "is_empty") and data.is_empty())
            or (hasattr(data, "empty") and data.empty)
        ):
            return []

        if "accepted_name" in data.columns:
            try:
                values = data["accepted_name"].drop_nulls().unique().to_list()
                species = [
                    v
                    for v in values
                    if isinstance(v, str) and len(v.strip()) > 0
                ]
                return sorted(species)
            except:
                pass

        return []

    def get_taxonomic_list(self, rank: str) -> list[str]:
        """Get unique values for a specific taxonomic rank."""
        data = self._load_data()
        if (
            data is None
            or (hasattr(data, "is_empty") and data.is_empty())
            or (hasattr(data, "empty") and data.empty)
        ):
            return []

        rank_column = rank.lower()
        if rank_column in data.columns:
            try:
                values = data[rank_column].drop_nulls().unique().to_list()
                return sorted(
                    [
                        v
                        for v in values
                        if isinstance(v, str) and len(v.strip()) > 0
                    ]
                )
            except:
                pass

        return []

    def get_genus_list(self) -> list[str]:
        return self.get_taxonomic_list("genus")

    def get_family_list(self) -> list[str]:
        return self.get_taxonomic_list("family")

    def get_order_list(self) -> list[str]:
        return self.get_taxonomic_list("order")

    def get_class_list(self) -> list[str]:
        return self.get_taxonomic_list("class")

    def get_phylum_list(self) -> list[str]:
        return self.get_taxonomic_list("phylum")

    def get_kingdom_list(self) -> list[str]:
        return self.get_taxonomic_list("kingdom")

    def get_formation_list(self) -> list[str]:
        data = self._load_data()
        if (
            data is None
            or (hasattr(data, "is_empty") and data.is_empty())
            or (hasattr(data, "empty") and data.empty)
        ):
            return []

        formation_columns = [
            col
            for col in data.columns
            if "formation" in col.lower() or "fm" in col.lower()
        ]
        formations = set()

        for col in formation_columns:
            formations.update(data[col].drop_nulls().unique().to_list())

        return sorted(list(formations))

    def get_locality_list(self) -> list[str]:
        data = self._load_data()
        if (
            data is None
            or (hasattr(data, "is_empty") and data.is_empty())
            or (hasattr(data, "empty") and data.empty)
        ):
            return []

        locality_columns = [
            col
            for col in data.columns
            if any(
                term in col.lower()
                for term in ["locality", "location", "site", "place"]
            )
        ]
        localities = set()

        for col in locality_columns:
            localities.update(data[col].drop_nulls().unique().to_list())

        return sorted(list(localities))

    def lookup_taxon_info(self, scientific_name: str) -> dict | None:
        if scientific_name in self._taxonomic_cache:
            return self._taxonomic_cache[scientific_name]

        data = self._load_data()
        if data.empty:
            return None

        species_columns = [
            col
            for col in data.columns
            if "species" in col.lower() or "taxon" in col.lower()
        ]

        if pl is None:
            return None

        matches = pl.DataFrame()
        for col in species_columns:
            try:
                col_matches = data.filter(
                    pl.col(col).str.contains(f"(?i){scientific_name}")
                )
                matches = pl.concat([matches, col_matches])
            except:
                continue

        if (
            matches is None
            or (hasattr(matches, "is_empty") and matches.is_empty())
            or (hasattr(matches, "empty") and matches.empty)
        ):
            return None

        taxonomic_info = {}
        hierarchical_columns = [
            "kingdom",
            "phylum",
            "class",
            "order",
            "family",
            "genus",
            "species",
        ]

        for col in hierarchical_columns:
            matching_cols = [c for c in matches.columns if col in c.lower()]
            if matching_cols:
                values = (
                    matches[matching_cols[0]].drop_nulls().unique().to_list()
                )
                if len(values) > 0:
                    taxonomic_info[col] = values[0]

        age_columns = [
            col
            for col in matches.columns
            if any(term in col.lower() for term in ["age", "period", "epoch"])
        ]
        if age_columns:
            ages = matches[age_columns[0]].drop_nulls().unique().to_list()
            if len(ages) > 0:
                taxonomic_info["age"] = ages[0]

        author_columns = [
            col for col in matches.columns if "author" in col.lower()
        ]
        if author_columns:
            authors = (
                matches[author_columns[0]].drop_nulls().unique().to_list()
            )
            if len(authors) > 0:
                taxonomic_info["author"] = authors[0]

        self._taxonomic_cache[scientific_name] = taxonomic_info
        return taxonomic_info

    def lookup_locality_info(self, locality_name: str) -> dict | None:
        if locality_name in self._locality_cache:
            return self._locality_cache[locality_name]

        data = self._load_data()
        if data.empty:
            return None

        locality_columns = [
            col
            for col in data.columns
            if any(
                term in col.lower()
                for term in ["locality", "location", "site", "place"]
            )
        ]

        if pl is None:
            return None

        matches = pl.DataFrame()
        for col in locality_columns:
            try:
                col_matches = data.filter(
                    pl.col(col).str.contains(f"(?i){locality_name}")
                )
                matches = pl.concat([matches, col_matches])
            except:
                continue

        if (
            matches is None
            or (hasattr(matches, "is_empty") and matches.is_empty())
            or (hasattr(matches, "empty") and matches.empty)
        ):
            return None

        locality_info = {}

        geographic_columns = ["country", "state", "province", "county"]
        for col in geographic_columns:
            matching_cols = [c for c in matches.columns if col in c.lower()]
            if matching_cols:
                values = (
                    matches[matching_cols[0]].drop_nulls().unique().to_list()
                )
                if len(values) > 0:
                    locality_info[col] = values[0]

        coord_columns = [
            col
            for col in matches.columns
            if any(
                term in col.lower() for term in ["lat", "long", "coord", "gps"]
            )
        ]
        if coord_columns:
            coords = []
            for col in coord_columns:
                values = matches[col].drop_nulls().unique().to_list()
                if len(values) > 0:
                    coords.append(str(values[0]))
            if coords:
                locality_info["coordinates"] = ", ".join(coords)

        formation_columns = [
            col for col in matches.columns if "formation" in col.lower()
        ]
        if formation_columns:
            formations = (
                matches[formation_columns[0]].drop_nulls().unique().to_list()
            )
            if len(formations) > 0:
                locality_info["formation"] = formations[0]

        age_columns = [
            col
            for col in matches.columns
            if any(term in col.lower() for term in ["age", "period", "epoch"])
        ]
        if age_columns:
            ages = matches[age_columns[0]].drop_nulls().unique().to_list()
            if len(ages) > 0:
                locality_info["age"] = ages[0]

        self._locality_cache[locality_name] = locality_info
        return locality_info

    def search_taxa(self, query: str, limit: int = 20) -> list[dict]:
        data = self._load_data()
        if (
            data is None
            or (hasattr(data, "is_empty") and data.is_empty())
            or (hasattr(data, "empty") and data.empty)
        ):
            return []

        results = []
        query_lower = query.lower()

        species_columns = [
            col
            for col in data.columns
            if "species" in col.lower() or "taxon" in col.lower()
        ]

        for col in species_columns:
            try:
                matching_rows = data.filter(
                    pl.col(col).str.contains(f"(?i){query_lower}")
                )

                for row in matching_rows.iter_rows(named=True):
                    result = {"scientific_name": row[col]}

                    for tax_level in [
                        "genus",
                        "family",
                        "order",
                        "class",
                        "phylum",
                    ]:
                        matching_cols = [
                            c for c in data.columns if tax_level in c.lower()
                        ]
                        if (
                            matching_cols
                            and row.get(matching_cols[0]) is not None
                        ):
                            result[tax_level] = row[matching_cols[0]]

                    results.append(result)

                    if len(results) >= limit:
                        return results
            except:
                continue

        return results

    def get_column_info(self) -> dict[str, list[str]]:
        data = self._load_data()
        if data is None:
            return {}

        try:
            if (
                hasattr(data, "is_empty")
                and data.is_empty()
                or hasattr(data, "empty")
                and data.empty
            ):
                return {}
        except:
            pass

        column_categories = {
            "taxonomic": [],
            "geographic": [],
            "temporal": [],
            "collection": [],
            "identification": [],
            "other": [],
        }

        taxonomic_terms = [
            "species",
            "genus",
            "family",
            "order",
            "class",
            "phylum",
            "kingdom",
            "taxon",
            "accepted",
        ]
        geographic_terms = [
            "lat",
            "lng",
            "country",
            "state",
            "county",
            "paleo",
            "cc",
            "formation",
            "stratgroup",
            "member",
        ]
        temporal_terms = [
            "age",
            "period",
            "epoch",
            "era",
            "stage",
            "ma",
            "interval",
            "early",
            "late",
        ]
        collection_terms = [
            "collection",
            "occurrence",
            "museum",
            "reference",
            "authorizer",
            "enterer",
        ]
        identification_terms = ["identified", "difference", "reid", "flags"]

        for col in data.columns:
            col_lower = col.lower()

            if any(term in col_lower for term in identification_terms):
                column_categories["identification"].append(col)
            elif any(term in col_lower for term in taxonomic_terms):
                column_categories["taxonomic"].append(col)
            elif any(term in col_lower for term in geographic_terms):
                column_categories["geographic"].append(col)
            elif any(term in col_lower for term in temporal_terms):
                column_categories["temporal"].append(col)
            elif any(term in col_lower for term in collection_terms):
                column_categories["collection"].append(col)
            else:
                column_categories["other"].append(col)

        return column_categories

    def get_database_stats(self) -> dict:
        data = self._load_data()
        if data is None:
            return {}

        try:
            if (
                hasattr(data, "is_empty")
                and data.is_empty()
                or hasattr(data, "empty")
                and data.empty
            ):
                return {}
        except:
            pass

        return {
            "total_records": len(data),
            "columns": len(data.columns),
            "unique_species": len(self.get_species_list()),
            "unique_genera": len(self.get_genus_list()),
            "unique_families": len(self.get_family_list()),
            "unique_orders": len(self.get_order_list()),
            "unique_classes": len(self.get_class_list()),
            "unique_phyla": len(self.get_phylum_list()),
            "unique_formations": len(self.get_formation_list()),
            "unique_localities": len(self.get_locality_list()),
        }
