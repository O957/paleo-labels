"""
Simplified Storage System for Paleo Labels
Streamlined file management with essential functionality preserved.
"""

import json
import tomli
import tomli_w
from datetime import datetime
from pathlib import Path


class SimpleStorage:
    """Simplified storage system with essential functionality."""
    
    def __init__(self, base_dir: Path = None):
        # Use existing data directory structure but simplified
        if base_dir is None:
            self.base_dir = Path.home() / ".paleo_labels"
        else:
            self.base_dir = Path(base_dir)
        
        # Create directory structure
        self.labels_dir = self.base_dir / "labels"
        self.templates_dir = self.base_dir / "templates" 
        self.styles_dir = self.base_dir / "styles"
        self.exports_dir = self.base_dir / "exports"
        
        for directory in [self.labels_dir, self.templates_dir, self.styles_dir, self.exports_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize metadata
        self.metadata_file = self.base_dir / "metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """Load storage metadata."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {
                    'created': datetime.now().isoformat(),
                    'version': '2.0',
                    'simplified': True,
                    'label_count': 0,
                    'template_count': 0
                }
                self._save_metadata()
        except Exception:
            self.metadata = {'error': 'Could not load metadata'}
    
    def _save_metadata(self):
        """Save storage metadata."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception:
            pass
    
    def save_label(self, name: str, label_data: dict[str, str]) -> bool:
        """Save a label to storage."""
        try:
            # Clean the name for filesystem
            safe_name = self._make_safe_filename(name)
            label_file = self.labels_dir / f"{safe_name}.toml"
            
            # Prepare label record
            label_record = {
                'name': name,
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
                'fields': label_data,
                'field_count': len(label_data)
            }
            
            # Save as TOML
            with open(label_file, 'wb') as f:
                tomli_w.dump(label_record, f)
            
            # Update metadata
            self.metadata['label_count'] = len(self.list_labels())
            self.metadata['last_modified'] = datetime.now().isoformat()
            self._save_metadata()
            
            return True
            
        except Exception as e:
            print(f"Error saving label: {e}")
            return False
    
    def load_label(self, name: str) -> dict[str, str]:
        """Load a label from storage."""
        try:
            safe_name = self._make_safe_filename(name)
            label_file = self.labels_dir / f"{safe_name}.toml"
            
            if not label_file.exists():
                return {}
            
            with open(label_file, 'rb') as f:
                label_record = tomli.load(f)
            
            return label_record.get('fields', {})
            
        except Exception as e:
            print(f"Error loading label: {e}")
            return {}
    
    def list_labels(self) -> list[str]:
        """List all available labels."""
        try:
            labels = []
            for label_file in self.labels_dir.glob("*.toml"):
                try:
                    with open(label_file, 'rb') as f:
                        label_record = tomli.load(f)
                        labels.append(label_record.get('name', label_file.stem))
                except Exception:
                    # Fallback to filename
                    labels.append(label_file.stem)
            
            return sorted(labels)
            
        except Exception:
            return []
    
    def delete_label(self, name: str) -> bool:
        """Delete a label from storage."""
        try:
            safe_name = self._make_safe_filename(name)
            label_file = self.labels_dir / f"{safe_name}.toml"
            
            if label_file.exists():
                label_file.unlink()
                
                # Update metadata
                self.metadata['label_count'] = len(self.list_labels())
                self._save_metadata()
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting label: {e}")
            return False
    
    def save_template(self, name: str, template_data: dict[str, any]) -> bool:
        """Save a template to storage."""
        try:
            safe_name = self._make_safe_filename(name)
            template_file = self.templates_dir / f"{safe_name}.toml"
            
            # Prepare template record
            template_record = {
                'name': name,
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
                'data': template_data
            }
            
            # Save as TOML
            with open(template_file, 'wb') as f:
                tomli_w.dump(template_record, f)
            
            # Update metadata
            self.metadata['template_count'] = len(self.list_templates())
            self._save_metadata()
            
            return True
            
        except Exception as e:
            print(f"Error saving template: {e}")
            return False
    
    def load_template(self, name: str) -> dict[str, any]:
        """Load a template from storage."""
        try:
            safe_name = self._make_safe_filename(name)
            template_file = self.templates_dir / f"{safe_name}.toml"
            
            if not template_file.exists():
                return {}
            
            with open(template_file, 'rb') as f:
                template_record = tomli.load(f)
            
            return template_record
            
        except Exception as e:
            print(f"Error loading template: {e}")
            return {}
    
    def list_templates(self) -> list[str]:
        """List all available templates."""
        try:
            templates = []
            for template_file in self.templates_dir.glob("*.toml"):
                try:
                    with open(template_file, 'rb') as f:
                        template_record = tomli.load(f)
                        templates.append(template_record.get('name', template_file.stem))
                except Exception:
                    templates.append(template_file.stem)
            
            return sorted(templates)
            
        except Exception:
            return []
    
    def delete_template(self, name: str) -> bool:
        """Delete a template from storage."""
        try:
            safe_name = self._make_safe_filename(name)
            template_file = self.templates_dir / f"{safe_name}.toml"
            
            if template_file.exists():
                template_file.unlink()
                
                # Update metadata
                self.metadata['template_count'] = len(self.list_templates())
                self._save_metadata()
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting template: {e}")
            return False
    
    def get_storage_stats(self) -> dict[str, any]:
        """Get storage statistics."""
        try:
            stats = {
                'labels': len(self.list_labels()),
                'templates': len(self.list_templates()),
                'storage_path': str(self.base_dir),
                'last_modified': self.metadata.get('last_modified', 'Unknown')
            }
            
            return stats
            
        except Exception:
            return {}
    
    def _make_safe_filename(self, name: str) -> str:
        """Convert a name to a safe filename."""
        # Replace unsafe characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        safe_name = ''.join(c if c in safe_chars else '_' for c in name)
        
        # Ensure it's not empty and not too long
        if not safe_name:
            safe_name = f"unnamed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if len(safe_name) > 100:
            safe_name = safe_name[:100]
        
        return safe_name


def initialize_simple_storage() -> SimpleStorage:
    """Initialize the simplified storage system."""
    return SimpleStorage()