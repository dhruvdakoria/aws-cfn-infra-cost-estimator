#!/usr/bin/env python3
"""
Test script to check for $0 costs in paid resources and identify query builder issues.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cost_estimator.infracost import InfracostEstimator
from cost_estimator.resource_mappings import get_paid_resources
from stack_analyzer.parser import CloudFormationParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_template_costs(template_path: str) -> List[Tuple[str, str, float]]:
    """Test costs for all paid resources in a template."""
    logger.info(f"🧪 Testing costs for template: {template_path}")
    
    if not os.path.exists(template_path):
        logger.error(f"❌ Template file not found: {template_path}")
        return []
    
    load_dotenv()
    
    try:
        # Parse template
        with open(template_path, 'r') as f:
            template_content = f.read()
        parser = CloudFormationParser(template_content)
        resources = parser.get_resources()
        
        # Initialize estimator
        estimator = InfracostEstimator()
        paid_resources = get_paid_resources()
        
        results = []
        
        for resource in resources:
            if resource.type in paid_resources:
                try:
                    # Add region to properties if not present
                    properties = resource.properties.copy()
                    if "Region" not in properties:
                        properties["Region"] = "us-east-1"
                    properties["id"] = resource.logical_id
                    
                    cost = estimator.get_resource_cost(resource.type, properties)
                    results.append((resource.logical_id, resource.type, cost.monthly_cost))
                    
                    if cost.monthly_cost > 0:
                        logger.info(f"✅ {resource.logical_id} ({resource.type}): ${cost.monthly_cost:.2f}/month")
                    else:
                        # Check if this is a free resource or a usage-based paid resource
                        from cost_estimator.resource_mappings import is_free_resource
                        if is_free_resource(resource.type):
                            logger.info(f"🆓 {resource.logical_id} ({resource.type}): $0.00/month (FREE RESOURCE)")
                        else:
                            # These are usage-based resources where base cost is $0
                            usage_based_resources = {
                                "AWS::SNS::Topic", "AWS::SQS::Queue", "AWS::KMS::Key", 
                                "AWS::ApiGateway::RestApi", "AWS::ApiGatewayV2::Api"
                            }
                            if resource.type in usage_based_resources:
                                logger.info(f"💰 {resource.logical_id} ({resource.type}): $0.00/month (USAGE-BASED PRICING)")
                            else:
                                logger.warning(f"⚠️ {resource.logical_id} ({resource.type}): $0.00/month - NEEDS QUERY BUILDER FIX")
                        
                except Exception as e:
                    logger.error(f"❌ Error estimating cost for {resource.logical_id} ({resource.type}): {e}")
                    results.append((resource.logical_id, resource.type, -1.0))  # -1 indicates error
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Failed to test template {template_path}: {e}")
        return []

def analyze_zero_cost_resources(results: List[Tuple[str, str, float]]) -> Dict[str, List[str]]:
    """Analyze which resource types are returning $0 costs and actually need fixing."""
    from cost_estimator.resource_mappings import is_free_resource
    
    zero_cost_types = {}
    
    # Resources that are expected to have $0 base cost (usage-based pricing)
    usage_based_resources = {
        "AWS::SNS::Topic", "AWS::SQS::Queue", "AWS::KMS::Key", 
        "AWS::ApiGateway::RestApi", "AWS::ApiGatewayV2::Api"
    }
    
    for logical_id, resource_type, cost in results:
        if cost == 0.0:
            # Skip free resources and known usage-based resources
            if not is_free_resource(resource_type) and resource_type not in usage_based_resources:
                if resource_type not in zero_cost_types:
                    zero_cost_types[resource_type] = []
                zero_cost_types[resource_type].append(logical_id)
    
    return zero_cost_types

def main():
    """Main function to test both templates."""
    logger.info("🚀 Testing Paid Resources Costs in CloudFormation Templates")
    
    templates = [
        "templates/test-paid-resources.yaml",
        "templates/comprehensive-test-stack.yaml"
    ]
    
    all_results = []
    
    for template in templates:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {template}")
        logger.info(f"{'='*60}")
        
        results = test_template_costs(template)
        all_results.extend(results)
        
        # Analyze zero cost resources for this template
        zero_cost_types = analyze_zero_cost_resources(results)
        
        if zero_cost_types:
            logger.warning(f"\n⚠️ Resources with $0 costs in {template}:")
            for resource_type, logical_ids in zero_cost_types.items():
                logger.warning(f"  {resource_type}: {', '.join(logical_ids)}")
        else:
            logger.info(f"✅ All paid resources in {template} have non-zero costs!")
    
    # Overall analysis
    logger.info(f"\n{'='*60}")
    logger.info("OVERALL ANALYSIS")
    logger.info(f"{'='*60}")
    
    all_zero_cost_types = analyze_zero_cost_resources(all_results)
    
    if all_zero_cost_types:
        logger.warning("⚠️ Resource types that need query builder fixes:")
        for resource_type, logical_ids in all_zero_cost_types.items():
            logger.warning(f"  🔧 {resource_type} (found in: {', '.join(logical_ids)})")
        
        logger.info("\n💡 To fix these issues:")
        logger.info("1. Check the query_builders.py file for these resource types")
        logger.info("2. Verify the attribute filters match Infracost API expectations")
        logger.info("3. Test the GraphQL queries manually if needed")
        logger.info("4. Update the query builders with correct service/productFamily/attributes")
        
        return 1
    else:
        logger.info("🎉 All paid resources are returning non-zero costs!")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 