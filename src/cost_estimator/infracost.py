import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional
from .core import CostEstimator, ResourceCost, ResourceNotSupportedError, PricingDataError
from .resource_mappings import get_paid_resources, get_free_resources, is_paid_resource, is_free_resource
from .query_builders import get_query_builder
from .pricing_models import get_pricing_info, get_estimated_monthly_cost

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
        
        try:
            # Get the appropriate query builder for this resource type
            query_builder = get_query_builder(resource_type)
            if not query_builder:
                raise ResourceNotSupportedError(f"No query builder found for resource type {resource_type}")
            
            # Build the GraphQL query
            query = query_builder(resource_properties)
            
            # Make the API request
            response = self._make_graphql_request(query)
            
            # Parse response
            products = response.get("data", {}).get("products", [])
            usd = 0.0
            for product in products:
                prices = product.get("prices", [])
                for price in prices:
                    price_value = price.get("USD")
                    if price_value is not None:
                        price_float = float(price_value)
                        # For resources like EIP, we want the non-zero price (idle cost)
                        if price_float > 0:
                            usd = price_float
                            break
                        elif usd == 0.0:  # Keep the first price if no non-zero price found
                            usd = price_float
                if usd > 0:  # Stop if we found a non-zero price
                    break
            
            # Get pricing model information
            pricing_model, base_cost, pricing_details, unit = get_pricing_info(resource_type)
            
            # For usage-based resources, provide meaningful cost information
            if pricing_model == "usage_based" and usd == 0.0:
                # Use base cost if available, otherwise show usage-based pricing
                monthly_cost = base_cost if base_cost > 0 else 0.0
                hourly_cost = monthly_cost / 730 if monthly_cost > 0 else 0.0
                
                return ResourceCost(
                    resource_type=resource_type,
                    resource_id=resource_properties.get("id", "unknown"),
                    hourly_cost=hourly_cost,
                    monthly_cost=monthly_cost,
                    currency="USD",
                    usage_type="usage_based",
                    description=None,
                    metadata={},
                    pricing_model=pricing_model,
                    pricing_details=pricing_details
                )
            else:
                # Fixed pricing or actual cost returned from API
                return ResourceCost(
                    resource_type=resource_type,
                    resource_id=resource_properties.get("id", "unknown"),
                    hourly_cost=usd,
                    monthly_cost=usd * 730,  # Approximate monthly cost
                    currency="USD",
                    usage_type="on_demand",
                    description=None,
                    metadata={},
                    pricing_model=pricing_model if pricing_model != "unknown" else "fixed",
                    pricing_details=pricing_details if pricing_details != "Pricing information not available" else None
                )
            
        except Exception as e:
            error_msg = f"Error getting cost for resource {resource_type}: {str(e)}"
            logger.error(error_msg)
            raise PricingDataError(error_msg)

    def get_supported_resources(self) -> List[str]:
        """Get list of all supported resource types (both paid and free)."""
        paid_resources = list(get_paid_resources().keys())
        free_resources = list(get_free_resources())
        return paid_resources + free_resources

    def is_resource_supported(self, resource_type: str) -> bool:
        """Check if a resource type is supported."""
        return is_paid_resource(resource_type) or is_free_resource(resource_type) 