#!/usr/bin/env python3
"""
Debug script to test query builders for KMS, API Gateway, and DynamoDB.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cost_estimator.query_builders import (
    KMSQueryBuilder, 
    APIGatewayQueryBuilder, 
    DynamoDBQueryBuilder,
    get_query_builder
)
from cost_estimator.infracost import InfracostEstimator

# Load environment variables
load_dotenv()

def test_query_builder(resource_type, properties, query_builder_func):
    """Test a specific query builder."""
    print(f"\n{'='*60}")
    print(f"Testing {resource_type}")
    print(f"{'='*60}")
    
    # Build the query
    query = query_builder_func(properties)
    print(f"Generated Query:")
    print(query)
    
    # Test with Infracost API
    try:
        estimator = InfracostEstimator()
        response = estimator._make_graphql_request(query)
        
        print(f"\nAPI Response:")
        print(json.dumps(response, indent=2))
        
        # Check if we got products and prices
        products = response.get("data", {}).get("products", [])
        if products:
            print(f"\nFound {len(products)} products")
            for i, product in enumerate(products):
                prices = product.get("prices", [])
                print(f"Product {i+1}: {len(prices)} prices")
                for j, price in enumerate(prices):
                    usd = price.get("USD", "N/A")
                    unit = price.get("unit", "N/A")
                    description = price.get("description", "N/A")
                    print(f"  Price {j+1}: ${usd} per {unit} - {description}")
        else:
            print("\nNo products found in response")
            
    except Exception as e:
        print(f"\nError testing query: {str(e)}")

def main():
    """Test the problematic query builders."""
    
    # Test KMS Key
    kms_properties = {
        "Region": "us-east-1",
        "Description": "Test KMS key",
        "KeyUsage": "ENCRYPT_DECRYPT"
    }
    test_query_builder("AWS::KMS::Key", kms_properties, KMSQueryBuilder.build_key_query)
    
    # Test API Gateway REST API
    api_properties = {
        "Region": "us-east-1",
        "Name": "TestAPI",
        "Description": "Test REST API",
        "EndpointConfiguration": {
            "Types": ["REGIONAL"]
        }
    }
    test_query_builder("AWS::ApiGateway::RestApi", api_properties, APIGatewayQueryBuilder.build_rest_api_query)
    
    # Test DynamoDB Table
    dynamodb_properties = {
        "Region": "us-east-1",
        "TableName": "TestTable",
        "BillingMode": "PAY_PER_REQUEST",
        "AttributeDefinitions": [
            {
                "AttributeName": "id",
                "AttributeType": "S"
            }
        ],
        "KeySchema": [
            {
                "AttributeName": "id",
                "KeyType": "HASH"
            }
        ]
    }
    test_query_builder("AWS::DynamoDB::Table", dynamodb_properties, DynamoDBQueryBuilder.build_table_query)
    
    print(f"\n{'='*60}")
    print("Testing query builder registry")
    print(f"{'='*60}")
    
    # Test if query builders are properly registered
    for resource_type in ["AWS::KMS::Key", "AWS::ApiGateway::RestApi", "AWS::DynamoDB::Table"]:
        builder = get_query_builder(resource_type)
        if builder:
            print(f"✅ {resource_type}: Query builder found")
        else:
            print(f"❌ {resource_type}: No query builder found")

if __name__ == "__main__":
    main() 