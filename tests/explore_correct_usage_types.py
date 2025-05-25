#!/usr/bin/env python3
"""
Explore correct usage types for KMS, API Gateway, and DynamoDB.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cost_estimator.infracost import InfracostEstimator

# Load environment variables
load_dotenv()

def explore_service(service_name, product_family, region="us-east-1"):
    """Explore a service to find available usage types."""
    print(f"\n{'='*80}")
    print(f"Exploring {service_name} - {product_family}")
    print(f"{'='*80}")
    
    # Query without usage type filter to see what's available
    query = f'''
    {{
      products(
        filter: {{
          vendorName: "aws",
          service: "{service_name}",
          productFamily: "{product_family}",
          region: "{region}"
        }}
      ) {{
        prices(filter: {{purchaseOption: "on_demand"}}) {{ 
          USD 
          unit
          description
          startUsageAmount
          endUsageAmount
        }}
        attributes {{
          key
          value
        }}
      }}
    }}
    '''
    
    try:
        estimator = InfracostEstimator()
        response = estimator._make_graphql_request(query)
        
        products = response.get("data", {}).get("products", [])
        print(f"Found {len(products)} products")
        
        # Collect all usage types
        usage_types = set()
        
        for i, product in enumerate(products[:5]):  # Limit to first 5 products
            print(f"\nProduct {i+1}:")
            
            # Show attributes
            attributes = product.get("attributes", [])
            product_attrs = {}
            for attr in attributes:
                key = attr.get("key", "")
                value = attr.get("value", "")
                product_attrs[key] = value
                if key == "usagetype":
                    usage_types.add(value)
            
            print(f"  Usage Type: {product_attrs.get('usagetype', 'N/A')}")
            print(f"  Operation: {product_attrs.get('operation', 'N/A')}")
            print(f"  Location: {product_attrs.get('location', 'N/A')}")
            print(f"  Group: {product_attrs.get('group', 'N/A')}")
            
            # Show prices
            prices = product.get("prices", [])
            print(f"  Prices: {len(prices)}")
            for j, price in enumerate(prices[:3]):  # Limit to first 3 prices
                usd = price.get("USD", "N/A")
                unit = price.get("unit", "N/A")
                description = price.get("description", "N/A")
                print(f"    Price {j+1}: ${usd} per {unit} - {description}")
        
        print(f"\nAll Usage Types found:")
        for usage_type in sorted(usage_types):
            print(f"  - {usage_type}")
            
    except Exception as e:
        print(f"Error exploring service: {str(e)}")

def test_specific_usage_type(service_name, product_family, usage_type, region="us-east-1"):
    """Test a specific usage type."""
    print(f"\n{'='*60}")
    print(f"Testing {service_name} with usage type: {usage_type}")
    print(f"{'='*60}")
    
    query = f'''
    {{
      products(
        filter: {{
          vendorName: "aws",
          service: "{service_name}",
          productFamily: "{product_family}",
          region: "{region}",
          attributeFilters: [
            {{ key: "usagetype", value: "{usage_type}" }}
          ]
        }}
      ) {{
        prices(filter: {{purchaseOption: "on_demand"}}) {{ 
          USD 
          unit
          description
          startUsageAmount
          endUsageAmount
        }}
      }}
    }}
    '''
    
    try:
        estimator = InfracostEstimator()
        response = estimator._make_graphql_request(query)
        
        products = response.get("data", {}).get("products", [])
        if products:
            print(f"✅ Found {len(products)} products")
            for i, product in enumerate(products[:2]):
                prices = product.get("prices", [])
                print(f"Product {i+1}: {len(prices)} prices")
                for j, price in enumerate(prices[:3]):
                    usd = price.get("USD", "N/A")
                    unit = price.get("unit", "N/A")
                    description = price.get("description", "N/A")
                    print(f"  ${usd} per {unit} - {description}")
        else:
            print("❌ No products found")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    """Explore services to find correct usage types."""
    
    # Explore KMS
    explore_service("awskms", "Key Management")
    
    # Test some common KMS usage types
    kms_usage_types = ["KMS-Keys", "KMS-Requests", "KMSKeys", "Keys"]
    for usage_type in kms_usage_types:
        test_specific_usage_type("awskms", "Key Management", usage_type)
    
    # Explore API Gateway
    explore_service("AmazonApiGateway", "API Calls")
    
    # Test some common API Gateway usage types
    api_usage_types = ["ApiGatewayRequest", "REST-API-Request", "ApiGateway-Request", "Requests"]
    for usage_type in api_usage_types:
        test_specific_usage_type("AmazonApiGateway", "API Calls", usage_type)
    
    # Explore DynamoDB
    explore_service("AmazonDynamoDB", "Database Storage")
    
    # Test some common DynamoDB usage types
    dynamo_usage_types = ["ReadRequestUnits", "WriteRequestUnits", "TimedStorage-ByteHrs", "RequestUnits"]
    for usage_type in dynamo_usage_types:
        test_specific_usage_type("AmazonDynamoDB", "Database Storage", usage_type)

if __name__ == "__main__":
    main() 