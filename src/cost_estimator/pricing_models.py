"""
Pricing models and details for AWS resources.
This module provides detailed pricing information for resources that have usage-based pricing.
Now uses dynamic pricing fetcher for real-time pricing instead of hardcoded values.
"""

from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Pricing model definitions
PRICING_MODELS = {
    # Usage-based resources with detailed pricing information
    "AWS::SNS::Topic": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Pay per request and notification delivery",
        "unit": "per request/notification"
    },
    
    "AWS::SQS::Queue": {
        "model": "usage_based", 
        "base_cost": 0.0,
        "details": "Pay per request with free tier",
        "unit": "per request"
    },
    
    "AWS::KMS::Key": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Customer managed keys with per-request charges",
        "unit": "per key + per request"
    },
    
    "AWS::ApiGateway::RestApi": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Pay per request plus data transfer",
        "unit": "per request"
    },
    
    "AWS::ApiGatewayV2::Api": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "HTTP APIs and WebSocket APIs pricing",
        "unit": "per request/message"
    },
    
    "AWS::CloudWatch::Alarm": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Standard and high-resolution alarm pricing",
        "unit": "per alarm per month"
    },
    
    "AWS::CloudWatch::Dashboard": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Dashboard pricing with free tier",
        "unit": "per dashboard per month"
    },
    
    "AWS::StepFunctions::StateMachine": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Standard and Express workflow pricing",
        "unit": "per state transition/request"
    },
    
    "AWS::Route53::HostedZone": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Hosted zone and query pricing",
        "unit": "per zone + per query"
    },
    
    "AWS::Route53::HealthCheck": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Health check monitoring",
        "unit": "per health check per month"
    },
    
    "AWS::DynamoDB::Table": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "On-demand or provisioned capacity pricing",
        "unit": "per request + storage"
    },
    
    "AWS::EKS::Cluster": {
        "model": "fixed",
        "base_cost": 73.0,  # $0.10 per hour = ~$73/month
        "details": "EKS cluster: $0.10 per hour ($73/month) + worker node costs",
        "unit": "per cluster per hour"
    },
    
    "AWS::ECR::Repository": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Storage and data transfer pricing",
        "unit": "per GB storage + data transfer"
    },
    
    "AWS::EFS::FileSystem": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Storage class based pricing",
        "unit": "per GB per month"
    },
    
    "AWS::CodeBuild::Project": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Build minutes by compute type",
        "unit": "per build minute"
    },
    
    "AWS::CloudTrail::Trail": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Management and data event pricing",
        "unit": "per 100K events"
    },
    
    "AWS::Kinesis::Stream": {
        "model": "fixed",
        "base_cost": 11.0,  # $0.015 per hour per shard = ~$11/month
        "details": "Shard hours: $0.015 per shard per hour + $0.014 per 1M PUT payload units",
        "unit": "per shard hour + per payload unit"
    },
    
    "AWS::Backup::BackupVault": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Backup storage by storage class",
        "unit": "per GB per month"
    },
    
    "AWS::Transfer::Server": {
        "model": "fixed",
        "base_cost": 216.0,  # $0.30 per hour = ~$216/month
        "details": "SFTP/FTPS/FTP endpoint: $0.30 per hour + $0.04 per GB data transfer",
        "unit": "per endpoint hour + per GB transfer"
    },
    
    "AWS::SSM::Parameter": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Standard parameters free, advanced parameters charged",
        "unit": "per 10K requests (advanced only)"
    },
    
    "AWS::SSM::Activation": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Managed instance pricing",
        "unit": "per managed instance per hour"
    },
    
    "AWS::WAF::WebACL": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Web ACL and rule pricing",
        "unit": "per ACL + per request + per rule"
    },
    
    "AWS::WAFv2::WebACL": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Web ACL and rule pricing",
        "unit": "per ACL + per request + per rule"
    },
    
    # Fixed-cost resources with clear pricing
    "AWS::EC2::Instance": {
        "model": "fixed",
        "base_cost": None,  # Varies by instance type
        "details": "On-demand pricing varies by instance type and region",
        "unit": "per instance per hour"
    },
    
    "AWS::RDS::DBInstance": {
        "model": "fixed", 
        "base_cost": None,
        "details": "On-demand pricing varies by instance class, engine, and region",
        "unit": "per instance per hour"
    },
    
    "AWS::S3::Bucket": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Storage and request pricing by storage class",
        "unit": "per GB storage + per request"
    },
    
    "AWS::Lambda::Function": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Request and compute duration pricing",
        "unit": "per request + per GB-second"
    },
    
    "AWS::Logs::LogGroup": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Log ingestion and storage pricing",
        "unit": "per GB ingested + per GB stored"
    },
    
    "AWS::SecretsManager::Secret": {
        "model": "fixed",
        "base_cost": 0.0,
        "details": "Secret storage and API call pricing",
        "unit": "per secret per month + per API call"
    }
}

def get_pricing_info(resource_type: str, region: str = "us-east-1") -> Tuple[str, float, str, str]:
    """
    Get pricing information for a resource type.
    Now uses dynamic pricing fetcher for real-time pricing.
    
    Returns:
        Tuple of (pricing_model, base_cost, details, unit)
    """
    # First check if we have static model information
    static_info = PRICING_MODELS.get(resource_type, {
        "model": "unknown",
        "base_cost": 0.0,
        "details": "Pricing information not available",
        "unit": "unknown"
    })
    
    # For usage-based resources, try to get dynamic pricing
    if static_info["model"] == "usage_based":
        try:
            from .dynamic_pricing import get_dynamic_pricing_fetcher
            fetcher = get_dynamic_pricing_fetcher()
            dynamic_info = fetcher.get_usage_based_pricing(resource_type, region)
            
            if dynamic_info and dynamic_info.get("pricing_details"):
                return (
                    static_info["model"],
                    dynamic_info.get("base_cost", 0.0),
                    dynamic_info.get("pricing_details", static_info["details"]),
                    static_info["unit"]
                )
        except Exception as e:
            logger.warning(f"Failed to fetch dynamic pricing for {resource_type}: {str(e)}")
    
    # Fall back to static information
    return (
        static_info["model"],
        static_info["base_cost"] or 0.0,
        static_info["details"],
        static_info["unit"]
    )

def is_usage_based_resource(resource_type: str) -> bool:
    """Check if a resource has usage-based pricing."""
    model, _, _, _ = get_pricing_info(resource_type)
    return model == "usage_based"

def get_estimated_monthly_cost(resource_type: str, usage_assumptions: Optional[Dict] = None) -> float:
    """
    Get estimated monthly cost based on typical usage assumptions.
    
    Args:
        resource_type: AWS resource type
        usage_assumptions: Dictionary of usage parameters (e.g., requests_per_month)
    
    Returns:
        Estimated monthly cost in USD
    """
    model, base_cost, _, _ = get_pricing_info(resource_type)
    
    if model == "fixed":
        return base_cost
    
    if model == "usage_based" and usage_assumptions:
        # Apply usage-based calculations for common scenarios
        if resource_type == "AWS::SNS::Topic":
            requests = usage_assumptions.get("requests_per_month", 100000)  # 100K default
            return (requests / 1000000) * 0.50  # $0.50 per 1M requests
        
        elif resource_type == "AWS::SQS::Queue":
            requests = usage_assumptions.get("requests_per_month", 100000)
            free_tier = 1000000  # 1M free per month
            billable_requests = max(0, requests - free_tier)
            return (billable_requests / 1000000) * 0.40
        
        elif resource_type == "AWS::KMS::Key":
            requests = usage_assumptions.get("requests_per_month", 10000)
            return 1.0 + (requests / 10000) * 0.03  # $1/month + $0.03 per 10K requests
        
        elif resource_type == "AWS::ApiGateway::RestApi":
            requests = usage_assumptions.get("requests_per_month", 100000)
            return (requests / 1000000) * 3.50
        
        elif resource_type == "AWS::CloudWatch::Alarm":
            alarms = usage_assumptions.get("alarm_count", 1)
            return alarms * 0.10
        
        elif resource_type == "AWS::Route53::HostedZone":
            zones = usage_assumptions.get("zone_count", 1)
            queries = usage_assumptions.get("queries_per_month", 1000000)
            return zones * 0.50 + (queries / 1000000) * 0.40
    
    return base_cost 