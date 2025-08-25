"""
Advanced database queries for Phase 3.
Complex PBDB queries with multiple filters and advanced search capabilities.
"""

from typing import Dict, List, Optional, Set, Tuple

import streamlit as st

try:
    import polars as pl
except ImportError:
    pl = None

try:
    from .paleobiology import PaleobiologyDatabase
except ImportError:
    from paleobiology import PaleobiologyDatabase


def advanced_database_queries_ui():
    """
    Main UI for advanced database queries.
    """
    st.header("Advanced Database Queries")
    st.write("Search the paleobiology database with complex filters")
    
    if 'paleodb' not in st.session_state:
        st.error("Database not initialized")
        return
    
    paleodb: PaleobiologyDatabase = st.session_state.paleodb
    
    if not paleodb.is_available():
        st.warning("Paleobiology database not available. Please ensure the data file exists.")
        return
    
    # Query builder tabs
    tab1, tab2, tab3 = st.tabs(["Query Builder", "Saved Queries", "Export Results"])
    
    with tab1:
        query_builder_ui(paleodb)
    
    with tab2:
        saved_queries_ui()
    
    with tab3:
        export_results_ui()


def query_builder_ui(paleodb: PaleobiologyDatabase):
    """
    Interactive query builder interface.
    """
    st.subheader("Query Builder")
    
    # Initialize query state
    if 'current_query' not in st.session_state:
        st.session_state.current_query = {
            'taxonomic_filters': {},
            'geographic_filters': {},
            'temporal_filters': {},
            'text_search': ''
        }
    
    query = st.session_state.current_query
    
    # Taxonomic filters
    st.subheader("🧬 Taxonomic Filters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        kingdom_filter = st.selectbox(
            "Kingdom:",
            [""] + paleodb.get_kingdom_list()[:50],  # Limit for performance
            key="kingdom_filter"
        )
        
        phylum_filter = st.selectbox(
            "Phylum:",
            [""] + paleodb.get_phylum_list()[:100],
            key="phylum_filter"
        )
        
        class_filter = st.selectbox(
            "Class:",
            [""] + paleodb.get_class_list()[:100],
            key="class_filter"
        )
    
    with col2:
        order_filter = st.selectbox(
            "Order:",
            [""] + paleodb.get_order_list()[:100],
            key="order_filter"
        )
        
        family_filter = st.selectbox(
            "Family:",
            [""] + paleodb.get_family_list()[:100],
            key="family_filter"
        )
        
        genus_filter = st.selectbox(
            "Genus:",
            [""] + paleodb.get_genus_list()[:100],
            key="genus_filter"
        )
    
    # Update query state
    query['taxonomic_filters'] = {
        'kingdom': kingdom_filter,
        'phylum': phylum_filter,
        'class': class_filter,
        'order': order_filter,
        'family': family_filter,
        'genus': genus_filter
    }
    
    # Geographic filters
    st.subheader("🌍 Geographic Filters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        formation_filter = st.selectbox(
            "Formation:",
            [""] + paleodb.get_formation_list()[:100],
            key="formation_filter"
        )
    
    with col2:
        locality_filter = st.selectbox(
            "Locality:",
            [""] + paleodb.get_locality_list()[:100],
            key="locality_filter"
        )
    
    query['geographic_filters'] = {
        'formation': formation_filter,
        'locality': locality_filter
    }
    
    # Text search
    st.subheader("🔍 Text Search")
    
    text_search = st.text_input(
        "Search in species names:",
        help="Search for species names containing this text",
        key="text_search"
    )
    
    query['text_search'] = text_search
    
    # Query execution
    st.subheader("Execute Query")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        result_limit = st.number_input(
            "Max Results:",
            min_value=1,
            max_value=1000,
            value=100,
            help="Limit results for performance"
        )
    
    with col2:
        if st.button("🔍 Execute Query", type="primary"):
            execute_advanced_query(paleodb, query, result_limit)
    
    with col3:
        if st.button("🗑️ Clear Filters"):
            clear_query_filters()


def execute_advanced_query(paleodb: PaleobiologyDatabase, query: Dict, limit: int):
    """
    Execute the advanced query with all filters.
    """
    if pl is None:
        st.error("Polars is required for advanced queries")
        return
    
    with st.spinner("Executing query..."):
        try:
            data = paleodb._load_data()
            if data is None or data.is_empty():
                st.warning("No data available")
                return
            
            filtered_data = data
            
            # Apply taxonomic filters
            for rank, value in query['taxonomic_filters'].items():
                if value:
                    rank_columns = [col for col in data.columns if rank.lower() in col.lower()]
                    if rank_columns:
                        filtered_data = filtered_data.filter(
                            pl.col(rank_columns[0]).str.contains(f"(?i){value}")
                        )
            
            # Apply geographic filters
            for filter_type, value in query['geographic_filters'].items():
                if value:
                    if filter_type == 'formation':
                        formation_columns = [col for col in data.columns 
                                           if 'formation' in col.lower() or 'fm' in col.lower()]
                        if formation_columns:
                            filtered_data = filtered_data.filter(
                                pl.col(formation_columns[0]).str.contains(f"(?i){value}")
                            )
                    elif filter_type == 'locality':
                        locality_columns = [col for col in data.columns 
                                          if any(term in col.lower() for term in ['locality', 'location', 'site'])]
                        if locality_columns:
                            filtered_data = filtered_data.filter(
                                pl.col(locality_columns[0]).str.contains(f"(?i){value}")
                            )
            
            # Apply text search
            if query['text_search']:
                species_columns = [col for col in data.columns 
                                 if 'species' in col.lower() or 'accepted_name' in col.lower()]
                if species_columns:
                    filtered_data = filtered_data.filter(
                        pl.col(species_columns[0]).str.contains(f"(?i){query['text_search']}")
                    )
            
            # Limit results
            if len(filtered_data) > limit:
                filtered_data = filtered_data.head(limit)
                st.warning(f"Results limited to first {limit} records")
            
            # Display results
            if len(filtered_data) == 0:
                st.info("No results found for your query")
            else:
                st.success(f"Found {len(filtered_data)} results")
                
                # Store results in session state
                st.session_state.query_results = filtered_data
                
                # Display results table
                display_query_results(filtered_data)
                
        except Exception as e:
            st.error(f"Query execution failed: {str(e)}")


def display_query_results(results):
    """
    Display query results in a user-friendly format.
    """
    st.subheader("Query Results")
    
    # Convert to pandas for display
    results_df = results.to_pandas()
    
    # Show key columns first
    key_columns = ['accepted_name', 'genus', 'family', 'order', 'class', 'phylum']
    display_columns = []
    
    for col in key_columns:
        matching_cols = [c for c in results_df.columns if col in c.lower()]
        if matching_cols:
            display_columns.append(matching_cols[0])
    
    # Add other interesting columns
    other_columns = [c for c in results_df.columns 
                    if any(term in c.lower() for term in ['formation', 'locality', 'age', 'period'])
                    and c not in display_columns]
    display_columns.extend(other_columns[:5])  # Limit additional columns
    
    if display_columns:
        st.dataframe(results_df[display_columns])
    else:
        st.dataframe(results_df.head())
    
    # Quick actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Import to Multi-Label Session"):
            import_results_to_multi_session(results)
    
    with col2:
        if st.button("💾 Save Query"):
            save_current_query()
    
    with col3:
        if st.button("📄 Export Results"):
            export_query_results(results)


def import_results_to_multi_session(results):
    """
    Import query results to the multi-label session.
    """
    try:
        results_df = results.to_pandas()
        
        # Initialize multi-labels if not exists
        if 'multi_labels' not in st.session_state:
            st.session_state.multi_labels = []
        
        imported_count = 0
        
        for _, row in results_df.iterrows():
            # Create label data from row
            label_data = {}
            
            # Map common fields
            field_mapping = {
                'accepted_name': 'scientific_name',
                'genus': 'genus', 
                'family': 'family',
                'order': 'order',
                'class': 'class',
                'phylum': 'phylum'
            }
            
            for db_field, label_field in field_mapping.items():
                matching_cols = [c for c in results_df.columns if db_field in c.lower()]
                if matching_cols and pd.notna(row[matching_cols[0]]):
                    label_data[label_field] = str(row[matching_cols[0]])
            
            # Add other relevant fields
            for col in results_df.columns:
                if any(term in col.lower() for term in ['formation', 'locality', 'age', 'period']):
                    if pd.notna(row[col]):
                        clean_field_name = col.replace('_', ' ').title()
                        label_data[clean_field_name] = str(row[col])
            
            if label_data:
                # Generate name from scientific name if available
                name = label_data.get('scientific_name', f"Query_Result_{imported_count + 1}")
                
                new_label = {
                    'id': len(st.session_state.multi_labels),
                    'type': 'Taxonomy',  # Default to taxonomy type for database imports
                    'data': label_data,
                    'name': name
                }
                
                st.session_state.multi_labels.append(new_label)
                imported_count += 1
        
        st.success(f"Imported {imported_count} results to Multi-Label Session!")
        st.info("Switch to Batch Processing > Multi-Label Session to edit them.")
        
    except Exception as e:
        st.error(f"Import failed: {str(e)}")


def saved_queries_ui():
    """
    UI for managing saved queries.
    """
    st.subheader("Saved Queries")
    st.info("Saved queries functionality coming soon!")


def export_results_ui():
    """
    UI for exporting query results.
    """
    st.subheader("Export Results")
    
    if 'query_results' not in st.session_state:
        st.info("No query results to export. Execute a query first.")
        return
    
    results = st.session_state.query_results
    
    st.write(f"**Current Results**: {len(results)} records")
    
    export_format = st.selectbox(
        "Export Format:",
        ["CSV", "JSON", "Labels (Multi-Session)"]
    )
    
    if st.button("📤 Export"):
        if export_format == "CSV":
            csv_data = results.to_pandas().to_csv(index=False)
            st.download_button(
                "📄 Download CSV",
                csv_data,
                "query_results.csv",
                "text/csv"
            )
        elif export_format == "JSON":
            json_data = results.to_pandas().to_json(orient='records', indent=2)
            st.download_button(
                "📄 Download JSON", 
                json_data,
                "query_results.json",
                "application/json"
            )
        elif export_format == "Labels (Multi-Session)":
            import_results_to_multi_session(results)


def clear_query_filters():
    """
    Clear all query filters.
    """
    filter_keys = [
        'kingdom_filter', 'phylum_filter', 'class_filter', 'order_filter',
        'family_filter', 'genus_filter', 'formation_filter', 'locality_filter',
        'text_search'
    ]
    
    for key in filter_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    st.session_state.current_query = {
        'taxonomic_filters': {},
        'geographic_filters': {},
        'temporal_filters': {},
        'text_search': ''
    }
    
    st.success("Filters cleared!")
    st.rerun()


def save_current_query():
    """
    Save the current query for later use.
    """
    st.info("Save query functionality coming soon!")