#!/usr/bin/env python3
"""
Test script to check region-specific services that are failing in ca-central-1.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cost_estimator.infracost import InfracostEstimator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_region_specific_services():
    """Test services that are showing $0 in ca-central-1."""
    load_dotenv()
    
    # Test regions
    regions = ["us-east-1", "ca-central-1"]
    
    # Test resources that are showing $0 in ca-central-1
    test_resources = [
        {
            "type": "AWS::S3::Bucket",
            "properties": {
                "BucketName": "test-bucket",
                "id": "test-s3"
            }
        },
        {
            "type": "AWS::Lambda::Function",
            "properties": {
                "FunctionName": "test-function",
                "Runtime": "python3.9",
                "id": "test-lambda"
            }
        },
        {
            "type": "AWS::EC2::Volume",
            "properties": {
                "VolumeType": "gp3",
                "Size": 100,
                "id": "test-volume"
            }
        },
        {
            "type": "AWS::ElasticLoadBalancingV2::LoadBalancer",
            "properties": {
                "Type": "application",
                "id": "test-alb"
            }
        },
        {
            "type": "AWS::Logs::LogGroup",
            "properties": {
                "LogGroupName": "test-logs",
                "id": "test-logs"
            }
        },
        {
            "type": "AWS::ApiGateway::RestApi",
            "properties": {
                "Name": "test-api",
                "id": "test-api"
            }
        },
        {
            "type": "AWS::SecretsManager::Secret",
            "properties": {
                "Name": "test-secret",
                "id": "test-secret"
            }
        }
    ]
    
    estimator = InfracostEstimator()
    
    print("🔍 Region-Specific Service Pricing Test")
    print("=" * 80)
    
    for resource in test_resources:
        print(f"\n📦 Resource: {resource['type']}")
        print("-" * 60)
        
        for region in regions:
            # Add region to properties
            properties = resource["properties"].copy()
            properties["Region"] = region
            
            try:
                cost = estimator.get_resource_cost(resource["type"], properties)
                status = "✅" if cost.monthly_cost > 0 else "❌"
                print(f"  {region:15} | {status} ${cost.monthly_cost:8.2f}/month | ${cost.hourly_cost:8.4f}/hour")
            except Exception as e:
                print(f"  {region:15} | ❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_region_specific_services() 