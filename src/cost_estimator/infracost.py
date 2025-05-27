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

def format_usage_amount(amount_str: str) -> str:
    """Format usage amounts in human-readable format (like Infracost: 333M, 1B, etc.)"""
    try:
        amount = int(amount_str)
        if amount >= 1_000_000_000:
            return f"{amount // 1_000_000_000}B"
        elif amount >= 1_000_000:
            return f"{amount // 1_000_000}M"
        elif amount >= 1_000:
            return f"{amount // 1_000}K"
        else:
            return str(amount)
    except (ValueError, TypeError):
        return amount_str

def format_tier_description(tier_index: int, start_amount: str, end_amount: str, unit: str) -> str:
    """Format tier description in Infracost style."""
    start_formatted = format_usage_amount(start_amount)
    
    if end_amount == "999999999999" or end_amount == "∞":
        if tier_index == 0:
            return f"first {start_formatted}"
        else:
            return f"over {start_formatted}"
    else:
        end_formatted = format_usage_amount(end_amount)
        if tier_index == 0:
            return f"first {end_formatted}"
        else:
            # Calculate the range for this tier
            try:
                start_int = int(start_amount)
                end_int = int(end_amount)
                range_amount = end_int - start_int
                range_formatted = format_usage_amount(str(range_amount))
                return f"next {range_formatted}"
            except (ValueError, TypeError):
                return f"next {end_formatted}"

def format_price_per_unit(price_usd: str, unit: str) -> str:
    """Format price per unit in Infracost style."""
    try:
        price = float(price_usd)
        # Convert to per-million for common units like requests
        if unit.lower() in ["requests", "request"] and price < 0.01:
            return f"${price * 1_000_000:.2f} per 1M {unit.lower()}"
        elif price < 0.000001:
            return f"${price:.8f} per {unit}"
        elif price < 0.001:
            return f"${price:.6f} per {unit}"
        else:
            return f"${price:.2f} per {unit}"
    except (ValueError, TypeError):
        return f"${price_usd} per {unit}"

def create_tiered_pricing_breakdown(prices: List[Dict]) -> Dict[str, Any]:
    """Create a detailed tiered pricing breakdown in Infracost style."""
    tier_breakdown = []
    total_tiers = len(prices)
    
    for i, price in enumerate(prices):
        start_amount = price.get("startUsageAmount", "0")
        end_amount = price.get("endUsageAmount", "∞")
        price_usd = price.get("USD", "0")
        unit = price.get("unit", "requests")
        
        # Format tier description
        tier_desc = format_tier_description(i, start_amount, end_amount, unit)
        price_desc = format_price_per_unit(price_usd, unit)
        
        tier_breakdown.append({
            "tier": i + 1,
            "description": f"{unit.title()} ({tier_desc})",
            "price": price_desc,
            "start_amount": start_amount,
            "end_amount": end_amount,
            "price_usd": float(price_usd),
            "unit": unit
        })
    
    return {
        "total_tiers": total_tiers,
        "tiers": tier_breakdown,
        "summary": f"Tiered pricing with {total_tiers} tiers"
    }

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
            resource_properties["Region"] = "us-east-1"  # Default region
        
        # Add a unique ID for the resource if not present
        if "id" not in resource_properties:
            resource_properties["id"] = f"{resource_type}-{hash(str(resource_properties))}"
        
        try:
            # Special handling for DynamoDB to show comprehensive pricing
            if resource_type == "AWS::DynamoDB::Table":
                return self._get_dynamodb_comprehensive_cost(resource_properties)
            
            # Get the appropriate query builder for this resource type
            query_builder = get_query_builder(resource_type)
            if not query_builder:
                raise ResourceNotSupportedError(f"No query builder found for resource type {resource_type}")
            
            # Build the GraphQL query
            query = query_builder(resource_properties)
            
            # Debug output for DynamoDB (disabled)
            # if resource_type in ["AWS::DynamoDB::Table"]:
            #     print(f"\n🔍 DEBUG: {resource_type}")
            #     print(f"Properties: {resource_properties}")
            #     print(f"Query: {query}")
            
            # Make the API request
            response = self._make_graphql_request(query)
            
            # Debug output for DynamoDB (disabled)
            # if resource_type in ["AWS::DynamoDB::Table"]:
            #     print(f"Response: {json.dumps(response, indent=2)}")
            
            # Parse response - now handle tiered pricing
            products = response.get("data", {}).get("products", [])
            prices = []
            if products:
                prices = products[0].get("prices", [])
            
            # If no products found, check for fallback pricing
            if not products:
                # Get pricing model information from static data as fallback
                region = resource_properties.get("Region", "us-east-1")
                pricing_model, base_cost, static_pricing_details, static_unit = get_pricing_info(resource_type, region)
                
                # Check if we have meaningful pricing information (either base_cost > 0 or detailed pricing info)
                if (base_cost and base_cost > 0) or (static_pricing_details and static_pricing_details != "Pricing information not available"):
                    # Use fallback pricing
                    if base_cost and base_cost > 0:
                        # Fixed cost resource
                        hourly_cost = base_cost / 730
                        monthly_cost = base_cost
                        description = f"Using fallback pricing: {static_pricing_details}"
                    else:
                        # Usage-based resource with base_cost = 0.0
                        hourly_cost = 0.0
                        monthly_cost = 0.0
                        description = "Monthly cost depends on usage"
                    
                    return ResourceCost(
                        resource_type=resource_type,
                        resource_id=resource_properties.get("id", "unknown"),
                        hourly_cost=hourly_cost,
                        monthly_cost=monthly_cost,
                        currency="USD",
                        usage_type="usage_based" if pricing_model == "usage_based" else "fallback_pricing",
                        description=description,
                        metadata={
                            "fallback_pricing": True,
                            "static_pricing_details": static_pricing_details
                        },
                        pricing_model=pricing_model,
                        pricing_details=static_pricing_details
                    )
                else:
                    # No fallback pricing available
                    raise PricingDataError(f"No pricing data available for {resource_type}")
            
            # Check if we have tiered pricing (multiple prices with usage amounts)
            has_tiered_pricing = len(prices) > 1 and any(p.get("startUsageAmount") for p in prices)
            
            if has_tiered_pricing:
                # Create detailed tiered pricing breakdown using Infracost style
                tier_breakdown = create_tiered_pricing_breakdown(prices)
                
                # Create summary for display
                first_tier = tier_breakdown["tiers"][0]
                pricing_summary = f"Tiered pricing with {tier_breakdown['total_tiers']} tiers"
                
                # Create detailed pricing information
                tier_details_formatted = []
                for tier in tier_breakdown["tiers"][:3]:  # Show first 3 tiers
                    tier_details_formatted.append(f"{tier['description']} → {tier['price']}")
                
                if tier_breakdown['total_tiers'] > 3:
                    tier_details_formatted.append(f"+ {tier_breakdown['total_tiers'] - 3} more tiers")
                
                pricing_details = f"{pricing_summary}\n{'; '.join(tier_details_formatted)}"
                
                # Use first tier price for base calculation
                first_tier_price = tier_breakdown["tiers"][0]["price_usd"]
                
                return ResourceCost(
                    resource_type=resource_type,
                    resource_id=resource_properties.get("id", "unknown"),
                    hourly_cost=0.0,  # Don't show hourly for tiered pricing
                    monthly_cost=0.0,  # Don't show fixed monthly for tiered pricing
                    currency="USD",
                    usage_type="tiered_pricing",
                    description="Monthly cost depends on usage",
                    metadata={
                        "pricing_tiers": tier_breakdown["total_tiers"],
                        "first_tier_price": first_tier_price,
                        "has_tiered_pricing": True,
                        "tier_breakdown": tier_breakdown,
                        "tier_details": [f"{t['description']} → {t['price']}" for t in tier_breakdown["tiers"]]
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

    def _get_dynamodb_comprehensive_cost(self, resource_properties: Dict[str, Any]) -> ResourceCost:
        """Get comprehensive DynamoDB pricing including read, write, storage, and additional features."""
        from .query_builders import DynamoDBQueryBuilder
        
        resource_id = resource_properties.get("id", "unknown")
        region = resource_properties.get("Region", "us-east-1")
        billing_mode = resource_properties.get("BillingMode", "PAY_PER_REQUEST")
        
        pricing_components = []
        total_base_cost = 0.0
        
        # 1. Read capacity pricing
        try:
            read_query = DynamoDBQueryBuilder.build_table_query(resource_properties)
            read_response = self._make_graphql_request(read_query)
            read_products = read_response.get("data", {}).get("products", [])
            if read_products and read_products[0].get("prices"):
                read_price = read_products[0]["prices"][0]
                read_usd = float(read_price.get("USD", 0))
                read_unit = read_price.get("unit", "ReadRequestUnits")
                read_desc = read_price.get("description", "")
                
                if read_usd > 0:
                    pricing_components.append(f"Read: ${read_usd * 1000000:.2f}/M")
                else:
                    pricing_components.append(f"Read: ${read_usd:.6f}/{read_unit}")
        except Exception as e:
            pricing_components.append("Read: Pricing unavailable")
        
        # 2. Write capacity pricing
        try:
            write_query = DynamoDBQueryBuilder.build_write_query(resource_properties)
            write_response = self._make_graphql_request(write_query)
            write_products = write_response.get("data", {}).get("products", [])
            if write_products and write_products[0].get("prices"):
                write_price = write_products[0]["prices"][0]
                write_usd = float(write_price.get("USD", 0))
                write_unit = write_price.get("unit", "WriteRequestUnits")
                write_desc = write_price.get("description", "")
                
                if write_usd > 0:
                    pricing_components.append(f"Write: ${write_usd * 1000000:.2f}/M")
                else:
                    pricing_components.append(f"Write: ${write_usd:.6f}/{write_unit}")
        except Exception as e:
            pricing_components.append("Write: Pricing unavailable")
        
        # 3. Storage pricing
        try:
            storage_query = DynamoDBQueryBuilder.build_storage_query(resource_properties)
            storage_response = self._make_graphql_request(storage_query)
            storage_products = storage_response.get("data", {}).get("products", [])
            if storage_products and storage_products[0].get("prices"):
                storage_price = storage_products[0]["prices"][0]
                storage_usd = float(storage_price.get("USD", 0))
                storage_unit = storage_price.get("unit", "GB-Mo")
                
                pricing_components.append(f"Storage: ${storage_usd:.3f}/{storage_unit}")
        except Exception as e:
            pricing_components.append("Storage: Pricing unavailable")
        
        # 4. Streams pricing (if applicable)
        stream_specification = resource_properties.get("StreamSpecification", {})
        if stream_specification.get("StreamEnabled", False):
            try:
                streams_query = DynamoDBQueryBuilder.build_streams_query(resource_properties)
                streams_response = self._make_graphql_request(streams_query)
                streams_products = streams_response.get("data", {}).get("products", [])
                if streams_products and streams_products[0].get("prices"):
                    streams_price = streams_products[0]["prices"][0]
                    streams_usd = float(streams_price.get("USD", 0))
                    streams_unit = streams_price.get("unit", "sRRUs")
                    
                    pricing_components.append(f"Streams: ${streams_usd:.6f}/{streams_unit}")
            except Exception as e:
                pricing_components.append("Streams: Pricing unavailable")
        
        # Create comprehensive pricing details with better formatting
        if pricing_components:
            # Create a more concise format that fits better in tables
            pricing_summary = f"DynamoDB {billing_mode.lower().replace('_', ' ')}: " + " | ".join(pricing_components)
            # Also create a detailed version for metadata
            pricing_details = pricing_summary
        else:
            pricing_details = f"DynamoDB pricing for {region}: On-demand read/write requests + storage costs"
        
        return ResourceCost(
            resource_type="AWS::DynamoDB::Table",
            resource_id=resource_id,
            hourly_cost=0.0,
            monthly_cost=0.0,
            currency="USD",
            usage_type="usage_based",
            description="Monthly cost depends on usage",
            metadata={
                "comprehensive_pricing": True,
                "billing_mode": billing_mode,
                "pricing_components": pricing_components,
                "region": region
            },
            pricing_model="usage_based",
            pricing_details=pricing_details
        )

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
                "AWS::DynamoDB::Table": "DynamoDB pricing: On-demand read/write requests + storage costs (varies by region and table class)"
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