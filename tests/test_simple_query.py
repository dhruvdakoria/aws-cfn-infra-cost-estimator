#!/usr/bin/env python3
"""
Test simple manually crafted queries to identify syntax issues.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def test_simple_query():
    """Test a simple manually crafted query."""
    
    api_key = os.getenv("INFRACOST_API_KEY")
    if not api_key:
        print("❌ INFRACOST_API_KEY not set")
        return
    
    # Simple query without attribute filters first
    query1 = '''
    {
      products(
        filter: {
          vendorName: "aws",
          service: "AmazonEC2",
          productFamily: "Compute Instance",
          region: "us-east-1"
        }
      ) {
        prices(filter: {purchaseOption: "on_demand"}) { USD }
      }
    }
    '''
    
    # Query with one attribute filter
    query2 = '''
    {
      products(
        filter: {
          vendorName: "aws",
          service: "AmazonEC2",
          productFamily: "Compute Instance",
          region: "us-east-1",
          attributeFilters: [
            { key: "instanceType", value: "t3.medium" }
          ]
        }
      ) {
        prices(filter: {purchaseOption: "on_demand"}) { USD }
      }
    }
    '''
    
    url = "https://pricing.api.infracost.io/graphql"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    for i, query in enumerate([query1, query2], 1):
        print(f"\n{'='*50}")
        print(f"Testing Query {i}")
        print(f"{'='*50}")
        print(query)
        
        try:
            response = requests.post(url, headers=headers, json={"query": query}, timeout=30)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("data", {}).get("products", [])
                print(f"✅ Success! Found {len(products)} products")
                if products:
                    print(f"First product: {products[0].get('description', 'No description')}")
            else:
                print(f"❌ API Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_simple_query() 