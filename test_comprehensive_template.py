#!/usr/bin/env python3
"""
Test script to analyze the comprehensive CloudFormation template.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cost_estimator.infracost import InfracostEstimator
from cost_estimator.resource_mappings import is_free_resource, is_paid_resource
from stack_analyzer.parser import CloudFormationParser

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_template(template_path: str, region: str = "us-east-1"):
    """Analyze a CloudFormation template and show pricing for all resources."""
    load_dotenv()
    
    print(f"🧪 COMPREHENSIVE TEMPLATE ANALYSIS")
    print(f"Template: {template_path}")
    print(f"Region: {region}")
    print("=" * 80)
    
    # Parse template
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    parser = CloudFormationParser(template_content)
    estimator = InfracostEstimator()
    
    # Analyze resources
    paid_resources = []
    free_resources = []
    unsupported_resources = []
    total_monthly_cost = 0.0
    
    for resource in parser.get_resources():
        resource_type = resource.type
        logical_id = resource.logical_id
        
        if is_free_resource(resource_type):
            free_resources.append((logical_id, resource_type))
        elif is_paid_resource(resource_type):
            try:
                # Add region to properties
                properties = resource.properties.copy()
                properties["Region"] = region
                properties["id"] = logical_id
                
                cost = estimator.get_resource_cost(resource_type, properties)
                paid_resources.append((logical_id, resource_type, cost.monthly_cost))
                total_monthly_cost += cost.monthly_cost
                
            except Exception as e:
                unsupported_resources.append((logical_id, resource_type, str(e)))
        else:
            unsupported_resources.append((logical_id, resource_type, "Not in resource mappings"))
    
    # Display results
    print(f"\n💰 PAID RESOURCES ({len(paid_resources)} resources)")
    print("-" * 80)
    if paid_resources:
        for logical_id, resource_type, cost in sorted(paid_resources, key=lambda x: x[2], reverse=True):
            status = "✅" if cost > 0 else "⚠️"
            print(f"{status} {logical_id:<30} | {resource_type:<40} | ${cost:8.2f}/month")
    else:
        print("No paid resources found")
    
    print(f"\n🆓 FREE RESOURCES ({len(free_resources)} resources)")
    print("-" * 80)
    if free_resources:
        for logical_id, resource_type in sorted(free_resources):
            print(f"✅ {logical_id:<30} | {resource_type:<40} | $    0.00/month")
    else:
        print("No free resources found")
    
    print(f"\n❌ UNSUPPORTED RESOURCES ({len(unsupported_resources)} resources)")
    print("-" * 80)
    if unsupported_resources:
        for logical_id, resource_type, error in sorted(unsupported_resources):
            print(f"❌ {logical_id:<30} | {resource_type:<40} | {error}")
    else:
        print("All resources are supported!")
    
    print(f"\n📊 SUMMARY")
    print("=" * 80)
    print(f"Total Resources: {len(paid_resources) + len(free_resources) + len(unsupported_resources)}")
    print(f"Paid Resources: {len(paid_resources)}")
    print(f"Free Resources: {len(free_resources)}")
    print(f"Unsupported Resources: {len(unsupported_resources)}")
    print(f"Total Monthly Cost: ${total_monthly_cost:.2f}")
    
    # Show resources with $0 cost (might need attention)
    zero_cost_resources = [r for r in paid_resources if r[2] == 0.0]
    if zero_cost_resources:
        print(f"\n⚠️ PAID RESOURCES WITH $0 COST ({len(zero_cost_resources)} resources)")
        print("-" * 80)
        print("These might be usage-based or need query builder fixes:")
        for logical_id, resource_type, cost in zero_cost_resources:
            print(f"⚠️ {logical_id:<30} | {resource_type}")

def main():
    """Main function."""
    template_path = "templates/all-paid-resources-test.yaml"
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return 1
    
    # Test both regions
    for region in ["us-east-1", "ca-central-1"]:
        analyze_template(template_path, region)
        print("\n" + "="*100 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 