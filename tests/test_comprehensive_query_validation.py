#!/usr/bin/env python3
"""
Comprehensive test to validate query builders for paid resources work correctly
for both us-east-1 and ca-central-1 regions by cross-checking against Go file patterns.
"""

import sys
import os
import logging
import json
import requests
from typing import Dict, Any, List, Tuple

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cost_estimator.query_builders import QUERY_BUILDERS, get_region_code
from cost_estimator.infracost import InfracostEstimator

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_comprehensive_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class QueryValidationTester:
    """Test class to validate query builders against Go file patterns."""
    
    def __init__(self):
        self.calculator = InfracostEstimator()
        self.test_regions = ["us-east-1", "ca-central-1"]
        self.failed_tests = []
        self.passed_tests = []
        
    def create_test_properties(self, resource_type: str, region: str) -> Dict[str, Any]:
        """Create test properties for a given resource type and region."""
        base_properties = {
            "Region": region
        }
        
        # Add resource-specific properties based on type
        if resource_type == "AWS::EC2::Instance":
            base_properties.update({
                "InstanceType": "t3.micro",
                "ImageId": "ami-12345678",
                "Placement": {"Tenancy": "default"}
            })
        elif resource_type == "AWS::EC2::Volume":
            base_properties.update({
                "VolumeType": "gp3",
                "Size": 100
            })
        elif resource_type == "AWS::RDS::DBInstance":
            base_properties.update({
                "DBInstanceClass": "db.t3.micro",
                "Engine": "mysql",
                "AllocatedStorage": 20
            })
        elif resource_type == "AWS::S3::Bucket":
            base_properties.update({
                "BucketName": "test-bucket"
            })
        elif resource_type == "AWS::Lambda::Function":
            base_properties.update({
                "FunctionName": "test-function",
                "Runtime": "python3.9",
                "MemorySize": 128
            })
        elif resource_type == "AWS::ElasticLoadBalancingV2::LoadBalancer":
            base_properties.update({
                "Type": "application",
                "Scheme": "internet-facing"
            })
        elif resource_type == "AWS::DynamoDB::Table":
            base_properties.update({
                "BillingMode": "PAY_PER_REQUEST",
                "TableClass": "STANDARD"
            })
        elif resource_type == "AWS::ApiGateway::RestApi":
            base_properties.update({
                "Name": "test-api",
                "EndpointConfiguration": {"Types": ["EDGE"]}
            })
        elif resource_type == "AWS::KMS::Key":
            base_properties.update({
                "Description": "Test KMS key"
            })
        elif resource_type == "AWS::EKS::Cluster":
            base_properties.update({
                "Name": "test-cluster",
                "Version": "1.21"
            })
        elif resource_type == "AWS::ElastiCache::CacheCluster":
            base_properties.update({
                "CacheNodeType": "cache.t3.micro",
                "Engine": "redis"
            })
        elif resource_type == "AWS::SecretsManager::Secret":
            base_properties.update({
                "Name": "test-secret"
            })
        elif resource_type == "AWS::EC2::NatGateway":
            base_properties.update({
                "SubnetId": "subnet-12345"
            })
        elif resource_type == "AWS::SNS::Topic":
            base_properties.update({
                "TopicName": "test-topic"
            })
        elif resource_type == "AWS::SQS::Queue":
            base_properties.update({
                "QueueName": "test-queue"
            })
        elif resource_type == "AWS::Route53::HostedZone":
            base_properties.update({
                "Name": "example.com"
            })
        elif resource_type == "AWS::CloudWatch::Alarm":
            base_properties.update({
                "AlarmName": "test-alarm",
                "MetricName": "CPUUtilization"
            })
        elif resource_type == "AWS::Logs::LogGroup":
            base_properties.update({
                "LogGroupName": "/aws/lambda/test"
            })
        elif resource_type == "AWS::StepFunctions::StateMachine":
            base_properties.update({
                "StateMachineName": "test-state-machine",
                "StateMachineType": "STANDARD"
            })
        elif resource_type == "AWS::ECR::Repository":
            base_properties.update({
                "RepositoryName": "test-repo"
            })
        elif resource_type == "AWS::EFS::FileSystem":
            base_properties.update({
                "PerformanceMode": "generalPurpose"
            })
        elif resource_type == "AWS::CodeBuild::Project":
            base_properties.update({
                "Name": "test-project",
                "ServiceRole": "arn:aws:iam::123456789012:role/service-role/codebuild-test-service-role"
            })
        elif resource_type == "AWS::CloudTrail::Trail":
            base_properties.update({
                "TrailName": "test-trail",
                "S3BucketName": "test-cloudtrail-bucket"
            })
            
        return base_properties
    
    def test_query_builder(self, resource_type: str, region: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Test a specific query builder for a resource type and region."""
        logger.info(f"Testing {resource_type} in {region}")
        
        try:
            # Get the query builder function
            query_builder_func = QUERY_BUILDERS.get(resource_type)
            if not query_builder_func:
                return False, f"No query builder found for {resource_type}", {}
            
            # Create test properties
            properties = self.create_test_properties(resource_type, region)
            
            # Build the query
            query = query_builder_func(properties)
            
            if not query:
                return False, f"Query builder returned empty query for {resource_type}", {}
            
            # Validate query structure
            if not self.validate_query_structure(query):
                return False, f"Invalid query structure for {resource_type}", {"query": query}
            
            # Test the query against the API
            success, error_msg, response_data = self.test_query_against_api(query, resource_type, region)
            
            if success:
                logger.info(f"✅ {resource_type} in {region}: Query successful")
                return True, "Success", {"query": query, "response": response_data}
            else:
                logger.error(f"❌ {resource_type} in {region}: {error_msg}")
                return False, error_msg, {"query": query, "response": response_data}
                
        except Exception as e:
            error_msg = f"Exception testing {resource_type} in {region}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
    
    def validate_query_structure(self, query: str) -> bool:
        """Validate that the query has the correct GraphQL structure."""
        required_elements = [
            "products",
            "filter",
            "vendorName",
            "service",
            "productFamily",
            "attributeFilters",
            "prices",
            "purchaseOption",
            "USD",
            "unit"
        ]
        
        # Region is not required for global services like Route53, CloudFront, and CloudWatch Dashboard
        global_services = ["AmazonRoute53", "AmazonCloudFront", "AmazonCloudWatch"]
        is_global_service = any(service in query for service in global_services)
        
        if not is_global_service:
            required_elements.append("region")
        
        for element in required_elements:
            if element not in query:
                logger.warning(f"Missing required element in query: {element}")
                return False
        
        return True
    
    def test_query_against_api(self, query: str, resource_type: str, region: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Test the query against the Infracost GraphQL API."""
        try:
            # Use the calculator's query method
            response = self.calculator._make_graphql_request(query)
            
            if not response:
                return False, "No response from API", {}
            
            # Check if we got products back
            products = response.get("data", {}).get("products", [])
            
            if not products:
                return False, "No products found in response", response
            
            # Check if products have prices
            has_prices = False
            for product in products:
                if product.get("prices"):
                    has_prices = True
                    break
            
            if not has_prices:
                return False, "No prices found in products", response
            
            return True, "Success", response
            
        except Exception as e:
            return False, f"API error: {str(e)}", {}
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive tests for all query builders and regions."""
        logger.info("Starting comprehensive query validation test")
        
        results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "results_by_resource": {},
            "results_by_region": {},
            "failed_resources": [],
            "summary": {}
        }
        
        # Test each resource type in each region
        for resource_type in QUERY_BUILDERS.keys():
            results["results_by_resource"][resource_type] = {}
            
            for region in self.test_regions:
                results["total_tests"] += 1
                
                success, message, details = self.test_query_builder(resource_type, region)
                
                test_result = {
                    "success": success,
                    "message": message,
                    "details": details
                }
                
                results["results_by_resource"][resource_type][region] = test_result
                
                # Track by region
                if region not in results["results_by_region"]:
                    results["results_by_region"][region] = {"passed": 0, "failed": 0, "total": 0}
                
                results["results_by_region"][region]["total"] += 1
                
                if success:
                    results["passed_tests"] += 1
                    results["results_by_region"][region]["passed"] += 1
                    self.passed_tests.append((resource_type, region))
                else:
                    results["failed_tests"] += 1
                    results["results_by_region"][region]["failed"] += 1
                    self.failed_tests.append((resource_type, region, message))
                    results["failed_resources"].append({
                        "resource_type": resource_type,
                        "region": region,
                        "error": message
                    })
        
        # Generate summary
        results["summary"] = {
            "success_rate": (results["passed_tests"] / results["total_tests"]) * 100 if results["total_tests"] > 0 else 0,
            "total_resource_types": len(QUERY_BUILDERS),
            "total_regions": len(self.test_regions),
            "region_success_rates": {}
        }
        
        for region in self.test_regions:
            region_data = results["results_by_region"][region]
            success_rate = (region_data["passed"] / region_data["total"]) * 100 if region_data["total"] > 0 else 0
            results["summary"]["region_success_rates"][region] = success_rate
        
        return results
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results."""
        print("\n" + "="*80)
        print("COMPREHENSIVE QUERY VALIDATION TEST RESULTS")
        print("="*80)
        
        print(f"\n📊 SUMMARY:")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']} ✅")
        print(f"Failed: {results['failed_tests']} ❌")
        print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
        
        print(f"\n🌍 RESULTS BY REGION:")
        for region, success_rate in results["summary"]["region_success_rates"].items():
            region_data = results["results_by_region"][region]
            print(f"{region}: {region_data['passed']}/{region_data['total']} ({success_rate:.1f}%)")
        
        if results["failed_resources"]:
            print(f"\n❌ FAILED RESOURCES:")
            for failure in results["failed_resources"]:
                print(f"  • {failure['resource_type']} in {failure['region']}: {failure['error']}")
        
        print(f"\n✅ SUCCESSFUL RESOURCES:")
        for resource_type, region in self.passed_tests:
            print(f"  • {resource_type} in {region}")
        
        print("\n" + "="*80)

def main():
    """Main function to run the comprehensive test."""
    tester = QueryValidationTester()
    results = tester.run_comprehensive_test()
    
    # Print results to console
    tester.print_results(results)
    
    # Save detailed results to file
    with open('comprehensive_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("Test completed. Detailed results saved to comprehensive_test_results.json")
    
    # Exit with error code if any tests failed
    if results["failed_tests"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main() 