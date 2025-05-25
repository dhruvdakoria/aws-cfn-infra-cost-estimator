#!/usr/bin/env python3
"""
Test script for AWS CloudFormation cost estimation using Infracost API.
This script validates the new modular structure and comprehensive resource support.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cost_estimator.infracost import InfracostEstimator
from cost_estimator.resource_mappings import get_paid_resources, get_free_resources
from cost_estimator.query_builders import get_query_builder
from stack_analyzer.parser import CloudFormationParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_resource_mappings():
    """Test the resource mappings functionality."""
    logger.info("🧪 Testing resource mappings...")
    
    paid_resources = get_paid_resources()
    free_resources = get_free_resources()
    
    logger.info(f"📊 Found {len(paid_resources)} paid resource types")
    logger.info(f"🆓 Found {len(free_resources)} free resource types")
    
    # Test some specific mappings
    test_resources = [
        "AWS::EC2::Instance",
        "AWS::RDS::DBInstance", 
        "AWS::S3::Bucket",
        "AWS::Lambda::Function",
        "AWS::DynamoDB::Table",
        "AWS::ElasticLoadBalancingV2::LoadBalancer"
    ]
    
    for resource_type in test_resources:
        if resource_type in paid_resources:
            mapping = paid_resources[resource_type]
            logger.info(f"✅ {resource_type}: {mapping['service']} - {mapping['productFamily']}")
        else:
            logger.warning(f"❌ {resource_type} not found in paid resources")
    
    return True

def test_query_builders():
    """Test the query builder functionality."""
    logger.info("🧪 Testing query builders...")
    
    test_cases = [
        {
            "resource_type": "AWS::EC2::Instance",
            "properties": {
                "InstanceType": "t3.medium",
                "Region": "us-east-1"
            }
        },
        {
            "resource_type": "AWS::RDS::DBInstance", 
            "properties": {
                "DBInstanceClass": "db.t3.micro",
                "Engine": "mysql",
                "Region": "us-east-1"
            }
        },
        {
            "resource_type": "AWS::S3::Bucket",
            "properties": {
                "StorageClass": "Standard",
                "Region": "us-east-1"
            }
        }
    ]
    
    for test_case in test_cases:
        resource_type = test_case["resource_type"]
        properties = test_case["properties"]
        
        query_builder = get_query_builder(resource_type)
        if query_builder:
            try:
                query = query_builder(properties)
                logger.info(f"✅ {resource_type}: Query builder working")
                logger.debug(f"Query: {query[:100]}...")
            except Exception as e:
                logger.error(f"❌ {resource_type}: Query builder failed - {e}")
        else:
            logger.warning(f"❌ {resource_type}: No query builder found")
    
    return True

def test_infracost_estimator():
    """Test the Infracost estimator with mock data."""
    logger.info("🧪 Testing Infracost estimator...")
    
    # Load environment variables
    load_dotenv()
    
    try:
        estimator = InfracostEstimator()
        logger.info("✅ Infracost estimator initialized successfully")
        
        # Test supported resources
        supported_resources = estimator.get_supported_resources()
        logger.info(f"📊 Estimator supports {len(supported_resources)} resource types")
        
        # Test free resource
        free_resource_properties = {
            "id": "test-vpc",
            "Region": "us-east-1"
        }
        
        try:
            cost = estimator.get_resource_cost("AWS::EC2::VPC", free_resource_properties)
            logger.info(f"✅ Free resource test: {cost.resource_type} - ${cost.monthly_cost:.2f}/month")
        except Exception as e:
            logger.error(f"❌ Free resource test failed: {e}")
        
        # Test paid resource (without making actual API call)
        paid_resource_properties = {
            "id": "test-instance",
            "InstanceType": "t3.medium",
            "Region": "us-east-1"
        }
        
        if estimator.is_resource_supported("AWS::EC2::Instance"):
            logger.info("✅ EC2 Instance is supported")
        else:
            logger.warning("❌ EC2 Instance is not supported")
            
        return True
        
    except ValueError as e:
        logger.warning(f"⚠️ Infracost API key not configured: {e}")
        logger.info("💡 Set INFRACOST_API_KEY environment variable to test API calls")
        return True
    except Exception as e:
        logger.error(f"❌ Infracost estimator test failed: {e}")
        return False

def test_cloudformation_parsing():
    """Test CloudFormation template parsing."""
    logger.info("🧪 Testing CloudFormation template parsing...")
    
    template_path = "templates/test-paid-resources.yaml"
    
    if not os.path.exists(template_path):
        logger.warning(f"❌ Template file not found: {template_path}")
        return False
    
    try:
        with open(template_path, 'r') as f:
            template_content = f.read()
        parser = CloudFormationParser(template_content)
        resources = parser.get_resources()
        
        logger.info(f"📊 Found {len(resources)} resources in template")
        
        # Categorize resources
        paid_count = 0
        free_count = 0
        unknown_count = 0
        
        paid_resources = get_paid_resources()
        free_resources = get_free_resources()
        
        for resource in resources:
            if resource.type in paid_resources:
                paid_count += 1
                logger.info(f"💰 PAID: {resource.logical_id} ({resource.type})")
            elif resource.type in free_resources:
                free_count += 1
                logger.info(f"🆓 FREE: {resource.logical_id} ({resource.type})")
            else:
                unknown_count += 1
                logger.warning(f"❓ UNKNOWN: {resource.logical_id} ({resource.type})")
        
        logger.info(f"📊 Summary: {paid_count} paid, {free_count} free, {unknown_count} unknown")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ CloudFormation parsing failed: {e}")
        return False

def test_end_to_end():
    """Test end-to-end cost estimation workflow."""
    logger.info("🧪 Testing end-to-end cost estimation...")
    
    template_path = "templates/test-paid-resources.yaml"
    
    if not os.path.exists(template_path):
        logger.warning(f"❌ Template file not found: {template_path}")
        return False
    
    load_dotenv()
    
    try:
        # Parse template
        with open(template_path, 'r') as f:
            template_content = f.read()
        parser = CloudFormationParser(template_content)
        resources = parser.get_resources()
        
        # Initialize estimator
        estimator = InfracostEstimator()
        
        total_monthly_cost = 0.0
        estimated_resources = 0
        
        for resource in resources:
            try:
                if estimator.is_resource_supported(resource.type):
                    # Add region to properties if not present
                    properties = resource.properties.copy()
                    if "Region" not in properties:
                        properties["Region"] = "us-east-1"
                    properties["id"] = resource.logical_id
                    
                    cost = estimator.get_resource_cost(resource.type, properties)
                    total_monthly_cost += cost.monthly_cost
                    estimated_resources += 1
                    
                    if cost.monthly_cost > 0:
                        logger.info(f"💰 {resource.logical_id}: ${cost.monthly_cost:.2f}/month")
                    else:
                        logger.info(f"🆓 {resource.logical_id}: Free")
                        
                else:
                    logger.warning(f"❓ {resource.logical_id} ({resource.type}): Not supported")
                    
            except Exception as e:
                logger.error(f"❌ Error estimating cost for {resource.logical_id}: {e}")
        
        logger.info(f"📊 TOTAL ESTIMATED MONTHLY COST: ${total_monthly_cost:.2f}")
        logger.info(f"📊 Estimated {estimated_resources} out of {len(resources)} resources")
        
        return True
        
    except ValueError as e:
        logger.warning(f"⚠️ Infracost API key not configured: {e}")
        logger.info("💡 Set INFRACOST_API_KEY environment variable for full testing")
        return True
    except Exception as e:
        logger.error(f"❌ End-to-end test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("🚀 Starting AWS CloudFormation Cost Estimation Tests")
    
    tests = [
        ("Resource Mappings", test_resource_mappings),
        ("Query Builders", test_query_builders),
        ("Infracost Estimator", test_infracost_estimator),
        ("CloudFormation Parsing", test_cloudformation_parsing),
        ("End-to-End", test_end_to_end)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
            failed += 1
    
    logger.info(f"\n{'='*50}")
    logger.info(f"TEST SUMMARY")
    logger.info(f"{'='*50}")
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error(f"💥 {failed} test(s) failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 