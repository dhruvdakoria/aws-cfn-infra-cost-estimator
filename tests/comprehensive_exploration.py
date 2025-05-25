#!/usr/bin/env python3
"""
Comprehensive exploration script to find correct patterns for all failing services.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def explore_all_services():
    """Explore all services to find correct patterns."""
    
    api_key = os.getenv("INFRACOST_API_KEY")
    if not api_key:
        print("❌ INFRACOST_API_KEY not set")
        return
    
    url = "https://pricing.api.infracost.io/graphql"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Services to explore
    services_to_explore = [
        {
            "name": "RDS",
            "service": "AmazonRDS",
            "search_terms": ["Database", "Instance", "MySQL", "db.t3.micro"]
        },
        {
            "name": "S3",
            "service": "AmazonS3", 
            "search_terms": ["Storage", "Standard", "ByteHrs"]
        },
        {
            "name": "Lambda",
            "service": "AWSLambda",
            "search_terms": ["Serverless", "Function", "GB-Second", "Request"]
        },
        {
            "name": "CloudWatch",
            "service": "AmazonCloudWatch",
            "search_terms": ["Log", "Storage", "Data", "Ingestion"]
        },
        {
            "name": "SNS",
            "service": "AmazonSNS",
            "search_terms": ["Notification", "Request", "Message"]
        },
        {
            "name": "SQS", 
            "service": "AmazonSQS",
            "search_terms": ["Queue", "Request", "Message"]
        },
        {
            "name": "KMS",
            "service": "awskms",
            "search_terms": ["Key", "Request", "Management"]
        },
        {
            "name": "API Gateway",
            "service": "AmazonApiGateway",
            "search_terms": ["API", "Request", "REST", "HTTP"]
        },
        {
            "name": "Secrets Manager",
            "service": "AWSSecretsManager",
            "search_terms": ["Secret", "Management"]
        }
    ]
    
    for service_info in services_to_explore:
        print(f"\n{'='*80}")
        print(f"EXPLORING: {service_info['name']} ({service_info['service']})")
        print(f"{'='*80}")
        
        # First, get all products for this service
        query = f'''
        {{
          products(
            filter: {{
              vendorName: "aws",
              service: "{service_info['service']}",
              region: "us-east-1"
            }}
          ) {{
            productFamily
            description
            attributes {{
              key
              value
            }}
            prices(filter: {{purchaseOption: "on_demand"}}) {{ USD }}
          }}
        }}
        '''
        
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
                        print(f"   Products: {len(family_products)}")
                        
                        # Show first few products with pricing
                        priced_products = [p for p in family_products if p.get("prices")]
                        if priced_products:
                            print(f"   Priced products: {len(priced_products)}")
                            
                            for i, product in enumerate(priced_products[:3]):
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
                    print(f"❌ No products found for {service_info['service']}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error exploring {service_info['name']}: {e}")

if __name__ == "__main__":
    explore_all_services() 