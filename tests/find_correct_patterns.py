#!/usr/bin/env python3
"""
Script to find correct usagetype patterns for AWS resources.
"""

import os
import sys
import json
import logging
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_resource_patterns():
    """Find correct patterns for AWS resources."""
    load_dotenv()
    
    api_key = os.getenv('INFRACOST_API_KEY')
    if not api_key:
        logger.error("INFRACOST_API_KEY not set")
        return
    
    url = "https://pricing.api.infracost.io/graphql"
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Patterns to explore based on AWS usage types
    patterns = [
        {
            "name": "EBS gp3 Volume",
            "usagetype": "EBS:VolumeUsage.gp3"
        },
        {
            "name": "EBS gp2 Volume", 
            "usagetype": "EBS:VolumeUsage.gp2"
        },
        {
            "name": "RDS db.t3.micro",
            "usagetype": "RDS:db.t3.micro"
        },
        {
            "name": "S3 Standard Storage",
            "usagetype": "TimedStorage-ByteHrs"
        },
        {
            "name": "Lambda Requests",
            "usagetype": "Lambda-Requests"
        },
        {
            "name": "Lambda Duration",
            "usagetype": "Lambda-GB-Second"
        },
        {
            "name": "CloudWatch Logs",
            "usagetype": "DataProcessing-Bytes"
        },
        {
            "name": "DynamoDB On-Demand",
            "usagetype": "DynamoDB-ReadRequestUnits"
        },
        {
            "name": "SNS Requests",
            "usagetype": "SNS-Requests"
        },
        {
            "name": "SQS Requests",
            "usagetype": "SQS-Requests"
        },
        {
            "name": "KMS Requests",
            "usagetype": "KMS-Requests"
        },
        {
            "name": "API Gateway Requests",
            "usagetype": "ApiGatewayRequest"
        },
        {
            "name": "ElastiCache cache.t3.micro",
            "usagetype": "NodeUsage:cache.t3.micro"
        },
        {
            "name": "Secrets Manager",
            "usagetype": "Secret"
        }
    ]
    
    for pattern in patterns:
        logger.info(f"\n{'='*60}")
        logger.info(f"Exploring: {pattern['name']}")
        logger.info(f"Usage Type: {pattern['usagetype']}")
        logger.info(f"{'='*60}")
        
        query = f"""
        {{
          products(
            filter: {{
              vendorName: "aws",
              region: "us-east-1",
              attributeFilters: [
                {{ key: "usagetype", value: "{pattern['usagetype']}" }}
              ]
            }}
          ) {{
            service
            productFamily
            attributes {{ key value }}
            prices(filter: {{purchaseOption: "on_demand"}}) {{ USD }}
          }}
        }}
        """
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("data", {}).get("products", [])
                
                if products:
                    logger.info(f"✅ Found {len(products)} products")
                    for i, product in enumerate(products[:2]):  # Show first 2
                        logger.info(f"Product {i+1}:")
                        logger.info(f"  Service: {product.get('service')}")
                        logger.info(f"  ProductFamily: {product.get('productFamily')}")
                        
                        prices = product.get('prices', [])
                        if prices:
                            logger.info(f"  Price: ${prices[0].get('USD')}")
                        else:
                            logger.info(f"  Price: No on-demand pricing")
                        logger.info("")
                else:
                    logger.warning(f"⚠️ No products found for {pattern['usagetype']}")
            else:
                logger.error(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")

def find_service_specific_patterns():
    """Find service-specific patterns."""
    load_dotenv()
    
    api_key = os.getenv('INFRACOST_API_KEY')
    if not api_key:
        logger.error("INFRACOST_API_KEY not set")
        return
    
    url = "https://pricing.api.infracost.io/graphql"
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Service-specific explorations
    service_patterns = [
        {
            "name": "RDS MySQL db.t3.micro",
            "service": "AmazonRDS",
            "productFamily": "Database Instance",
            "attributes": [
                {"key": "instanceType", "value": "db.t3.micro"},
                {"key": "databaseEngine", "value": "MySQL"}
            ]
        },
        {
            "name": "S3 Standard Storage",
            "service": "AmazonS3",
            "productFamily": "Storage",
            "attributes": [
                {"key": "storageClass", "value": "General Purpose"}
            ]
        },
        {
            "name": "Lambda Function",
            "service": "AWSLambda",
            "productFamily": "Serverless Compute",
            "attributes": []
        },
        {
            "name": "CloudWatch Logs",
            "service": "AmazonCloudWatch",
            "productFamily": "Log Group",
            "attributes": []
        }
    ]
    
    for pattern in service_patterns:
        logger.info(f"\n{'='*60}")
        logger.info(f"Exploring: {pattern['name']}")
        logger.info(f"Service: {pattern['service']}")
        logger.info(f"ProductFamily: {pattern['productFamily']}")
        logger.info(f"{'='*60}")
        
        attr_filters = ""
        for attr in pattern['attributes']:
            attr_filters += f'{{ key: "{attr["key"]}", value: "{attr["value"]}" }}\n                '
        
        query = f"""
        {{
          products(
            filter: {{
              vendorName: "aws",
              service: "{pattern['service']}",
              productFamily: "{pattern['productFamily']}",
              region: "us-east-1",
              attributeFilters: [
                {attr_filters}
              ]
            }}
          ) {{
            service
            productFamily
            attributes {{ key value }}
            prices(filter: {{purchaseOption: "on_demand"}}) {{ USD }}
          }}
        }}
        """
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("data", {}).get("products", [])
                
                if products:
                    logger.info(f"✅ Found {len(products)} products")
                    for i, product in enumerate(products[:2]):  # Show first 2
                        logger.info(f"Product {i+1}:")
                        logger.info(f"  Service: {product.get('service')}")
                        logger.info(f"  ProductFamily: {product.get('productFamily')}")
                        
                        # Show key attributes
                        attributes = product.get('attributes', [])
                        key_attrs = [attr for attr in attributes if attr['key'] in ['usagetype', 'operation', 'group', 'instanceType', 'databaseEngine']]
                        for attr in key_attrs:
                            logger.info(f"  {attr['key']}: {attr['value']}")
                        
                        prices = product.get('prices', [])
                        if prices:
                            logger.info(f"  Price: ${prices[0].get('USD')}")
                        else:
                            logger.info(f"  Price: No on-demand pricing")
                        logger.info("")
                else:
                    logger.warning(f"⚠️ No products found")
            else:
                logger.error(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    logger.info("🔍 Finding correct resource patterns...")
    
    logger.info("\n" + "="*80)
    logger.info("EXPLORING USAGE TYPE PATTERNS")
    logger.info("="*80)
    find_resource_patterns()
    
    logger.info("\n" + "="*80)
    logger.info("EXPLORING SERVICE-SPECIFIC PATTERNS")
    logger.info("="*80)
    find_service_specific_patterns() 