"""
Pricing models and details for AWS resources.
This module provides detailed pricing information for resources that have usage-based pricing.
"""

from typing import Dict, Optional, Tuple

# Pricing model definitions
PRICING_MODELS = {
    # Usage-based resources with detailed pricing information
    "AWS::SNS::Topic": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Pay per request: $0.50 per 1M requests, $0.06 per 100K HTTP/S notifications, $0.75 per 100K SMS",
        "unit": "per request/notification"
    },
    
    "AWS::SQS::Queue": {
        "model": "usage_based", 
        "base_cost": 0.0,
        "details": "Pay per request: $0.40 per 1M requests (first 1M free per month)",
        "unit": "per request"
    },
    
    "AWS::KMS::Key": {
        "model": "usage_based",
        "base_cost": 1.0,  # $1/month per key
        "details": "Customer managed keys: $1/month per key + $0.03 per 10K requests",
        "unit": "per key + per request"
    },
    
    "AWS::ApiGateway::RestApi": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Pay per request: $3.50 per 1M requests + data transfer costs",
        "unit": "per request"
    },
    
    "AWS::ApiGatewayV2::Api": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "HTTP APIs: $1.00 per 1M requests, WebSocket APIs: $1.00 per 1M messages",
        "unit": "per request/message"
    },
    
    "AWS::CloudWatch::Alarm": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Standard alarms: $0.10 per alarm per month, High-resolution alarms: $0.30 per alarm per month",
        "unit": "per alarm per month"
    },
    
    "AWS::CloudWatch::Dashboard": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "First 3 dashboards free, then $3.00 per dashboard per month",
        "unit": "per dashboard per month"
    },
    
    "AWS::StepFunctions::StateMachine": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Standard workflows: $0.025 per 1K state transitions, Express workflows: $1.00 per 1M requests",
        "unit": "per state transition/request"
    },
    
    "AWS::Route53::HostedZone": {
        "model": "usage_based",
        "base_cost": 0.5,  # $0.50 per hosted zone per month
        "details": "Hosted zones: $0.50 per zone per month + $0.40 per 1M queries",
        "unit": "per zone + per query"
    },
    
    "AWS::Route53::HealthCheck": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Health checks: $0.50 per health check per month",
        "unit": "per health check per month"
    },
    
    "AWS::DynamoDB::Table": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "On-demand: $1.25 per 1M write requests, $0.25 per 1M read requests + storage costs",
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
        "details": "Storage: $0.10 per GB per month, Data transfer: varies by region",
        "unit": "per GB storage + data transfer"
    },
    
    "AWS::EFS::FileSystem": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Standard storage: $0.30 per GB per month, Infrequent Access: $0.025 per GB per month",
        "unit": "per GB per month"
    },
    
    "AWS::CodeBuild::Project": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Build minutes: $0.005 per minute (general1.small), varies by compute type",
        "unit": "per build minute"
    },
    
    "AWS::CloudTrail::Trail": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Management events: First trail free, additional trails $2.00 per 100K events",
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
        "details": "Backup storage: $0.05 per GB per month, varies by storage class",
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
        "details": "Standard parameters: Free, Advanced parameters: $0.05 per 10K requests",
        "unit": "per 10K requests (advanced only)"
    },
    
    "AWS::SSM::Activation": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Managed instances: $0.00695 per managed instance per hour",
        "unit": "per managed instance per hour"
    },
    
    "AWS::WAF::WebACL": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Web ACL: $1.00 per month + $0.60 per 1M requests + rule costs",
        "unit": "per ACL + per request + per rule"
    },
    
    "AWS::WAFv2::WebACL": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Web ACL: $1.00 per month + $0.60 per 1M requests + rule costs",
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
        "details": "Standard storage: $0.023 per GB per month + request costs",
        "unit": "per GB storage + per request"
    },
    
    "AWS::Lambda::Function": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Requests: $0.20 per 1M requests + $0.0000166667 per GB-second",
        "unit": "per request + per GB-second"
    },
    
    "AWS::Logs::LogGroup": {
        "model": "usage_based",
        "base_cost": 0.0,
        "details": "Ingestion: $0.50 per GB + Storage: $0.03 per GB per month",
        "unit": "per GB ingested + per GB stored"
    },
    
    "AWS::SecretsManager::Secret": {
        "model": "fixed",
        "base_cost": 0.4,  # $0.40 per secret per month
        "details": "Secrets: $0.40 per secret per month + $0.05 per 10K API calls",
        "unit": "per secret per month + per API call"
    }
}

def get_pricing_info(resource_type: str) -> Tuple[str, float, str, str]:
    """
    Get pricing information for a resource type.
    
    Returns:
        Tuple of (pricing_model, base_cost, details, unit)
    """
    info = PRICING_MODELS.get(resource_type, {
        "model": "unknown",
        "base_cost": 0.0,
        "details": "Pricing information not available",
        "unit": "unknown"
    })
    
    return (
        info["model"],
        info["base_cost"] or 0.0,
        info["details"],
        info["unit"]
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