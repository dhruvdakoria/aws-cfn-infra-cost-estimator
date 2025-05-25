#!/usr/bin/env python3
"""
Focused test script to validate pricing accuracy for paid AWS resources.
"""

import sys
import os
import logging
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cost_estimator.infracost import InfracostEstimator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_paid_resources():
    """Test specific paid resources to validate pricing accuracy."""
    load_dotenv()
    
    try:
        estimator = InfracostEstimator()
        logger.info("✅ Infracost estimator initialized successfully")
        
        # Test specific paid resources with detailed properties
        test_resources = [
            ('AWS::EC2::Instance', {
                'InstanceType': 't3.medium', 
                'Region': 'us-east-1', 
                'OperatingSystem': 'Linux',
                'Tenancy': 'Shared',
                'id': 'test-instance'
            }),
            ('AWS::RDS::DBInstance', {
                'DBInstanceClass': 'db.t3.micro', 
                'Engine': 'mysql', 
                'Region': 'us-east-1', 
                'id': 'test-db'
            }),
            ('AWS::EC2::NatGateway', {
                'Region': 'us-east-1', 
                'id': 'test-nat'
            }),
            ('AWS::EC2::EIP', {
                'Region': 'us-east-1', 
                'Domain': 'vpc',
                'id': 'test-eip'
            }),
            ('AWS::S3::Bucket', {
                'StorageClass': 'Standard', 
                'Region': 'us-east-1', 
                'id': 'test-bucket'
            }),
            ('AWS::Lambda::Function', {
                'Runtime': 'python3.9', 
                'MemorySize': 256, 
                'Region': 'us-east-1', 
                'id': 'test-lambda'
            }),
            ('AWS::ElasticLoadBalancingV2::LoadBalancer', {
                'Type': 'application',
                'Region': 'us-east-1',
                'id': 'test-alb'
            }),
            ('AWS::DynamoDB::Table', {
                'BillingMode': 'PAY_PER_REQUEST',
                'Region': 'us-east-1',
                'id': 'test-table'
            }),
            ('AWS::KMS::Key', {
                'Region': 'us-east-1',
                'id': 'test-key'
            }),
            ('AWS::SecretsManager::Secret', {
                'Region': 'us-east-1',
                'id': 'test-secret'
            })
        ]

        print('\n🧪 Testing individual paid resources with Infracost API:')
        print('=' * 70)
        
        total_cost = 0.0
        paid_count = 0
        free_count = 0
        error_count = 0

        for resource_type, properties in test_resources:
            try:
                cost = estimator.get_resource_cost(resource_type, properties)
                if cost.monthly_cost > 0:
                    print(f'💰 {resource_type}: ${cost.monthly_cost:.2f}/month (PAID)')
                    total_cost += cost.monthly_cost
                    paid_count += 1
                else:
                    print(f'🆓 {resource_type}: ${cost.monthly_cost:.2f}/month (FREE)')
                    free_count += 1
            except Exception as e:
                print(f'❌ {resource_type}: Error - {e}')
                error_count += 1

        print('=' * 70)
        print(f'📊 SUMMARY:')
        print(f'   💰 Paid resources: {paid_count}')
        print(f'   🆓 Free resources: {free_count}')
        print(f'   ❌ Errors: {error_count}')
        print(f'   💵 Total monthly cost: ${total_cost:.2f}')
        print('=' * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_paid_resources()
    sys.exit(0 if success else 1) 