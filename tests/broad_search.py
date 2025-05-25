#!/usr/bin/env python3
"""
Broad search for KMS and DynamoDB request pricing.
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

def search_for_kms():
    """Search broadly for KMS pricing."""
    estimator = InfracostEstimator()
    
    print("="*80)
    print("BROAD SEARCH FOR KMS")
    print("="*80)
    
    # Search for anything with "kms" in the service name
    query = '''
    {
      products(
        filter: {
          vendorName: "aws",
          region: "us-east-1"
        }
      ) {
        attributes {
          key
          value
        }
        prices(filter: {purchaseOption: "on_demand"}) { 
          USD 
          unit
          description
        }
      }
    }
    '''
    
    try:
        response = estimator._make_graphql_request(query)
        products = response.get("data", {}).get("products", [])
        
        print(f"Searching through {len(products)} products for KMS...")
        
        kms_products = []
        for product in products:
            attributes = {attr['key']: attr['value'] for attr in product.get('attributes', [])}
            
            # Look for KMS-related attributes
            service = attributes.get('servicename', '').lower()
            product_family = attributes.get('productFamily', '').lower()
            usage_type = attributes.get('usagetype', '').lower()
            operation = attributes.get('operation', '').lower()
            
            if any('kms' in field for field in [service, product_family, usage_type, operation]):
                kms_products.append((product, attributes))
        
        print(f"Found {len(kms_products)} KMS-related products")
        
        for i, (product, attributes) in enumerate(kms_products[:5]):
            print(f"\nKMS Product {i+1}:")
            print(f"  Service: {attributes.get('servicename', 'N/A')}")
            print(f"  Product Family: {attributes.get('productFamily', 'N/A')}")
            print(f"  Usage Type: {attributes.get('usagetype', 'N/A')}")
            print(f"  Operation: {attributes.get('operation', 'N/A')}")
            
            prices = product.get('prices', [])
            if prices:
                price = prices[0]
                print(f"  Price: ${price.get('USD')} per {price.get('unit')} - {price.get('description')}")
                
    except Exception as e:
        print(f"Error: {str(e)}")

def search_for_dynamodb_requests():
    """Search broadly for DynamoDB request pricing."""
    estimator = InfracostEstimator()
    
    print("\n" + "="*80)
    print("BROAD SEARCH FOR DYNAMODB REQUESTS")
    print("="*80)
    
    # Search for DynamoDB products with request-related usage types
    query = '''
    {
      products(
        filter: {
          vendorName: "aws",
          service: "AmazonDynamoDB",
          region: "us-east-1"
        }
      ) {
        attributes {
          key
          value
        }
        prices(filter: {purchaseOption: "on_demand"}) { 
          USD 
          unit
          description
        }
      }
    }
    '''
    
    try:
        response = estimator._make_graphql_request(query)
        products = response.get("data", {}).get("products", [])
        
        print(f"Found {len(products)} DynamoDB products")
        
        request_products = []
        for product in products:
            attributes = {attr['key']: attr['value'] for attr in product.get('attributes', [])}
            usage_type = attributes.get('usagetype', '').lower()
            operation = attributes.get('operation', '').lower()
            product_family = attributes.get('productFamily', '').lower()
            
            # Look for request-related terms
            if any(term in usage_type for term in ['request', 'read', 'write', 'capacity']) or \
               any(term in operation for term in ['request', 'read', 'write']) or \
               any(term in product_family for term in ['request', 'api']):
                request_products.append((product, attributes))
        
        print(f"Found {len(request_products)} request-related products")
        
        for i, (product, attributes) in enumerate(request_products):
            print(f"\nDynamoDB Request Product {i+1}:")
            print(f"  Product Family: {attributes.get('productFamily', 'N/A')}")
            print(f"  Usage Type: {attributes.get('usagetype', 'N/A')}")
            print(f"  Operation: {attributes.get('operation', 'N/A')}")
            
            prices = product.get('prices', [])
            if prices:
                price = prices[0]
                print(f"  Price: ${price.get('USD')} per {price.get('unit')} - {price.get('description')}")
                
    except Exception as e:
        print(f"Error: {str(e)}")

def test_specific_dynamodb_families():
    """Test specific DynamoDB product families."""
    estimator = InfracostEstimator()
    
    print("\n" + "="*80)
    print("TESTING SPECIFIC DYNAMODB FAMILIES")
    print("="*80)
    
    # Try different product families
    families = [
        "Database Storage",
        "NoSQL Database", 
        "Database",
        "DynamoDB",
        "API Request",
        "Database Operation",
        "Request"
    ]
    
    for family in families:
        print(f"\nTesting family: {family}")
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
            attributes {{
              key
              value
            }}
            prices(filter: {{purchaseOption: "on_demand"}}) {{ 
              USD 
              unit
              description
            }}
          }}
        }}
        '''
        
        try:
            response = estimator._make_graphql_request(query)
            products = response.get("data", {}).get("products", [])
            
            if products:
                print(f"  ✅ Found {len(products)} products")
                
                # Show usage types
                usage_types = set()
                for product in products:
                    attributes = {attr['key']: attr['value'] for attr in product.get('attributes', [])}
                    usage_type = attributes.get('usagetype', '')
                    if usage_type:
                        usage_types.add(usage_type)
                
                print(f"  Usage types: {sorted(usage_types)}")
            else:
                print(f"  ❌ No products")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

def main():
    """Run all searches."""
    search_for_kms()
    search_for_dynamodb_requests()
    test_specific_dynamodb_families()

if __name__ == "__main__":
    main() 