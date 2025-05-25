#!/usr/bin/env python3
"""
Debug script to test individual query builders and API responses.
This helps identify issues with attribute filters and query construction.
"""

import os
import sys
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cost_estimator.infracost import InfracostEstimator
from cost_estimator.query_builders import *
from stack_analyzer.parser import CloudFormationParser

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_individual_queries():
    """Test individual query builders with detailed debugging."""
    load_dotenv()
    
    # Test cases for resources that should be paid
    test_cases = [
        {
            "name": "NAT Gateway",
            "resource_type": "AWS::EC2::NatGateway",
            "properties": {
                "Region": "us-east-1",
                "id": "test-nat-gateway"
            }
        },
        {
            "name": "Elastic IP",
            "resource_type": "AWS::EC2::EIP", 
            "properties": {
                "Domain": "vpc",
                "Region": "us-east-1",
                "id": "test-eip"
            }
        },
        {
            "name": "EBS Volume",
            "resource_type": "AWS::EC2::Volume",
            "properties": {
                "Size": 100,
                "VolumeType": "gp3",
                "Region": "us-east-1",
                "id": "test-volume"
            }
        },
        {
            "name": "Application Load Balancer",
            "resource_type": "AWS::ElasticLoadBalancingV2::LoadBalancer",
            "properties": {
                "Type": "application",
                "Scheme": "internet-facing",
                "Region": "us-east-1",
                "id": "test-alb"
            }
        },
        {
            "name": "RDS Instance",
            "resource_type": "AWS::RDS::DBInstance",
            "properties": {
                "DBInstanceClass": "db.t3.micro",
                "Engine": "mysql",
                "AllocatedStorage": 20,
                "Region": "us-east-1",
                "id": "test-db"
            }
        },
        {
            "name": "S3 Bucket",
            "resource_type": "AWS::S3::Bucket",
            "properties": {
                "Region": "us-east-1",
                "id": "test-bucket"
            }
        },
        {
            "name": "Lambda Function",
            "resource_type": "AWS::Lambda::Function",
            "properties": {
                "Runtime": "python3.9",
                "MemorySize": 256,
                "Region": "us-east-1",
                "id": "test-lambda"
            }
        },
        {
            "name": "ElastiCache Cluster",
            "resource_type": "AWS::ElastiCache::CacheCluster",
            "properties": {
                "CacheNodeType": "cache.t3.micro",
                "Engine": "redis",
                "NumCacheNodes": 1,
                "Region": "us-east-1",
                "id": "test-cache"
            }
        }
    ]
    
    try:
        estimator = InfracostEstimator()
        
        for test_case in test_cases:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing: {test_case['name']}")
            logger.info(f"Resource Type: {test_case['resource_type']}")
            logger.info(f"{'='*60}")
            
            # Get the query builder
            query_builder = get_query_builder(test_case['resource_type'])
            if not query_builder:
                logger.error(f"❌ No query builder found for {test_case['resource_type']}")
                continue
                
            # Build the query
            try:
                query = query_builder(test_case['properties'])
                logger.info(f"📝 Generated Query:")
                logger.info(query)
                
                # Make the API call
                cost = estimator.get_resource_cost(test_case['resource_type'], test_case['properties'])
                logger.info(f"💰 Cost Result: ${cost.monthly_cost:.2f}/month")
                
                if cost.monthly_cost == 0:
                    logger.warning(f"⚠️ Expected paid resource but got $0.00 - possible query issue")
                else:
                    logger.info(f"✅ Successfully got cost estimate")
                    
            except Exception as e:
                logger.error(f"❌ Error testing {test_case['name']}: {e}")
                
    except Exception as e:
        logger.error(f"❌ Failed to initialize estimator: {e}")

def test_template_resources():
    """Test all paid resources from the template."""
    template_path = "templates/test-paid-resources.yaml"
    
    if not os.path.exists(template_path):
        logger.error(f"❌ Template file not found: {template_path}")
        return
        
    load_dotenv()
    
    try:
        # Parse template
        with open(template_path, 'r') as f:
            template_content = f.read()
        parser = CloudFormationParser(template_content)
        resources = parser.get_resources()
        
        estimator = InfracostEstimator()
        
        # Focus on paid resources that returned $0
        paid_resources_zero_cost = []
        
        for resource in resources:
            if estimator.is_resource_supported(resource.type):
                properties = resource.properties.copy()
                if "Region" not in properties:
                    properties["Region"] = "us-east-1"
                properties["id"] = resource.logical_id
                
                try:
                    cost = estimator.get_resource_cost(resource.type, properties)
                    if cost.monthly_cost == 0:
                        paid_resources_zero_cost.append({
                            "logical_id": resource.logical_id,
                            "resource_type": resource.type,
                            "properties": properties
                        })
                except Exception as e:
                    logger.error(f"❌ Error testing {resource.logical_id}: {e}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"RESOURCES WITH ZERO COST (SHOULD BE PAID)")
        logger.info(f"{'='*60}")
        
        for resource in paid_resources_zero_cost:
            logger.info(f"🔍 {resource['logical_id']} ({resource['resource_type']})")
            
            # Test the query builder
            query_builder = get_query_builder(resource['resource_type'])
            if query_builder:
                try:
                    query = query_builder(resource['properties'])
                    logger.info(f"Query: {query[:200]}...")
                except Exception as e:
                    logger.error(f"Query builder error: {e}")
            
    except Exception as e:
        logger.error(f"❌ Template test failed: {e}")

if __name__ == "__main__":
    logger.info("🔍 Starting detailed query builder debugging...")
    
    logger.info("\n" + "="*80)
    logger.info("TESTING INDIVIDUAL QUERIES")
    logger.info("="*80)
    test_individual_queries()
    
    logger.info("\n" + "="*80)
    logger.info("TESTING TEMPLATE RESOURCES")
    logger.info("="*80)
    test_template_resources() 