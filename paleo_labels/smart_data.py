"""
Smart Data Engine for Simplified Paleo Labels
Polars-based auto-completion and PBDB integration for intelligent suggestions.
"""

import polars as pl
from collections import defaultdict, Counter
from pathlib import Path
import requests
import io
from datetime import datetime

from simple_storage import SimpleStorage


class SmartDataEngine:
    """Polars-based engine for smart suggestions and data processing."""
    
    def __init__(self, storage: SimpleStorage):
        self.storage = storage
        self._suggestions_cache = None
        self._pbdb_cache = {}
        self._last_cache_refresh = None
        
        # Common paleontology field patterns
        self.field_patterns = {
            'scientific_name': ['genus', 'species', 'family', 'order', 'class', 'phylum'],
            'specimen_number': ['collection_date', 'collector', 'locality', 'field_notes'],
            'locality': ['country', 'state', 'county', 'coordinates', 'formation'],
            'collector': ['collection_date', 'field_notes', 'institution'],
            'formation': ['age', 'geological_age', 'period', 'locality'],
            'genus': ['species', 'family', 'order', 'scientific_name'],
            'species': ['genus', 'family', 'scientific_name'],
            'coordinates': ['locality', 'country', 'state', 'elevation']
        }
        
        # Common field suggestions (fallback)
        self.common_fields = [
            'Scientific Name', 'Genus', 'Species', 'Family', 'Order', 'Class',
            'Specimen Number', 'Locality', 'Formation', 'Age', 'Collector',
            'Collection Date', 'Country', 'State', 'County', 'Institution',
            'Catalog Number', 'Field Notes', 'Coordinates', 'Elevation'
        ]
    
    def _refresh_suggestions_cache(self):
        """Refresh the suggestions cache from all stored labels using Polars."""
        try:
            all_labels_data = []
            
            # Collect all label data
            for label_name in self.storage.list_labels():
                label_data = self.storage.load_label(label_name)
                if label_data:
                    # Flatten label data for analysis
                    for key, value in label_data.items():
                        if isinstance(key, str) and isinstance(value, str):
                            all_labels_data.append({
                                'key': key.strip(),
                                'value': value.strip(),
                                'key_lower': key.strip().lower(),
                                'value_lower': value.strip().lower(),
                                'label_name': label_name
                            })
            
            if not all_labels_data:
                self._suggestions_cache = pl.DataFrame()
                return
            
            # Create Polars DataFrame
            df = pl.DataFrame(all_labels_data)
            
            # Cache the DataFrame for fast lookups
            self._suggestions_cache = df
            self._last_cache_refresh = datetime.now()
            
        except Exception as e:
            print(f"Error refreshing suggestions cache: {e}")
            self._suggestions_cache = pl.DataFrame()
    
    def get_key_suggestions(self, partial_key: str = "", current_fields: list[str] = None, limit: int = 10) -> list[str]:
        """Get intelligent key suggestions using Polars analysis."""
        if self._suggestions_cache is None or self._suggestions_cache.is_empty():
            self._refresh_suggestions_cache()
        
        suggestions = []
        
        # Get learned suggestions from previous labels
        if self._suggestions_cache is not None and not self._suggestions_cache.is_empty():
            try:
                # Filter by partial key match
                partial_lower = partial_key.lower()
                
                if partial_lower:
                    filtered_df = self._suggestions_cache.filter(
                        pl.col('key_lower').str.contains(partial_lower, literal=False)
                    )
                else:
                    filtered_df = self._suggestions_cache
                
                # Get key frequency counts and sort
                key_counts = (filtered_df
                             .group_by('key')
                             .agg(pl.count().alias('count'))
                             .sort('count', descending=True))
                
                if not key_counts.is_empty():
                    learned_suggestions = key_counts.select('key').to_series().to_list()
                    suggestions.extend(learned_suggestions[:limit//2])
                
            except Exception as e:
                print(f"Error getting learned key suggestions: {e}")
        
        # Add pattern-based suggestions if we have current fields
        if current_fields:
            pattern_suggestions = self._get_pattern_suggestions(current_fields)
            suggestions.extend(pattern_suggestions)
        
        # Add common field suggestions if we don't have enough
        common_matches = [
            field for field in self.common_fields
            if partial_key.lower() in field.lower() and field not in suggestions
        ]
        suggestions.extend(common_matches)
        
        # Remove duplicates while preserving order and filter out existing fields
        seen = set()
        current_fields_lower = {f.lower() for f in (current_fields or [])}
        filtered_suggestions = []
        
        for suggestion in suggestions:
            if (suggestion.lower() not in seen and 
                suggestion.lower() not in current_fields_lower):
                seen.add(suggestion.lower())
                filtered_suggestions.append(suggestion)
        
        return filtered_suggestions[:limit]
    
    def get_value_suggestions(self, key: str, partial_value: str = "", limit: int = 10) -> list[str]:
        """Get intelligent value suggestions for a specific key using Polars."""
        if self._suggestions_cache is None or self._suggestions_cache.is_empty():
            self._refresh_suggestions_cache()
        
        suggestions = []
        key_lower = key.lower().strip()
        
        # Get learned value suggestions
        if self._suggestions_cache is not None and not self._suggestions_cache.is_empty():
            try:
                # Filter by key and partial value match
                filtered_df = self._suggestions_cache.filter(
                    pl.col('key_lower') == key_lower
                )
                
                if partial_value:
                    partial_lower = partial_value.lower()
                    filtered_df = filtered_df.filter(
                        pl.col('value_lower').str.contains(partial_lower, literal=False)
                    )
                
                # Get value frequency counts
                if not filtered_df.is_empty():
                    value_counts = (filtered_df
                                   .group_by('value')
                                   .agg(pl.count().alias('count'))
                                   .sort('count', descending=True))
                    
                    if not value_counts.is_empty():
                        learned_suggestions = value_counts.select('value').to_series().to_list()
                        suggestions.extend(learned_suggestions)
                
            except Exception as e:
                print(f"Error getting learned value suggestions: {e}")
        
        # Check for PBDB integration for taxonomic fields
        taxonomic_fields = ['scientific_name', 'genus', 'species', 'family', 'order', 'class', 'phylum']
        if key_lower in taxonomic_fields or any(tax in key_lower for tax in taxonomic_fields):
            pbdb_suggestions = self._get_pbdb_suggestions(key, partial_value)
            suggestions.extend(pbdb_suggestions)
        
        # Remove duplicates while preserving order
        seen = set()
        filtered_suggestions = []
        for suggestion in suggestions:
            if suggestion.lower() not in seen:
                seen.add(suggestion.lower())
                filtered_suggestions.append(suggestion)
        
        return filtered_suggestions[:limit]
    
    def _get_pattern_suggestions(self, current_fields: list[str]) -> list[str]:
        """Get pattern-based field suggestions based on current fields."""
        suggestions = []
        current_lower = {field.lower() for field in current_fields}
        
        for current_field in current_fields:
            field_lower = current_field.lower()
            if field_lower in self.field_patterns:
                for related_field in self.field_patterns[field_lower]:
                    if related_field not in current_lower:
                        # Convert to proper case
                        proper_field = related_field.replace('_', ' ').title()
                        if proper_field not in suggestions:
                            suggestions.append(proper_field)
        
        return suggestions
    
    def _get_pbdb_suggestions(self, key: str, partial_value: str, limit: int = 5) -> list[str]:
        """Get taxonomic suggestions from PBDB API."""
        if not partial_value or len(partial_value) < 2:
            return []
        
        # Use cache to avoid repeated API calls
        cache_key = f"{key}:{partial_value.lower()}"
        if cache_key in self._pbdb_cache:
            return self._pbdb_cache[cache_key]
        
        try:
            # Determine PBDB search parameter based on field
            search_param = "taxon_name"
            key_lower = key.lower()
            
            if "genus" in key_lower:
                search_param = "taxon_name"
            elif "species" in key_lower:
                search_param = "taxon_name"
            elif "family" in key_lower:
                search_param = "taxon_name"
            
            # Make PBDB API request
            url = "https://paleobiodb.org/data1.2/taxa/auto.json"
            params = {
                search_param: partial_value,
                "limit": limit
            }
            
            response = requests.get(url, params=params, timeout=3)
            if response.status_code == 200:
                data = response.json()
                suggestions = []
                
                if "records" in data:
                    for record in data["records"]:
                        if "nam" in record:
                            suggestions.append(record["nam"])
                
                # Cache the results
                self._pbdb_cache[cache_key] = suggestions
                return suggestions
            
        except Exception as e:
            print(f"PBDB API error: {e}")
        
        return []
    
    def process_csv_data(self, csv_content: bytes) -> list[dict[str, str]]:
        """Process CSV data using Polars for batch label creation."""
        try:
            # Read CSV with Polars
            df = pl.read_csv(io.BytesIO(csv_content))
            
            # Convert to list of dictionaries
            labels_data = []
            for row in df.iter_rows(named=True):
                # Convert all values to strings and clean
                label_data = {
                    str(key): str(value).strip() if value is not None else ""
                    for key, value in row.items()
                }
                labels_data.append(label_data)
            
            return labels_data
            
        except Exception as e:
            print(f"Error processing CSV data: {e}")
            return []
    
    def analyze_field_patterns(self) -> dict[str, any]:
        """Analyze patterns in stored labels using Polars for insights."""
        if self._suggestions_cache is None or self._suggestions_cache.is_empty():
            self._refresh_suggestions_cache()
        
        if self._suggestions_cache is None or self._suggestions_cache.is_empty():
            return {}
        
        try:
            analysis = {}
            
            # Most common fields
            field_counts = (self._suggestions_cache
                           .group_by('key')
                           .agg(pl.count().alias('count'))
                           .sort('count', descending=True))
            
            if not field_counts.is_empty():
                analysis['most_common_fields'] = field_counts.head(10).to_dicts()
            
            # Field co-occurrence patterns
            # Group by label_name to find fields that appear together
            label_fields = (self._suggestions_cache
                           .group_by('label_name')
                           .agg(pl.col('key').alias('fields')))
            
            # This could be extended for more sophisticated pattern analysis
            analysis['total_labels'] = len(self.storage.list_labels())
            analysis['total_unique_fields'] = self._suggestions_cache.select('key').n_unique()
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing field patterns: {e}")
            return {}
    
    def get_smart_next_fields(self, current_fields: dict[str, str]) -> list[str]:
        """Get smart suggestions for what fields to add next based on current data."""
        suggestions = []
        
        # Pattern-based suggestions
        pattern_suggestions = self._get_pattern_suggestions(list(current_fields.keys()))
        suggestions.extend(pattern_suggestions[:3])
        
        # Frequency-based suggestions from similar labels
        if self._suggestions_cache is not None and not self._suggestions_cache.is_empty():
            try:
                current_keys = set(k.lower() for k in current_fields.keys())
                
                # Find labels that have any of our current fields
                similar_labels = self._suggestions_cache.filter(
                    pl.col('key_lower').is_in(list(current_keys))
                )
                
                if not similar_labels.is_empty():
                    # Get other fields from those labels
                    other_fields = (similar_labels
                                   .filter(~pl.col('key_lower').is_in(list(current_keys)))
                                   .group_by('key')
                                   .agg(pl.count().alias('count'))
                                   .sort('count', descending=True))
                    
                    if not other_fields.is_empty():
                        similar_suggestions = other_fields.select('key').to_series().to_list()
                        suggestions.extend(similar_suggestions[:3])
                
            except Exception as e:
                print(f"Error getting smart next fields: {e}")
        
        # Remove duplicates while preserving order
        seen = set()
        filtered_suggestions = []
        for suggestion in suggestions:
            if suggestion.lower() not in seen:
                seen.add(suggestion.lower())
                filtered_suggestions.append(suggestion)
        
        return filtered_suggestions[:5]
    
    def detect_label_type(self, fields: dict[str, str]) -> str:
        """Under-the-hood schema detection based on field patterns."""
        field_keys = {k.lower() for k in fields.keys()}
        
        # Define type indicators
        type_indicators = {
            'Specimen': {'specimen_number', 'catalog_number', 'collection_date', 'collector'},
            'Taxonomy': {'scientific_name', 'genus', 'species', 'family', 'order', 'class'},
            'Locality': {'locality', 'country', 'state', 'county', 'coordinates', 'formation'},
            'Collection': {'expedition', 'project', 'institution', 'collection'},
            'Locale': {'formation', 'age', 'geological_age', 'period', 'era'}
        }
        
        # Score each type based on field matches
        type_scores = {}
        for label_type, indicators in type_indicators.items():
            score = len(field_keys.intersection(indicators))
            if score > 0:
                type_scores[label_type] = score
        
        # Return the type with highest score, or 'General' as fallback
        if type_scores:
            return max(type_scores, key=type_scores.get)
        
        return 'General'


def initialize_smart_data(storage: SimpleStorage) -> SmartDataEngine:
    """Initialize the smart data engine."""
    return SmartDataEngine(storage)