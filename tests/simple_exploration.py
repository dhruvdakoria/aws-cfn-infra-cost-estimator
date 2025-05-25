#!/usr/bin/env python3
"""
Simple exploration script to find correct patterns for failing services.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def explore_service(service_name):
    """Explore a specific service."""
    
    api_key = os.getenv("INFRACOST_API_KEY")
    if not api_key:
        print("❌ INFRACOST_API_KEY not set")
        return
    
    url = "https://pricing.api.infracost.io/graphql"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print(f"EXPLORING: {service_name}")
    print(f"{'='*60}")
    
    # Query to get all products for this service
    query = f"""
    {{
      products(
        filter: {{
          vendorName: "aws",
          service: "{service_name}",
          region: "us-east-1"
        }}
      ) {{
        productFamily
        attributes {{ key value }}
        prices(filter: {{purchaseOption: "on_demand"}}) {{ USD }}
      }}
    }}
    """
    
    try:
        response = requests.post(url, headers=headers, json={"query": query}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get("data", {}).get("products", [])
            
            if products:
                print(f"✅ Found {len(products)} products")
                
                # Group by product family
                families = {}
                for product in products:
                    family = product.get("productFamily", "Unknown")
                    if family not in families:
                        families[family] = []
                    families[family].append(product)
                
                # Show each product family
                for family, family_products in families.items():
                    print(f"\n📁 Product Family: {family}")
                    
                    # Show first few products with pricing
                    priced_products = [p for p in family_products if p.get("prices")]
                    if priced_products:
                        print(f"   Priced products: {len(priced_products)}")
                        
                        for i, product in enumerate(priced_products[:2]):
                            print(f"   Product {i+1}:")
                            
                            # Show key attributes
                            attributes = product.get("attributes", [])
                            key_attrs = [attr for attr in attributes if attr['key'] in 
                                       ['usagetype', 'operation', 'group', 'instanceType', 'databaseEngine', 'storageClass']]
                            for attr in key_attrs:
                                print(f"     {attr['key']}: {attr['value']}")
                            
                            prices = product.get("prices", [])
                            if prices:
                                print(f"     Price: ${prices[0].get('USD')}")
                            print("")
                    else:
                        print(f"   No priced products found")
            else:
                print(f"❌ No products found for {service_name}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error exploring {service_name}: {e}")

def main():
    """Main function to explore all failing services."""
    services = [
        "AmazonRDS",
        "AmazonS3", 
        "AWSLambda",
        "AmazonCloudWatch",
        "AmazonSNS",
        "AmazonSQS",
        "awskms",
        "AmazonApiGateway",
        "AWSSecretsManager"
    ]
    
    for service in services:
        explore_service(service)

if __name__ == "__main__":
    main() 