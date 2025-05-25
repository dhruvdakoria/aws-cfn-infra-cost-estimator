#!/usr/bin/env python3
"""
Script to find more specific patterns for remaining AWS services.
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

def find_more_patterns():
    """Find patterns for remaining services."""
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
    
    # More specific patterns to explore
    patterns = [
        {
            "name": "Secrets Manager Secret",
            "service": "AWSSecretsManager",
            "productFamily": "Secret",
            "usagetype": None
        },
        {
            "name": "CloudWatch Logs Storage",
            "service": "AmazonCloudWatch",
            "productFamily": "Log Group",
            "usagetype": None
        },
        {
            "name": "DynamoDB On-Demand",
            "service": "AmazonDynamoDB",
            "productFamily": "Database Storage",
            "usagetype": None
        },
        {
            "name": "SNS Notifications",
            "service": "AmazonSNS",
            "productFamily": "Notification",
            "usagetype": None
        },
        {
            "name": "SQS Requests",
            "service": "AmazonSQS",
            "productFamily": "Queue",
            "usagetype": None
        },
        {
            "name": "KMS Key Usage",
            "service": "awskms",
            "productFamily": "Key Management",
            "usagetype": None
        },
        {
            "name": "API Gateway REST",
            "service": "AmazonApiGateway",
            "productFamily": "API Gateway",
            "usagetype": None
        }
    ]
    
    for pattern in patterns:
        logger.info(f"\n{'='*60}")
        logger.info(f"Exploring: {pattern['name']}")
        logger.info(f"Service: {pattern['service']}")
        logger.info(f"ProductFamily: {pattern['productFamily']}")
        logger.info(f"{'='*60}")
        
        # First, explore without usagetype to see what's available
        query = f"""
        {{
          products(
            filter: {{
              vendorName: "aws",
              service: "{pattern['service']}",
              productFamily: "{pattern['productFamily']}",
              region: "us-east-1"
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
                    for i, product in enumerate(products[:3]):  # Show first 3
                        logger.info(f"Product {i+1}:")
                        logger.info(f"  Service: {product.get('service')}")
                        logger.info(f"  ProductFamily: {product.get('productFamily')}")
                        
                        # Show key attributes
                        attributes = product.get('attributes', [])
                        key_attrs = [attr for attr in attributes if attr['key'] in ['usagetype', 'operation', 'group']]
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

def test_specific_usagetypes():
    """Test specific usagetypes found from AWS documentation."""
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
    
    # Specific usagetypes to test
    usagetypes = [
        "SecretManagerSecret",
        "Secret-Month",
        "LogsStorage-ByteHrs",
        "DynamoDB-WriteRequestUnits",
        "DynamoDB-ReadRequestUnits",
        "SNS-Requests-Tier1",
        "SQS-Requests-Tier1",
        "KMS-Requests",
        "ApiGatewayRequest",
        "ApiGatewayRequest-REST"
    ]
    
    for usagetype in usagetypes:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing usagetype: {usagetype}")
        logger.info(f"{'='*60}")
        
        query = f"""
        {{
          products(
            filter: {{
              vendorName: "aws",
              region: "us-east-1",
              attributeFilters: [
                {{ key: "usagetype", value: "{usagetype}" }}
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
                    logger.warning(f"⚠️ No products found for {usagetype}")
            else:
                logger.error(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    logger.info("🔍 Finding more service patterns...")
    
    logger.info("\n" + "="*80)
    logger.info("EXPLORING SERVICE PATTERNS")
    logger.info("="*80)
    find_more_patterns()
    
    logger.info("\n" + "="*80)
    logger.info("TESTING SPECIFIC USAGETYPES")
    logger.info("="*80)
    test_specific_usagetypes() 