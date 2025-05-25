#!/usr/bin/env python3
"""
Explore available services and product families for failing resources.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def explore_service(service_name, search_terms):
    """Explore a service to find correct product families."""
    
    api_key = os.getenv("INFRACOST_API_KEY")
    if not api_key:
        print("❌ INFRACOST_API_KEY not set")
        return
    
    print(f"\n{'='*60}")
    print(f"Exploring service: {service_name}")
    print(f"Search terms: {search_terms}")
    print(f"{'='*60}")
    
    # Query to get all product families for a service
    query = f'''
    {{
      products(
        filter: {{
          vendorName: "aws",
          service: "{service_name}",
          region: "us-east-1"
        }}
      ) {{
        productFamily
        description
        attributes {{
          key
          value
        }}
      }}
    }}
    '''
    
    url = "https://pricing.api.infracost.io/graphql"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json={"query": query}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get("data", {}).get("products", [])
            
            if products:
                print(f"✅ Found {len(products)} products")
                
                # Get unique product families
                families = set()
                relevant_products = []
                
                for product in products:
                    family = product.get("productFamily", "")
                    families.add(family)
                    
                    # Check if this product is relevant to our search terms
                    description = product.get("description", "").lower()
                    if any(term.lower() in description for term in search_terms):
                        relevant_products.append(product)
                
                print(f"\nProduct Families found:")
                for family in sorted(families):
                    print(f"  - {family}")
                
                if relevant_products:
                    print(f"\nRelevant products (matching search terms):")
                    for i, product in enumerate(relevant_products[:5]):  # Show first 5
                        print(f"  {i+1}. Family: {product.get('productFamily', 'N/A')}")
                        print(f"     Description: {product.get('description', 'N/A')}")
                        attributes = product.get("attributes", [])
                        if attributes:
                            print(f"     Attributes:")
                            for attr in attributes[:3]:  # Show first 3 attributes
                                print(f"       {attr.get('key', 'N/A')}: {attr.get('value', 'N/A')}")
                        print()
                else:
                    print(f"\n❌ No products found matching search terms: {search_terms}")
            else:
                print("❌ No products found for this service")
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def main():
    """Explore services for failing resources."""
    
    services_to_explore = [
        ("AmazonRDS", ["mysql", "database", "instance"]),
        ("AmazonS3", ["storage", "bucket"]),
        ("AWSLambda", ["lambda", "function", "compute"]),
        ("AmazonCloudWatch", ["log", "logs"]),
        ("AmazonSNS", ["notification", "topic", "message"]),
        ("AmazonSQS", ["queue", "message"]),
        ("awskms", ["key", "encryption"]),
        ("AWSSecretsManager", ["secret", "password"]),
        ("AmazonApiGateway", ["api", "gateway", "rest"])
    ]
    
    for service, search_terms in services_to_explore:
        explore_service(service, search_terms)

if __name__ == "__main__":
    main() 