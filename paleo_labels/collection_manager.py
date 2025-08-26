"""
Collection management system for Phase 3.
Organize labels into projects, expeditions, and hierarchical collections.
"""

import json
import pathlib
from datetime import datetime
from typing import Dict, List, Optional, Set
from uuid import uuid4

import streamlit as st

try:
    from .storage import LabelStorage
    from .schemas import LABEL_SCHEMAS
except ImportError:
    from storage import LabelStorage
    from schemas import LABEL_SCHEMAS


class CollectionManager:
    """Manage hierarchical collections of labels."""
    
    def __init__(self, storage: LabelStorage):
        self.storage = storage
        self.collections_dir = storage.user_data_dir / "collections"
        self.collections_dir.mkdir(exist_ok=True)
    
    def create_collection(self, name: str, collection_type: str = "project", 
                         description: str = "", parent_id: str = None) -> str:
        """Create a new collection."""
        collection_id = str(uuid4())[:8]
        
        collection_data = {
            'id': collection_id,
            'name': name,
            'type': collection_type,  # project, expedition, site, etc.
            'description': description,
            'parent_id': parent_id,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'labels': [],
            'subcollections': [],
            'metadata': {}
        }
        
        collection_file = self.collections_dir / f"{collection_id}.json"
        with open(collection_file, 'w') as f:
            json.dump(collection_data, f, indent=2)
        
        # Update parent if specified
        if parent_id:
            parent = self.load_collection(parent_id)
            if parent and collection_id not in parent['subcollections']:
                parent['subcollections'].append(collection_id)
                self.save_collection(parent)
        
        return collection_id
    
    def load_collection(self, collection_id: str) -> Optional[Dict]:
        """Load a collection by ID."""
        try:
            collection_file = self.collections_dir / f"{collection_id}.json"
            if not collection_file.exists():
                return None
            
            with open(collection_file) as f:
                return json.load(f)
        except Exception:
            return None
    
    def save_collection(self, collection_data: Dict) -> bool:
        """Save collection data."""
        try:
            collection_id = collection_data['id']
            collection_data['modified'] = datetime.now().isoformat()
            
            collection_file = self.collections_dir / f"{collection_id}.json"
            with open(collection_file, 'w') as f:
                json.dump(collection_data, f, indent=2)
            return True
        except Exception:
            return False
    
    def list_collections(self, collection_type: str = None) -> List[Dict]:
        """List all collections, optionally filtered by type."""
        collections = []
        
        try:
            for collection_file in self.collections_dir.glob("*.json"):
                with open(collection_file) as f:
                    collection = json.load(f)
                
                if collection_type is None or collection.get('type') == collection_type:
                    collections.append(collection)
        except Exception:
            pass
        
        # Sort by creation date
        collections.sort(key=lambda x: x.get('created', ''), reverse=True)
        return collections
    
    def add_label_to_collection(self, collection_id: str, label_name: str) -> bool:
        """Add a label to a collection."""
        collection = self.load_collection(collection_id)
        if not collection:
            return False
        
        if label_name not in collection['labels']:
            collection['labels'].append(label_name)
            return self.save_collection(collection)
        
        return True
    
    def remove_label_from_collection(self, collection_id: str, label_name: str) -> bool:
        """Remove a label from a collection."""
        collection = self.load_collection(collection_id)
        if not collection:
            return False
        
        if label_name in collection['labels']:
            collection['labels'].remove(label_name)
            return self.save_collection(collection)
        
        return True
    
    def get_collection_hierarchy(self) -> Dict:
        """Get the full collection hierarchy."""
        all_collections = self.list_collections()
        hierarchy = {}
        
        # Build hierarchy with root collections (no parent)
        for collection in all_collections:
            if not collection.get('parent_id'):
                hierarchy[collection['id']] = collection
                hierarchy[collection['id']]['children'] = []
        
        # Add children to their parents
        for collection in all_collections:
            parent_id = collection.get('parent_id')
            if parent_id and parent_id in hierarchy:
                hierarchy[parent_id]['children'].append(collection)
        
        return hierarchy
    
    def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection."""
        try:
            # Load collection to check for children
            collection = self.load_collection(collection_id)
            if not collection:
                return False
            
            # Remove from parent if exists
            parent_id = collection.get('parent_id')
            if parent_id:
                parent = self.load_collection(parent_id)
                if parent and collection_id in parent['subcollections']:
                    parent['subcollections'].remove(collection_id)
                    self.save_collection(parent)
            
            # Delete file
            collection_file = self.collections_dir / f"{collection_id}.json"
            if collection_file.exists():
                collection_file.unlink()
            
            return True
        except Exception:
            return False
    
    def search_collections(self, query: str) -> List[Dict]:
        """Search collections by name or description."""
        query_lower = query.lower()
        matching_collections = []
        
        for collection in self.list_collections():
            name_match = query_lower in collection.get('name', '').lower()
            desc_match = query_lower in collection.get('description', '').lower()
            
            if name_match or desc_match:
                matching_collections.append(collection)
        
        return matching_collections


def collections_ui():
    """Main UI for collection management."""
    st.header("Collection Management")
    st.write("Organize your labels into projects, expeditions, and sites")
    
    if 'storage' not in st.session_state:
        st.error("Storage not initialized")
        return
    
    # Initialize collection manager
    if 'collection_manager' not in st.session_state:
        st.session_state.collection_manager = CollectionManager(st.session_state.storage)
    
    collection_manager: CollectionManager = st.session_state.collection_manager
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Browse Collections", "Create Collection", "Manage Labels", "Collection Stats"])
    
    with tab1:
        browse_collections_ui(collection_manager)
    
    with tab2:
        create_collection_ui(collection_manager)
    
    with tab3:
        manage_collection_labels_ui(collection_manager)
    
    with tab4:
        collection_stats_ui(collection_manager)


def browse_collections_ui(collection_manager: CollectionManager):
    """UI for browsing collections."""
    st.subheader("Browse Collections")
    
    collections = collection_manager.list_collections()
    
    if not collections:
        st.info("No collections found. Create your first collection!")
        return
    
    # Search collections
    search_query = st.text_input("🔍 Search collections:", placeholder="Enter collection name or description...")
    
    if search_query:
        collections = collection_manager.search_collections(search_query)
        st.write(f"Found {len(collections)} matching collections")
    
    # Filter by type
    collection_types = list(set(c.get('type', 'project') for c in collections))
    selected_type = st.selectbox("Filter by type:", ["All"] + collection_types)
    
    if selected_type != "All":
        collections = [c for c in collections if c.get('type') == selected_type]
    
    # Display collections
    for collection in collections:
        with st.expander(f"📁 {collection['name']} ({collection.get('type', 'project').title()})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Description**: {collection.get('description', 'No description')}")
                st.write(f"**Created**: {collection.get('created', 'Unknown')[:10]}")
                st.write(f"**Labels**: {len(collection.get('labels', []))}")
                st.write(f"**Subcollections**: {len(collection.get('subcollections', []))}")
                
                # Show labels in collection
                labels = collection.get('labels', [])
                if labels:
                    st.write("**Labels in this collection:**")
                    for i, label_name in enumerate(labels[:5]):  # Show first 5
                        st.write(f"• {label_name}")
                    if len(labels) > 5:
                        st.write(f"... and {len(labels) - 5} more")
            
            with col2:
                if st.button(f"🗑️ Delete", key=f"delete_collection_{collection['id']}"):
                    if collection_manager.delete_collection(collection['id']):
                        st.success("Collection deleted!")
                        st.rerun()
                    else:
                        st.error("Error deleting collection")


def create_collection_ui(collection_manager: CollectionManager):
    """UI for creating new collections."""
    st.subheader("Create New Collection")
    
    # Collection details
    col1, col2 = st.columns(2)
    
    with col1:
        collection_name = st.text_input("Collection Name:", placeholder="e.g., Morrison Formation Survey 2024")
        collection_type = st.selectbox("Collection Type:", ["project", "expedition", "site", "formation", "custom"])
    
    with col2:
        collection_description = st.text_area("Description:", placeholder="Describe the purpose and scope of this collection...")
    
    # Parent collection (for hierarchy)
    existing_collections = collection_manager.list_collections()
    parent_options = ["None"] + [f"{c['name']} ({c['id']})" for c in existing_collections]
    
    parent_selection = st.selectbox("Parent Collection (optional):", parent_options)
    parent_id = None
    
    if parent_selection != "None":
        parent_id = parent_selection.split("(")[-1].rstrip(")")
    
    # Create collection
    if st.button("📁 Create Collection", type="primary"):
        if collection_name:
            collection_id = collection_manager.create_collection(
                name=collection_name,
                collection_type=collection_type,
                description=collection_description,
                parent_id=parent_id
            )
            
            st.success(f"Collection '{collection_name}' created with ID: {collection_id}")
            st.rerun()
        else:
            st.warning("Please enter a collection name")


def manage_collection_labels_ui(collection_manager: CollectionManager):
    """UI for managing labels within collections."""
    st.subheader("Manage Collection Labels")
    
    collections = collection_manager.list_collections()
    storage: LabelStorage = st.session_state.storage
    all_labels = storage.list_labels()
    
    if not collections:
        st.info("No collections found. Create a collection first.")
        return
    
    if not all_labels:
        st.info("No labels found. Create some labels first.")
        return
    
    # Select collection
    collection_options = [f"{c['name']} ({c['id']})" for c in collections]
    selected_collection_str = st.selectbox("Select Collection:", collection_options)
    
    if not selected_collection_str:
        return
    
    collection_id = selected_collection_str.split("(")[-1].rstrip(")")
    collection = collection_manager.load_collection(collection_id)
    
    if not collection:
        st.error("Could not load selected collection")
        return
    
    st.write(f"**Managing labels for**: {collection['name']}")
    
    # Show current labels in collection
    current_labels = collection.get('labels', [])
    
    if current_labels:
        st.write(f"**Current labels in collection ({len(current_labels)}):**")
        for label_name in current_labels:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• {label_name}")
            with col2:
                if st.button("❌", key=f"remove_label_{label_name}", help="Remove from collection"):
                    if collection_manager.remove_label_from_collection(collection_id, label_name):
                        st.success(f"Removed {label_name}")
                        st.rerun()
    else:
        st.info("No labels in this collection yet.")
    
    # Add labels to collection
    st.subheader("Add Labels to Collection")
    
    # Filter out labels already in collection
    available_labels = [label for label in all_labels if label not in current_labels]
    
    if available_labels:
        selected_labels = st.multiselect(
            "Choose labels to add:",
            available_labels,
            help="Select one or more labels to add to this collection"
        )
        
        if selected_labels and st.button("➕ Add Selected Labels"):
            added_count = 0
            for label_name in selected_labels:
                if collection_manager.add_label_to_collection(collection_id, label_name):
                    added_count += 1
            
            st.success(f"Added {added_count} labels to collection!")
            st.rerun()
    else:
        st.info("All available labels are already in this collection.")


def collection_stats_ui(collection_manager: CollectionManager):
    """UI for showing collection statistics."""
    st.subheader("Collection Statistics")
    
    collections = collection_manager.list_collections()
    
    if not collections:
        st.info("No collections to analyze.")
        return
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Collections", len(collections))
    
    with col2:
        total_labels = sum(len(c.get('labels', [])) for c in collections)
        st.metric("Total Labels in Collections", total_labels)
    
    with col3:
        collection_types = list(set(c.get('type', 'project') for c in collections))
        st.metric("Collection Types", len(collection_types))
    
    with col4:
        avg_labels = total_labels / len(collections) if collections else 0
        st.metric("Avg Labels per Collection", f"{avg_labels:.1f}")
    
    # Collection breakdown
    st.subheader("Collection Breakdown")
    
    # By type
    type_counts = {}
    for collection in collections:
        collection_type = collection.get('type', 'project')
        type_counts[collection_type] = type_counts.get(collection_type, 0) + 1
    
    st.write("**Collections by Type:**")
    for collection_type, count in sorted(type_counts.items()):
        st.write(f"• {collection_type.title()}: {count}")
    
    # Largest collections
    st.subheader("Largest Collections")
    collections_by_size = sorted(collections, key=lambda x: len(x.get('labels', [])), reverse=True)
    
    for collection in collections_by_size[:5]:  # Top 5
        label_count = len(collection.get('labels', []))
        st.write(f"• **{collection['name']}**: {label_count} labels ({collection.get('type', 'project').title()})")


def get_labels_by_collection(collection_id: str) -> List[str]:
    """Get all labels in a collection."""
    if 'collection_manager' not in st.session_state:
        return []
    
    collection_manager: CollectionManager = st.session_state.collection_manager
    collection = collection_manager.load_collection(collection_id)
    
    if collection:
        return collection.get('labels', [])
    
    return []


def add_label_to_collection_quick(label_name: str, collection_id: str = None) -> bool:
    """Quick function to add a label to a collection."""
    if 'collection_manager' not in st.session_state:
        return False
    
    collection_manager: CollectionManager = st.session_state.collection_manager
    
    if collection_id:
        return collection_manager.add_label_to_collection(collection_id, label_name)
    
    return False