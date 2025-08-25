"""
Smart auto-completion system for Phase 3.
Learns from previous labels to suggest keys and values for faster label creation.
"""

from collections import Counter, defaultdict

import streamlit as st

try:
    from .schemas import LABEL_SCHEMAS, get_schema_for_label_type
    from .storage import LabelStorage
except ImportError:
    from schemas import get_schema_for_label_type
    from storage import LabelStorage


class AutoCompleteEngine:
    """Engine for learning from previous labels and providing suggestions."""

    def __init__(self, storage: LabelStorage):
        self.storage = storage
        self._key_suggestions_cache = None
        self._value_suggestions_cache = None
        self._last_refresh = None

    def _refresh_cache(self):
        """Refresh the auto-completion cache by analyzing all saved labels."""
        key_frequency = Counter()
        value_suggestions = defaultdict(lambda: Counter())

        # Analyze all saved labels
        for label_name in self.storage.list_labels():
            try:
                label_data = self.storage.load_label(label_name)
                if not label_data:
                    continue

                for key, value in label_data.items():
                    if isinstance(key, str) and isinstance(value, str):
                        # Normalize keys and values
                        normalized_key = key.strip().lower()
                        normalized_value = value.strip()

                        if normalized_key and normalized_value:
                            key_frequency[key.strip()] += 1
                            value_suggestions[normalized_key][
                                normalized_value
                            ] += 1

            except Exception:
                continue

        self._key_suggestions_cache = key_frequency
        self._value_suggestions_cache = value_suggestions

    def get_key_suggestions(
        self, partial_key: str = "", limit: int = 10
    ) -> list[str]:
        """Get suggested keys based on previous usage and current input."""
        if self._key_suggestions_cache is None:
            self._refresh_cache()

        partial_lower = partial_key.lower()

        # Filter keys that match partial input
        matching_keys = [
            key
            for key in self._key_suggestions_cache.keys()
            if partial_lower in key.lower()
        ]

        # Sort by frequency (most used first)
        matching_keys.sort(
            key=lambda k: self._key_suggestions_cache[k], reverse=True
        )

        return matching_keys[:limit]

    def get_value_suggestions(
        self, key: str, partial_value: str = "", limit: int = 10
    ) -> list[str]:
        """Get suggested values for a specific key based on previous usage."""
        if self._value_suggestions_cache is None:
            self._refresh_cache()

        normalized_key = key.strip().lower()
        partial_lower = partial_value.lower()

        if normalized_key not in self._value_suggestions_cache:
            return []

        # Get values for this key
        value_counter = self._value_suggestions_cache[normalized_key]

        # Filter values that match partial input
        matching_values = [
            value
            for value in value_counter.keys()
            if partial_lower in value.lower()
        ]

        # Sort by frequency (most used first)
        matching_values.sort(key=lambda v: value_counter[v], reverse=True)

        return matching_values[:limit]

    def get_combined_suggestions(
        self, label_type: str, limit: int = 20
    ) -> dict[str, list[str]]:
        """Get combined suggestions including schema fields and learned keys."""
        suggestions = {}

        # Get schema-based suggestions if available
        if label_type != "General":
            schema = get_schema_for_label_type(label_type)
            schema_keys = list(schema.keys())

            # Add aliases
            for field, config in schema.items():
                schema_keys.extend(config.get("aliases", []))

            suggestions["schema"] = schema_keys

        # Get learned suggestions from previous labels
        learned_keys = self.get_key_suggestions(limit=limit)
        suggestions["learned"] = learned_keys

        return suggestions

    def get_smart_field_suggestions(
        self, current_data: dict[str, str], label_type: str
    ) -> dict[str, str]:
        """Get smart suggestions for next fields based on current label data."""
        suggestions = {}

        # Analyze patterns in existing labels to suggest what fields typically go together
        if self._value_suggestions_cache is None:
            self._refresh_cache()

        # Look for common field combinations
        current_keys = set(k.lower() for k in current_data)

        # Simple pattern matching - if user has certain keys, suggest related ones
        field_patterns = {
            "scientific_name": ["genus", "family", "order", "class", "phylum"],
            "specimen_number": ["collection_date", "collector", "locality"],
            "locality": ["country", "state", "county", "coordinates"],
            "collector": ["collection_date", "field_notes"],
            "formation": ["age", "geological_age", "period"],
        }

        for current_key in current_keys:
            if current_key in field_patterns:
                for suggested_key in field_patterns[current_key]:
                    if suggested_key not in current_keys:
                        # Get the most common value for this field
                        common_values = self.get_value_suggestions(
                            suggested_key, limit=1
                        )
                        if common_values:
                            suggestions[suggested_key] = common_values[0]

        return suggestions


def render_autocomplete_text_input(
    label: str,
    value: str = "",
    key: str = None,
    autocomplete_engine: AutoCompleteEngine = None,
    field_type: str = "key",
    related_key: str = None,
    **kwargs,
) -> str:
    """
    Render a text input with auto-completion suggestions.

    Args:
        label: Input label
        value: Current value
        key: Streamlit key
        autocomplete_engine: Auto-completion engine
        field_type: "key" or "value"
        related_key: For value suggestions, the associated key
    """

    # Regular text input
    user_input = st.text_input(label, value=value, key=key, **kwargs)

    if autocomplete_engine and user_input:
        # Get suggestions based on type
        if field_type == "key":
            suggestions = autocomplete_engine.get_key_suggestions(
                user_input, limit=5
            )
        elif field_type == "value" and related_key:
            suggestions = autocomplete_engine.get_value_suggestions(
                related_key, user_input, limit=5
            )
        else:
            suggestions = []

        # Show suggestions if available
        if suggestions:
            with st.expander("💡 Suggestions", expanded=False):
                for suggestion in suggestions:
                    if st.button(
                        f"📝 {suggestion}", key=f"suggest_{key}_{suggestion}"
                    ):
                        # Update session state to reflect the chosen suggestion
                        st.session_state[key] = suggestion
                        st.rerun()

    return user_input


def render_smart_suggestions_panel(
    current_data: dict[str, str],
    label_type: str,
    autocomplete_engine: AutoCompleteEngine,
):
    """
    Render a panel showing smart suggestions for next fields to add.
    """
    smart_suggestions = autocomplete_engine.get_smart_field_suggestions(
        current_data, label_type
    )

    if smart_suggestions:
        st.subheader("🔮 Smart Suggestions")
        st.write("Based on your current fields, you might want to add:")

        for suggested_key, suggested_value in smart_suggestions.items():
            col1, col2, col3 = st.columns([2, 3, 1])

            with col1:
                st.write(f"**{suggested_key}**")
            with col2:
                st.write(f"→ {suggested_value}")
            with col3:
                if st.button("➕", key=f"add_suggestion_{suggested_key}"):
                    # Add this field to the current manual entry
                    add_suggested_field_to_manual_entry(
                        suggested_key, suggested_value
                    )


def add_suggested_field_to_manual_entry(key: str, value: str):
    """Add a suggested field to the current manual entry session."""
    if "num_rows" not in st.session_state:
        st.session_state.num_rows = 1

    # Add new row with the suggested field
    new_index = st.session_state.num_rows
    st.session_state[f"key_{new_index}"] = key
    st.session_state[f"value_{new_index}"] = value
    st.session_state.num_rows += 1

    st.success(f"Added field: {key} = {value}")
    st.rerun()


def show_autocomplete_stats(autocomplete_engine: AutoCompleteEngine):
    """Show statistics about the auto-completion system."""
    if autocomplete_engine._key_suggestions_cache is None:
        autocomplete_engine._refresh_cache()

    key_count = len(autocomplete_engine._key_suggestions_cache)
    total_labels = len(autocomplete_engine.storage.list_labels())

    st.metric("Learned Fields", key_count)
    st.metric("Total Labels Analyzed", total_labels)

    if key_count > 0:
        # Show most common fields
        top_fields = autocomplete_engine.get_key_suggestions(limit=5)
        st.write("**Most Used Fields:**")
        for field in top_fields:
            frequency = autocomplete_engine._key_suggestions_cache[field]
            st.write(f"• {field} (used {frequency} times)")


def initialize_autocomplete_engine() -> AutoCompleteEngine:
    """Initialize the auto-completion engine in session state."""
    if "autocomplete_engine" not in st.session_state:
        if "storage" in st.session_state:
            st.session_state.autocomplete_engine = AutoCompleteEngine(
                st.session_state.storage
            )
        else:
            return None

    return st.session_state.autocomplete_engine
