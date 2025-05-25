#!/usr/bin/env python3
"""
Test script for the enhanced cost calculator with tiered pricing and usage estimation.
This demonstrates the improvements made to integrate CloudFormation properties and handle tiered pricing.
"""

import sys
import os
import json
from typing import Dict, Any

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from cost_estimator.enhanced_cost_calculator import EnhancedCostCalculator, UsageEstimator
from cost_estimator.infracost import InfracostEstimator

def test_usage_estimation():
    """Test usage estimation for different resource types."""
    print("=== Testing Usage Estimation ===\n")
    
    estimator = UsageEstimator()
    
    # Test API Gateway usage estimation
    print("1. API Gateway REST API Usage Estimation:")
    api_gateway_props = {
        "Name": "ProductionAPI",
        "Description": "High-scale production API",
        "EndpointConfiguration": {
            "Types": ["REGIONAL"]
        }
    }
    
    usage = estimator.estimate_api_gateway_usage(api_gateway_props)
    print(f"   Properties: {api_gateway_props}")
    print(f"   Estimated Usage: {usage}")
    print()
    
    # Test EC2 usage estimation
    print("2. EC2 Instance Usage Estimation:")
    ec2_props = {
        "InstanceType": "m5.large",
        "ImageId": "ami-0abcdef1234567890"
    }
    
    usage = estimator.estimate_ec2_usage(ec2_props)
    print(f"   Properties: {ec2_props}")
    print(f"   Estimated Usage: {usage}")
    print()
    
    # Test Lambda usage estimation
    print("3. Lambda Function Usage Estimation:")
    lambda_props = {
        "MemorySize": 512,
        "Timeout": 30,
        "Runtime": "nodejs18.x"
    }
    
    usage = estimator.estimate_lambda_usage(lambda_props)
    print(f"   Properties: {lambda_props}")
    print(f"   Estimated Usage: {usage}")
    print()


def test_enhanced_cost_calculation():
    """Test enhanced cost calculation with real API calls."""
    print("=== Testing Enhanced Cost Calculation ===\n")
    
    try:
        calculator = EnhancedCostCalculator()
        
        # Test API Gateway with tiered pricing
        print("1. API Gateway REST API with Tiered Pricing:")
        api_props = {
            "Region": "us-east-1",
            "Name": "ProductionAPI",
            "Description": "Production API with high traffic",
            "EndpointConfiguration": {
                "Types": ["REGIONAL"]
            }
        }
        
        cost, usage = calculator.calculate_resource_cost_with_usage(
            "AWS::ApiGateway::RestApi", 
            api_props
        )
        
        print(f"   Resource: AWS::ApiGateway::RestApi")
        print(f"   Properties: {api_props}")
        print(f"   Estimated Usage: {usage}")
        print(f"   Monthly Cost: ${cost.monthly_cost:.2f}")
        print(f"   Pricing Model: {cost.pricing_model}")
        print(f"   Usage Type: {cost.usage_type}")
        print(f"   Metadata: {cost.metadata}")
        print()
        
        # Test with usage override
        print("2. API Gateway with Usage Override:")
        usage_override = {"monthly_requests": 500000000}  # 500M requests
        
        cost, usage = calculator.calculate_resource_cost_with_usage(
            "AWS::ApiGateway::RestApi", 
            api_props,
            usage_override
        )
        
        print(f"   Usage Override: {usage_override}")
        print(f"   Final Usage: {usage}")
        print(f"   Monthly Cost: ${cost.monthly_cost:.2f}")
        print()
        
        # Test EC2 instance
        print("3. EC2 Instance Cost Calculation:")
        ec2_props = {
            "Region": "us-east-1",
            "InstanceType": "m5.large",
            "ImageId": "ami-0abcdef1234567890",
            "Placement": {
                "Tenancy": "default"
            }
        }
        
        cost, usage = calculator.calculate_resource_cost_with_usage(
            "AWS::EC2::Instance", 
            ec2_props
        )
        
        print(f"   Resource: AWS::EC2::Instance")
        print(f"   Properties: {ec2_props}")
        print(f"   Estimated Usage: {usage}")
        print(f"   Monthly Cost: ${cost.monthly_cost:.2f}")
        print(f"   Pricing Model: {cost.pricing_model}")
        print()
        
    except Exception as e:
        print(f"   Error: {str(e)}")
        print("   Note: This requires a valid INFRACOST_API_KEY environment variable")
        print()


def test_stack_cost_calculation():
    """Test calculating costs for an entire CloudFormation stack."""
    print("=== Testing Stack Cost Calculation ===\n")
    
    # Sample CloudFormation stack resources
    stack_resources = [
        {
            "LogicalResourceId": "MyAPI",
            "Type": "AWS::ApiGateway::RestApi",
            "Properties": {
                "Name": "ProductionAPI",
                "Description": "Main production API",
                "EndpointConfiguration": {
                    "Types": ["REGIONAL"]
                }
            }
        },
        {
            "LogicalResourceId": "WebServer",
            "Type": "AWS::EC2::Instance",
            "Properties": {
                "InstanceType": "m5.large",
                "ImageId": "ami-0abcdef1234567890"
            }
        },
        {
            "LogicalResourceId": "Database",
            "Type": "AWS::RDS::DBInstance",
            "Properties": {
                "DBInstanceClass": "db.t3.micro",
                "Engine": "postgres",
                "AllocatedStorage": 20
            }
        },
        {
            "LogicalResourceId": "ProcessorFunction",
            "Type": "AWS::Lambda::Function",
            "Properties": {
                "MemorySize": 256,
                "Timeout": 15,
                "Runtime": "python3.9"
            }
        }
    ]
    
    # Usage overrides for specific resources
    usage_overrides = {
        "MyAPI": {
            "monthly_requests": 1000000000  # 1B requests for high-traffic API
        },
        "ProcessorFunction": {
            "monthly_requests": 5000000  # 5M invocations
        }
    }
    
    try:
        calculator = EnhancedCostCalculator()
        
        result = calculator.calculate_stack_cost_with_usage(
            stack_resources, 
            usage_overrides
        )
        
        print("Stack Cost Analysis:")
        print(f"Total Monthly Cost: ${result['total_monthly_cost']:.2f}")
        print(f"Total Hourly Cost: ${result['total_hourly_cost']:.2f}")
        print(f"Currency: {result['currency']}")
        print()
        
        print("Resource Breakdown:")
        for resource in result['resource_costs']:
            print(f"  {resource['resource_id']} ({resource['resource_type']}):")
            print(f"    Monthly Cost: ${resource['monthly_cost']:.2f}")
            print(f"    Pricing Model: {resource['pricing_model']}")
            if 'error' in resource:
                print(f"    Error: {resource['error']}")
            print()
        
        print("Usage Details:")
        for resource_id, usage in result['usage_details'].items():
            print(f"  {resource_id}: {usage}")
        print()
        
        print("Summary:")
        summary = result['summary']
        print(f"  Total Resources: {summary['total_resources']}")
        print(f"  Successful Calculations: {summary['successful_calculations']}")
        print(f"  Failed Calculations: {summary['failed_calculations']}")
        print()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Note: This requires a valid INFRACOST_API_KEY environment variable")
        print()


def test_tiered_pricing_comparison():
    """Compare basic vs enhanced cost calculation for tiered pricing."""
    print("=== Testing Tiered Pricing Comparison ===\n")
    
    try:
        # Basic estimator
        basic_estimator = InfracostEstimator()
        
        # Enhanced calculator
        enhanced_calculator = EnhancedCostCalculator()
        
        api_props = {
            "Region": "us-east-1",
            "Name": "TestAPI"
        }
        
        print("Comparing Basic vs Enhanced Cost Calculation:")
        print()
        
        # Basic calculation
        print("1. Basic InfracostEstimator:")
        basic_cost = basic_estimator.get_resource_cost("AWS::ApiGateway::RestApi", api_props)
        print(f"   Monthly Cost: ${basic_cost.monthly_cost:.2f}")
        print(f"   Usage Type: {basic_cost.usage_type}")
        print(f"   Pricing Model: {basic_cost.pricing_model}")
        print(f"   Metadata: {basic_cost.metadata}")
        print()
        
        # Enhanced calculation with different usage levels
        usage_scenarios = [
            {"monthly_requests": 100000000, "name": "100M requests"},
            {"monthly_requests": 500000000, "name": "500M requests"},
            {"monthly_requests": 2000000000, "name": "2B requests"},
            {"monthly_requests": 25000000000, "name": "25B requests"}
        ]
        
        print("2. Enhanced Calculator with Different Usage Levels:")
        for scenario in usage_scenarios:
            cost, usage = enhanced_calculator.calculate_resource_cost_with_usage(
                "AWS::ApiGateway::RestApi", 
                api_props,
                {"monthly_requests": scenario["monthly_requests"]}
            )
            
            cost_per_million = (cost.monthly_cost / scenario["monthly_requests"]) * 1000000
            print(f"   {scenario['name']}: ${cost.monthly_cost:.2f}/month (${cost_per_million:.2f} per million)")
        
        print()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Note: This requires a valid INFRACOST_API_KEY environment variable")
        print()


def main():
    """Run all tests."""
    print("Enhanced Cost Calculator Test Suite")
    print("=" * 50)
    print()
    
    # Test 1: Usage Estimation (doesn't require API key)
    test_usage_estimation()
    
    # Test 2: Enhanced Cost Calculation (requires API key)
    test_enhanced_cost_calculation()
    
    # Test 3: Stack Cost Calculation (requires API key)
    test_stack_cost_calculation()
    
    # Test 4: Tiered Pricing Comparison (requires API key)
    test_tiered_pricing_comparison()
    
    print("Test suite completed!")
    print()
    print("Note: Some tests require the INFRACOST_API_KEY environment variable to be set.")
    print("Usage estimation tests work without an API key.")


if __name__ == "__main__":
    main() 