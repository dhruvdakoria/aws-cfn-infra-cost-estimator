import boto3
from typing import Dict, List, Any, Optional
from .core import CostEstimator, ResourceCost, ResourceNotSupportedError, PricingDataError

class AWSPricingEstimator(CostEstimator):
    """Cost estimator using AWS Pricing API as fallback."""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.pricing_client = boto3.client('pricing', region_name=region)
        self._supported_resources = None
    
    def get_supported_resources(self) -> List[str]:
        """Get list of supported AWS resources."""
        if self._supported_resources is None:
            try:
                # Get all services from AWS Pricing API
                paginator = self.pricing_client.get_paginator('describe_services')
                services = []
                for page in paginator.paginate():
                    services.extend([service['ServiceCode'] for service in page['Services']])
                self._supported_resources = services
            except Exception as e:
                raise PricingDataError(f"Error getting supported resources: {str(e)}")
        return self._supported_resources
    
    def is_resource_supported(self, resource_type: str) -> bool:
        """Check if a resource type is supported by AWS Pricing API."""
        return resource_type in self.get_supported_resources()
    
    def _get_pricing_data(self, service_code: str, filters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get pricing data from AWS Pricing API."""
        try:
            response = self.pricing_client.get_products(
                ServiceCode=service_code,
                Filters=filters
            )
            return response
        except Exception as e:
            raise PricingDataError(f"Error getting pricing data: {str(e)}")
    
    def get_resource_cost(self, resource_type: str, resource_properties: Dict[str, Any]) -> ResourceCost:
        """Get cost information for a single resource using AWS Pricing API."""
        if not self.is_resource_supported(resource_type):
            raise ResourceNotSupportedError(f"Resource type {resource_type} is not supported by AWS Pricing API")
        
        try:
            # Convert CloudFormation resource type to AWS service code
            service_code = self._get_service_code(resource_type)
            
            # Build filters based on resource properties
            filters = self._build_pricing_filters(resource_type, resource_properties)
            
            # Get pricing data
            pricing_data = self._get_pricing_data(service_code, filters)
            
            # Parse pricing data and calculate costs
            hourly_cost, monthly_cost = self._calculate_costs(pricing_data)
            
            return ResourceCost(
                resource_type=resource_type,
                resource_id=resource_properties.get("id", "unknown"),
                hourly_cost=hourly_cost,
                monthly_cost=monthly_cost,
                currency="USD",
                usage_type=self._get_usage_type(resource_type, resource_properties),
                description=self._get_resource_description(resource_type, resource_properties),
                metadata=self._get_resource_metadata(resource_type, resource_properties)
            )
            
        except Exception as e:
            raise PricingDataError(f"Error getting cost for resource {resource_type}: {str(e)}")
    
    def _get_service_code(self, resource_type: str) -> str:
        """Convert CloudFormation resource type to AWS service code."""
        # Map of common CloudFormation resource types to AWS service codes
        service_map = {
            "AWS::EC2::Instance": "AmazonEC2",
            "AWS::RDS::DBInstance": "AmazonRDS",
            "AWS::S3::Bucket": "AmazonS3",
            "AWS::DynamoDB::Table": "AmazonDynamoDB",
            "AWS::Lambda::Function": "AWSLambda",
            # Add more mappings as needed
        }
        return service_map.get(resource_type, resource_type.split("::")[1])
    
    def _build_pricing_filters(self, resource_type: str, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build filters for AWS Pricing API based on resource properties."""
        filters = []
        
        # Add common filters
        filters.append({
            'Type': 'TERM_MATCH',
            'Field': 'ServiceCode',
            'Value': self._get_service_code(resource_type)
        })
        
        # Add resource-specific filters
        if resource_type == "AWS::EC2::Instance":
            filters.extend([
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'instanceType',
                    'Value': properties.get('InstanceType', 't2.micro')
                },
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'operatingSystem',
                    'Value': properties.get('ImageId', {}).get('OperatingSystem', 'Linux')
                }
            ])
        # Add more resource-specific filter building logic as needed
        
        return filters
    
    def _calculate_costs(self, pricing_data: Dict[str, Any]) -> tuple[float, float]:
        """Calculate hourly and monthly costs from pricing data."""
        # This is a simplified implementation
        # In reality, you would need to parse the complex pricing data structure
        # and handle different pricing models (on-demand, reserved, etc.)
        hourly_cost = 0.0
        monthly_cost = 0.0
        
        try:
            # Extract the first price dimension
            price_dimensions = pricing_data.get('PriceList', [{}])[0].get('terms', {}).get('OnDemand', {})
            for dimension in price_dimensions.values():
                price_per_unit = float(dimension.get('priceDimensions', {}).get('pricePerUnit', {}).get('USD', 0))
                hourly_cost = price_per_unit
                monthly_cost = hourly_cost * 730  # Average hours in a month
                break
        except (KeyError, IndexError, ValueError):
            pass
        
        return hourly_cost, monthly_cost
    
    def _get_usage_type(self, resource_type: str, properties: Dict[str, Any]) -> Optional[str]:
        """Get usage type for the resource."""
        if resource_type == "AWS::EC2::Instance":
            return "OnDemand"
        return None
    
    def _get_resource_description(self, resource_type: str, properties: Dict[str, Any]) -> Optional[str]:
        """Get description for the resource."""
        return properties.get('Description')
    
    def _get_resource_metadata(self, resource_type: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Get additional metadata for the resource."""
        return {
            'region': self.region,
            'properties': properties
        } 