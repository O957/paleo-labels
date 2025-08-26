"""
Label relationship system for managing connections between different label types.
Handles validation and visualization of label connections.
"""

try:
    from .schemas import LABEL_SCHEMAS
    from .storage import LabelStorage
except ImportError:
    from schemas import LABEL_SCHEMAS
    from storage import LabelStorage


class LabelRelationshipManager:
    VALID_CONNECTIONS = {
        "Collection": ["Locale", "Expedition", "Specimen", "Specimens"],
        "Specimen": ["Taxonomy", "Locale", "Collection", "Expedition"],
        "Specimens": ["Taxonomy", "Locale", "Collection", "Expedition"],
        "Taxonomy": ["Specimen", "Specimens"],
        "Expedition": ["Locale", "Collection", "Specimen", "Specimens"],
        "Locale": ["Collection", "Expedition", "Specimen", "Specimens"],
        "General": list(LABEL_SCHEMAS.keys()),
    }

    def __init__(self, storage: LabelStorage):
        self.storage = storage

    def can_connect(self, from_type: str, to_type: str) -> bool:
        return to_type in self.VALID_CONNECTIONS.get(from_type, [])

    def connect_labels(self, label1: str, label2: str) -> bool:
        metadata1 = self.storage.get_metadata(label1)
        metadata2 = self.storage.get_metadata(label2)

        if not metadata1 or not metadata2:
            return False

        type1 = metadata1.get("label_type")
        type2 = metadata2.get("label_type")

        if not self.can_connect(type1, type2) and not self.can_connect(
            type2, type1
        ):
            return False

        self.storage.add_label_connection(label1, label2)
        self.storage.add_label_connection(label2, label1)

        return True

    def disconnect_labels(self, label1: str, label2: str) -> None:
        self.storage.remove_label_connection(label1, label2)
        self.storage.remove_label_connection(label2, label1)

    def get_connections(self, label_name: str) -> list[dict]:
        connected_names = self.storage.get_connected_labels(label_name)
        connections = []

        for connected_name in connected_names:
            metadata = self.storage.get_metadata(connected_name)
            if metadata:
                connections.append(
                    {
                        "name": connected_name,
                        "type": metadata.get("label_type", "Unknown"),
                        "created": metadata.get("created"),
                        "modified": metadata.get("modified"),
                    }
                )

        return connections

    def get_connection_suggestions(self, label_name: str) -> list[dict]:
        metadata = self.storage.get_metadata(label_name)
        if not metadata:
            return []

        label_type = metadata.get("label_type")
        valid_types = self.VALID_CONNECTIONS.get(label_type, [])

        suggestions = []
        current_connections = set(
            self.storage.get_connected_labels(label_name)
        )

        for other_label in self.storage.list_labels():
            if other_label == label_name or other_label in current_connections:
                continue

            other_metadata = self.storage.get_metadata(other_label)
            if not other_metadata:
                continue

            other_type = other_metadata.get("label_type")
            if other_type in valid_types:
                suggestions.append(
                    {
                        "name": other_label,
                        "type": other_type,
                        "created": other_metadata.get("created"),
                        "modified": other_metadata.get("modified"),
                    }
                )

        suggestions.sort(key=lambda x: x.get("modified", ""), reverse=True)
        return suggestions

    def validate_connections(self, label_name: str) -> list[str]:
        errors = []
        metadata = self.storage.get_metadata(label_name)

        if not metadata:
            return ["Label metadata not found"]

        label_type = metadata.get("label_type")
        connected_labels = self.storage.get_connected_labels(label_name)

        for connected_label in connected_labels:
            connected_metadata = self.storage.get_metadata(connected_label)

            if not connected_metadata:
                errors.append(f"Connected label '{connected_label}' not found")
                continue

            connected_type = connected_metadata.get("label_type")

            if not self.can_connect(label_type, connected_type):
                errors.append(
                    f"Invalid connection: {label_type} cannot connect to {connected_type}"
                )

        return errors

    def get_relationship_tree(
        self, root_label: str, max_depth: int = 3
    ) -> dict:
        visited = set()

        def build_tree(label_name: str, depth: int) -> dict:
            if depth > max_depth or label_name in visited:
                return {"name": label_name, "children": []}

            visited.add(label_name)
            metadata = self.storage.get_metadata(label_name)
            label_type = (
                metadata.get("label_type", "Unknown")
                if metadata
                else "Unknown"
            )

            children = []
            for connected_label in self.storage.get_connected_labels(
                label_name
            ):
                if connected_label not in visited:
                    children.append(build_tree(connected_label, depth + 1))

            return {
                "name": label_name,
                "type": label_type,
                "children": children,
                "metadata": metadata,
            }

        return build_tree(root_label, 0)

    def find_path(
        self, start_label: str, end_label: str, max_depth: int = 5
    ) -> list[str] | None:
        if start_label == end_label:
            return [start_label]

        visited = set()
        queue = [(start_label, [start_label])]

        while queue:
            current_label, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            if current_label in visited:
                continue

            visited.add(current_label)

            for connected_label in self.storage.get_connected_labels(
                current_label
            ):
                if connected_label == end_label:
                    return path + [connected_label]

                if connected_label not in visited:
                    queue.append((connected_label, path + [connected_label]))

        return None

    def get_orphaned_labels(self) -> list[dict]:
        orphaned = []

        for label_name in self.storage.list_labels():
            connections = self.storage.get_connected_labels(label_name)
            metadata = self.storage.get_metadata(label_name)

            if not connections and metadata:
                orphaned.append(
                    {
                        "name": label_name,
                        "type": metadata.get("label_type", "Unknown"),
                        "created": metadata.get("created"),
                        "modified": metadata.get("modified"),
                    }
                )

        return orphaned

    def get_connection_stats(self) -> dict:
        stats = {
            "total_labels": len(self.storage.list_labels()),
            "connected_labels": 0,
            "orphaned_labels": 0,
            "total_connections": 0,
            "connections_by_type": {},
        }

        for label_name in self.storage.list_labels():
            connections = self.storage.get_connected_labels(label_name)
            metadata = self.storage.get_metadata(label_name)

            if connections:
                stats["connected_labels"] += 1
                stats["total_connections"] += len(connections)
            else:
                stats["orphaned_labels"] += 1

            if metadata:
                label_type = metadata.get("label_type", "Unknown")
                if label_type not in stats["connections_by_type"]:
                    stats["connections_by_type"][label_type] = 0
                stats["connections_by_type"][label_type] += len(connections)

        stats["total_connections"] //= 2

        return stats
