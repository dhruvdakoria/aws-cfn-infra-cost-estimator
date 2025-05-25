"""
Enhanced cost calculator that integrates tiered pricing and usage estimation.
This module provides improved cost calculation logic using the updated query builders.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from .query_builders import calculate_tiered_cost, get_query_builder
from .infracost import InfracostEstimator
from .core import ResourceCost, PricingDataError

logger = logging.getLogger(__name__)


class UsageEstimator:
    """Estimates monthly usage for AWS resources based on their properties and typical patterns."""
    
    @staticmethod
    def estimate_api_gateway_usage(properties: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate API Gateway usage based on properties."""
        # Extract properties that might indicate usage patterns
        name = properties.get("Name", "")
        description = properties.get("Description", "")
        endpoint_config = properties.get("EndpointConfiguration", {})
        
        # Default assumptions based on API type and configuration
        base_requests = 100000  # 100K requests/month default
        
        # Adjust based on endpoint type
        endpoint_types = endpoint_config.get("Types", ["EDGE"])
        if "REGIONAL" in endpoint_types:
            base_requests *= 2  # Regional APIs might handle more traffic
        elif "PRIVATE" in endpoint_types:
            base_requests *= 0.5  # Private APIs might have less traffic
        
        # Adjust based on naming patterns (heuristic)
        if any(keyword in name.lower() for keyword in ["prod", "production"]):
            base_requests *= 10
        elif any(keyword in name.lower() for keyword in ["dev", "test", "staging"]):
            base_requests *= 0.3
        elif any(keyword in name.lower() for keyword in ["high", "scale", "enterprise"]):
            base_requests *= 20
        
        return {
            "monthly_requests": base_requests,
            "request_size_kb": 4,  # Average request size
            "response_size_kb": 8   # Average response size
        }
    
    @staticmethod
    def estimate_ec2_usage(properties: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate EC2 usage based on properties."""
        instance_type = properties.get("InstanceType", "t2.micro")
        
        # Estimate based on instance type
        if instance_type.startswith("t"):
            # Burstable instances - likely development/testing
            monthly_hours = 200  # Part-time usage
        elif instance_type.startswith("m") or instance_type.startswith("c"):
            # General purpose/compute optimized - likely production
            monthly_hours = 730  # Full-time usage
        elif instance_type.startswith("r") or instance_type.startswith("x"):
            # Memory optimized - likely database/analytics
            monthly_hours = 730  # Full-time usage
        else:
            monthly_hours = 500  # Default moderate usage
        
        return {
            "monthly_hours": monthly_hours,
            "cpu_utilization_percent": 30,  # Average CPU utilization
            "network_gb_per_month": 100     # Average network usage
        }
    
    @staticmethod
    def estimate_rds_usage(properties: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate RDS usage based on properties."""
        instance_class = properties.get("DBInstanceClass", "db.t3.micro")
        multi_az = properties.get("MultiAZ", False)
        allocated_storage = properties.get("AllocatedStorage", 20)
        
        # Database usage is typically 24/7
        monthly_hours = 730
        
        # Estimate IOPS based on storage and instance class
        if instance_class.startswith("db.t"):
            estimated_iops = allocated_storage * 3  # Burstable baseline
        elif instance_class.startswith("db.m"):
            estimated_iops = allocated_storage * 10  # General purpose
        else:
            estimated_iops = allocated_storage * 20  # High performance
        
        return {
            "monthly_hours": monthly_hours,
            "monthly_iops": estimated_iops * 730,  # IOPS per hour * hours
            "backup_storage_gb": allocated_storage * 0.5,  # 50% of primary storage
            "multi_az_factor": 2 if multi_az else 1
        }
    
    @staticmethod
    def estimate_lambda_usage(properties: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate Lambda usage based on properties."""
        memory_size = properties.get("MemorySize", 128)
        timeout = properties.get("Timeout", 3)
        runtime = properties.get("Runtime", "python3.9")
        
        # Estimate based on memory size and runtime
        if memory_size <= 128:
            monthly_requests = 50000  # Small functions
        elif memory_size <= 512:
            monthly_requests = 100000  # Medium functions
        else:
            monthly_requests = 200000  # Large functions
        
        # Adjust for runtime (some runtimes indicate different usage patterns)
        if "java" in runtime:
            monthly_requests *= 0.7  # Java typically has longer cold starts, fewer invocations
        elif "node" in runtime:
            monthly_requests *= 1.2  # Node.js often used for high-frequency APIs
        
        return {
            "monthly_requests": monthly_requests,
            "average_duration_ms": min(timeout * 1000 * 0.6, 5000),  # 60% of timeout, max 5s
            "memory_mb": memory_size
        }
    
    @staticmethod
    def estimate_dynamodb_usage(properties: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate DynamoDB usage based on properties."""
        billing_mode = properties.get("BillingMode", "PAY_PER_REQUEST")
        provisioned_throughput = properties.get("ProvisionedThroughput", {})
        
        if billing_mode == "PROVISIONED":
            read_capacity = provisioned_throughput.get("ReadCapacityUnits", 5)
            write_capacity = provisioned_throughput.get("WriteCapacityUnits", 5)
            
            # Convert capacity units to monthly requests
            monthly_reads = read_capacity * 730 * 3600  # RCU * hours * seconds
            monthly_writes = write_capacity * 730 * 3600  # WCU * hours * seconds
        else:
            # On-demand pricing - estimate based on typical usage
            monthly_reads = 1000000   # 1M reads
            monthly_writes = 200000   # 200K writes
        
        return {
            "monthly_read_requests": monthly_reads,
            "monthly_write_requests": monthly_writes,
            "average_item_size_kb": 1,  # 1KB average item size
            "storage_gb": 10  # 10GB estimated storage
        }
    
    @staticmethod
    def estimate_s3_usage(properties: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate S3 usage based on properties."""
        versioning = properties.get("VersioningConfiguration", {})
        lifecycle = properties.get("LifecycleConfiguration", {})
        
        # Base storage estimate
        storage_gb = 100  # 100GB default
        
        # Adjust based on versioning
        if versioning.get("Status") == "Enabled":
            storage_gb *= 1.5  # Versioning increases storage
        
        # Estimate requests based on storage size
        monthly_put_requests = storage_gb * 100  # 100 PUTs per GB
        monthly_get_requests = storage_gb * 1000  # 1000 GETs per GB
        
        return {
            "storage_gb": storage_gb,
            "monthly_put_requests": monthly_put_requests,
            "monthly_get_requests": monthly_get_requests,
            "data_transfer_gb": storage_gb * 0.1  # 10% of storage transferred monthly
        }
    
    @classmethod
    def estimate_usage(cls, resource_type: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate usage for any supported resource type."""
        estimators = {
            "AWS::ApiGateway::RestApi": cls.estimate_api_gateway_usage,
            "AWS::ApiGatewayV2::Api": cls.estimate_api_gateway_usage,
            "AWS::EC2::Instance": cls.estimate_ec2_usage,
            "AWS::RDS::DBInstance": cls.estimate_rds_usage,
            "AWS::RDS::DBCluster": cls.estimate_rds_usage,
            "AWS::Lambda::Function": cls.estimate_lambda_usage,
            "AWS::DynamoDB::Table": cls.estimate_dynamodb_usage,
            "AWS::S3::Bucket": cls.estimate_s3_usage,
        }
        
        estimator = estimators.get(resource_type)
        if estimator:
            return estimator(properties)
        
        # Default usage estimation for unsupported types
        return {
            "monthly_hours": 730,  # Assume full-time usage
            "monthly_requests": 100000,  # Default request volume
            "storage_gb": 50  # Default storage
        }


class EnhancedCostCalculator:
    """Enhanced cost calculator with tiered pricing and usage estimation."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.infracost_estimator = InfracostEstimator(api_key)
        self.usage_estimator = UsageEstimator()
    
    def calculate_resource_cost_with_usage(
        self, 
        resource_type: str, 
        resource_properties: Dict[str, Any],
        usage_override: Optional[Dict[str, Any]] = None
    ) -> Tuple[ResourceCost, Dict[str, Any]]:
        """
        Calculate resource cost with usage estimation and tiered pricing.
        
        Args:
            resource_type: AWS resource type
            resource_properties: CloudFormation resource properties
            usage_override: Optional usage parameters to override estimates
        
        Returns:
            Tuple of (ResourceCost, usage_details)
        """
        try:
            # Step 1: Estimate usage based on resource properties
            estimated_usage = self.usage_estimator.estimate_usage(resource_type, resource_properties)
            
            # Step 2: Apply any usage overrides
            if usage_override:
                estimated_usage.update(usage_override)
            
            # Step 3: Get pricing data using enhanced query builder
            query_builder = get_query_builder(resource_type)
            if not query_builder:
                # Fallback to basic cost estimation
                return self.infracost_estimator.get_resource_cost(resource_type, resource_properties), estimated_usage
            
            # Step 4: Build query and get pricing data
            query = query_builder(resource_properties)
            response = self.infracost_estimator._make_graphql_request(query)
            
            # Step 5: Calculate cost using tiered pricing
            monthly_cost = self._calculate_tiered_cost_from_response(
                response, resource_type, estimated_usage
            )
            
            # Step 6: Create enhanced ResourceCost object
            resource_cost = ResourceCost(
                resource_type=resource_type,
                resource_id=resource_properties.get("id", "unknown"),
                hourly_cost=monthly_cost / 730,
                monthly_cost=monthly_cost,
                currency="USD",
                usage_type="usage_based",
                description=f"Cost calculated with estimated usage: {estimated_usage}",
                metadata={
                    "estimated_usage": estimated_usage,
                    "pricing_tiers_used": True,
                    "query_used": query
                },
                pricing_model="usage_based",
                pricing_details=f"Tiered pricing with estimated usage"
            )
            
            return resource_cost, estimated_usage
            
        except Exception as e:
            logger.error(f"Error calculating enhanced cost for {resource_type}: {str(e)}")
            # Fallback to basic estimation
            basic_cost = self.infracost_estimator.get_resource_cost(resource_type, resource_properties)
            estimated_usage = self.usage_estimator.estimate_usage(resource_type, resource_properties)
            return basic_cost, estimated_usage
    
    def _calculate_tiered_cost_from_response(
        self, 
        response: Dict[str, Any], 
        resource_type: str, 
        usage: Dict[str, Any]
    ) -> float:
        """Calculate cost from API response using tiered pricing."""
        try:
            products = response.get("data", {}).get("products", [])
            if not products:
                return 0.0
            
            # Get prices from the first product
            prices = products[0].get("prices", [])
            if not prices:
                return 0.0
            
            # Determine the usage metric based on resource type
            monthly_usage = self._get_monthly_usage_for_resource(resource_type, usage)
            
            # Calculate cost using tiered pricing
            if len(prices) > 1 and any(p.get("startUsageAmount") for p in prices):
                # Multiple prices with tiers - use tiered calculation
                return calculate_tiered_cost(prices, monthly_usage)
            else:
                # Single price - simple calculation
                price_per_unit = float(prices[0].get("USD", 0))
                return price_per_unit * monthly_usage
                
        except Exception as e:
            logger.error(f"Error calculating tiered cost: {str(e)}")
            return 0.0
    
    def _get_monthly_usage_for_resource(self, resource_type: str, usage: Dict[str, Any]) -> float:
        """Extract the primary usage metric for cost calculation."""
        usage_mappings = {
            "AWS::ApiGateway::RestApi": "monthly_requests",
            "AWS::ApiGatewayV2::Api": "monthly_requests",
            "AWS::EC2::Instance": "monthly_hours",
            "AWS::RDS::DBInstance": "monthly_hours",
            "AWS::RDS::DBCluster": "monthly_hours",
            "AWS::Lambda::Function": "monthly_requests",
            "AWS::DynamoDB::Table": "monthly_read_requests",
            "AWS::S3::Bucket": "storage_gb",
        }
        
        usage_key = usage_mappings.get(resource_type, "monthly_hours")
        return float(usage.get(usage_key, 0))
    
    def calculate_stack_cost_with_usage(
        self, 
        resources: List[Dict[str, Any]],
        usage_overrides: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate total cost for a CloudFormation stack with usage estimation.
        
        Args:
            resources: List of CloudFormation resources
            usage_overrides: Optional usage overrides per resource
        
        Returns:
            Dictionary with detailed cost breakdown
        """
        total_monthly_cost = 0.0
        total_hourly_cost = 0.0
        resource_costs = []
        usage_details = {}
        
        for resource in resources:
            resource_type = resource.get("Type")
            resource_properties = resource.get("Properties", {})
            resource_id = resource.get("LogicalResourceId", "unknown")
            
            # Add region to properties if not present
            if "Region" not in resource_properties:
                resource_properties["Region"] = "us-east-1"  # Default region
            
            # Get usage override for this specific resource
            resource_usage_override = None
            if usage_overrides and resource_id in usage_overrides:
                resource_usage_override = usage_overrides[resource_id]
            
            try:
                cost, usage = self.calculate_resource_cost_with_usage(
                    resource_type, resource_properties, resource_usage_override
                )
                
                total_monthly_cost += cost.monthly_cost
                total_hourly_cost += cost.hourly_cost
                
                resource_costs.append({
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "monthly_cost": cost.monthly_cost,
                    "hourly_cost": cost.hourly_cost,
                    "pricing_model": cost.pricing_model,
                    "usage_type": cost.usage_type
                })
                
                usage_details[resource_id] = usage
                
            except Exception as e:
                logger.error(f"Error calculating cost for resource {resource_id}: {str(e)}")
                # Add zero cost entry for failed calculations
                resource_costs.append({
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "monthly_cost": 0.0,
                    "hourly_cost": 0.0,
                    "pricing_model": "error",
                    "usage_type": "unknown",
                    "error": str(e)
                })
        
        return {
            "total_monthly_cost": total_monthly_cost,
            "total_hourly_cost": total_hourly_cost,
            "currency": "USD",
            "resource_costs": resource_costs,
            "usage_details": usage_details,
            "summary": {
                "total_resources": len(resources),
                "successful_calculations": len([r for r in resource_costs if r.get("pricing_model") != "error"]),
                "failed_calculations": len([r for r in resource_costs if r.get("pricing_model") == "error"])
            }
        } 