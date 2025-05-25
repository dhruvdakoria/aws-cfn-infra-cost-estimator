#!/usr/bin/env python3
"""
Debug script to investigate why specific resources are returning $0.00 cost.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cost_estimator.query_builders import (
    EC2QueryBuilder, RDSQueryBuilder, S3QueryBuilder, LambdaQueryBuilder,
    CloudWatchQueryBuilder, SNSQueryBuilder, SQSQueryBuilder, KMSQueryBuilder,
    APIGatewayQueryBuilder, SecretsManagerQueryBuilder
)

load_dotenv()

def test_api_query(query_name, query):
    """Test a specific query against the Infracost API."""
    print(f"\n{'='*60}")
    print(f"Testing: {query_name}")
    print(f"{'='*60}")
    
    api_key = os.getenv("INFRACOST_API_KEY")
    if not api_key:
        print("❌ INFRACOST_API_KEY not set")
        return
    
    url = "https://pricing.api.infracost.io/graphql"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    print(f"Query: {query}")
    
    try:
        response = requests.post(url, headers=headers, json={"query": query}, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check if we got products
            products = data.get("data", {}).get("products", [])
            if products:
                print(f"✅ Found {len(products)} products")
                for i, product in enumerate(products[:3]):  # Show first 3
                    print(f"  Product {i+1}: {product.get('description', 'No description')}")
                    prices = product.get("prices", [])
                    if prices:
                        print(f"    Price: {prices[0].get('USD', 'No price')}")
            else:
                print("❌ No products found")
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def main():
    """Test the failing resources."""
    
    # Test cases for failing resources
    test_cases = [
        {
            "name": "EIP (Idle)",
            "query": EC2QueryBuilder.build_eip_query({"Region": "us-east-1"})
        },
        {
            "name": "RDS Instance (db.t3.micro, MySQL)",
            "query": RDSQueryBuilder.build_instance_query({
                "Region": "us-east-1",
                "DBInstanceClass": "db.t3.micro",
                "Engine": "mysql"
            })
        },
        {
            "name": "S3 Bucket (Standard)",
            "query": S3QueryBuilder.build_bucket_query({
                "Region": "us-east-1",
                "StorageClass": "Standard"
            })
        },
        {
            "name": "Lambda Function",
            "query": LambdaQueryBuilder.build_function_query({"Region": "us-east-1"})
        },
        {
            "name": "CloudWatch Log Group",
            "query": CloudWatchQueryBuilder.build_logs_query({"Region": "us-east-1"})
        },
        {
            "name": "SNS Topic",
            "query": SNSQueryBuilder.build_topic_query({"Region": "us-east-1"})
        },
        {
            "name": "SQS Queue",
            "query": SQSQueryBuilder.build_queue_query({"Region": "us-east-1"})
        },
        {
            "name": "KMS Key",
            "query": KMSQueryBuilder.build_key_query({"Region": "us-east-1"})
        },
        {
            "name": "API Gateway REST API",
            "query": APIGatewayQueryBuilder.build_rest_api_query({"Region": "us-east-1"})
        },
        {
            "name": "Secrets Manager Secret",
            "query": SecretsManagerQueryBuilder.build_secret_query({"Region": "us-east-1"})
        }
    ]
    
    for test_case in test_cases:
        test_api_query(test_case["name"], test_case["query"])

if __name__ == "__main__":
    main() 