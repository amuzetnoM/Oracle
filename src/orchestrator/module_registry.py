"""
Module Registry

Registry for discovering and managing system modules.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging


class ModuleStatus(Enum):
    """Module lifecycle statuses."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class Module:
    """Represents a system module."""
    name: str
    module_type: str  # e.g., 'data_ingestion', 'prediction_core'
    instance: Any
    status: ModuleStatus = ModuleStatus.UNINITIALIZED
    registered_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


class ModuleRegistry:
    """
    Registry for system modules.
    
    Provides module discovery, lifecycle management, and dependency tracking.
    """
    
    def __init__(self):
        """Initialize module registry."""
        self.logger = logging.getLogger(__name__)
        self.modules: Dict[str, Module] = {}
    
    def register(
        self,
        name: str,
        module_type: str,
        instance: Any,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Module:
        """
        Register a module.
        
        Args:
            name: Unique module name
            module_type: Type/category of module
            instance: Module instance
            dependencies: List of module names this depends on
            metadata: Additional metadata
        
        Returns:
            Module object
        """
        if name in self.modules:
            raise ValueError(f"Module '{name}' already registered")
        
        module = Module(
            name=name,
            module_type=module_type,
            instance=instance,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        
        self.modules[name] = module
        self.logger.info(f"Registered module: {name} ({module_type})")
        
        return module
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a module.
        
        Args:
            name: Module name
        
        Returns:
            True if successful
        """
        if name not in self.modules:
            return False
        
        del self.modules[name]
        self.logger.info(f"Unregistered module: {name}")
        
        return True
    
    def get(self, name: str) -> Optional[Module]:
        """
        Get a module by name.
        
        Args:
            name: Module name
        
        Returns:
            Module object or None
        """
        return self.modules.get(name)
    
    def get_by_type(self, module_type: str) -> List[Module]:
        """
        Get all modules of a specific type.
        
        Args:
            module_type: Module type
        
        Returns:
            List of modules
        """
        return [
            m for m in self.modules.values()
            if m.module_type == module_type
        ]
    
    def get_by_status(self, status: ModuleStatus) -> List[Module]:
        """
        Get all modules with a specific status.
        
        Args:
            status: Module status
        
        Returns:
            List of modules
        """
        return [
            m for m in self.modules.values()
            if m.status == status
        ]
    
    def update_status(
        self,
        name: str,
        status: ModuleStatus
    ) -> bool:
        """
        Update module status.
        
        Args:
            name: Module name
            status: New status
        
        Returns:
            True if successful
        """
        if name not in self.modules:
            return False
        
        module = self.modules[name]
        old_status = module.status
        module.status = status
        module.last_updated = datetime.now()
        
        self.logger.info(
            f"Module {name} status: {old_status} -> {status}"
        )
        
        return True
    
    def check_dependencies(self, name: str) -> Dict[str, bool]:
        """
        Check if module dependencies are satisfied.
        
        Args:
            name: Module name
        
        Returns:
            Dictionary mapping dependency to satisfied (bool)
        """
        if name not in self.modules:
            return {}
        
        module = self.modules[name]
        dependency_status = {}
        
        for dep_name in module.dependencies:
            if dep_name not in self.modules:
                dependency_status[dep_name] = False
            else:
                dep_module = self.modules[dep_name]
                # Consider dependency satisfied if in READY or RUNNING state
                dependency_status[dep_name] = dep_module.status in [
                    ModuleStatus.READY,
                    ModuleStatus.RUNNING
                ]
        
        return dependency_status
    
    def get_startup_order(self) -> List[str]:
        """
        Get module startup order based on dependencies.
        
        Uses topological sort to determine order.
        
        Returns:
            List of module names in startup order
        """
        # Build dependency graph
        graph = {
            name: module.dependencies
            for name, module in self.modules.items()
        }
        
        # Topological sort
        visited = set()
        order = []
        
        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            
            if name in graph:
                for dep in graph[name]:
                    if dep in graph:
                        visit(dep)
            
            order.append(name)
        
        for name in graph:
            visit(name)
        
        return order
    
    def list_all(self) -> List[Module]:
        """
        List all registered modules.
        
        Returns:
            List of all modules
        """
        return list(self.modules.values())
    
    def get_summary(self) -> Dict:
        """
        Get registry summary.
        
        Returns:
            Dictionary with summary statistics
        """
        status_counts = {}
        for status in ModuleStatus:
            status_counts[status.value] = len(self.get_by_status(status))
        
        type_counts = {}
        for module in self.modules.values():
            if module.module_type not in type_counts:
                type_counts[module.module_type] = 0
            type_counts[module.module_type] += 1
        
        return {
            'total_modules': len(self.modules),
            'status_counts': status_counts,
            'type_counts': type_counts
        }
