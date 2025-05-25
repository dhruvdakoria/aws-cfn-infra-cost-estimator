#!/usr/bin/env python3
"""
Test script to compare pricing between different regions.
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

def test_region_pricing():
    """Test pricing differences between regions."""
    load_dotenv()
    
    # Test regions
    regions = ["us-east-1", "ca-central-1", "eu-west-1"]
    
    # Test resources with known pricing differences
    test_resources = [
        {
            "type": "AWS::EC2::Instance",
            "properties": {
                "InstanceType": "t3.micro",
                "ImageId": "ami-12345678",
                "id": "test-instance"
            }
        },
        {
            "type": "AWS::RDS::DBInstance",
            "properties": {
                "DBInstanceClass": "db.t3.micro",
                "Engine": "mysql",
                "AllocatedStorage": 20,
                "id": "test-db"
            }
        }
    ]
    
    estimator = InfracostEstimator()
    
    print("🌍 Regional Pricing Comparison")
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
                print(f"  {region:15} | ${cost.monthly_cost:8.2f}/month | ${cost.hourly_cost:8.4f}/hour")
            except Exception as e:
                print(f"  {region:15} | ERROR: {str(e)}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_region_pricing() 