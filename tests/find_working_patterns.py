#!/usr/bin/env python3
"""
Find working patterns for KMS, API Gateway, and DynamoDB.
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

def test_working_patterns():
    """Test the patterns that we know work."""
    estimator = InfracostEstimator()
    
    print("="*80)
    print("TESTING WORKING PATTERNS")
    print("="*80)
    
    # Test API Gateway with correct usage type
    print("\n1. API Gateway REST API (USE1-ApiGatewayRequest)")
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
        for i, price in enumerate(prices[:3]):
            print(f"  Price {i+1}: ${price.get('USD')} per {price.get('unit')} - {price.get('description')}")
    else:
        print("❌ No products found")
    
    # Test DynamoDB storage
    print("\n2. DynamoDB Storage (TimedStorage-ByteHrs)")
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
        for i, price in enumerate(prices[:3]):
            print(f"  Price {i+1}: ${price.get('USD')} per {price.get('unit')} - {price.get('description')}")
    else:
        print("❌ No products found")

def explore_kms_alternatives():
    """Explore different ways to find KMS pricing."""
    estimator = InfracostEstimator()
    
    print("\n" + "="*80)
    print("EXPLORING KMS ALTERNATIVES")
    print("="*80)
    
    # Try different service names for KMS
    kms_services = ["awskms", "AWSKeyManagementService", "AWSKMS", "AmazonKMS"]
    kms_families = ["Key Management", "KMS", "Encryption", "Keys"]
    
    for service in kms_services:
        for family in kms_families:
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
                    # Show first product details
                    product = products[0]
                    attributes = {attr['key']: attr['value'] for attr in product.get('attributes', [])}
                    print(f"    Usage Type: {attributes.get('usagetype', 'N/A')}")
                    prices = product.get('prices', [])
                    if prices:
                        price = prices[0]
                        print(f"    Price: ${price.get('USD')} per {price.get('unit')} - {price.get('description')}")
                    break
                else:
                    print(f"  ❌ No products")
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")

def explore_dynamodb_requests():
    """Explore DynamoDB request pricing."""
    estimator = InfracostEstimator()
    
    print("\n" + "="*80)
    print("EXPLORING DYNAMODB REQUEST PRICING")
    print("="*80)
    
    # Try different product families for DynamoDB
    families = ["Database Storage", "NoSQL Database", "Database", "DynamoDB"]
    
    for family in families:
        print(f"\nTrying AmazonDynamoDB - {family}")
        query = f'''
        {{
          products(
            filter: {{
              vendorName: "aws",
              service: "AmazonDynamoDB",
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
                
                # Collect all usage types
                usage_types = set()
                for product in products:
                    attributes = {attr['key']: attr['value'] for attr in product.get('attributes', [])}
                    usage_type = attributes.get('usagetype', '')
                    if usage_type:
                        usage_types.add(usage_type)
                
                print(f"  Usage types: {sorted(usage_types)}")
                
                # Show products with request-related usage types
                for product in products:
                    attributes = {attr['key']: attr['value'] for attr in product.get('attributes', [])}
                    usage_type = attributes.get('usagetype', '')
                    if 'request' in usage_type.lower() or 'read' in usage_type.lower() or 'write' in usage_type.lower():
                        print(f"    Request-related: {usage_type}")
                        prices = product.get('prices', [])
                        if prices:
                            price = prices[0]
                            print(f"      ${price.get('USD')} per {price.get('unit')} - {price.get('description')}")
                break
            else:
                print(f"  ❌ No products")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

def main():
    """Run all explorations."""
    test_working_patterns()
    explore_kms_alternatives()
    explore_dynamodb_requests()

if __name__ == "__main__":
    main() 