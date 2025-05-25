#!/usr/bin/env python3
"""
Quick test to find correct DynamoDB pricing patterns.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def test_dynamodb_patterns():
    """Test different DynamoDB patterns."""
    api_key = os.getenv('INFRACOST_API_KEY')
    if not api_key:
        print("INFRACOST_API_KEY not set")
        return
    
    url = "https://pricing.api.infracost.io/graphql"
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Test different DynamoDB patterns
    patterns = [
        {
            "name": "DynamoDB Service Exploration",
            "query": """
            {
              products(
                filter: {
                  vendorName: "aws",
                  service: "AmazonDynamoDB",
                  region: "us-east-1"
                }
              ) {
                service
                productFamily
                attributes { key value }
                prices(filter: {purchaseOption: "on_demand"}) { USD }
              }
            }
            """
        },
        {
            "name": "DynamoDB Database Storage",
            "query": """
            {
              products(
                filter: {
                  vendorName: "aws",
                  service: "AmazonDynamoDB",
                  productFamily: "Database Storage",
                  region: "us-east-1"
                }
              ) {
                service
                productFamily
                attributes { key value }
                prices(filter: {purchaseOption: "on_demand"}) { USD }
              }
            }
            """
        },
        {
            "name": "DynamoDB ReadRequestUnits",
            "query": """
            {
              products(
                filter: {
                  vendorName: "aws",
                  region: "us-east-1",
                  attributeFilters: [
                    { key: "usagetype", value: "DynamoDB-ReadRequestUnits" }
                  ]
                }
              ) {
                service
                productFamily
                attributes { key value }
                prices(filter: {purchaseOption: "on_demand"}) { USD }
              }
            }
            """
        },
        {
            "name": "DynamoDB WriteRequestUnits",
            "query": """
            {
              products(
                filter: {
                  vendorName: "aws",
                  region: "us-east-1",
                  attributeFilters: [
                    { key: "usagetype", value: "DynamoDB-WriteRequestUnits" }
                  ]
                }
              ) {
                service
                productFamily
                attributes { key value }
                prices(filter: {purchaseOption: "on_demand"}) { USD }
              }
            }
            """
        }
    ]
    
    for pattern in patterns:
        print(f"\n{'='*60}")
        print(f"Testing: {pattern['name']}")
        print(f"{'='*60}")
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json={"query": pattern['query']},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("data", {}).get("products", [])
                
                if products:
                    print(f"✅ Found {len(products)} products")
                    for i, product in enumerate(products[:3]):  # Show first 3
                        print(f"Product {i+1}:")
                        print(f"  Service: {product.get('service')}")
                        print(f"  ProductFamily: {product.get('productFamily')}")
                        
                        # Show key attributes
                        attributes = product.get('attributes', [])
                        for attr in attributes:
                            if attr['key'] in ['usagetype', 'operation', 'group', 'productFamily']:
                                print(f"  {attr['key']}: {attr['value']}")
                        
                        prices = product.get('prices', [])
                        if prices:
                            print(f"  Price: ${prices[0].get('USD')}")
                        else:
                            print(f"  Price: No on-demand pricing")
                        print("")
                else:
                    print(f"⚠️ No products found")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_dynamodb_patterns() 