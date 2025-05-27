import os
import sys
import logging
from typing import List, Optional, Tuple
from dotenv import load_dotenv

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cost_estimator.infracost import InfracostEstimator
from cost_estimator.core import ResourceCost
from stack_analyzer.parser import CloudFormationParser
from stack_analyzer.diff import StackDiffAnalyzer, ResourceDiff
from formatter.output import CostReportFormatter

# Configure logging to be less verbose
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING
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
        
        # Show region being used if explicitly provided
        if aws_region:
            print(f"🌍 Using AWS region: {self.aws_region}")
        
        # Initialize cost estimator
        self.infracost = InfracostEstimator(infracost_api_key)
    
    def estimate_costs(
        self,
        old_template: str,
        new_template: str,
        output_format: str = "table"
    ) -> str:
        """Estimate costs for CloudFormation stack changes."""
        try:
            # Check if templates are the same (new deployment scenario)
            if old_template.strip() == new_template.strip():
                # Same template - show cost breakdown for new deployment
                new_parser = CloudFormationParser(new_template)
                new_costs = self._get_resource_costs(new_parser)
                return CostReportFormatter.format_single_template_breakdown(new_costs)
            
            # Different templates - analyze differences
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
            elif output_format == "table":
                return CostReportFormatter.format_cost_comparison_table(
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
                
                # Get cost using Infracost
                if self.infracost.is_resource_supported(resource.type):
                    cost = self.infracost.get_resource_cost(
                        resource.type,
                        properties
                    )
                else:
                    logger.warning(f"Resource type {resource.type} is not supported by Infracost")
                    continue
                
                costs.append(cost)
                
            except Exception as e:
                logger.error(f"Error getting cost for resource {resource.logical_id}: {str(e)}")
                continue
        
        return costs

def main():
    """Main entry point for the script."""
    if len(sys.argv) < 3:
        print("Usage: python main.py <old_template_file> <new_template_file> [output_format] [region]")
        print("  output_format: table (default), github, full")
        print("  region: AWS region (default: from .env or us-east-1)")
        print("  Note: If same template is passed for both old and new, shows cost breakdown for new deployment")
        sys.exit(1)
    
    old_template_file = sys.argv[1]
    new_template_file = sys.argv[2]
    output_format = sys.argv[3] if len(sys.argv) > 3 else "table"
    aws_region = sys.argv[4] if len(sys.argv) > 4 else None
    
    try:
        # Read template files
        with open(old_template_file, 'r') as f:
            old_template = f.read()
        with open(new_template_file, 'r') as f:
            new_template = f.read()
        
        # Initialize cost estimator with optional region
        estimator = CostEstimator(aws_region=aws_region)
        
        # Generate cost report
        report = estimator.estimate_costs(old_template, new_template, output_format)
        
        # Output the report
        print(report)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 