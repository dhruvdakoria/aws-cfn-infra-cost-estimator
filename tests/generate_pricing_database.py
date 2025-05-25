#!/usr/bin/env python3
"""
Generate comprehensive pricing database for all supported AWS resources.
This script creates a JSON file containing pricing information for all resources
in both us-east-1 and ca-central-1 regions.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cost_estimator.infracost import InfracostEstimator
from cost_estimator.resource_mappings import get_paid_resources, get_free_resources
from cost_estimator.dynamic_pricing import get_dynamic_pricing_fetcher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PricingDatabaseGenerator:
    """Generates comprehensive pricing database for all AWS resources."""
    
    def __init__(self):
        load_dotenv()
        self.estimator = InfracostEstimator()
        self.pricing_fetcher = get_dynamic_pricing_fetcher()
        self.regions = ["us-east-1", "ca-central-1"]
        
    def generate_pricing_database(self) -> Dict[str, Any]:
        """Generate comprehensive pricing database."""
        logger.info("🚀 Starting pricing database generation...")
        
        database = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "regions": self.regions,
                "total_paid_resources": len(get_paid_resources()),
                "total_free_resources": len(get_free_resources()),
                "generator_version": "3.0"
            },
            "paid_resources": {},
            "free_resources": {},
            "regional_comparison": {},
            "summary": {}
        }
        
        # Process paid resources
        logger.info("📊 Processing paid resources...")
        database["paid_resources"] = self._process_paid_resources()
        
        # Process free resources
        logger.info("🆓 Processing free resources...")
        database["free_resources"] = self._process_free_resources()
        
        # Generate regional comparison
        logger.info("🌍 Generating regional comparison...")
        database["regional_comparison"] = self._generate_regional_comparison(database["paid_resources"])
        
        # Generate summary
        database["summary"] = self._generate_summary(database)
        
        logger.info("✅ Pricing database generation completed!")
        return database
    
    def _process_paid_resources(self) -> Dict[str, Any]:
        """Process all paid resources and get their pricing information."""
        paid_resources = {}
        paid_resource_types = list(get_paid_resources().keys())
        
        for i, resource_type in enumerate(paid_resource_types, 1):
            logger.info(f"Processing {i}/{len(paid_resource_types)}: {resource_type}")
            
            resource_data = {
                "resource_type": resource_type,
                "terraform_equivalent": get_paid_resources()[resource_type].get("terraform_equivalent", ""),
                "service": get_paid_resources()[resource_type].get("service", ""),
                "product_family": get_paid_resources()[resource_type].get("productFamily", ""),
                "regions": {}
            }
            
            # Get pricing for each region
            for region in self.regions:
                try:
                    region_data = self._get_resource_pricing(resource_type, region)
                    resource_data["regions"][region] = region_data
                except Exception as e:
                    logger.error(f"Error processing {resource_type} in {region}: {str(e)}")
                    resource_data["regions"][region] = {
                        "error": str(e),
                        "pricing_available": False
                    }
            
            paid_resources[resource_type] = resource_data
        
        return paid_resources
    
    def _process_free_resources(self) -> Dict[str, Any]:
        """Process all free resources."""
        free_resources = {}
        free_resource_types = list(get_free_resources())
        
        for resource_type in free_resource_types:
            free_resources[resource_type] = {
                "resource_type": resource_type,
                "pricing_model": "free",
                "cost": {
                    "hourly": 0.0,
                    "monthly": 0.0,
                    "currency": "USD"
                },
                "description": "This resource is free to use",
                "regions": {region: {"pricing_available": True, "cost": 0.0} for region in self.regions}
            }
        
        return free_resources
    
    def _get_resource_pricing(self, resource_type: str, region: str) -> Dict[str, Any]:
        """Get detailed pricing information for a specific resource in a region."""
        try:
            # Prepare resource properties
            properties = {
                "Region": region,
                "id": f"pricing-test-{resource_type.replace('::', '-').lower()}"
            }
            
            # Get cost estimate
            cost = self.estimator.get_resource_cost(resource_type, properties)
            
            # Get dynamic pricing information
            dynamic_pricing = self.pricing_fetcher.get_usage_based_pricing(resource_type, region)
            
            return {
                "pricing_available": True,
                "pricing_model": cost.pricing_model,
                "cost": {
                    "hourly": cost.hourly_cost,
                    "monthly": cost.monthly_cost,
                    "currency": cost.currency
                },
                "usage_type": cost.usage_type,
                "pricing_details": cost.pricing_details,
                "dynamic_pricing": dynamic_pricing if dynamic_pricing else None,
                "metadata": cost.metadata
            }
            
        except Exception as e:
            return {
                "pricing_available": False,
                "error": str(e),
                "pricing_model": "unknown"
            }
    
    def _generate_regional_comparison(self, paid_resources: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparison between regions."""
        comparison = {
            "price_differences": {},
            "region_summary": {}
        }
        
        # Calculate regional summaries
        for region in self.regions:
            total_resources = 0
            working_resources = 0
            total_monthly_cost = 0.0
            
            for resource_type, resource_data in paid_resources.items():
                region_data = resource_data["regions"].get(region, {})
                total_resources += 1
                
                if region_data.get("pricing_available", False):
                    working_resources += 1
                    cost_data = region_data.get("cost", {})
                    total_monthly_cost += cost_data.get("monthly", 0.0)
            
            comparison["region_summary"][region] = {
                "total_resources": total_resources,
                "working_resources": working_resources,
                "success_rate": (working_resources / total_resources * 100) if total_resources > 0 else 0,
                "total_monthly_cost": total_monthly_cost
            }
        
        # Calculate price differences between regions
        if len(self.regions) >= 2:
            region1, region2 = self.regions[0], self.regions[1]
            
            for resource_type, resource_data in paid_resources.items():
                region1_data = resource_data["regions"].get(region1, {})
                region2_data = resource_data["regions"].get(region2, {})
                
                if (region1_data.get("pricing_available") and 
                    region2_data.get("pricing_available")):
                    
                    cost1 = region1_data["cost"]["monthly"]
                    cost2 = region2_data["cost"]["monthly"]
                    
                    if cost1 > 0 and cost2 > 0:
                        difference = cost2 - cost1
                        percentage = (difference / cost1) * 100
                        
                        comparison["price_differences"][resource_type] = {
                            f"{region1}_monthly": cost1,
                            f"{region2}_monthly": cost2,
                            "difference": difference,
                            "percentage_change": percentage
                        }
        
        return comparison
    
    def _generate_summary(self, database: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics."""
        paid_resources = database["paid_resources"]
        free_resources = database["free_resources"]
        
        summary = {
            "total_resources": len(paid_resources) + len(free_resources),
            "paid_resources_count": len(paid_resources),
            "free_resources_count": len(free_resources),
            "regions_tested": len(self.regions),
            "pricing_models": {
                "fixed": 0,
                "usage_based": 0,
                "free": len(free_resources),
                "unknown": 0
            },
            "success_rates": {}
        }
        
        # Count pricing models
        for resource_data in paid_resources.values():
            for region_data in resource_data["regions"].values():
                if region_data.get("pricing_available"):
                    model = region_data.get("pricing_model", "unknown")
                    if model in summary["pricing_models"]:
                        summary["pricing_models"][model] += 1
                    else:
                        summary["pricing_models"]["unknown"] += 1
        
        # Calculate success rates by region
        for region in self.regions:
            working = 0
            total = len(paid_resources)
            
            for resource_data in paid_resources.values():
                region_data = resource_data["regions"].get(region, {})
                if region_data.get("pricing_available", False):
                    working += 1
            
            summary["success_rates"][region] = {
                "working": working,
                "total": total,
                "percentage": (working / total * 100) if total > 0 else 0
            }
        
        return summary

def main():
    """Main function to generate and save the pricing database."""
    try:
        # Generate pricing database
        generator = PricingDatabaseGenerator()
        database = generator.generate_pricing_database()
        
        # Save to JSON file
        output_file = "aws_resources_pricing_database.json"
        with open(output_file, 'w') as f:
            json.dump(database, f, indent=2, sort_keys=True)
        
        # Print summary
        print("\n" + "="*80)
        print("🎯 PRICING DATABASE GENERATION COMPLETE")
        print("="*80)
        
        summary = database["summary"]
        print(f"📊 Total Resources: {summary['total_resources']}")
        print(f"💰 Paid Resources: {summary['paid_resources_count']}")
        print(f"🆓 Free Resources: {summary['free_resources_count']}")
        print(f"🌍 Regions Tested: {summary['regions_tested']}")
        
        print("\n📈 Success Rates by Region:")
        for region, stats in summary["success_rates"].items():
            print(f"  {region}: {stats['working']}/{stats['total']} ({stats['percentage']:.1f}%)")
        
        print("\n💡 Pricing Models:")
        for model, count in summary["pricing_models"].items():
            print(f"  {model.title()}: {count}")
        
        print(f"\n💾 Database saved to: {output_file}")
        print(f"📁 File size: {os.path.getsize(output_file) / 1024:.1f} KB")
        
        # Show regional comparison if available
        if "regional_comparison" in database and database["regional_comparison"]["region_summary"]:
            print("\n🌍 Regional Cost Comparison:")
            for region, stats in database["regional_comparison"]["region_summary"].items():
                print(f"  {region}: ${stats['total_monthly_cost']:.2f}/month")
        
        print("\n✅ Pricing database generation completed successfully!")
        
    except Exception as e:
        logger.error(f"Error generating pricing database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 