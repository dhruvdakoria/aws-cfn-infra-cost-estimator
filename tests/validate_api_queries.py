#!/usr/bin/env python3
"""
Validation script to test known working queries and identify correct attribute filters.
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

def test_known_working_queries():
    """Test known working queries from Infracost documentation."""
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
    
    # Known working queries from documentation
    test_queries = [
        {
            "name": "EC2 m3.large (from docs)",
            "query": """
            {
              products(
                filter: {
                  vendorName: "aws",
                  service: "AmazonEC2",
                  productFamily: "Compute Instance",
                  region: "us-east-1",
                  attributeFilters: [
                    { key: "instanceType", value: "m3.large" }
                    { key: "operatingSystem", value: "Linux" }
                    { key: "tenancy", value: "Shared" }
                    { key: "capacitystatus", value: "Used" }
                    { key: "preInstalledSw", value: "NA" }
                  ]
                }
              ) {
                prices(filter: {purchaseOption: "on_demand"}) { USD }
              }
            }
            """
        },
        {
            "name": "EC2 t3.medium (our case)",
            "query": """
            {
              products(
                filter: {
                  vendorName: "aws",
                  service: "AmazonEC2",
                  productFamily: "Compute Instance",
                  region: "us-east-1",
                  attributeFilters: [
                    { key: "instanceType", value: "t3.medium" }
                    { key: "operatingSystem", value: "Linux" }
                    { key: "tenancy", value: "Shared" }
                    { key: "capacitystatus", value: "Used" }
                    { key: "preInstalledSw", value: "NA" }
                  ]
                }
              ) {
                prices(filter: {purchaseOption: "on_demand"}) { USD }
              }
            }
            """
        }
    ]
    
    for test in test_queries:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {test['name']}")
        logger.info(f"{'='*60}")
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json={"query": test["query"]},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response: {json.dumps(data, indent=2)}")
                
                products = data.get("data", {}).get("products", [])
                if products and products[0].get("prices"):
                    price = products[0]["prices"][0].get("USD")
                    logger.info(f"✅ SUCCESS: Price found: ${price}/hour")
                else:
                    logger.warning(f"⚠️ No prices found in response")
            else:
                logger.error(f"❌ HTTP Error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")

def explore_service_families():
    """Explore available service and productFamily combinations."""
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
    
    # Query to explore available services and product families
    exploration_queries = [
        {
            "name": "NAT Gateway exploration",
            "query": """
            {
              products(
                filter: {
                  vendorName: "aws",
                  region: "us-east-1",
                  attributeFilters: [
                    { key: "usagetype", value: "NatGateway-Hours" }
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
            "name": "EIP exploration",
            "query": """
            {
              products(
                filter: {
                  vendorName: "aws",
                  region: "us-east-1",
                  attributeFilters: [
                    { key: "usagetype", value: "ElasticIP:IdleAddress" }
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
            "name": "EBS gp3 exploration",
            "query": """
            {
              products(
                filter: {
                  vendorName: "aws",
                  service: "AmazonEC2",
                  region: "us-east-1",
                  attributeFilters: [
                    { key: "usagetype", value: "EBS:VolumeUsage.gp3" }
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
            "name": "ALB exploration",
            "query": """
            {
              products(
                filter: {
                  vendorName: "aws",
                  region: "us-east-1",
                  attributeFilters: [
                    { key: "usagetype", value: "LoadBalancerUsage" }
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
    
    for test in exploration_queries:
        logger.info(f"\n{'='*60}")
        logger.info(f"Exploring: {test['name']}")
        logger.info(f"{'='*60}")
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json={"query": test["query"]},
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
                        logger.info("")
                else:
                    logger.warning(f"⚠️ No products found")
            else:
                logger.error(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    logger.info("🔍 Starting API query validation...")
    
    logger.info("\n" + "="*80)
    logger.info("TESTING KNOWN WORKING QUERIES")
    logger.info("="*80)
    test_known_working_queries()
    
    logger.info("\n" + "="*80)
    logger.info("EXPLORING SERVICE FAMILIES")
    logger.info("="*80)
    explore_service_families() 