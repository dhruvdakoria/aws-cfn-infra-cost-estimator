#!/usr/bin/env python3
"""
Test script to check instance type pricing in different regions.
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

def test_instance_types():
    """Test different instance types in different regions."""
    load_dotenv()
    
    # Test regions
    regions = ["us-east-1", "ca-central-1"]
    
    # Test instance types
    instance_types = ["t3.micro", "m3.large", "t3.small", "m5.large"]
    
    estimator = InfracostEstimator()
    
    print("🖥️ Instance Type Pricing by Region")
    print("=" * 80)
    
    for instance_type in instance_types:
        print(f"\n📦 Instance Type: {instance_type}")
        print("-" * 60)
        
        for region in regions:
            properties = {
                "InstanceType": instance_type,
                "ImageId": "ami-12345678",
                "Region": region,
                "id": f"test-{instance_type}"
            }
            
            try:
                cost = estimator.get_resource_cost("AWS::EC2::Instance", properties)
                print(f"  {region:15} | ${cost.monthly_cost:8.2f}/month | ${cost.hourly_cost:8.4f}/hour")
            except Exception as e:
                print(f"  {region:15} | ERROR: {str(e)}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_instance_types() 