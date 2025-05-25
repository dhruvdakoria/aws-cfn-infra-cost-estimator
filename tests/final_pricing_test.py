#!/usr/bin/env python3
"""
Final test script to verify all pricing fixes are working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cost_estimator.infracost import InfracostEstimator
from dotenv import load_dotenv

load_dotenv()

def test_all_pricing():
    """Test all key resources to verify pricing fixes."""
    
    # Test key resources
    test_cases = [
        ('RDS Instance', 'AWS::RDS::DBInstance', {'DBInstanceClass': 'db.t3.micro', 'Engine': 'mysql', 'Region': 'us-east-1', 'id': 'test-db'}),
        ('S3 Bucket', 'AWS::S3::Bucket', {'Region': 'us-east-1', 'id': 'test-bucket'}),
        ('Lambda Function', 'AWS::Lambda::Function', {'Runtime': 'python3.9', 'MemorySize': 256, 'Region': 'us-east-1', 'id': 'test-lambda'}),
        ('CloudWatch Logs', 'AWS::Logs::LogGroup', {'Region': 'us-east-1', 'id': 'test-logs'}),
        ('SNS Topic', 'AWS::SNS::Topic', {'Region': 'us-east-1', 'id': 'test-sns'}),
        ('SQS Queue', 'AWS::SQS::Queue', {'Region': 'us-east-1', 'id': 'test-sqs'}),
        ('KMS Key', 'AWS::KMS::Key', {'Region': 'us-east-1', 'id': 'test-kms'}),
        ('API Gateway', 'AWS::ApiGateway::RestApi', {'Region': 'us-east-1', 'id': 'test-api'}),
        ('Secrets Manager', 'AWS::SecretsManager::Secret', {'Region': 'us-east-1', 'id': 'test-secret'})
    ]

    estimator = InfracostEstimator()

    print('🎯 FINAL PRICING TEST RESULTS')
    print('='*60)

    total_fixed = 0
    total_tested = len(test_cases)

    for name, resource_type, properties in test_cases:
        try:
            cost = estimator.get_resource_cost(resource_type, properties)
            if cost.monthly_cost > 0:
                status = '✅'
                total_fixed += 1
            else:
                status = '❌'
            print(f'{status} {name:<20} ${cost.monthly_cost:>8.2f}/month')
        except Exception as e:
            print(f'❌ {name:<20} ERROR: {str(e)[:40]}...')

    print('='*60)
    print(f'📊 SUMMARY: {total_fixed}/{total_tested} resources now return pricing')
    
    if total_fixed == total_tested:
        print('🎉 ALL PRICING ISSUES FIXED!')
    else:
        print(f'⚠️  {total_tested - total_fixed} resources still need fixes')

if __name__ == "__main__":
    test_all_pricing() 