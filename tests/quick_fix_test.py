#!/usr/bin/env python3
"""
Quick test to fix the query builders with correct usage types.
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

def test_fixed_queries():
    """Test the corrected queries."""
    estimator = InfracostEstimator()
    
    print("="*80)
    print("TESTING FIXED QUERIES")
    print("="*80)
    
    # 1. API Gateway with region-prefixed usage type
    print("\n1. API Gateway REST API (Fixed)")
    query = '''
    {
      products(
        filter: {
          vendorName: "aws",
          service: "AmazonApiGateway",
          productFamily: "API Calls",
          region: "us-east-1",
          attributeFilters: [
            { key: "usagetype", value: "USE1-ApiGatewayRequest" }
          ]
        }
      ) {
        prices(filter: {purchaseOption: "on_demand"}) { 
          USD 
          unit
          description
          startUsageAmount
          endUsageAmount
        }
      }
    }
    '''
    
    response = estimator._make_graphql_request(query)
    products = response.get("data", {}).get("products", [])
    if products:
        print(f"✅ Found {len(products)} products")
        prices = products[0].get("prices", [])
        print(f"Has tiered pricing: {len(prices) > 1}")
        for i, price in enumerate(prices[:3]):
            start = price.get('startUsageAmount', '0')
            end = price.get('endUsageAmount', '∞')
            print(f"  Tier {i+1}: {start}-{end} → ${price.get('USD')} per {price.get('unit')}")
    else:
        print("❌ No products found")
    
    # 2. DynamoDB storage (this works)
    print("\n2. DynamoDB Storage (Working)")
    query = '''
    {
      products(
        filter: {
          vendorName: "aws",
          service: "AmazonDynamoDB",
          productFamily: "Database Storage",
          region: "us-east-1",
          attributeFilters: [
            { key: "usagetype", value: "TimedStorage-ByteHrs" }
          ]
        }
      ) {
        prices(filter: {purchaseOption: "on_demand"}) { 
          USD 
          unit
          description
          startUsageAmount
          endUsageAmount
        }
      }
    }
    '''
    
    response = estimator._make_graphql_request(query)
    products = response.get("data", {}).get("products", [])
    if products:
        print(f"✅ Found {len(products)} products")
        prices = products[0].get("prices", [])
        print(f"Has tiered pricing: {len(prices) > 1}")
        for i, price in enumerate(prices[:3]):
            start = price.get('startUsageAmount', '0')
            end = price.get('endUsageAmount', '∞')
            print(f"  Tier {i+1}: {start}-{end} → ${price.get('USD')} per {price.get('unit')}")
    else:
        print("❌ No products found")
    
    # 3. Try KMS with different approach - maybe it's in a different service
    print("\n3. KMS Alternative Search")
    
    # Try searching for encryption-related services
    services_to_try = [
        ("AmazonKMS", "Key Management"),
        ("AWSKeyManagementService", "Encryption"),
        ("awskms", "Encryption"),
        ("AmazonEC2", "Key Management"),  # Sometimes KMS is under EC2
    ]
    
    for service, family in services_to_try:
        print(f"\nTrying {service} - {family}")
        query = f'''
        {{
          products(
            filter: {{
              vendorName: "aws",
              service: "{service}",
              productFamily: "{family}",
              region: "us-east-1"
            }}
          ) {{
            prices(filter: {{purchaseOption: "on_demand"}}) {{ 
              USD 
              unit
              description
            }}
            attributes {{
              key
              value
            }}
          }}
        }}
        '''
        
        try:
            response = estimator._make_graphql_request(query)
            products = response.get("data", {}).get("products", [])
            if products:
                print(f"  ✅ Found {len(products)} products")
                # Show first product
                product = products[0]
                attributes = {attr['key']: attr['value'] for attr in product.get('attributes', [])}
                print(f"    Usage Type: {attributes.get('usagetype', 'N/A')}")
                prices = product.get('prices', [])
                if prices:
                    price = prices[0]
                    print(f"    Price: ${price.get('USD')} per {price.get('unit')}")
                break
            else:
                print(f"  ❌ No products")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

def main():
    """Run the tests."""
    test_fixed_queries()

if __name__ == "__main__":
    main() 