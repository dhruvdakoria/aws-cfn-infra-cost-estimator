import os
import sys
import logging
from typing import List, Optional, Tuple
from dotenv import load_dotenv

from cost_estimator.infracost import InfracostEstimator
from cost_estimator.aws_pricing import AWSPricingEstimator
from cost_estimator.core import ResourceCost
from stack_analyzer.parser import CloudFormationParser
from stack_analyzer.diff import StackDiffAnalyzer, ResourceDiff
from formatter.output import CostReportFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CostEstimator:
    """Main class for estimating CloudFormation stack costs."""
    
    def __init__(self, infracost_api_key: Optional[str] = None, aws_region: Optional[str] = None):
        """Initialize the cost estimator with API keys and configuration."""
        load_dotenv()  # Load environment variables from .env file
        
        # Get region from parameter, environment variable, or default
        self.aws_region = aws_region or os.getenv("AWS_REGION") or "us-east-1"
        logger.info(f"Using AWS region: {self.aws_region}")
        
        # Initialize cost estimators
        self.infracost = InfracostEstimator(infracost_api_key)
        self.aws_pricing = AWSPricingEstimator(self.aws_region)
    
    def estimate_costs(
        self,
        old_template: str,
        new_template: str,
        output_format: str = "github"
    ) -> str:
        """Estimate costs for CloudFormation stack changes."""
        try:
            # Analyze stack differences
            diff_analyzer = StackDiffAnalyzer(old_template, new_template)
            resource_diffs = diff_analyzer.get_resource_diffs()
            
            # Get costs for old and new resources
            old_costs = self._get_resource_costs(diff_analyzer.old_parser)
            new_costs = self._get_resource_costs(diff_analyzer.new_parser)
            
            # Format the report
            if output_format == "github":
                return CostReportFormatter.format_github_comment(
                    old_costs, new_costs, resource_diffs
                )
            else:
                return CostReportFormatter.format_full_report(
                    old_costs, new_costs, resource_diffs
                )
                
        except Exception as e:
            logger.error(f"Error estimating costs: {str(e)}")
            raise
    
    def _get_resource_costs(self, parser: CloudFormationParser) -> List[ResourceCost]:
        """Get costs for all resources in a template."""
        costs = []
        
        for resource in parser.get_resources():
            try:
                # Prepare resource properties with region information
                properties = resource.properties.copy()
                properties["Region"] = self.aws_region
                properties["id"] = resource.logical_id
                
                # Try Infracost first
                if self.infracost.is_resource_supported(resource.type):
                    cost = self.infracost.get_resource_cost(
                        resource.type,
                        properties
                    )
                # Fall back to AWS Pricing API
                elif self.aws_pricing.is_resource_supported(resource.type):
                    cost = self.aws_pricing.get_resource_cost(
                        resource.type,
                        properties
                    )
                else:
                    logger.warning(f"Resource type {resource.type} is not supported by any cost estimator")
                    continue
                
                costs.append(cost)
                
            except Exception as e:
                logger.error(f"Error getting cost for resource {resource.logical_id}: {str(e)}")
                continue
        
        return costs

def main():
    """Main entry point for the script."""
    if len(sys.argv) < 3:
        print("Usage: python main.py <old_template_file> <new_template_file> [output_format]")
        sys.exit(1)
    
    old_template_file = sys.argv[1]
    new_template_file = sys.argv[2]
    output_format = sys.argv[3] if len(sys.argv) > 3 else "github"
    
    try:
        # Read template files
        with open(old_template_file, 'r') as f:
            old_template = f.read()
        with open(new_template_file, 'r') as f:
            new_template = f.read()
        
        # Initialize cost estimator
        estimator = CostEstimator()
        
        # Generate cost report
        report = estimator.estimate_costs(old_template, new_template, output_format)
        
        # Output the report
        print(report)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 