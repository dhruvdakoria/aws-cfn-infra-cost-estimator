"""
GraphQL query builders for different AWS services.
Each service has its own query builder with specific attribute filters.
"""

from typing import Dict, Any


def get_region_code(region: str) -> str:
    """Convert AWS region to billing region code used in usage types."""
    region_mapping = {
        "us-east-1": "USE1",
        "us-east-2": "USE2", 
        "us-west-1": "USW1",
        "us-west-2": "USW2",
        "ca-central-1": "CAN1",
        "ca-west-1": "CAN2",
        "eu-west-1": "EU",
        "eu-west-2": "EUW2",
        "eu-west-3": "EUW3",
        "eu-central-1": "EUC1",
        "eu-central-2": "EUC2",
        "eu-north-1": "EUN1",
        "eu-south-1": "EUS1",
        "eu-south-2": "EUS2",
        "ap-northeast-1": "APN1",
        "ap-northeast-2": "APN2",
        "ap-northeast-3": "APN3",
        "ap-southeast-1": "APS1",
        "ap-southeast-2": "APS2",
        "ap-southeast-3": "APS4",
        "ap-southeast-4": "APS6",
        "ap-south-1": "APS3",
        "ap-south-2": "APS5",
        "ap-east-1": "APE1",
        "af-south-1": "AFS1",
        "me-south-1": "MES1",
        "me-central-1": "MEC1",
        "sa-east-1": "SAE1",
        "il-central-1": "ILC1",
        "us-gov-east-1": "UGE1",
        "us-gov-west-1": "UGW1"
    }
    return region_mapping.get(region, "USE1")  # Default to US East 1


class QueryBuilder:
    """Base class for building GraphQL queries for Infracost API."""
    
    @staticmethod
    def _build_base_query(service: str, product_family: str, region: str, 
                         attribute_filters: list, purchase_option: str = "on_demand") -> str:
        """Build a base GraphQL query with common structure."""
        filters_str = ""
        for i, filter_item in enumerate(attribute_filters):
            comma = "," if i < len(attribute_filters) - 1 else ""
            filters_str += f'{{ key: "{filter_item["key"]}", value: "{filter_item["value"]}" }}{comma}\n                '
        
        query = f'''
        {{
          products(
            filter: {{
              vendorName: "aws",
              service: "{service}",
              productFamily: "{product_family}",
              region: "{region}",
              attributeFilters: [
                {filters_str}
              ]
            }}
          ) {{
            prices(filter: {{purchaseOption: "{purchase_option}"}}) {{ USD }}
          }}
        }}
        '''
        return query


class EC2QueryBuilder(QueryBuilder):
    """Query builder for EC2 instances."""
    
    @staticmethod
    def build_instance_query(properties: Dict[str, Any]) -> str:
        instance_type = properties.get("InstanceType", "t2.micro")
        region = properties.get("Region", "us-east-1")
        operating_system = properties.get("OperatingSystem", "Linux")
        tenancy = properties.get("Tenancy", "Shared")
        
        attribute_filters = [
            {"key": "instanceType", "value": instance_type},
            {"key": "operatingSystem", "value": operating_system},
            {"key": "tenancy", "value": tenancy},
            {"key": "capacitystatus", "value": "Used"},
            {"key": "preInstalledSw", "value": "NA"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "Compute Instance", region, attribute_filters
        )
    
    @staticmethod
    def build_ebs_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        volume_type = properties.get("VolumeType", "gp3")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for EBS volumes
        if region_code == "USE1":
            usagetype = f"EBS:VolumeUsage.{volume_type}"
        else:
            usagetype = f"{region_code}-EBS:VolumeUsage.{volume_type}"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "Storage", region, attribute_filters
        )
    
    @staticmethod
    def build_eip_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for Elastic IP
        if region_code == "USE1":
            usagetype = "ElasticIP:IdleAddress"
        else:
            usagetype = f"{region_code}-ElasticIP:IdleAddress"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "IP Address", region, attribute_filters
        )
    
    @staticmethod
    def build_snapshot_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "productFamily", "value": "Storage Snapshot"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "Storage Snapshot", region, attribute_filters
        )


class RDSQueryBuilder(QueryBuilder):
    """Query builder for RDS instances."""
    
    @staticmethod
    def build_instance_query(properties: Dict[str, Any]) -> str:
        instance_class = properties.get("DBInstanceClass", "db.t3.micro")
        region = properties.get("Region", "us-east-1")
        engine = properties.get("Engine", "mysql")
        
        # Use correct attribute filters based on exploration
        attribute_filters = [
            {"key": "instanceType", "value": instance_class},
            {"key": "databaseEngine", "value": "MySQL"}  # Use exact case from API
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonRDS", "Database Instance", region, attribute_filters
        )
    
    @staticmethod
    def build_cluster_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        engine = properties.get("Engine", "aurora-mysql")
        
        attribute_filters = [
            {"key": "databaseEngine", "value": engine}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonRDS", "Database Cluster", region, attribute_filters
        )


class S3QueryBuilder(QueryBuilder):
    """Query builder for S3 storage."""
    
    @staticmethod
    def build_bucket_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        storage_class = properties.get("StorageClass", "Standard")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for S3 storage
        if region_code == "USE1":
            usagetype = "TimedStorage-ByteHrs"
        else:
            usagetype = f"{region_code}-TimedStorage-ByteHrs"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype},
            {"key": "storageClass", "value": "General Purpose"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonS3", "Storage", region, attribute_filters
        )


class LambdaQueryBuilder(QueryBuilder):
    """Query builder for Lambda functions."""
    
    @staticmethod
    def build_function_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for Lambda
        if region_code == "USE1":
            usagetype = "Lambda-GB-Second"
        else:
            usagetype = f"{region_code}-Lambda-GB-Second"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSLambda", "Serverless", region, attribute_filters
        )


class ELBQueryBuilder(QueryBuilder):
    """Query builder for Elastic Load Balancers."""
    
    @staticmethod
    def build_alb_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        load_balancer_type = properties.get("Type", "application")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for Load Balancer
        if region_code == "USE1":
            usagetype = "LoadBalancerUsage"
        else:
            usagetype = f"{region_code}-LoadBalancerUsage"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype},
            {"key": "operation", "value": "LoadBalancing"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSELB", "Load Balancer", region, attribute_filters
        )
    
    @staticmethod
    def build_classic_elb_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "loadBalancerType", "value": "classic"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSELB", "Load Balancer", region, attribute_filters
        )


class CloudWatchQueryBuilder(QueryBuilder):
    """Query builder for CloudWatch services."""
    
    @staticmethod
    def build_logs_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for CloudWatch Logs
        if region_code == "USE1":
            usagetype = "DataProcessing-Bytes"
        else:
            usagetype = f"{region_code}-DataProcessing-Bytes"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonCloudWatch", "Data Payload", region, attribute_filters
        )
    
    @staticmethod
    def build_dashboard_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AmazonCloudWatch", "Dashboard", region, attribute_filters, purchase_option=""
        )
    
    @staticmethod
    def build_alarm_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AmazonCloudWatch", "Alarm", region, attribute_filters, purchase_option=""
        )


class DynamoDBQueryBuilder(QueryBuilder):
    """Query builder for DynamoDB tables."""
    
    @staticmethod
    def build_table_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        billing_mode = properties.get("BillingMode", "PAY_PER_REQUEST")
        
        # Use correct attribute filters for DynamoDB storage
        # DynamoDB storage is typically not region-specific for usage type
        attribute_filters = [
            {"key": "usagetype", "value": "TimedStorage-ByteHrs"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonDynamoDB", "Database Storage", region, attribute_filters
        )


class APIGatewayQueryBuilder(QueryBuilder):
    """Query builder for API Gateway."""
    
    @staticmethod
    def build_rest_api_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for API Gateway REST requests
        usagetype = f"{region_code}-ApiGatewayRequest"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonApiGateway", "API Calls", region, attribute_filters
        )
    
    @staticmethod
    def build_v2_api_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        protocol_type = properties.get("ProtocolType", "HTTP")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for API Gateway HTTP requests
        if protocol_type.upper() == "HTTP":
            usagetype = f"{region_code}-ApiGatewayHttpRequest"
        else:
            usagetype = f"{region_code}-ApiGatewayRequest"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonApiGateway", "API Calls", region, attribute_filters
        )


class KMSQueryBuilder(QueryBuilder):
    """Query builder for KMS keys."""
    
    @staticmethod
    def build_key_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # KMS keys have a fixed monthly cost per key
        if region_code == "USE1":
            usagetype = "KMS-Keys"
        else:
            usagetype = f"{region_code}-KMS-Keys"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "awskms", "Key Management", region, attribute_filters
        )


class EKSQueryBuilder(QueryBuilder):
    """Query builder for EKS clusters."""
    
    @staticmethod
    def build_cluster_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # EKS clusters have a fixed hourly cost
        if region_code == "USE1":
            usagetype = "EKS-Cluster-Hours"
        else:
            usagetype = f"{region_code}-EKS-Cluster-Hours"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEKS", "Kubernetes Cluster", region, attribute_filters
        )
    
    @staticmethod
    def build_nodegroup_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        instance_types = properties.get("InstanceTypes", ["t3.medium"])
        
        attribute_filters = [
            {"key": "instanceType", "value": instance_types[0] if instance_types else "t3.medium"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEKS", "Node Group", region, attribute_filters
        )


class ElastiCacheQueryBuilder(QueryBuilder):
    """Query builder for ElastiCache clusters."""
    
    @staticmethod
    def build_cluster_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        cache_node_type = properties.get("CacheNodeType", "cache.t3.micro")
        engine = properties.get("Engine", "redis")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for ElastiCache
        if region_code == "USE1":
            usagetype = f"NodeUsage:{cache_node_type}"
        else:
            usagetype = f"{region_code}-NodeUsage:{cache_node_type}"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype},
            {"key": "instanceType", "value": cache_node_type},
            {"key": "cacheEngine", "value": engine.title()}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonElastiCache", "Cache Instance", region, attribute_filters
        )


class RedshiftQueryBuilder(QueryBuilder):
    """Query builder for Redshift clusters."""
    
    @staticmethod
    def build_cluster_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        node_type = properties.get("NodeType", "dc2.large")
        
        attribute_filters = [
            {"key": "instanceType", "value": node_type}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonRedshift", "Compute Instance", region, attribute_filters
        )


class Route53QueryBuilder(QueryBuilder):
    """Query builder for Route 53 services."""
    
    @staticmethod
    def build_hosted_zone_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Route 53 hosted zones have a fixed monthly cost
        # Route 53 hosted zones are not region-specific
        attribute_filters = [
            {"key": "usagetype", "value": "HostedZone"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonRoute53", "Hosted Zone", region, attribute_filters
        )
    
    @staticmethod
    def build_health_check_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AmazonRoute53", "Health Check", region, attribute_filters, purchase_option=""
        )


class SNSQueryBuilder(QueryBuilder):
    """Query builder for SNS topics."""
    
    @staticmethod
    def build_topic_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for SNS requests
        if region_code == "USE1":
            usagetype = "Requests-Tier1"
        else:
            usagetype = f"{region_code}-Requests-Tier1"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonSNS", "API Request", region, attribute_filters
        )


class SQSQueryBuilder(QueryBuilder):
    """Query builder for SQS queues."""
    
    @staticmethod
    def build_queue_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        queue_type = properties.get("FifoQueue", False)
        region_code = get_region_code(region)
        
        # Use region-specific usage type for SQS requests (using SNS pattern)
        if region_code == "USE1":
            usagetype = "Requests-Tier1"
        else:
            usagetype = f"{region_code}-Requests-Tier1"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonSNS", "API Request", region, attribute_filters
        )


class SecretsManagerQueryBuilder(QueryBuilder):
    """Query builder for Secrets Manager."""
    
    @staticmethod
    def build_secret_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for Secrets Manager
        usagetype = f"{region_code}-AWSSecretsManager-Secrets"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSSecretsManager", "Secret", region, attribute_filters
        )


class StepFunctionsQueryBuilder(QueryBuilder):
    """Query builder for Step Functions."""
    
    @staticmethod
    def build_state_machine_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        state_machine_type = properties.get("StateMachineType", "STANDARD")
        
        attribute_filters = [
            {"key": "workflowType", "value": state_machine_type.lower()}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSStepFunctions", "State Machine", region, attribute_filters, purchase_option=""
        )


class VPCQueryBuilder(QueryBuilder):
    """Query builder for VPC services."""
    
    @staticmethod
    def build_nat_gateway_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for NAT Gateway
        if region_code == "USE1":
            usagetype = "NatGateway-Hours"
        else:
            usagetype = f"{region_code}-NatGateway-Hours"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "NAT Gateway", region, attribute_filters
        )
    
    @staticmethod
    def build_vpn_connection_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AmazonVPC", "VPN Connection", region, attribute_filters
        )
    
    @staticmethod
    def build_vpc_endpoint_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        vpc_endpoint_type = properties.get("VpcEndpointType", "Interface")
        
        attribute_filters = [
            {"key": "endpointType", "value": vpc_endpoint_type}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonVPC", "VPC Endpoint", region, attribute_filters
        )


class WAFQueryBuilder(QueryBuilder):
    """Query builder for WAF services."""
    
    @staticmethod
    def build_web_acl_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AWSWAF", "Web ACL", region, attribute_filters, purchase_option=""
        )


# Additional Query Builders for Missing Resources

class AutoScalingQueryBuilder(QueryBuilder):
    """Query builder for Auto Scaling Groups."""
    
    @staticmethod
    def build_asg_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        instance_type = properties.get("InstanceType", "t3.micro")
        
        attribute_filters = [
            {"key": "instanceType", "value": instance_type},
            {"key": "operatingSystem", "value": "Linux"},
            {"key": "tenancy", "value": "Shared"},
            {"key": "capacitystatus", "value": "Used"},
            {"key": "preInstalledSw", "value": "NA"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "Compute Instance", region, attribute_filters
        )


class ECRQueryBuilder(QueryBuilder):
    """Query builder for ECR repositories."""
    
    @staticmethod
    def build_repository_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "RepositoryStorage"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonECR", "Container Registry", region, attribute_filters
        )


class EFSQueryBuilder(QueryBuilder):
    """Query builder for EFS file systems."""
    
    @staticmethod
    def build_filesystem_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "storageClass", "value": "Standard"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEFS", "Storage", region, attribute_filters
        )


class CodeBuildQueryBuilder(QueryBuilder):
    """Query builder for CodeBuild projects."""
    
    @staticmethod
    def build_project_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        compute_type = properties.get("ComputeType", "BUILD_GENERAL1_SMALL")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for CodeBuild
        if region_code == "USE1":
            usagetype = "Build-Min"
        else:
            usagetype = f"{region_code}-Build-Min"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSCodeBuild", "Build", region, attribute_filters
        )


class KinesisQueryBuilder(QueryBuilder):
    """Query builder for Kinesis streams."""
    
    @staticmethod
    def build_stream_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for Kinesis
        if region_code == "USE1":
            usagetype = "ShardHour"
        else:
            usagetype = f"{region_code}-ShardHour"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonKinesis", "Kinesis Streams", region, attribute_filters
        )


class CloudTrailQueryBuilder(QueryBuilder):
    """Query builder for CloudTrail."""
    
    @staticmethod
    def build_trail_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for CloudTrail
        if region_code == "USE1":
            usagetype = "DataEvents"
        else:
            usagetype = f"{region_code}-DataEvents"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSCloudTrail", "CloudTrail", region, attribute_filters
        )


class BackupQueryBuilder(QueryBuilder):
    """Query builder for AWS Backup."""
    
    @staticmethod
    def build_vault_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "BackupStorage"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSBackup", "Backup Storage", region, attribute_filters
        )


class TransferQueryBuilder(QueryBuilder):
    """Query builder for AWS Transfer Family."""
    
    @staticmethod
    def build_server_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "ProtocolEndpoint"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSTransfer", "Transfer Server", region, attribute_filters
        )


class SSMQueryBuilder(QueryBuilder):
    """Query builder for Systems Manager."""
    
    @staticmethod
    def build_parameter_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        parameter_type = properties.get("Type", "String")
        
        if parameter_type == "SecureString":
            attribute_filters = [
                {"key": "usagetype", "value": "AdvancedParameter"}
            ]
        else:
            attribute_filters = [
                {"key": "usagetype", "value": "Parameter"}
            ]
        
        return QueryBuilder._build_base_query(
            "AmazonSSM", "Parameter Store", region, attribute_filters
        )
    
    @staticmethod
    def build_activation_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "Activation"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonSSM", "Activation", region, attribute_filters
        )


class CloudFrontQueryBuilder(QueryBuilder):
    """Query builder for CloudFront."""
    
    @staticmethod
    def build_distribution_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "Requests-HTTP-Proxy"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonCloudFront", "Content Delivery", region, attribute_filters
        )
    
    @staticmethod
    def build_function_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "Request"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonCloudFront", "CloudFront Functions", region, attribute_filters
        )


class DocumentDBQueryBuilder(QueryBuilder):
    """Query builder for DocumentDB."""
    
    @staticmethod
    def build_cluster_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "databaseEngine", "value": "DocumentDB"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonDocDB", "Database Cluster", region, attribute_filters
        )
    
    @staticmethod
    def build_instance_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        instance_class = properties.get("DBInstanceClass", "db.t3.medium")
        
        attribute_filters = [
            {"key": "instanceType", "value": instance_class},
            {"key": "databaseEngine", "value": "DocumentDB"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonDocDB", "Database Instance", region, attribute_filters
        )


class NeptuneQueryBuilder(QueryBuilder):
    """Query builder for Neptune."""
    
    @staticmethod
    def build_cluster_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "databaseEngine", "value": "Neptune"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonNeptune", "Database Cluster", region, attribute_filters
        )
    
    @staticmethod
    def build_instance_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        instance_class = properties.get("DBInstanceClass", "db.t3.medium")
        
        attribute_filters = [
            {"key": "instanceType", "value": instance_class},
            {"key": "databaseEngine", "value": "Neptune"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonNeptune", "Database Instance", region, attribute_filters
        )


class ElasticsearchQueryBuilder(QueryBuilder):
    """Query builder for Elasticsearch."""
    
    @staticmethod
    def build_domain_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        instance_type = properties.get("InstanceType", "t3.small.elasticsearch")
        
        attribute_filters = [
            {"key": "instanceType", "value": instance_type}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonES", "Search Instance", region, attribute_filters
        )


class LightsailQueryBuilder(QueryBuilder):
    """Query builder for Lightsail."""
    
    @staticmethod
    def build_instance_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        bundle_id = properties.get("BundleId", "nano_2_0")
        
        attribute_filters = [
            {"key": "bundleId", "value": bundle_id}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonLightsail", "Instance", region, attribute_filters
        )


class MQQueryBuilder(QueryBuilder):
    """Query builder for Amazon MQ."""
    
    @staticmethod
    def build_broker_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        instance_type = properties.get("HostInstanceType", "mq.t3.micro")
        engine_type = properties.get("EngineType", "ActiveMQ")
        
        attribute_filters = [
            {"key": "instanceType", "value": instance_type},
            {"key": "brokerEngine", "value": engine_type}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonMQ", "Message Broker", region, attribute_filters
        )


class MSKQueryBuilder(QueryBuilder):
    """Query builder for MSK (Managed Streaming for Apache Kafka)."""
    
    @staticmethod
    def build_cluster_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        instance_type = properties.get("InstanceType", "kafka.t3.small")
        
        attribute_filters = [
            {"key": "instanceType", "value": instance_type}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonMSK", "Kafka Cluster", region, attribute_filters
        )


class ConfigQueryBuilder(QueryBuilder):
    """Query builder for AWS Config."""
    
    @staticmethod
    def build_rule_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "ConfigurationItemRecorded"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSConfig", "Config Rule", region, attribute_filters
        )
    
    @staticmethod
    def build_recorder_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "ConfigurationItemRecorded"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSConfig", "Configuration Recorder", region, attribute_filters
        )


class DMSQueryBuilder(QueryBuilder):
    """Query builder for Database Migration Service."""
    
    @staticmethod
    def build_replication_instance_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        instance_class = properties.get("ReplicationInstanceClass", "dms.t3.micro")
        
        attribute_filters = [
            {"key": "instanceType", "value": instance_class}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSDatabaseMigrationService", "Database Migration", region, attribute_filters
        )


class ACMPCAQueryBuilder(QueryBuilder):
    """Query builder for ACM Private Certificate Authority."""
    
    @staticmethod
    def build_certificate_authority_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "PrivateCA"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSACMPCA", "Certificate Authority", region, attribute_filters
        )


class APIGatewayStageQueryBuilder(QueryBuilder):
    """Query builder for API Gateway Stage."""
    
    @staticmethod
    def build_stage_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for API Gateway requests
        usagetype = f"{region_code}-ApiGatewayRequest"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonApiGateway", "API Calls", region, attribute_filters
        )


class ApplicationAutoScalingQueryBuilder(QueryBuilder):
    """Query builder for Application Auto Scaling."""
    
    @staticmethod
    def build_scalable_target_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Application Auto Scaling itself is free, but the underlying resources have costs
        # Return a minimal query that will result in $0 cost
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AWSApplicationAutoScaling", "Scaling", region, attribute_filters, purchase_option=""
        )


class CertificateManagerQueryBuilder(QueryBuilder):
    """Query builder for Certificate Manager."""
    
    @staticmethod
    def build_certificate_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Public certificates are free, private certificates have costs
        certificate_type = properties.get("CertificateAuthorityArn", "")
        
        if certificate_type:  # Private certificate
            attribute_filters = [
                {"key": "usagetype", "value": "PrivateCertificate"}
            ]
        else:  # Public certificate (free)
            attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AWSCertificateManager", "Certificate", region, attribute_filters, purchase_option=""
        )


class CloudFormationQueryBuilder(QueryBuilder):
    """Query builder for CloudFormation."""
    
    @staticmethod
    def build_stack_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # CloudFormation stacks are free, but may have handler costs
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AWSCloudFormation", "Stack", region, attribute_filters, purchase_option=""
        )
    
    @staticmethod
    def build_stackset_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # CloudFormation StackSets are free
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AWSCloudFormation", "StackSet", region, attribute_filters, purchase_option=""
        )


class DirectConnectQueryBuilder(QueryBuilder):
    """Query builder for Direct Connect."""
    
    @staticmethod
    def build_connection_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        bandwidth = properties.get("Bandwidth", "1Gbps")
        
        attribute_filters = [
            {"key": "portSpeed", "value": bandwidth}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSDirectConnect", "Dedicated Connection", region, attribute_filters
        )
    
    @staticmethod
    def build_virtual_interface_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AWSDirectConnect", "Virtual Interface", region, attribute_filters
        )


class DirectoryServiceQueryBuilder(QueryBuilder):
    """Query builder for Directory Service."""
    
    @staticmethod
    def build_microsoft_ad_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        edition = properties.get("Edition", "Standard")
        
        attribute_filters = [
            {"key": "directoryType", "value": "Microsoft AD"},
            {"key": "directorySize", "value": edition}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSDirectoryService", "Directory Service", region, attribute_filters
        )
    
    @staticmethod
    def build_simple_ad_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        size = properties.get("Size", "Small")
        
        attribute_filters = [
            {"key": "directoryType", "value": "Simple AD"},
            {"key": "directorySize", "value": size}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSDirectoryService", "Directory Service", region, attribute_filters
        )


class EC2AdvancedQueryBuilder(QueryBuilder):
    """Query builder for advanced EC2 services."""
    
    @staticmethod
    def build_client_vpn_endpoint_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "ClientVPN-EndpointHours"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "VPN", region, attribute_filters
        )
    
    @staticmethod
    def build_dedicated_host_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        instance_type = properties.get("InstanceType", "m5.large")
        
        attribute_filters = [
            {"key": "instanceType", "value": instance_type},
            {"key": "tenancy", "value": "Host"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "Dedicated Host", region, attribute_filters
        )
    
    @staticmethod
    def build_spot_fleet_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Spot fleet pricing is based on underlying instances
        attribute_filters = [
            {"key": "instanceType", "value": "m5.large"},
            {"key": "operatingSystem", "value": "Linux"},
            {"key": "tenancy", "value": "Shared"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "Compute Instance", region, attribute_filters, purchase_option="spot"
        )
    
    @staticmethod
    def build_transit_gateway_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "TransitGateway-Hours"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "Transit Gateway", region, attribute_filters
        )
    
    @staticmethod
    def build_transit_gateway_attachment_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "TransitGateway-VPC-Attachment-Hours"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "Transit Gateway", region, attribute_filters
        )


class ECSQueryBuilder(QueryBuilder):
    """Query builder for ECS services."""
    
    @staticmethod
    def build_service_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        launch_type = properties.get("LaunchType", "EC2")
        
        if launch_type == "FARGATE":
            attribute_filters = [
                {"key": "usagetype", "value": "Fargate-vCPU-Hours"}
            ]
            return QueryBuilder._build_base_query(
                "AmazonECS", "Compute", region, attribute_filters
            )
        else:
            # EC2 launch type - costs are from underlying EC2 instances
            attribute_filters = []
            return QueryBuilder._build_base_query(
                "AmazonECS", "Container Service", region, attribute_filters, purchase_option=""
            )


class EKSFargateQueryBuilder(QueryBuilder):
    """Query builder for EKS Fargate."""
    
    @staticmethod
    def build_fargate_profile_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "Fargate-vCPU-Hours"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEKS", "Compute", region, attribute_filters
        )


class ElasticBeanstalkQueryBuilder(QueryBuilder):
    """Query builder for Elastic Beanstalk."""
    
    @staticmethod
    def build_environment_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Elastic Beanstalk itself is free, costs come from underlying resources
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AWSElasticBeanstalk", "Environment", region, attribute_filters, purchase_option=""
        )


class EventBridgeQueryBuilder(QueryBuilder):
    """Query builder for EventBridge."""
    
    @staticmethod
    def build_event_bus_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "Events"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEventBridge", "Event", region, attribute_filters
        )


class FSxQueryBuilder(QueryBuilder):
    """Query builder for FSx file systems."""
    
    @staticmethod
    def build_filesystem_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        filesystem_type = properties.get("FileSystemType", "WINDOWS")
        
        if filesystem_type == "WINDOWS":
            service = "AmazonFSx"
            product_family = "File System"
        elif filesystem_type == "LUSTRE":
            service = "AmazonFSx"
            product_family = "Lustre File System"
        else:
            service = "AmazonFSx"
            product_family = "File System"
        
        attribute_filters = [
            {"key": "fileSystemType", "value": filesystem_type}
        ]
        
        return QueryBuilder._build_base_query(
            service, product_family, region, attribute_filters
        )


class GlobalAcceleratorQueryBuilder(QueryBuilder):
    """Query builder for Global Accelerator."""
    
    @staticmethod
    def build_accelerator_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AWSGlobalAccelerator", "Accelerator", region, attribute_filters
        )
    
    @staticmethod
    def build_endpoint_group_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AWSGlobalAccelerator", "Endpoint Group", region, attribute_filters
        )


class GlueQueryBuilder(QueryBuilder):
    """Query builder for AWS Glue."""
    
    @staticmethod
    def build_crawler_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "Crawler-DPU-Hour"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSGlue", "Crawler", region, attribute_filters
        )
    
    @staticmethod
    def build_database_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Glue Data Catalog databases are free up to certain limits
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AWSGlue", "Data Catalog", region, attribute_filters, purchase_option=""
        )
    
    @staticmethod
    def build_job_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "Job-DPU-Hour"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSGlue", "Job", region, attribute_filters
        )


class KinesisAdvancedQueryBuilder(QueryBuilder):
    """Query builder for advanced Kinesis services."""
    
    @staticmethod
    def build_analytics_application_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "KPU-Hour"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonKinesisAnalytics", "Analytics", region, attribute_filters
        )
    
    @staticmethod
    def build_firehose_delivery_stream_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "DeliveryStream-Records"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonKinesisFirehose", "Data Delivery", region, attribute_filters
        )


class MWAAQueryBuilder(QueryBuilder):
    """Query builder for Managed Workflows for Apache Airflow."""
    
    @staticmethod
    def build_environment_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        environment_class = properties.get("EnvironmentClass", "mw1.small")
        
        attribute_filters = [
            {"key": "instanceType", "value": environment_class}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonMWAA", "Environment", region, attribute_filters
        )


class NetworkFirewallQueryBuilder(QueryBuilder):
    """Query builder for Network Firewall."""
    
    @staticmethod
    def build_firewall_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "Firewall-Hours"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSNetworkFirewall", "Firewall", region, attribute_filters
        )


class Route53AdvancedQueryBuilder(QueryBuilder):
    """Query builder for advanced Route 53 services."""
    
    @staticmethod
    def build_record_set_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # DNS queries are charged per query, not per record
        attribute_filters = [
            {"key": "usagetype", "value": "DNS-Queries"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonRoute53", "DNS Query", region, attribute_filters
        )


class Route53ResolverQueryBuilder(QueryBuilder):
    """Query builder for Route 53 Resolver."""
    
    @staticmethod
    def build_resolver_endpoint_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "usagetype", "value": "ResolverEndpoint"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonRoute53", "Resolver Endpoint", region, attribute_filters
        )


class SNSAdvancedQueryBuilder(QueryBuilder):
    """Query builder for SNS subscriptions."""
    
    @staticmethod
    def build_subscription_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        protocol = properties.get("Protocol", "email")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for SNS requests
        if region_code == "USE1":
            usagetype = "Requests-Tier1"
        else:
            usagetype = f"{region_code}-Requests-Tier1"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonSNS", "API Request", region, attribute_filters
        )


# Query builder registry for easy lookup
QUERY_BUILDERS = {
    # EC2
    "AWS::EC2::Instance": EC2QueryBuilder.build_instance_query,
    "AWS::EC2::Volume": EC2QueryBuilder.build_ebs_query,
    "AWS::EC2::EIP": EC2QueryBuilder.build_eip_query,
    "AWS::EC2::Snapshot": EC2QueryBuilder.build_snapshot_query,
    
    # RDS
    "AWS::RDS::DBInstance": RDSQueryBuilder.build_instance_query,
    "AWS::RDS::DBCluster": RDSQueryBuilder.build_cluster_query,
    
    # S3
    "AWS::S3::Bucket": S3QueryBuilder.build_bucket_query,
    
    # Lambda
    "AWS::Lambda::Function": LambdaQueryBuilder.build_function_query,
    
    # ELB
    "AWS::ElasticLoadBalancingV2::LoadBalancer": ELBQueryBuilder.build_alb_query,
    "AWS::ElasticLoadBalancing::LoadBalancer": ELBQueryBuilder.build_classic_elb_query,
    
    # CloudWatch
    "AWS::Logs::LogGroup": CloudWatchQueryBuilder.build_logs_query,
    "AWS::CloudWatch::Dashboard": CloudWatchQueryBuilder.build_dashboard_query,
    "AWS::CloudWatch::Alarm": CloudWatchQueryBuilder.build_alarm_query,
    
    # DynamoDB
    "AWS::DynamoDB::Table": DynamoDBQueryBuilder.build_table_query,
    
    # API Gateway
    "AWS::ApiGateway::RestApi": APIGatewayQueryBuilder.build_rest_api_query,
    "AWS::ApiGatewayV2::Api": APIGatewayQueryBuilder.build_v2_api_query,
    
    # KMS
    "AWS::KMS::Key": KMSQueryBuilder.build_key_query,
    
    # EKS
    "AWS::EKS::Cluster": EKSQueryBuilder.build_cluster_query,
    "AWS::EKS::Nodegroup": EKSQueryBuilder.build_nodegroup_query,
    
    # ElastiCache
    "AWS::ElastiCache::CacheCluster": ElastiCacheQueryBuilder.build_cluster_query,
    "AWS::ElastiCache::ReplicationGroup": ElastiCacheQueryBuilder.build_cluster_query,
    
    # Redshift
    "AWS::Redshift::Cluster": RedshiftQueryBuilder.build_cluster_query,
    
    # Route 53
    "AWS::Route53::HostedZone": Route53QueryBuilder.build_hosted_zone_query,
    "AWS::Route53::HealthCheck": Route53QueryBuilder.build_health_check_query,
    
    # SNS
    "AWS::SNS::Topic": SNSQueryBuilder.build_topic_query,
    
    # SQS
    "AWS::SQS::Queue": SQSQueryBuilder.build_queue_query,
    
    # Secrets Manager
    "AWS::SecretsManager::Secret": SecretsManagerQueryBuilder.build_secret_query,
    
    # Step Functions
    "AWS::StepFunctions::StateMachine": StepFunctionsQueryBuilder.build_state_machine_query,
    
    # VPC
    "AWS::EC2::NatGateway": VPCQueryBuilder.build_nat_gateway_query,
    "AWS::EC2::VPNConnection": VPCQueryBuilder.build_vpn_connection_query,
    "AWS::EC2::VPCEndpoint": VPCQueryBuilder.build_vpc_endpoint_query,
    
    # WAF
    "AWS::WAF::WebACL": WAFQueryBuilder.build_web_acl_query,
    "AWS::WAFv2::WebACL": WAFQueryBuilder.build_web_acl_query,
    
    # Auto Scaling
    "AWS::AutoScaling::AutoScalingGroup": AutoScalingQueryBuilder.build_asg_query,
    
    # ECR
    "AWS::ECR::Repository": ECRQueryBuilder.build_repository_query,
    
    # EFS
    "AWS::EFS::FileSystem": EFSQueryBuilder.build_filesystem_query,
    
    # CodeBuild
    "AWS::CodeBuild::Project": CodeBuildQueryBuilder.build_project_query,
    
    # Kinesis
    "AWS::Kinesis::Stream": KinesisQueryBuilder.build_stream_query,
    
    # CloudTrail
    "AWS::CloudTrail::Trail": CloudTrailQueryBuilder.build_trail_query,
    
    # Backup
    "AWS::Backup::BackupVault": BackupQueryBuilder.build_vault_query,
    
    # Transfer
    "AWS::Transfer::Server": TransferQueryBuilder.build_server_query,
    
    # SSM
    "AWS::SSM::Parameter": SSMQueryBuilder.build_parameter_query,
    "AWS::SSM::Activation": SSMQueryBuilder.build_activation_query,
    
    # CloudFront
    "AWS::CloudFront::Distribution": CloudFrontQueryBuilder.build_distribution_query,
    "AWS::CloudFront::Function": CloudFrontQueryBuilder.build_function_query,
    
    # DocumentDB
    "AWS::DocDB::DBCluster": DocumentDBQueryBuilder.build_cluster_query,
    "AWS::DocDB::DBInstance": DocumentDBQueryBuilder.build_instance_query,
    
    # Neptune
    "AWS::Neptune::DBCluster": NeptuneQueryBuilder.build_cluster_query,
    "AWS::Neptune::DBInstance": NeptuneQueryBuilder.build_instance_query,
    
    # Elasticsearch
    "AWS::Elasticsearch::Domain": ElasticsearchQueryBuilder.build_domain_query,
    
    # Lightsail
    "AWS::Lightsail::Instance": LightsailQueryBuilder.build_instance_query,
    
    # MQ
    "AWS::MQ::Broker": MQQueryBuilder.build_broker_query,
    
    # MSK
    "AWS::MSK::Cluster": MSKQueryBuilder.build_cluster_query,
    
    # Config
    "AWS::Config::ConfigRule": ConfigQueryBuilder.build_rule_query,
    "AWS::Config::ConfigurationRecorder": ConfigQueryBuilder.build_recorder_query,
    
    # DMS
    "AWS::DMS::ReplicationInstance": DMSQueryBuilder.build_replication_instance_query,
    
    # Additional missing resources
    "AWS::ACMPCA::CertificateAuthority": ACMPCAQueryBuilder.build_certificate_authority_query,
    "AWS::ApiGateway::Stage": APIGatewayStageQueryBuilder.build_stage_query,
    "AWS::ApplicationAutoScaling::ScalableTarget": ApplicationAutoScalingQueryBuilder.build_scalable_target_query,
    "AWS::CertificateManager::Certificate": CertificateManagerQueryBuilder.build_certificate_query,
    "AWS::CloudFormation::Stack": CloudFormationQueryBuilder.build_stack_query,
    "AWS::CloudFormation::StackSet": CloudFormationQueryBuilder.build_stackset_query,
    "AWS::DirectConnect::Connection": DirectConnectQueryBuilder.build_connection_query,
    "AWS::DirectConnect::VirtualInterface": DirectConnectQueryBuilder.build_virtual_interface_query,
    "AWS::DirectoryService::MicrosoftAD": DirectoryServiceQueryBuilder.build_microsoft_ad_query,
    "AWS::DirectoryService::SimpleAD": DirectoryServiceQueryBuilder.build_simple_ad_query,
    "AWS::EC2::ClientVpnEndpoint": EC2AdvancedQueryBuilder.build_client_vpn_endpoint_query,
    "AWS::EC2::DedicatedHost": EC2AdvancedQueryBuilder.build_dedicated_host_query,
    "AWS::EC2::SpotFleet": EC2AdvancedQueryBuilder.build_spot_fleet_query,
    "AWS::EC2::TransitGateway": EC2AdvancedQueryBuilder.build_transit_gateway_query,
    "AWS::EC2::TransitGatewayVpcAttachment": EC2AdvancedQueryBuilder.build_transit_gateway_attachment_query,
    "AWS::ECS::Service": ECSQueryBuilder.build_service_query,
    "AWS::EKS::FargateProfile": EKSFargateQueryBuilder.build_fargate_profile_query,
    "AWS::ElasticBeanstalk::Environment": ElasticBeanstalkQueryBuilder.build_environment_query,
    "AWS::Events::EventBus": EventBridgeQueryBuilder.build_event_bus_query,
    "AWS::FSx::FileSystem": FSxQueryBuilder.build_filesystem_query,
    "AWS::GlobalAccelerator::Accelerator": GlobalAcceleratorQueryBuilder.build_accelerator_query,
    "AWS::GlobalAccelerator::EndpointGroup": GlobalAcceleratorQueryBuilder.build_endpoint_group_query,
    "AWS::Glue::Crawler": GlueQueryBuilder.build_crawler_query,
    "AWS::Glue::Database": GlueQueryBuilder.build_database_query,
    "AWS::Glue::Job": GlueQueryBuilder.build_job_query,
    "AWS::KinesisAnalytics::Application": KinesisAdvancedQueryBuilder.build_analytics_application_query,
    "AWS::KinesisFirehose::DeliveryStream": KinesisAdvancedQueryBuilder.build_firehose_delivery_stream_query,
    "AWS::MWAA::Environment": MWAAQueryBuilder.build_environment_query,
    "AWS::NetworkFirewall::Firewall": NetworkFirewallQueryBuilder.build_firewall_query,
    "AWS::Route53::RecordSet": Route53AdvancedQueryBuilder.build_record_set_query,
    "AWS::Route53Resolver::ResolverEndpoint": Route53ResolverQueryBuilder.build_resolver_endpoint_query,
    "AWS::SNS::Subscription": SNSAdvancedQueryBuilder.build_subscription_query,
}


def get_query_builder(resource_type: str):
    """Get the appropriate query builder function for a resource type."""
    return QUERY_BUILDERS.get(resource_type) 