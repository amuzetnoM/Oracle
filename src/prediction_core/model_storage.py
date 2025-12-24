"""
Model Storage - Saves and loads trained models.

Provides utilities for:
- Serializing models to JSON/pickle
- Loading models from disk
- Model versioning
- Model metadata tracking
"""

from typing import Dict, Any, Optional, List
import json
import pickle
from pathlib import Path
from datetime import datetime


class ModelStorage:
    """
    Handles saving and loading of trained models.
    
    Supports JSON (for small models) and pickle (for large models).
    Maintains model metadata and versioning.
    """
    
    def __init__(self, storage_dir: str = "./models"):
        """
        Initialize model storage.
        
        Args:
            storage_dir: Directory to store models
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata file
        self.metadata_file = self.storage_dir / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from disk."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        else:
            return {'models': {}}
    
    def _save_metadata(self):
        """Save metadata to disk."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def save_model(
        self,
        model: Any,
        name: str,
        version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        format: str = "json"
    ) -> str:
        """
        Save a model to disk.
        
        Args:
            model: Model object with to_dict() method (for JSON) or any object (for pickle)
            name: Model name
            version: Model version (auto-generated if None)
            metadata: Additional metadata to store
            format: Storage format ("json" or "pickle")
            
        Returns:
            Path to saved model
        """
        # Generate version if not provided
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create filename
        filename = f"{name}_v{version}.{format}"
        filepath = self.storage_dir / filename
        
        # Save model
        if format == "json":
            # Requires model to have to_dict() method
            if not hasattr(model, 'to_dict'):
                raise ValueError("Model must have to_dict() method for JSON format")
            
            model_dict = model.to_dict()
            with open(filepath, 'w') as f:
                json.dump(model_dict, f, indent=2)
        
        elif format == "pickle":
            with open(filepath, 'wb') as f:
                pickle.dump(model, f)
        
        else:
            raise ValueError(f"Unknown format: {format}")
        
        # Update metadata
        model_metadata = {
            'name': name,
            'version': version,
            'filepath': str(filepath),
            'format': format,
            'saved_at': datetime.now().isoformat(),
            'custom_metadata': metadata or {}
        }
        
        model_id = f"{name}_v{version}"
        self.metadata['models'][model_id] = model_metadata
        self._save_metadata()
        
        return str(filepath)
    
    def load_model(
        self,
        name: str,
        version: Optional[str] = None,
        model_class: Optional[type] = None
    ) -> Any:
        """
        Load a model from disk.
        
        Args:
            name: Model name
            version: Model version (loads latest if None)
            model_class: Class with from_dict() method (for JSON format)
            
        Returns:
            Loaded model
        """
        # Find model metadata
        if version is None:
            # Find latest version
            matching_models = [
                (k, v) for k, v in self.metadata['models'].items()
                if k.startswith(f"{name}_v")
            ]
            
            if not matching_models:
                raise ValueError(f"No models found with name: {name}")
            
            # Sort by saved_at and get latest
            matching_models.sort(key=lambda x: x[1]['saved_at'], reverse=True)
            model_id, model_metadata = matching_models[0]
        else:
            model_id = f"{name}_v{version}"
            if model_id not in self.metadata['models']:
                raise ValueError(f"Model not found: {model_id}")
            model_metadata = self.metadata['models'][model_id]
        
        # Load model
        filepath = Path(model_metadata['filepath'])
        format = model_metadata['format']
        
        if format == "json":
            # Requires model_class with from_dict() method
            if model_class is None or not hasattr(model_class, 'from_dict'):
                raise ValueError("model_class with from_dict() method required for JSON format")
            
            with open(filepath, 'r') as f:
                model_dict = json.load(f)
            
            model = model_class.from_dict(model_dict)
        
        elif format == "pickle":
            with open(filepath, 'rb') as f:
                model = pickle.load(f)
        
        else:
            raise ValueError(f"Unknown format: {format}")
        
        return model
    
    def list_models(self, name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all saved models.
        
        Args:
            name: Filter by model name (None = all models)
            
        Returns:
            List of model metadata
        """
        models = []
        
        for model_id, metadata in self.metadata['models'].items():
            if name is None or metadata['name'] == name:
                models.append(metadata)
        
        # Sort by saved_at descending
        models.sort(key=lambda x: x['saved_at'], reverse=True)
        
        return models
    
    def delete_model(self, name: str, version: str):
        """
        Delete a model from disk.
        
        Args:
            name: Model name
            version: Model version
        """
        model_id = f"{name}_v{version}"
        
        if model_id not in self.metadata['models']:
            raise ValueError(f"Model not found: {model_id}")
        
        # Get filepath and delete
        filepath = Path(self.metadata['models'][model_id]['filepath'])
        if filepath.exists():
            filepath.unlink()
        
        # Remove from metadata
        del self.metadata['models'][model_id]
        self._save_metadata()
    
    def get_model_info(self, name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metadata for a model.
        
        Args:
            name: Model name
            version: Model version (latest if None)
            
        Returns:
            Model metadata
        """
        if version is None:
            # Find latest version
            matching_models = [
                (k, v) for k, v in self.metadata['models'].items()
                if k.startswith(f"{name}_v")
            ]
            
            if not matching_models:
                raise ValueError(f"No models found with name: {name}")
            
            matching_models.sort(key=lambda x: x[1]['saved_at'], reverse=True)
            _, model_metadata = matching_models[0]
        else:
            model_id = f"{name}_v{version}"
            if model_id not in self.metadata['models']:
                raise ValueError(f"Model not found: {model_id}")
            model_metadata = self.metadata['models'][model_id]
        
        return model_metadata
    
    def cleanup_old_versions(self, name: str, keep_latest: int = 3):
        """
        Delete old versions of a model, keeping only the latest N.
        
        Args:
            name: Model name
            keep_latest: Number of latest versions to keep
        """
        # Find all versions of this model
        matching_models = [
            (k, v) for k, v in self.metadata['models'].items()
            if k.startswith(f"{name}_v")
        ]
        
        if len(matching_models) <= keep_latest:
            return  # Nothing to cleanup
        
        # Sort by saved_at
        matching_models.sort(key=lambda x: x[1]['saved_at'], reverse=True)
        
        # Delete old versions
        for model_id, metadata in matching_models[keep_latest:]:
            # Extract version from model_id
            version = model_id.split('_v')[-1]
            self.delete_model(name, version)
