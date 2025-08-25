"""
Local data storage system for paleontological labels and styles.
Handles user data directory management and label metadata.
"""

import json
import pathlib
import uuid
from datetime import datetime

try:
    import platformdirs
except ImportError:
    import os

    class platformdirs:
        @staticmethod
        def user_data_dir(app_name):
            return os.path.expanduser(f"~/.{app_name}")


import toml


class LabelStorage:
    def __init__(self, app_name: str = "paleo-labels"):
        self.app_name = app_name
        self._user_data_dir = None
        self._labels_dir = None
        self._ensure_directories()

    @property
    def user_data_dir(self) -> pathlib.Path:
        if self._user_data_dir is None:
            self._user_data_dir = pathlib.Path(
                platformdirs.user_data_dir(self.app_name)
            )
        return self._user_data_dir

    @property
    def labels_dir(self) -> pathlib.Path:
        if self._labels_dir is None:
            project_root = pathlib.Path(__file__).parent.parent
            self._labels_dir = project_root / "labels"
        return self._labels_dir

    @property
    def styles_dir(self) -> pathlib.Path:
        return self.user_data_dir / "styles"

    @property
    def metadata_dir(self) -> pathlib.Path:
        return self.user_data_dir / "metadata"

    def _ensure_directories(self) -> None:
        directories = [
            self.user_data_dir,
            self.labels_dir,
            self.styles_dir,
            self.metadata_dir,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def save_label(
        self, label_data: dict, label_type: str, name: str | None = None
    ) -> str:
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            name = f"{label_type.lower()}_{timestamp}_{unique_id}"
        else:
            unique_id = str(uuid.uuid4())[:8]
            name = f"{name}_{unique_id}"

        label_file = self.labels_dir / f"{name}.json"

        with open(label_file, "w") as f:
            json.dump(label_data, f, indent=2)

        metadata = {
            "name": name,
            "label_type": label_type,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "connections": [],
        }
        self._save_metadata(name, metadata)

        return name

    def load_label(self, name: str) -> dict | None:
        label_file = self.labels_dir / f"{name}.json"
        if not label_file.exists():
            label_file_toml = self.labels_dir / f"{name}.toml"
            if label_file_toml.exists():
                with open(label_file_toml) as f:
                    return toml.load(f)
            return None

        with open(label_file) as f:
            return json.load(f)

    def save_style(self, style_data: dict, name: str | None = None) -> str:
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"style_{timestamp}"

        style_file = self.styles_dir / f"{name}.toml"

        with open(style_file, "w") as f:
            toml.dump(style_data, f)

        return name

    def load_style(self, name: str) -> dict | None:
        style_file = self.styles_dir / f"{name}.toml"
        if not style_file.exists():
            return None

        with open(style_file) as f:
            return toml.load(f)

    def list_labels(self) -> list[str]:
        json_labels = [f.stem for f in self.labels_dir.glob("*.json")]
        toml_labels = [f.stem for f in self.labels_dir.glob("*.toml")]
        return sorted(list(set(json_labels + toml_labels)))

    def list_styles(self) -> list[str]:
        return [f.stem for f in self.styles_dir.glob("*.toml")]

    def delete_label(self, name: str) -> bool:
        label_file_json = self.labels_dir / f"{name}.json"
        label_file_toml = self.labels_dir / f"{name}.toml"
        metadata_file = self.metadata_dir / f"{name}.json"

        deleted = False
        if label_file_json.exists():
            label_file_json.unlink()
            deleted = True
        elif label_file_toml.exists():
            label_file_toml.unlink()
            deleted = True

        if metadata_file.exists():
            metadata_file.unlink()

        return deleted

    def delete_style(self, name: str) -> bool:
        style_file = self.styles_dir / f"{name}.toml"
        if style_file.exists():
            style_file.unlink()
            return True
        return False

    def _save_metadata(self, name: str, metadata: dict) -> None:
        metadata_file = self.metadata_dir / f"{name}.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def get_metadata(self, name: str) -> dict | None:
        metadata_file = self.metadata_dir / f"{name}.json"
        if not metadata_file.exists():
            return None

        with open(metadata_file) as f:
            return json.load(f)

    def update_metadata(self, name: str, updates: dict) -> None:
        metadata = self.get_metadata(name) or {}
        metadata.update(updates)
        metadata["modified"] = datetime.now().isoformat()
        self._save_metadata(name, metadata)

    def add_label_connection(
        self, label_name: str, connected_label: str
    ) -> None:
        metadata = self.get_metadata(label_name) or {
            "name": label_name,
            "connections": [],
            "created": datetime.now().isoformat(),
        }

        if connected_label not in metadata["connections"]:
            metadata["connections"].append(connected_label)
            self.update_metadata(label_name, metadata)

    def remove_label_connection(
        self, label_name: str, connected_label: str
    ) -> None:
        metadata = self.get_metadata(label_name)
        if metadata and connected_label in metadata.get("connections", []):
            metadata["connections"].remove(connected_label)
            self.update_metadata(label_name, metadata)

    def get_connected_labels(self, label_name: str) -> list[str]:
        metadata = self.get_metadata(label_name)
        return metadata.get("connections", []) if metadata else []

    def search_labels(
        self, query: str, label_type: str | None = None
    ) -> list[dict]:
        results = []
        query_lower = query.lower()

        for label_name in self.list_labels():
            label_data = self.load_label(label_name)
            metadata = self.get_metadata(label_name)

            if not label_data:
                continue

            if label_type and metadata:
                if metadata.get("label_type") != label_type:
                    continue

            label_text = " ".join(str(v) for v in label_data.values()).lower()
            if query_lower in label_text or query_lower in label_name.lower():
                results.append(
                    {
                        "name": label_name,
                        "data": label_data,
                        "metadata": metadata or {},
                    }
                )

        return results

    def get_recent_labels(self, limit: int = 10) -> list[dict]:
        labels_with_metadata = []

        for label_name in self.list_labels():
            metadata = self.get_metadata(label_name)
            if metadata:
                labels_with_metadata.append(
                    {"name": label_name, "metadata": metadata}
                )

        labels_with_metadata.sort(
            key=lambda x: x["metadata"].get("modified", ""), reverse=True
        )

        return labels_with_metadata[:limit]
