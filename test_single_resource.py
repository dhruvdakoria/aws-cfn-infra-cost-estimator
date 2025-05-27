#!/usr/bin/env python3
"""
Test script for a single AWS resource type
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cost_estimator.query_builders import QUERY_BUILDERS
from cost_estimator.infracost import InfracostEstimator

def test_single_resource(resource_type: str, regions: list = ["us-east-1", "ca-central-1"]):
    """Test a single resource type in specified regions."""
    calculator = InfracostEstimator()
    
    print(f"\n🧪 Testing {resource_type}")
    print("=" * 60)
    
    # Get the query builder function
    query_builder_func = QUERY_BUILDERS.get(resource_type)
    if not query_builder_func:
        print(f"❌ No query builder found for {resource_type}")
        return False
    
    success_count = 0
    total_tests = len(regions)
    
    for region in regions:
        print(f"\n📍 Testing in {region}:")
        
        # Create test properties based on resource type
        properties = create_test_properties(resource_type, region)
        
        try:
            # Build the query
            query = query_builder_func(properties)
            print(f"🔍 Query: {query[:200]}...")
            
            # Test against API
            response = calculator._make_graphql_request(query)
            
            if not response:
                print(f"❌ No response from API")
                continue
            
            products = response.get("data", {}).get("products", [])
            
            if not products:
                print(f"❌ No products found")
                continue
            
            # Check if products have prices
            has_prices = any(product.get("prices") for product in products)
            
            if not has_prices:
                print(f"❌ No prices found")
                continue
            
            print(f"✅ Success! Found {len(products)} products with prices")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print(f"\n📊 Results: {success_count}/{total_tests} regions successful")
    return success_count == total_tests

def create_test_properties(resource_type: str, region: str):
    """Create test properties for a resource type."""
    base_properties = {"Region": region}
    
    if resource_type == "AWS::EKS::Nodegroup":
        base_properties.update({
            "NodegroupName": "test-nodegroup",
            "ClusterName": "test-cluster", 
            "InstanceTypes": ["t3.medium"],
            "AmiType": "AL2_x86_64",
            "CapacityType": "ON_DEMAND",
            "DiskSize": 20
        })
    elif resource_type == "AWS::StepFunctions::StateMachine":
        base_properties.update({
            "StateMachineName": "test-state-machine",
            "StateMachineType": "STANDARD"
        })
    elif resource_type == "AWS::EC2::VPNConnection":
        base_properties.update({
            "Type": "ipsec.1",
            "CustomerGatewayId": "cgw-12345678"
        })
    elif resource_type == "AWS::WAF::WebACL":
        base_properties.update({
            "Name": "test-web-acl",
            "Scope": "REGIONAL"
        })
    elif resource_type == "AWS::WAFv2::WebACL":
        base_properties.update({
            "Name": "test-web-acl-v2",
            "Scope": "REGIONAL"
        })
    elif resource_type == "AWS::ECR::Repository":
        base_properties.update({
            "RepositoryName": "test-repo"
        })
    elif resource_type == "AWS::Transfer::Server":
        base_properties.update({
            "Protocols": ["SFTP"]
        })
    elif resource_type == "AWS::SSM::Parameter":
        base_properties.update({
            "Name": "/test/parameter",
            "Type": "String",
            "Tier": "Advanced"  # Must be Advanced tier to have costs
        })
    elif resource_type == "AWS::SSM::Activation":
        base_properties.update({
            "RegistrationLimit": 2000
        })
    elif resource_type == "AWS::Lightsail::Instance":
        base_properties.update({
            "BundleId": "nano_2_0"
        })
    elif resource_type == "AWS::MQ::Broker":
        base_properties.update({
            "HostInstanceType": "mq.t3.micro",
            "EngineType": "ActiveMQ",
            "DeploymentMode": "SINGLE_INSTANCE"
        })
    elif resource_type == "AWS::MSK::Cluster":
        base_properties.update({
            "BrokerNodeGroupInfo": {
                "InstanceType": "kafka.t3.small"
            }
        })
    elif resource_type == "AWS::DMS::ReplicationInstance":
        base_properties.update({
            "ReplicationInstanceClass": "dms.t3.micro",
            "MultiAZ": False
        })
    elif resource_type == "AWS::CodeBuild::Project":
        base_properties.update({
            "Name": "test-project",
            "ServiceRole": "arn:aws:iam::123456789012:role/service-role/codebuild-test-service-role",
            "Environment": {
                "ComputeType": "BUILD_GENERAL1_SMALL",
                "Type": "LINUX_CONTAINER"
            }
        })
    elif resource_type == "AWS::CloudTrail::Trail":
        base_properties.update({
            "TrailName": "test-trail",
            "S3BucketName": "test-cloudtrail-bucket"
        })
    elif resource_type == "AWS::CloudFront::Distribution":
        base_properties.update({
            "DistributionConfig": {
                "Origins": [
                    {
                        "Id": "test-origin",
                        "DomainName": "example.com"
                    }
                ],
                "DefaultCacheBehavior": {
                    "TargetOriginId": "test-origin",
                    "ViewerProtocolPolicy": "redirect-to-https"
                },
                "Enabled": True
            }
        })
    elif resource_type == "AWS::ElasticBeanstalk::Environment":
        base_properties.update({
            "ApplicationName": "test-app",
            "EnvironmentName": "test-env"
        })
    elif resource_type == "AWS::Elasticsearch::Domain":
        base_properties.update({
            "DomainName": "test-domain",
            "ClusterConfig": {
                "InstanceType": "m4.large.elasticsearch",
                "InstanceCount": 1
            }
        })
    elif resource_type == "AWS::Neptune::DBInstance":
        base_properties.update({
            "DBInstanceClass": "db.t3.medium",
            "DBClusterIdentifier": "test-cluster"
        })
    elif resource_type == "AWS::ECS::Service":
        base_properties.update({
            "ServiceName": "test-service",
            "LaunchType": "FARGATE",
            "TaskDefinition": "test-task-def"
        })
    elif resource_type == "AWS::EKS::FargateProfile":
        base_properties.update({
            "FargateProfileName": "test-fargate-profile",
            "ClusterName": "test-cluster"
        })
    # Add more resource types as needed
    
    return base_properties

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 test_single_resource.py <resource_type>")
        print("Example: python3 test_single_resource.py AWS::EKS::Nodegroup")
        sys.exit(1)
    
    resource_type = sys.argv[1]
    success = test_single_resource(resource_type)
    sys.exit(0 if success else 1) 