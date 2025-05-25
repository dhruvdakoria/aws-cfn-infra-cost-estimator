import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from .core import CostEstimator, ResourceCost, PricingDataError, ResourceNotSupportedError
from .resource_mappings import is_paid_resource, is_free_resource, get_pricing_info
from .query_builders import get_query_builder

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class InfracostEstimator(CostEstimator):
    """Cost estimator using Infracost GraphQL API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("INFRACOST_API_KEY")
        if not self.api_key:
            raise ValueError("Infracost API key is required")
        if not self.api_key.startswith("ico-"):
            logger.warning("API key doesn't start with 'ico-'. This may not be a valid Infracost API key.")
        self.base_url = "https://pricing.api.infracost.io/graphql"

    def _make_graphql_request(self, query: str) -> Dict:
        """Make a GraphQL request to the Infracost API."""
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            logger.debug(f"GraphQL query: {query}")
            response = requests.post(self.base_url, headers=headers, json={"query": query})
            response.raise_for_status()
            logger.debug(f"GraphQL response: {response.text}")
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Error making request to Infracost GraphQL API: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f"\nResponse: {e.response.text}"
            logger.error(error_msg)
            raise PricingDataError(error_msg)

    def get_resource_cost(self, resource_type: str, resource_properties: Dict[str, Any]) -> ResourceCost:
        """Get cost information for a single resource using Infracost GraphQL API."""
        
        # Handle free resources
        if is_free_resource(resource_type):
            logger.info(f"🆓 Resource {resource_type} is free according to Infracost documentation")
            return ResourceCost(
                resource_type=resource_type,
                resource_id=resource_properties.get("id", "unknown"),
                hourly_cost=0.0,
                monthly_cost=0.0,
                currency="USD",
                usage_type="free",
                description="Free resource",
                metadata={"free_resource": True},
                pricing_model="free",
                pricing_details="This resource is free to use"
            )
        
        # Handle paid resources
        if not is_paid_resource(resource_type):
            raise ResourceNotSupportedError(f"Resource type {resource_type} is not supported by Infracost GraphQL API")
        
        if not self.api_key:
            raise ValueError("Infracost API key is required")
        
        # Add region to properties if not present
        if "Region" not in resource_properties:
            resource_properties["Region"] = self.region
        
        # Add a unique ID for the resource if not present
        if "id" not in resource_properties:
            resource_properties["id"] = f"{resource_type}-{hash(str(resource_properties))}"
        
        try:
            # Get the appropriate query builder for this resource type
            query_builder = get_query_builder(resource_type)
            if not query_builder:
                raise ResourceNotSupportedError(f"No query builder found for resource type {resource_type}")
            
            # Build the GraphQL query
            query = query_builder(resource_properties)
            
            # Make the API request
            response = self._make_graphql_request(query)
            
            # Parse response - now handle tiered pricing
            products = response.get("data", {}).get("products", [])
            prices = []
            if products:
                prices = products[0].get("prices", [])
            
            # Check if we have tiered pricing (multiple prices with usage amounts)
            has_tiered_pricing = len(prices) > 1 and any(p.get("startUsageAmount") for p in prices)
            
            if has_tiered_pricing:
                # For tiered pricing, create detailed pricing information
                tier_details = []
                for i, price in enumerate(prices):
                    start_amount = price.get("startUsageAmount", "0")
                    end_amount = price.get("endUsageAmount", "∞")
                    price_usd = price.get("USD", "0")
                    unit = price.get("unit", "requests")
                    
                    if end_amount == "999999999999":
                        end_amount = "∞"
                    
                    tier_details.append(f"Tier {i+1}: {start_amount}-{end_amount} {unit} → ${price_usd} per {unit}")
                
                pricing_details = f"Tiered pricing with {len(prices)} tiers - actual cost depends on usage volume"
                if tier_details:
                    pricing_details += f"\n{'; '.join(tier_details[:3])}"  # Show first 3 tiers
                    if len(tier_details) > 3:
                        pricing_details += f" + {len(tier_details) - 3} more tiers"
                
                # Use first tier price for base calculation
                first_tier_price = float(prices[0].get("USD", 0))
                
                return ResourceCost(
                    resource_type=resource_type,
                    resource_id=resource_properties.get("id", "unknown"),
                    hourly_cost=first_tier_price,
                    monthly_cost=first_tier_price * 730,  # Base calculation
                    currency="USD",
                    usage_type="tiered_pricing",
                    description="Cost varies by usage tier - use EnhancedCostCalculator for accurate estimates",
                    metadata={
                        "pricing_tiers": len(prices),
                        "first_tier_price": first_tier_price,
                        "has_tiered_pricing": True,
                        "all_tier_prices": [float(p.get("USD", 0)) for p in prices],
                        "tier_details": tier_details
                    },
                    pricing_model="usage_based",
                    pricing_details=pricing_details
                )
            
            # Single price or no tiered pricing - extract detailed pricing information
            usd = 0.0
            pricing_details_from_api = None
            unit_from_api = None
            
            for product in products:
                prices = product.get("prices", [])
                for price in prices:
                    price_value = price.get("USD")
                    if price_value is not None:
                        price_float = float(price_value)
                        # For resources like EIP, we want the non-zero price (idle cost)
                        if price_float > 0:
                            usd = price_float
                            pricing_details_from_api = price.get("description", "")
                            unit_from_api = price.get("unit", "")
                            break
                        elif usd == 0.0:  # Keep the first price if no non-zero price found
                            usd = price_float
                            pricing_details_from_api = price.get("description", "")
                            unit_from_api = price.get("unit", "")
                if usd > 0:  # Stop if we found a non-zero price
                    break
            
            # Get pricing model information from static data as fallback
            region = resource_properties.get("Region", "us-east-1")
            pricing_model, base_cost, static_pricing_details, static_unit = get_pricing_info(resource_type, region)
            
            # Create enhanced pricing details using API information when available
            enhanced_pricing_details = None
            if pricing_details_from_api and unit_from_api:
                # Use API information for better details
                if usd > 0:
                    enhanced_pricing_details = f"${usd:.6f} per {unit_from_api}"
                    if pricing_details_from_api:
                        enhanced_pricing_details += f" - {pricing_details_from_api}"
                else:
                    enhanced_pricing_details = f"Usage-based pricing per {unit_from_api}"
                    if pricing_details_from_api:
                        enhanced_pricing_details += f" - {pricing_details_from_api}"
            elif static_pricing_details and static_pricing_details != "Pricing information not available":
                # Use static information as fallback only if it's meaningful
                enhanced_pricing_details = static_pricing_details
            else:
                # Generate enhanced pricing details based on resource type
                enhanced_pricing_details = self._generate_basic_pricing_details(resource_type, usd, unit_from_api or static_unit)
            
            # If we still have generic static information, try to enhance it
            if enhanced_pricing_details in [
                "Customer managed keys with per-request charges",
                "Hosted zone and query pricing", 
                "Dashboard pricing with free tier",
                "Standard and Express workflow pricing",
                "Storage and data transfer pricing",
                "Build minutes by compute type",
                "Management and data event pricing"
            ] or (enhanced_pricing_details and enhanced_pricing_details.startswith("Usage-based pricing per") and usd == 0.0):
                # Replace with enhanced details when we have no actual pricing from API
                enhanced_pricing_details = self._generate_basic_pricing_details(resource_type, usd, unit_from_api or static_unit)
            
            # Special handling for resources that return monthly prices as hourly values
            monthly_priced_resources = {
                "AWS::SecretsManager::Secret": 0.40,  # $0.40 per secret per month
                "AWS::Route53::HostedZone": 0.50,     # $0.50 per hosted zone per month
                "AWS::KMS::Key": 1.00,                # $1.00 per key per month
            }
            
            if resource_type in monthly_priced_resources:
                # For these resources, the API returns the monthly price, not hourly
                expected_monthly_cost = monthly_priced_resources[resource_type]
                if abs(usd - expected_monthly_cost) < 0.01:  # If API returns monthly price
                    monthly_cost = usd
                    hourly_cost = usd / 730
                else:
                    # If API returns hourly price, convert normally
                    hourly_cost = usd
                    monthly_cost = usd * 730
            else:
                # For usage-based resources, provide meaningful cost information
                if pricing_model == "usage_based" and usd == 0.0:
                    # Use base cost if available, otherwise show usage-based pricing
                    monthly_cost = base_cost if base_cost > 0 else 0.0
                    hourly_cost = monthly_cost / 730 if monthly_cost > 0 else 0.0
                else:
                    # Fixed pricing or actual cost returned from API
                    hourly_cost = usd
                    monthly_cost = usd * 730  # Approximate monthly cost
            
            return ResourceCost(
                resource_type=resource_type,
                resource_id=resource_properties.get("id", "unknown"),
                hourly_cost=hourly_cost,
                monthly_cost=monthly_cost,
                currency="USD",
                usage_type="on_demand" if pricing_model == "fixed" else "usage_based",
                description=None,
                metadata={
                    "api_pricing_details": pricing_details_from_api,
                    "api_unit": unit_from_api,
                    "api_price_usd": usd
                },
                pricing_model=pricing_model if pricing_model != "unknown" else "fixed",
                pricing_details=enhanced_pricing_details
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Infracost API: {str(e)}")
            raise PricingDataError(f"Failed to fetch pricing data: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing pricing data for {resource_type}: {str(e)}")
            raise PricingDataError(f"Error processing pricing data: {str(e)}")

    def _generate_basic_pricing_details(self, resource_type: str, price_usd: float, unit: str) -> str:
        """Generate basic pricing details for resources without detailed API information."""
        if price_usd > 0 and unit:
            return f"${price_usd:.6f} per {unit}"
        elif unit:
            # Handle compound units that already contain "per"
            if unit.startswith("per "):
                return f"Usage-based pricing {unit}"
            else:
                return f"Usage-based pricing per {unit}"
        else:
            # Resource-specific fallback details
            resource_details = {
                "AWS::KMS::Key": "$1.00 per key per month + $0.03 per 10,000 requests",
                "AWS::ApiGateway::RestApi": "REST API requests with tiered pricing starting at $3.50 per million requests",
                "AWS::ApiGatewayV2::Api": "HTTP API requests starting at $1.00 per million requests",
                "AWS::Route53::HostedZone": "$0.50 per hosted zone per month + $0.40 per million queries",
                "AWS::CloudWatch::Dashboard": "$3.00 per dashboard per month",
                "AWS::CloudWatch::Alarm": "$0.10 per standard alarm per month",
                "AWS::StepFunctions::StateMachine": "Standard workflows: $0.025 per 1,000 state transitions",
                "AWS::ECR::Repository": "$0.10 per GB per month for storage",
                "AWS::EFS::FileSystem": "$0.30 per GB per month for Standard storage",
                "AWS::CodeBuild::Project": "Build minutes pricing varies by compute type",
                "AWS::CloudTrail::Trail": "First trail free, additional trails $2.00 per 100,000 events",
                "AWS::DynamoDB::Table": "On-demand: $1.25 per million read requests, $1.25 per million write requests + $0.25 per GB storage per month"
            }
            return resource_details.get(resource_type, "Usage-based pricing - cost depends on actual usage")

    def get_supported_resources(self) -> List[str]:
        """Get list of all supported resource types (both paid and free)."""
        paid_resources = list(get_paid_resources().keys())
        free_resources = list(get_free_resources())
        return paid_resources + free_resources

    def is_resource_supported(self, resource_type: str) -> bool:
        """Check if a resource type is supported."""
        return is_paid_resource(resource_type) or is_free_resource(resource_type) 