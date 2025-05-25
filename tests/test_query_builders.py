#!/usr/bin/env python3
"""
Test script to demonstrate the updated query builders with CloudFormation properties
and tiered pricing handling.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from cost_estimator.query_builders import (
    APIGatewayQueryBuilder, 
    EC2QueryBuilder, 
    RDSQueryBuilder,
    calculate_tiered_cost
)

def test_api_gateway_with_properties():
    """Test API Gateway query builder with actual CloudFormation properties."""
    print("=== Testing API Gateway Query Builder ===")
    
    # Example CloudFormation properties for API Gateway REST API
    rest_api_properties = {
        "Region": "us-east-1",
        "Name": "MyRestAPI",
        "Description": "My REST API for testing",
        "EndpointConfiguration": {
            "Types": ["REGIONAL"]
        },
        "Policy": {},
        "Parameters": {}
    }
    
    query = APIGatewayQueryBuilder.build_rest_api_query(rest_api_properties)
    print("REST API Query:")
    print(query)
    print()
    
    # Example CloudFormation properties for API Gateway V2 (HTTP API)
    http_api_properties = {
        "Region": "us-west-2",
        "Name": "MyHttpAPI",
        "Description": "My HTTP API for testing",
        "ProtocolType": "HTTP",
        "CorsConfiguration": {
            "AllowOrigins": ["*"],
            "AllowMethods": ["GET", "POST"]
        }
    }
    
    query = APIGatewayQueryBuilder.build_v2_api_query(http_api_properties)
    print("HTTP API Query:")
    print(query)
    print()


def test_ec2_with_properties():
    """Test EC2 query builder with actual CloudFormation properties."""
    print("=== Testing EC2 Query Builder ===")
    
    # Example CloudFormation properties for EC2 instance
    ec2_properties = {
        "Region": "us-east-1",
        "InstanceType": "m5.large",
        "ImageId": "ami-0abcdef1234567890",  # Linux AMI
        "KeyName": "my-key-pair",
        "SecurityGroups": ["sg-12345678"],
        "SubnetId": "subnet-12345678",
        "UserData": "#!/bin/bash\necho 'Hello World'",
        "Placement": {
            "Tenancy": "default",
            "AvailabilityZone": "us-east-1a"
        }
    }
    
    query = EC2QueryBuilder.build_instance_query(ec2_properties)
    print("EC2 Instance Query:")
    print(query)
    print()
    
    # Example CloudFormation properties for EBS volume
    ebs_properties = {
        "Region": "us-east-1",
        "VolumeType": "gp3",
        "Size": 100,
        "Iops": 3000,
        "Throughput": 125,
        "Encrypted": True
    }
    
    query = EC2QueryBuilder.build_ebs_query(ebs_properties)
    print("EBS Volume Query:")
    print(query)
    print()


def test_rds_with_properties():
    """Test RDS query builder with actual CloudFormation properties."""
    print("=== Testing RDS Query Builder ===")
    
    # Example CloudFormation properties for RDS instance
    rds_properties = {
        "Region": "us-east-1",
        "DBInstanceClass": "db.t3.micro",
        "Engine": "postgres",
        "EngineVersion": "13.7",
        "AllocatedStorage": 20,
        "StorageType": "gp2",
        "MultiAZ": False,
        "LicenseModel": "postgresql-license"
    }
    
    query = RDSQueryBuilder.build_instance_query(rds_properties)
    print("RDS Instance Query:")
    print(query)
    print()
    
    # Example CloudFormation properties for RDS cluster
    cluster_properties = {
        "Region": "us-west-2",
        "Engine": "aurora-postgresql",
        "EngineVersion": "13.7",
        "DatabaseName": "mydb",
        "MasterUsername": "postgres",
        "BackupRetentionPeriod": 7
    }
    
    query = RDSQueryBuilder.build_cluster_query(cluster_properties)
    print("RDS Cluster Query:")
    print(query)
    print()


def test_tiered_pricing():
    """Test tiered pricing calculation."""
    print("=== Testing Tiered Pricing Calculation ===")
    
    # Example API Gateway pricing tiers (based on your query result)
    api_gateway_prices = [
        {
            "USD": "0.0000035",
            "unit": "Requests",
            "description": "API calls received",
            "startUsageAmount": "0",
            "endUsageAmount": "333000000"
        },
        {
            "USD": "0.0000028", 
            "unit": "Requests",
            "description": "API calls received",
            "startUsageAmount": "333000000",
            "endUsageAmount": "1000000000"
        },
        {
            "USD": "0.00000238",
            "unit": "Requests", 
            "description": "API calls received",
            "startUsageAmount": "1000000000",
            "endUsageAmount": "20000000000"
        },
        {
            "USD": "0.00000151",
            "unit": "Requests",
            "description": "API calls received", 
            "startUsageAmount": "20000000000",
            "endUsageAmount": "999999999999"
        }
    ]
    
    # Test different usage scenarios
    test_cases = [
        100000000,      # 100M requests (first tier)
        500000000,      # 500M requests (spans first two tiers)
        2000000000,     # 2B requests (spans first three tiers)
        25000000000     # 25B requests (spans all tiers)
    ]
    
    for monthly_usage in test_cases:
        cost = calculate_tiered_cost(api_gateway_prices, monthly_usage)
        print(f"Monthly usage: {monthly_usage:,} requests")
        print(f"Monthly cost: ${cost:.2f}")
        print(f"Cost per million requests: ${(cost / monthly_usage * 1000000):.2f}")
        print()


if __name__ == "__main__":
    test_api_gateway_with_properties()
    test_ec2_with_properties()
    test_rds_with_properties()
    test_tiered_pricing() 