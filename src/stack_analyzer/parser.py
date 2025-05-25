import yaml
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Patch: Custom YAML loader to handle CloudFormation intrinsic functions as plain values
class CFNYamlLoader(yaml.SafeLoader):
    pass

def cfn_tag_constructor(loader, node):
    # Return the tag and value as a string or just the value
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    elif isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None

# Register all common CloudFormation tags
for tag in [
    '!Ref', '!GetAtt', '!Sub', '!Join', '!Select', '!Split', '!ImportValue', '!FindInMap',
    '!Base64', '!Cidr', '!If', '!And', '!Or', '!Not', '!Equals', '!Condition', '!GetAZs', '!Transform'
]:
    CFNYamlLoader.add_constructor(tag, cfn_tag_constructor)

@dataclass
class Resource:
    """Represents a CloudFormation resource."""
    type: str
    properties: Dict[str, Any]
    logical_id: str
    metadata: Optional[Dict[str, Any]] = None

class CloudFormationParser:
    """Parser for CloudFormation templates."""
    
    def __init__(self, template_content: str):
        self.template_content = template_content
        self.template = self._parse_template()
    
    def _parse_template(self) -> Dict[str, Any]:
        """Parse the CloudFormation template content."""
        try:
            if self.template_content.strip().startswith('{'):
                return json.loads(self.template_content)
            # Use the patched loader
            return yaml.load(self.template_content, Loader=CFNYamlLoader)
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"Error parsing CloudFormation template: {str(e)}")
    
    def get_resources(self) -> List[Resource]:
        """Extract resources from the template."""
        resources = []
        template_resources = self.template.get('Resources', {})
        
        for logical_id, resource_data in template_resources.items():
            resource_type = resource_data.get('Type')
            properties = resource_data.get('Properties', {})
            metadata = resource_data.get('Metadata')
            
            resources.append(Resource(
                type=resource_type,
                properties=properties,
                logical_id=logical_id,
                metadata=metadata
            ))
        
        return resources
    
    def get_resource_by_type(self, resource_type: str) -> List[Resource]:
        """Get resources of a specific type."""
        return [r for r in self.get_resources() if r.type == resource_type]
    
    def get_resource_by_logical_id(self, logical_id: str) -> Optional[Resource]:
        """Get a resource by its logical ID."""
        for resource in self.get_resources():
            if resource.logical_id == logical_id:
                return resource
        return None
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get template parameters."""
        return self.template.get('Parameters', {})
    
    def get_outputs(self) -> Dict[str, Any]:
        """Get template outputs."""
        return self.template.get('Outputs', {})
    
    def get_conditions(self) -> Dict[str, Any]:
        """Get template conditions."""
        return self.template.get('Conditions', {})
    
    def get_mappings(self) -> Dict[str, Any]:
        """Get template mappings."""
        return self.template.get('Mappings', {})
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get template metadata."""
        return self.template.get('Metadata', {})
    
    def get_description(self) -> Optional[str]:
        """Get template description."""
        return self.template.get('Description')
    
    def get_aws_template_format_version(self) -> Optional[str]:
        """Get AWS template format version."""
        return self.template.get('AWSTemplateFormatVersion')
    
    def get_transform(self) -> Optional[str]:
        """Get template transform."""
        return self.template.get('Transform') 