from typing import Dict, List, Any, Set, Tuple
from dataclasses import dataclass
from .parser import Resource, CloudFormationParser

@dataclass
class ResourceDiff:
    """Represents the difference between two resources."""
    logical_id: str
    resource_type: str
    change_type: str  # 'ADD', 'REMOVE', 'MODIFY'
    old_properties: Dict[str, Any]
    new_properties: Dict[str, Any]
    property_changes: Dict[str, Tuple[Any, Any]]  # property_name: (old_value, new_value)

class StackDiffAnalyzer:
    """Analyzes differences between two CloudFormation stacks."""
    
    def __init__(self, old_template: str, new_template: str):
        self.old_parser = CloudFormationParser(old_template)
        self.new_parser = CloudFormationParser(new_template)
    
    def get_resource_diffs(self) -> List[ResourceDiff]:
        """Get differences between resources in old and new templates."""
        old_resources = {r.logical_id: r for r in self.old_parser.get_resources()}
        new_resources = {r.logical_id: r for r in self.new_parser.get_resources()}
        
        diffs = []
        
        # Find added and modified resources
        for logical_id, new_resource in new_resources.items():
            if logical_id not in old_resources:
                # Resource was added
                diffs.append(ResourceDiff(
                    logical_id=logical_id,
                    resource_type=new_resource.type,
                    change_type='ADD',
                    old_properties={},
                    new_properties=new_resource.properties,
                    property_changes={}
                ))
            else:
                # Resource might have been modified
                old_resource = old_resources[logical_id]
                property_changes = self._get_property_changes(
                    old_resource.properties,
                    new_resource.properties
                )
                
                if property_changes:
                    diffs.append(ResourceDiff(
                        logical_id=logical_id,
                        resource_type=new_resource.type,
                        change_type='MODIFY',
                        old_properties=old_resource.properties,
                        new_properties=new_resource.properties,
                        property_changes=property_changes
                    ))
        
        # Find removed resources
        for logical_id, old_resource in old_resources.items():
            if logical_id not in new_resources:
                diffs.append(ResourceDiff(
                    logical_id=logical_id,
                    resource_type=old_resource.type,
                    change_type='REMOVE',
                    old_properties=old_resource.properties,
                    new_properties={},
                    property_changes={}
                ))
        
        return diffs
    
    def _get_property_changes(
        self,
        old_properties: Dict[str, Any],
        new_properties: Dict[str, Any]
    ) -> Dict[str, Tuple[Any, Any]]:
        """Get changes between old and new properties."""
        changes = {}
        
        # Find modified and added properties
        for key, new_value in new_properties.items():
            if key not in old_properties:
                changes[key] = (None, new_value)
            elif old_properties[key] != new_value:
                changes[key] = (old_properties[key], new_value)
        
        # Find removed properties
        for key, old_value in old_properties.items():
            if key not in new_properties:
                changes[key] = (old_value, None)
        
        return changes
    
    def get_added_resources(self) -> List[Resource]:
        """Get resources that were added in the new template."""
        return [
            r for r in self.new_parser.get_resources()
            if r.logical_id not in {r.logical_id for r in self.old_parser.get_resources()}
        ]
    
    def get_removed_resources(self) -> List[Resource]:
        """Get resources that were removed in the new template."""
        return [
            r for r in self.old_parser.get_resources()
            if r.logical_id not in {r.logical_id for r in self.new_parser.get_resources()}
        ]
    
    def get_modified_resources(self) -> List[Tuple[Resource, Resource]]:
        """Get pairs of resources that were modified (old, new)."""
        old_resources = {r.logical_id: r for r in self.old_parser.get_resources()}
        new_resources = {r.logical_id: r for r in self.new_parser.get_resources()}
        
        modified = []
        for logical_id in set(old_resources.keys()) & set(new_resources.keys()):
            old_resource = old_resources[logical_id]
            new_resource = new_resources[logical_id]
            
            if old_resource.properties != new_resource.properties:
                modified.append((old_resource, new_resource))
        
        return modified
    
    def get_unchanged_resources(self) -> List[Resource]:
        """Get resources that remained unchanged."""
        old_resources = {r.logical_id: r for r in self.old_parser.get_resources()}
        new_resources = {r.logical_id: r for r in self.new_parser.get_resources()}
        
        unchanged = []
        for logical_id in set(old_resources.keys()) & set(new_resources.keys()):
            old_resource = old_resources[logical_id]
            new_resource = new_resources[logical_id]
            
            if old_resource.properties == new_resource.properties:
                unchanged.append(new_resource)
        
        return unchanged 