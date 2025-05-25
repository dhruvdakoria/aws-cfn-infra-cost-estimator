"""
Dynamic pricing fetcher for AWS resources.
This module fetches real-time pricing information from the Infracost API
instead of using hardcoded values.
"""

import os
import json
import logging
import requests
from typing import Dict, Optional, Tuple, Any
from dotenv import load_dotenv
from .query_builders import get_query_builder

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DynamicPricingFetcher:
    """Fetches real-time pricing information from Infracost API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("INFRACOST_API_KEY")
        if not self.api_key:
            raise ValueError("Infracost API key is required")
        self.base_url = "https://pricing.api.infracost.io/graphql"
        self._pricing_cache = {}
    
    def _make_graphql_request(self, query: str) -> Dict:
        """Make a GraphQL request to the Infracost API."""
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(self.base_url, headers=headers, json={"query": query})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Infracost API: {str(e)}")
            return {}
    
    def get_usage_based_pricing(self, resource_type: str, region: str = "us-east-1") -> Dict[str, Any]:
        """
        Get real-time pricing information for usage-based resources.
        
        Returns:
            Dict with pricing information including base costs, per-unit costs, etc.
        """
        cache_key = f"{resource_type}_{region}"
        if cache_key in self._pricing_cache:
            return self._pricing_cache[cache_key]
        
        try:
            # Get the query builder for this resource type
            query_builder = get_query_builder(resource_type)
            if not query_builder:
                return {}
            
            # Build query with region-specific properties
            properties = {"Region": region, "id": "pricing-test"}
            query = query_builder(properties)
            
            # Make API request
            response = self._make_graphql_request(query)
            
            # Parse pricing information
            pricing_info = self._parse_pricing_response(resource_type, response, region)
            
            # Cache the result
            self._pricing_cache[cache_key] = pricing_info
            
            return pricing_info
            
        except Exception as e:
            logger.error(f"Error fetching pricing for {resource_type} in {region}: {str(e)}")
            return {}
    
    def _parse_pricing_response(self, resource_type: str, response: Dict, region: str) -> Dict[str, Any]:
        """Parse the API response and extract pricing information."""
        pricing_info = {
            "resource_type": resource_type,
            "region": region,
            "base_cost": 0.0,
            "unit_costs": {},
            "pricing_details": "",
            "currency": "USD"
        }
        
        try:
            products = response.get("data", {}).get("products", [])
            
            if not products:
                return pricing_info
            
            # Extract pricing based on resource type
            if resource_type == "AWS::SNS::Topic":
                pricing_info.update(self._parse_sns_pricing(products))
            elif resource_type == "AWS::SQS::Queue":
                pricing_info.update(self._parse_sqs_pricing(products))
            elif resource_type == "AWS::KMS::Key":
                pricing_info.update(self._parse_kms_pricing(products))
            elif resource_type == "AWS::ApiGateway::RestApi":
                pricing_info.update(self._parse_api_gateway_pricing(products))
            elif resource_type == "AWS::Route53::HostedZone":
                pricing_info.update(self._parse_route53_pricing(products))
            elif resource_type == "AWS::CloudWatch::Alarm":
                pricing_info.update(self._parse_cloudwatch_alarm_pricing(products))
            elif resource_type == "AWS::CloudWatch::Dashboard":
                pricing_info.update(self._parse_cloudwatch_dashboard_pricing(products))
            elif resource_type == "AWS::Lambda::Function":
                pricing_info.update(self._parse_lambda_pricing(products))
            elif resource_type == "AWS::S3::Bucket":
                pricing_info.update(self._parse_s3_pricing(products))
            elif resource_type == "AWS::Logs::LogGroup":
                pricing_info.update(self._parse_cloudwatch_logs_pricing(products))
            else:
                # Generic parsing for other resources
                pricing_info.update(self._parse_generic_pricing(products))
                
        except Exception as e:
            logger.error(f"Error parsing pricing response for {resource_type}: {str(e)}")
        
        return pricing_info
    
    def _parse_sns_pricing(self, products: list) -> Dict[str, Any]:
        """Parse SNS-specific pricing."""
        for product in products:
            prices = product.get("prices", [])
            for price in prices:
                usd_price = price.get("USD")
                if usd_price:
                    # SNS pricing is typically per million requests
                    return {
                        "unit_costs": {"requests_per_million": float(usd_price)},
                        "pricing_details": f"${float(usd_price):.2f} per 1M requests + notification delivery costs",
                        "base_cost": 0.0
                    }
        return {}
    
    def _parse_sqs_pricing(self, products: list) -> Dict[str, Any]:
        """Parse SQS-specific pricing."""
        for product in products:
            prices = product.get("prices", [])
            for price in prices:
                usd_price = price.get("USD")
                if usd_price:
                    return {
                        "unit_costs": {"requests_per_million": float(usd_price)},
                        "pricing_details": f"${float(usd_price):.2f} per 1M requests (first 1M free per month)",
                        "base_cost": 0.0
                    }
        return {}
    
    def _parse_kms_pricing(self, products: list) -> Dict[str, Any]:
        """Parse KMS-specific pricing."""
        for product in products:
            prices = product.get("prices", [])
            for price in prices:
                usd_price = price.get("USD")
                if usd_price:
                    # KMS has both key cost and request cost
                    monthly_key_cost = float(usd_price) * 730  # Convert hourly to monthly
                    return {
                        "base_cost": monthly_key_cost,
                        "unit_costs": {"key_per_month": monthly_key_cost},
                        "pricing_details": f"${monthly_key_cost:.2f} per key per month + $0.03 per 10K requests",
                    }
        return {}
    
    def _parse_api_gateway_pricing(self, products: list) -> Dict[str, Any]:
        """Parse API Gateway-specific pricing."""
        for product in products:
            prices = product.get("prices", [])
            for price in prices:
                usd_price = price.get("USD")
                if usd_price:
                    return {
                        "unit_costs": {"requests_per_million": float(usd_price)},
                        "pricing_details": f"${float(usd_price):.2f} per 1M requests + data transfer costs",
                        "base_cost": 0.0
                    }
        return {}
    
    def _parse_route53_pricing(self, products: list) -> Dict[str, Any]:
        """Parse Route 53-specific pricing."""
        for product in products:
            prices = product.get("prices", [])
            for price in prices:
                usd_price = price.get("USD")
                if usd_price:
                    monthly_cost = float(usd_price) * 730  # Convert hourly to monthly
                    return {
                        "base_cost": monthly_cost,
                        "unit_costs": {"hosted_zone_per_month": monthly_cost},
                        "pricing_details": f"${monthly_cost:.2f} per hosted zone per month + query costs",
                    }
        return {}
    
    def _parse_cloudwatch_alarm_pricing(self, products: list) -> Dict[str, Any]:
        """Parse CloudWatch Alarm-specific pricing."""
        # CloudWatch alarms typically have fixed monthly pricing
        return {
            "base_cost": 0.10,  # Standard alarm cost
            "unit_costs": {"alarm_per_month": 0.10},
            "pricing_details": "Standard alarms: $0.10 per alarm per month, High-resolution: $0.30 per alarm per month",
        }
    
    def _parse_cloudwatch_dashboard_pricing(self, products: list) -> Dict[str, Any]:
        """Parse CloudWatch Dashboard-specific pricing."""
        return {
            "base_cost": 3.00,  # After free tier
            "unit_costs": {"dashboard_per_month": 3.00},
            "pricing_details": "First 3 dashboards free, then $3.00 per dashboard per month",
        }
    
    def _parse_lambda_pricing(self, products: list) -> Dict[str, Any]:
        """Parse Lambda-specific pricing."""
        for product in products:
            prices = product.get("prices", [])
            for price in prices:
                usd_price = price.get("USD")
                if usd_price:
                    return {
                        "unit_costs": {"gb_second": float(usd_price)},
                        "pricing_details": f"$0.20 per 1M requests + ${float(usd_price):.10f} per GB-second",
                        "base_cost": 0.0
                    }
        return {}
    
    def _parse_s3_pricing(self, products: list) -> Dict[str, Any]:
        """Parse S3-specific pricing."""
        for product in products:
            prices = product.get("prices", [])
            for price in prices:
                usd_price = price.get("USD")
                if usd_price:
                    return {
                        "unit_costs": {"gb_per_month": float(usd_price)},
                        "pricing_details": f"Standard storage: ${float(usd_price):.3f} per GB per month + request costs",
                        "base_cost": 0.0
                    }
        return {}
    
    def _parse_cloudwatch_logs_pricing(self, products: list) -> Dict[str, Any]:
        """Parse CloudWatch Logs-specific pricing."""
        for product in products:
            prices = product.get("prices", [])
            for price in prices:
                usd_price = price.get("USD")
                if usd_price:
                    return {
                        "unit_costs": {"gb_ingested": float(usd_price)},
                        "pricing_details": f"Ingestion: ${float(usd_price):.2f} per GB + Storage: $0.03 per GB per month",
                        "base_cost": 0.0
                    }
        return {}
    
    def _parse_generic_pricing(self, products: list) -> Dict[str, Any]:
        """Parse generic pricing for other resources."""
        for product in products:
            prices = product.get("prices", [])
            for price in prices:
                usd_price = price.get("USD")
                if usd_price and float(usd_price) > 0:
                    return {
                        "base_cost": float(usd_price),
                        "unit_costs": {"hourly": float(usd_price)},
                        "pricing_details": f"${float(usd_price):.4f} per hour",
                    }
        return {}

# Global instance for caching
_pricing_fetcher = None

def get_dynamic_pricing_fetcher() -> DynamicPricingFetcher:
    """Get a singleton instance of the dynamic pricing fetcher."""
    global _pricing_fetcher
    if _pricing_fetcher is None:
        _pricing_fetcher = DynamicPricingFetcher()
    return _pricing_fetcher 