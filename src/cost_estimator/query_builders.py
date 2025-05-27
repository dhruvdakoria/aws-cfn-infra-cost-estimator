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
        """Build a base GraphQL query with common structure including pricing tier information."""
        filters_str = ""
        for i, filter_item in enumerate(attribute_filters):
            comma = "," if i < len(attribute_filters) - 1 else ""
            if "valueRegex" in filter_item:
                filters_str += f'{{ key: "{filter_item["key"]}", value_regex: "{filter_item["valueRegex"]}" }}{comma}\n                '
            else:
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
            prices(filter: {{purchaseOption: "{purchase_option}"}}) {{ 
              USD 
              unit
              description
              startUsageAmount
              endUsageAmount
            }}
          }}
        }}
        '''
        return query
    
    @staticmethod
    def _build_global_query(service: str, product_family: str, 
                           attribute_filters: list, purchase_option: str = "on_demand") -> str:
        """Build a GraphQL query for global services (without region filter)."""
        filters_str = ""
        for i, filter_item in enumerate(attribute_filters):
            comma = "," if i < len(attribute_filters) - 1 else ""
            if "valueRegex" in filter_item:
                filters_str += f'{{ key: "{filter_item["key"]}", value_regex: "{filter_item["valueRegex"]}" }}{comma}\n                '
            else:
                filters_str += f'{{ key: "{filter_item["key"]}", value: "{filter_item["value"]}" }}{comma}\n                '
        
        query = f'''
        {{
          products(
            filter: {{
              vendorName: "aws",
              service: "{service}",
              productFamily: "{product_family}",
              attributeFilters: [
                {filters_str}
              ]
            }}
          ) {{
            prices(filter: {{purchaseOption: "{purchase_option}"}}) {{ 
              USD 
              unit
              description
              startUsageAmount
              endUsageAmount
            }}
          }}
        }}
        '''
        return query


class EC2QueryBuilder(QueryBuilder):
    """Query builder for EC2 instances."""
    
    @staticmethod
    def build_instance_query(properties: Dict[str, Any]) -> str:
        # Extract actual properties from CloudFormation template
        instance_type = properties.get("InstanceType", "t2.micro")
        region = properties.get("Region", "us-east-1")
        
        # Extract image ID to determine OS
        image_id = properties.get("ImageId", "")
        operating_system = "Linux"  # Default
        
        # Try to infer OS from common patterns
        if image_id:
            if "windows" in image_id.lower():
                operating_system = "Windows"
            elif "rhel" in image_id.lower():
                operating_system = "RHEL"
            elif "suse" in image_id.lower():
                operating_system = "SUSE"
        
        # Extract tenancy from placement
        placement = properties.get("Placement", {})
        tenancy = placement.get("Tenancy", "default")
        if tenancy == "default":
            tenancy = "Shared"
        elif tenancy == "dedicated":
            tenancy = "Dedicated"
        elif tenancy == "host":
            tenancy = "Host"
        
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
        # Extract actual EBS properties
        volume_type = properties.get("VolumeType", "gp3")
        
        # Use regex pattern like Go files to match any region-specific usage type
        attribute_filters = [
            {"key": "volumeApiName", "value": volume_type}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "Storage", region, attribute_filters
        )
    
    @staticmethod
    def build_eip_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Use regex pattern to match any region-specific usage type for EIP
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/ElasticIP:IdleAddress/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "IP Address", region, attribute_filters
        )
    
    @staticmethod
    def build_snapshot_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Use regex pattern like Go files to match EBS snapshot usage
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/EBS:SnapshotUsage$/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "Storage Snapshot", region, attribute_filters
        )


class RDSQueryBuilder(QueryBuilder):
    """Query builder for RDS instances."""
    
    @staticmethod
    def build_instance_query(properties: Dict[str, Any]) -> str:
        # Extract actual RDS properties
        instance_class = properties.get("DBInstanceClass", "db.t3.micro")
        region = properties.get("Region", "us-east-1")
        engine = properties.get("Engine", "mysql")
        engine_version = properties.get("EngineVersion", "")
        license_model = properties.get("LicenseModel", "")
        multi_az = properties.get("MultiAZ", False)
        storage_type = properties.get("StorageType", "gp2")
        allocated_storage = properties.get("AllocatedStorage", 20)
        
        # Map engine to correct case for API
        engine_mapping = {
            "mysql": "MySQL",
            "postgres": "PostgreSQL", 
            "postgresql": "PostgreSQL",
            "oracle-ee": "Oracle",
            "oracle-se2": "Oracle",
            "oracle-se1": "Oracle",
            "oracle-se": "Oracle",
            "sqlserver-ee": "SQL Server",
            "sqlserver-se": "SQL Server",
            "sqlserver-ex": "SQL Server",
            "sqlserver-web": "SQL Server",
            "mariadb": "MariaDB"
        }
        
        database_engine = engine_mapping.get(engine.lower(), "MySQL")
        
        attribute_filters = [
            {"key": "instanceType", "value": instance_class},
            {"key": "databaseEngine", "value": database_engine}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonRDS", "Database Instance", region, attribute_filters
        )
    
    @staticmethod
    def build_cluster_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Extract cluster properties
        engine = properties.get("Engine", "aurora-mysql")
        
        # Map engine to database engine value
        engine_mapping = {
            "aurora-mysql": "Aurora MySQL",
            "aurora-postgresql": "Aurora PostgreSQL",
            "aurora": "Aurora MySQL"  # Default
        }
        
        database_engine = engine_mapping.get(engine, "Aurora MySQL")
        
        # Use regex pattern for Aurora storage usage that works across regions
        attribute_filters = [
            {"key": "databaseEngine", "value": "Any"},
            {"key": "usagetype", "valueRegex": "/Aurora.*StorageUsage/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonRDS", "Database Storage", region, attribute_filters
        )


class S3QueryBuilder(QueryBuilder):
    """Query builder for S3 storage."""
    
    @staticmethod
    def build_bucket_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        # Extract actual S3 bucket properties
        bucket_name = properties.get("BucketName", "")
        access_control = properties.get("AccessControl", "")
        versioning_configuration = properties.get("VersioningConfiguration", {})
        lifecycle_configuration = properties.get("LifecycleConfiguration", {})
        notification_configuration = properties.get("NotificationConfiguration", {})
        logging_configuration = properties.get("LoggingConfiguration", {})
        
        # Use regex pattern to match any region-specific usage type for S3 storage
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/TimedStorage-ByteHrs/"},
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
        # Extract actual Lambda function properties
        function_name = properties.get("FunctionName", "")
        runtime = properties.get("Runtime", "python3.9")
        memory_size = properties.get("MemorySize", 128)
        timeout = properties.get("Timeout", 3)
        environment = properties.get("Environment", {})
        vpc_config = properties.get("VpcConfig", {})
        dead_letter_config = properties.get("DeadLetterConfig", {})
        
        # Use regex pattern to match any region-specific usage type for Lambda
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/GB-Second/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSLambda", "Serverless", region, attribute_filters
        )


class ELBQueryBuilder(QueryBuilder):
    """Query builder for Elastic Load Balancers."""
    
    @staticmethod
    def build_alb_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        # Extract actual ALB properties
        load_balancer_type = properties.get("Type", "application")
        name = properties.get("Name", "")
        scheme = properties.get("Scheme", "internet-facing")
        ip_address_type = properties.get("IpAddressType", "ipv4")
        subnets = properties.get("Subnets", [])
        security_groups = properties.get("SecurityGroups", [])
        load_balancer_attributes = properties.get("LoadBalancerAttributes", [])
        
        # Use regex pattern to match any region-specific usage type for Load Balancer
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/LoadBalancerUsage/"},
            {"key": "operation", "value": "LoadBalancing"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSELB", "Load Balancer", region, attribute_filters
        )
    
    @staticmethod
    def build_classic_elb_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Use regex pattern like Go files to match Classic ELB usage
        attribute_filters = [
            {"key": "locationType", "value": "AWS Region"},
            {"key": "usagetype", "valueRegex": "/LoadBalancerUsage/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSELB", "Load Balancer", region, attribute_filters
        )


class CloudWatchQueryBuilder(QueryBuilder):
    """Query builder for CloudWatch services."""
    
    @staticmethod
    def build_logs_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Use regex pattern to match any region-specific usage type for CloudWatch Logs
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/DataProcessing-Bytes/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonCloudWatch", "Data Payload", region, attribute_filters
        )
    
    @staticmethod
    def build_dashboard_query(properties: Dict[str, Any]) -> str:
        # CloudWatch Dashboard uses AmazonCloudWatch service and Dashboard product family
        # Use regex to match dashboard usage types and ensure we get monthly pricing
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/Dashboard/"},
            {"key": "operation", "value": "CreateDashboard"}
        ]
        
        return QueryBuilder._build_global_query(
            "AmazonCloudWatch", "Dashboard", attribute_filters, purchase_option="on_demand"
        )
    
    @staticmethod
    def build_alarm_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # CloudWatch Alarm uses AmazonCloudWatch service and Alarm product family per Go file
        attribute_filters = [
            {"key": "alarmType", "valueRegex": "/Standard/"},
            {"key": "usagetype", "valueRegex": "/AlarmMonitorUsage$/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonCloudWatch", "Alarm", region, attribute_filters, purchase_option="on_demand"
        )


class DynamoDBQueryBuilder(QueryBuilder):
    """Query builder for DynamoDB tables with comprehensive pricing support."""
    
    @staticmethod
    def build_table_query(properties: Dict[str, Any]) -> str:
        """Build primary query for DynamoDB table - focuses on read request units for on-demand billing."""
        region = properties.get("Region", "us-east-1")
        billing_mode = properties.get("BillingMode", "PAY_PER_REQUEST")
        table_class = properties.get("TableClass", "STANDARD")
        
        # Use the correct product family based on billing mode (from dynamodb_table.go)
        if billing_mode == "PAY_PER_REQUEST":
            # On-demand billing - use PayPerRequest Throughput product family with group filter
            attribute_filters = [
                {"key": "group", "value": "DDB-ReadUnits"}
            ]
            
            return QueryBuilder._build_base_query(
                "AmazonDynamoDB", "Amazon DynamoDB PayPerRequest Throughput", region, attribute_filters
            )
        else:
            # Provisioned billing - use Provisioned IOPS product family with group filter
            attribute_filters = [
                {"key": "group", "value": "DDB-ReadUnits"}
            ]
            
            return QueryBuilder._build_base_query(
                "AmazonDynamoDB", "Provisioned IOPS", region, attribute_filters
            )
    
    @staticmethod
    def build_write_query(properties: Dict[str, Any]) -> str:
        """Build query for DynamoDB write capacity pricing."""
        region = properties.get("Region", "us-east-1")
        billing_mode = properties.get("BillingMode", "PAY_PER_REQUEST")
        table_class = properties.get("TableClass", "STANDARD")
        
        region_code = get_region_code(region)
        
        # Build query based on billing mode and table class for WRITE operations
        if billing_mode == "PAY_PER_REQUEST":
            # On-demand billing - use write request units
            if table_class == "STANDARD_INFREQUENT_ACCESS":
                # Use region-specific usage type for IA write requests
                if region_code == "USE1":
                    usagetype = "IA-WriteRequestUnits"
                else:
                    usagetype = f"{region_code}-IA-WriteRequestUnits"
                    
                attribute_filters = [
                    {"key": "usagetype", "value": usagetype}
                ]
            else:
                # Use region-specific usage type for standard write requests
                if region_code == "USE1":
                    usagetype = "WriteRequestUnits"
                else:
                    usagetype = f"{region_code}-WriteRequestUnits"
                    
                attribute_filters = [
                    {"key": "usagetype", "value": usagetype}
                ]
        else:
            # Provisioned billing - use write capacity units
            if table_class == "STANDARD_INFREQUENT_ACCESS":
                # Use region-specific usage type for IA write capacity
                if region_code == "USE1":
                    usagetype = "IA-WriteCapacityUnit-Hrs"
                else:
                    usagetype = f"{region_code}-IA-WriteCapacityUnit-Hrs"
                    
                attribute_filters = [
                    {"key": "usagetype", "value": usagetype}
                ]
            else:
                # Use region-specific usage type for standard write capacity
                if region_code == "USE1":
                    usagetype = "WriteCapacityUnit-Hrs"
                else:
                    usagetype = f"{region_code}-WriteCapacityUnit-Hrs"
                    
                attribute_filters = [
                    {"key": "usagetype", "value": usagetype}
                ]
        
        # Use the correct product family based on billing mode
        if billing_mode == "PAY_PER_REQUEST":
            return QueryBuilder._build_base_query(
                "AmazonDynamoDB", "Amazon DynamoDB PayPerRequest Throughput", region, [{"key": "group", "value": "DDB-WriteUnits"}]
            )
        else:
            return QueryBuilder._build_base_query(
                "AmazonDynamoDB", "Provisioned IOPS", region, [{"key": "group", "value": "DDB-WriteUnits"}]
            )
    
    @staticmethod
    def build_storage_query(properties: Dict[str, Any]) -> str:
        """Build query for DynamoDB storage costs."""
        region = properties.get("Region", "us-east-1")
        table_class = properties.get("TableClass", "STANDARD")
        
        region_code = get_region_code(region)
        
        # Use region-specific usage type for storage
        if table_class == "STANDARD_INFREQUENT_ACCESS":
            if region_code == "USE1":
                usagetype = "IA-TimedStorage-ByteHrs"
            else:
                usagetype = f"{region_code}-IA-TimedStorage-ByteHrs"
        else:
            if region_code == "USE1":
                usagetype = "TimedStorage-ByteHrs"
            else:
                usagetype = f"{region_code}-TimedStorage-ByteHrs"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonDynamoDB", "Database Storage", region, attribute_filters
        )
    
    @staticmethod
    def build_backup_query(properties: Dict[str, Any]) -> str:
        """Build query for DynamoDB backup costs."""
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for backup storage
        if region_code == "USE1":
            usagetype = "USE1-TimedBackupStorage-ByteHrs"
        else:
            usagetype = f"{region_code}-TimedBackupStorage-ByteHrs"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonDynamoDB", "Database Storage", region, attribute_filters
        )
    
    @staticmethod
    def build_pitr_query(properties: Dict[str, Any]) -> str:
        """Build query for DynamoDB Point-in-Time Recovery costs."""
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for PITR storage
        if region_code == "USE1":
            usagetype = "USE1-TimedPITRStorage-ByteHrs"
        else:
            usagetype = f"{region_code}-TimedPITRStorage-ByteHrs"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonDynamoDB", "Database Storage", region, attribute_filters
        )
    
    @staticmethod
    def build_streams_query(properties: Dict[str, Any]) -> str:
        """Build query for DynamoDB Streams costs."""
        region = properties.get("Region", "us-east-1")
        region_code = get_region_code(region)
        
        # Use region-specific usage type for streams
        if region_code == "USE1":
            usagetype = "USE1-Streams-Requests"
        else:
            usagetype = f"{region_code}-Streams-Requests"
        
        attribute_filters = [
            {"key": "group", "value": "DDB-StreamsReadRequests"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonDynamoDB", "API Request", region, attribute_filters
        )
    
    @staticmethod
    def build_global_table_query(properties: Dict[str, Any]) -> str:
        """Build query for DynamoDB Global Tables replication costs."""
        region = properties.get("Region", "us-east-1")
        billing_mode = properties.get("BillingMode", "PAY_PER_REQUEST")
        table_class = properties.get("TableClass", "STANDARD")
        
        # Build query for replicated write costs
        if billing_mode == "PAY_PER_REQUEST":
            if table_class == "STANDARD_INFREQUENT_ACCESS":
                attribute_filters = [
                    {"key": "group", "value": "DDB-ReplicatedWriteUnitsIA"},
                    {"key": "operation", "value": "PayPerRequestThroughput"},
                    {"key": "usagetype", "value": "IA-ReplWriteRequestUnits"}
                ]
            else:
                attribute_filters = [
                    {"key": "group", "value": "DDB-ReplicatedWriteUnits"},
                    {"key": "operation", "value": "PayPerRequestThroughput"},
                    {"key": "usagetype", "value": "ReplWriteRequestUnits"}
                ]
        else:
            if table_class == "STANDARD_INFREQUENT_ACCESS":
                attribute_filters = [
                    {"key": "group", "value": "DDB-ReplicatedWriteUnitsIA"},
                    {"key": "operation", "value": "CommittedThroughput"},
                    {"key": "usagetype", "value": "IA-ReplWriteCapacityUnit-Hrs"}
                ]
            else:
                attribute_filters = [
                    {"key": "group", "value": "DDB-ReplicatedWriteUnits"},
                    {"key": "operation", "value": "CommittedThroughput"},
                    {"key": "usagetype", "value": "ReplWriteCapacityUnit-Hrs"}
                ]
        
        # Use the correct product family based on billing mode
        if billing_mode == "PAY_PER_REQUEST":
            return QueryBuilder._build_base_query(
                "AmazonDynamoDB", "Amazon DynamoDB PayPerRequest Throughput", region, attribute_filters
            )
        else:
            return QueryBuilder._build_base_query(
                "AmazonDynamoDB", "DDB-Operation-ReplicatedWrite", region, attribute_filters
            )


class APIGatewayQueryBuilder(QueryBuilder):
    """Query builder for API Gateway."""
    
    @staticmethod
    def build_rest_api_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        # Extract actual properties from CloudFormation template
        name = properties.get("Name", "")
        description = properties.get("Description", "")
        endpoint_configuration = properties.get("EndpointConfiguration", {})
        endpoint_types = endpoint_configuration.get("Types", ["EDGE"])
        
        # Use regex pattern to match any region-specific usage type for API Gateway REST requests
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/ApiGatewayRequest/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonApiGateway", "API Calls", region, attribute_filters
        )
    
    @staticmethod
    def build_v2_api_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        # Extract actual properties from CloudFormation template
        protocol_type = properties.get("ProtocolType", "HTTP")
        name = properties.get("Name", "")
        description = properties.get("Description", "")
        cors_configuration = properties.get("CorsConfiguration", {})
        
        # Use regex pattern to match any region-specific usage type for API Gateway HTTP requests
        if protocol_type.upper() == "HTTP":
            attribute_filters = [
                {"key": "usagetype", "valueRegex": "/ApiGatewayHttpRequest/"}
            ]
        else:
            attribute_filters = [
                {"key": "usagetype", "valueRegex": "/ApiGatewayRequest/"}
            ]
        
        return QueryBuilder._build_base_query(
            "AmazonApiGateway", "API Calls", region, attribute_filters
        )


class KMSQueryBuilder(QueryBuilder):
    """Query builder for KMS keys."""
    
    @staticmethod
    def build_key_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # KMS keys have a fixed monthly cost per key
        # Use the correct usage type pattern found in Infracost API
        usagetype = f"{region}-KMS-Keys"
        
        attribute_filters = [
            {"key": "usagetype", "value": usagetype}
        ]
        
        return QueryBuilder._build_base_query(
            "awskms", "Encryption Key", region, attribute_filters
        )


class EKSQueryBuilder(QueryBuilder):
    """Query builder for EKS clusters."""
    
    @staticmethod
    def build_cluster_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        cluster_name = properties.get("Name", "")
        version = properties.get("Version", "1.21")
        
        # EKS clusters have a fixed hourly cost - use correct usage type pattern
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/EKS.*Cluster/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEKS", "Compute", region, attribute_filters, purchase_option="on_demand"
        )
    
    @staticmethod
    def build_nodegroup_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        # Extract actual node group properties
        nodegroup_name = properties.get("NodegroupName", "")
        cluster_name = properties.get("ClusterName", "")
        instance_types = properties.get("InstanceTypes", ["t3.medium"])
        ami_type = properties.get("AmiType", "AL2_x86_64")
        capacity_type = properties.get("CapacityType", "ON_DEMAND")
        scaling_config = properties.get("ScalingConfig", {})
        disk_size = properties.get("DiskSize", 20)
        node_role = properties.get("NodeRole", "")
        
        # EKS Node Groups use EC2 instances, so use EC2 pricing structure
        # Determine operating system from AMI type
        if "BOTTLEROCKET" in ami_type:
            operating_system = "Linux"
        elif "WINDOWS" in ami_type:
            operating_system = "Windows"
        else:
            operating_system = "Linux"  # AL2_x86_64, AL2_ARM_64
        
        # Determine purchase option
        purchase_option = "on_demand" if capacity_type == "ON_DEMAND" else "spot"
        
        attribute_filters = [
            {"key": "instanceType", "value": instance_types[0] if instance_types else "t3.medium"},
            {"key": "tenancy", "value": "Shared"},
            {"key": "operatingSystem", "value": operating_system},
            {"key": "preInstalledSw", "value": "NA"},
            {"key": "licenseModel", "value": "No License required"},
            {"key": "capacitystatus", "value": "Used"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "Compute Instance", region, attribute_filters, purchase_option=purchase_option
        )


class ElastiCacheQueryBuilder(QueryBuilder):
    """Query builder for ElastiCache clusters."""
    
    @staticmethod
    def build_cluster_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        cache_node_type = properties.get("CacheNodeType", "cache.t3.micro")
        engine = properties.get("Engine", "redis")
        
        # Use the same pattern as Go files for ElastiCache
        attribute_filters = [
            {"key": "instanceType", "value": cache_node_type},
            {"key": "locationType", "value": "AWS Region"},
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
        # Route 53 hosted zones have a fixed monthly cost
        # Route 53 is a global service, so no region filter is needed
        attribute_filters = [
            {"key": "usagetype", "value": "HostedZone"}
        ]
        
        return QueryBuilder._build_global_query(
            "AmazonRoute53", "DNS Zone", attribute_filters
        )
    
    @staticmethod
    def build_health_check_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Route53 health checks - use basic AWS health check
        attribute_filters = [
            {"key": "usagetype", "value": "Health-Check-AWS"}
        ]
        
        return QueryBuilder._build_global_query(
            "AmazonRoute53", "DNS Health Check", attribute_filters
        )


class SNSQueryBuilder(QueryBuilder):
    """Query builder for SNS topics."""
    
    @staticmethod
    def build_topic_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Use regex pattern to match any region-specific usage type for SNS requests
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/Requests-Tier1$/"}
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
        
        # Use regex pattern to match any region-specific usage type for SQS requests
        # SQS uses the same service as SNS for API requests
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/Requests-Tier1$/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonSNS", "API Request", region, attribute_filters
        )


class SecretsManagerQueryBuilder(QueryBuilder):
    """Query builder for Secrets Manager."""
    
    @staticmethod
    def build_secret_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Secrets Manager uses AWSSecretsManager service and Secret product family per Go file
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AWSSecretsManager", "Secret", region, attribute_filters
        )


class StepFunctionsQueryBuilder(QueryBuilder):
    """Query builder for Step Functions."""
    
    @staticmethod
    def build_state_machine_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        state_machine_type = properties.get("StateMachineType", "STANDARD")
        
        # Use the correct service name and product family from Go file
        if state_machine_type.upper() == "EXPRESS":
            # Express workflows are charged by requests and duration
            attribute_filters = [
                {"key": "usagetype", "valueRegex": "/StepFunctions-Request/"}
            ]
        else:
            # Standard workflows are charged by state transitions
            attribute_filters = [
                {"key": "usagetype", "valueRegex": "/StateTransition/"}
            ]
        
        return QueryBuilder._build_base_query(
            "AmazonStates", "AWS Step Functions", region, attribute_filters, purchase_option="on_demand"
        )


class VPCQueryBuilder(QueryBuilder):
    """Query builder for VPC services."""
    
    @staticmethod
    def build_nat_gateway_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Use regex pattern to match any region-specific usage type for NAT Gateway
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/NatGateway-Hours/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEC2", "NAT Gateway", region, attribute_filters
        )
    
    @staticmethod
    def build_vpn_connection_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # VPN connections use AmazonVPC service and Cloud Connectivity product family per Go file
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AmazonVPC", "Cloud Connectivity", region, attribute_filters
        )
    
    @staticmethod
    def build_vpc_endpoint_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        vpc_endpoint_type = properties.get("VpcEndpointType", "Interface")
        
        # Map CloudFormation endpoint types to Infracost endpoint types
        endpoint_type_mapping = {
            "Interface": "PrivateLink",
            "Gateway": "Gateway",
            "GatewayLoadBalancer": "Gateway Load Balancer Endpoint"
        }
        
        endpoint_type = endpoint_type_mapping.get(vpc_endpoint_type, "PrivateLink")
        
        attribute_filters = [
            {"key": "endpointType", "value": endpoint_type}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonVPC", "VpcEndpoint", region, attribute_filters
        )


class WAFQueryBuilder(QueryBuilder):
    """Query builder for WAF services."""
    
    @staticmethod
    def build_web_acl_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        scope = properties.get("Scope", "REGIONAL")
        
        # WAF Web ACLs use awswaf service - pattern works for both WAF and WAFv2
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/^[A-Z0-9]*-(?!ShieldProtected-)WebACL/i"}
        ]
        
        return QueryBuilder._build_base_query(
            "awswaf", "Web Application Firewall", region, attribute_filters
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
        repository_name = properties.get("RepositoryName", "")
        
        # ECR uses AmazonECR service and EC2 Container Registry product family per Go file
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AmazonECR", "EC2 Container Registry", region, attribute_filters
        )


class EFSQueryBuilder(QueryBuilder):
    """Query builder for EFS file systems."""
    
    @staticmethod
    def build_filesystem_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        attribute_filters = [
            {"key": "storageClass", "value": "General Purpose"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonEFS", "Storage", region, attribute_filters
        )


class CodeBuildQueryBuilder(QueryBuilder):
    """Query builder for CodeBuild projects."""
    
    @staticmethod
    def build_project_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        environment = properties.get("Environment", {})
        compute_type = environment.get("ComputeType", "BUILD_GENERAL1_SMALL")
        environment_type = environment.get("Type", "LINUX_CONTAINER")
        
        # CodeBuild uses CodeBuild service and Compute product family per Go file
        # Map environment type and compute type like the Go file
        environment_type_mapping = {
            "LINUX_CONTAINER": "Linux",
            "LINUX_GPU_CONTAINER": "LinuxGPU", 
            "ARM_CONTAINER": "ARM",
            "WINDOWS_SERVER_2019_CONTAINER": "Windows"
        }
        
        compute_type_mapping = {
            "BUILD_GENERAL1_SMALL": "g1.small",
            "BUILD_GENERAL1_MEDIUM": "g1.medium",
            "BUILD_GENERAL1_LARGE": "g1.large",
            "BUILD_GENERAL1_2XLARGE": "g1.2xlarge"
        }
        
        mapped_env_type = environment_type_mapping.get(environment_type, "Linux")
        mapped_compute_type = compute_type_mapping.get(compute_type, "g1.small")
        
        attribute_filters = [
            {"key": "usagetype", "valueRegex": f"/{mapped_env_type}:{mapped_compute_type}/"}
        ]
        
        return QueryBuilder._build_base_query(
            "CodeBuild", "Compute", region, attribute_filters
        )


class KinesisQueryBuilder(QueryBuilder):
    """Query builder for Kinesis streams."""
    
    @staticmethod
    def build_stream_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        shard_count = properties.get("ShardCount", 1)
        retention_period = properties.get("RetentionPeriodHours", 24)
        
        # Kinesis streams use AmazonKinesis service and Kinesis Streams product family per Go file
        # Use shard hour usage type for provisioned streams
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/ShardHour/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonKinesis", "Kinesis Streams", region, attribute_filters
        )


class CloudTrailQueryBuilder(QueryBuilder):
    """Query builder for CloudTrail."""
    
    @staticmethod
    def build_trail_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        trail_name = properties.get("TrailName", "")
        s3_bucket_name = properties.get("S3BucketName", "")
        include_global_service_events = properties.get("IncludeGlobalServiceEvents", True)
        is_multi_region_trail = properties.get("IsMultiRegionTrail", False)
        
        # CloudTrail uses AWSCloudTrail service per Go file
        # Use data events product family as the primary cost component
        attribute_filters = []
        
        return QueryBuilder._build_base_query(
            "AWSCloudTrail", "Management Tools - AWS CloudTrail Data Events Recorded", region, attribute_filters
        )


class BackupQueryBuilder(QueryBuilder):
    """Query builder for AWS Backup."""
    
    @staticmethod
    def build_vault_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Backup Vault uses AWSBackup service and AWS Backup Storage product family per Go file
        # Use EFS warm backup as the primary cost component
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/WarmStorage-ByteHrs-EFS$/i"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSBackup", "AWS Backup Storage", region, attribute_filters
        )


class TransferQueryBuilder(QueryBuilder):
    """Query builder for AWS Transfer Family."""
    
    @staticmethod
    def build_server_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Transfer Family uses AWSTransfer service and AWS Transfer Family product family per Go file
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/^[A-Z0-9]*-ProtocolHours$/"},
            {"key": "operation", "valueRegex": "/^FTP:S3$/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSTransfer", "AWS Transfer Family", region, attribute_filters
        )


class SSMQueryBuilder(QueryBuilder):
    """Query builder for Systems Manager."""
    
    @staticmethod
    def build_parameter_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        parameter_type = properties.get("Type", "String")
        tier = properties.get("Tier", "Standard")
        
        # SSM Parameter uses AWSSystemsManager service per Go file
        if tier.lower() == "advanced":
            # Advanced tier has parameter storage costs
            attribute_filters = [
                {"key": "usagetype", "valueRegex": "/PS-Advanced-Param-Tier1/"}
            ]
            return QueryBuilder._build_base_query(
                "AWSSystemsManager", "AWS Systems Manager", region, attribute_filters
            )
        else:
            # Standard tier parameters are free - return a query that will show $0 cost
            attribute_filters = [
                {"key": "usagetype", "valueRegex": "/PS-Advanced-Param-Tier1/"}
            ]
            return QueryBuilder._build_base_query(
                "AWSSystemsManager", "AWS Systems Manager", region, attribute_filters
            )
    
    @staticmethod
    def build_activation_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # SSM Activation uses AWSSystemsManager service per Go file
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/MI-AdvInstances-Hrs/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSSystemsManager", "AWS Systems Manager", region, attribute_filters
        )


class CloudFrontQueryBuilder(QueryBuilder):
    """Query builder for CloudFront."""
    
    @staticmethod
    def build_distribution_query(properties: Dict[str, Any]) -> str:
        # CloudFront is a global service, so no region filter needed
        # CloudFront Go file shows no ProductFamily is used, only service and attribute filters
        # Use invalidation requests as a basic cost component that should be available
        attribute_filters = [
            {"key": "usagetype", "value": "Invalidations"}
        ]
        
        return QueryBuilder._build_global_query(
            "AmazonCloudFront", "", attribute_filters
        )
    
    @staticmethod
    def build_function_query(properties: Dict[str, Any]) -> str:
        # CloudFront is a global service, so no region filter needed
        # CloudFront Functions use AmazonCloudFront service with no ProductFamily per Go file
        attribute_filters = [
            {"key": "requestDescription", "valueRegex": "/CloudFront Functions/"}
        ]
        
        return QueryBuilder._build_global_query(
            "AmazonCloudFront", "", attribute_filters
        )


class DocumentDBQueryBuilder(QueryBuilder):
    """Query builder for DocumentDB."""
    
    @staticmethod
    def build_cluster_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # DocumentDB Cluster uses AmazonDocDB service and Storage Snapshot product family per Go file
        # Only has backup storage costs
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/(^|-)BackupUsage$/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonDocDB", "Storage Snapshot", region, attribute_filters
        )
    
    @staticmethod
    def build_instance_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        instance_class = properties.get("DBInstanceClass", "db.t3.medium")
        
        # DocumentDB uses AmazonDocDB service and Database Instance product family per Go file
        attribute_filters = [
            {"key": "instanceType", "value": instance_class},
            {"key": "volumeType", "value": "General Purpose"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonDocDB", "Database Instance", region, attribute_filters
        )


class NeptuneQueryBuilder(QueryBuilder):
    """Query builder for Neptune."""
    
    @staticmethod
    def build_cluster_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Neptune Cluster uses AmazonNeptune service with no ProductFamily per Go file
        # Use storage usage as the primary cost component
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/StorageUsage$/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonNeptune", "", region, attribute_filters
        )
    
    @staticmethod
    def build_instance_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        instance_class = properties.get("DBInstanceClass", "db.t3.medium")
        
        # Neptune uses AmazonNeptune service and no ProductFamily per Go file
        # Uses specific attribute filters for instanceType and usagetype
        instance_class_lower = instance_class.lower()
        attribute_filters = [
            {"key": "instanceType", "value": instance_class_lower},
            {"key": "usagetype", "valueRegex": f"/InstanceUsage:{instance_class_lower}$/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonNeptune", "", region, attribute_filters
        )


class ElasticsearchQueryBuilder(QueryBuilder):
    """Query builder for Elasticsearch."""
    
    @staticmethod
    def build_domain_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        cluster_config = properties.get("ClusterConfig", {})
        instance_type = cluster_config.get("InstanceType", "m4.large.elasticsearch")
        
        # Elasticsearch uses AmazonES service and Amazon OpenSearch Service Instance product family per Go file
        # Convert instance type from .elasticsearch to .search format as per Go file
        opensearch_instance_type = instance_type.replace(".elasticsearch", ".search")
        
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/ESInstance/"},
            {"key": "instanceType", "value": opensearch_instance_type}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonES", "Amazon OpenSearch Service Instance", region, attribute_filters
        )


class LightsailQueryBuilder(QueryBuilder):
    """Query builder for Lightsail."""
    
    @staticmethod
    def build_instance_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        bundle_id = properties.get("BundleId", "nano_2_0")
        
        # Lightsail uses AmazonLightsail service and Lightsail Instance product family per Go file
        # Parse bundle ID to get memory size
        bundle_prefix_mappings = {
            "nano": "0.5GB",
            "micro": "1GB", 
            "small": "2GB",
            "medium": "4GB",
            "large": "8GB",
            "xlarge": "16GB",
            "2xlarge": "32GB",
            "4xlarge": "64GB",
        }
        
        bundle_prefix = bundle_id.split("_")[0].lower()
        memory = bundle_prefix_mappings.get(bundle_prefix, bundle_prefix)
        
        # Check for Windows
        operating_system_suffix = "_win" if "_win_" in bundle_id.lower() else ""
        
        usage_type_regex = f"-BundleUsage:{memory}{operating_system_suffix}$"
        
        attribute_filters = [
            {"key": "usagetype", "valueRegex": f"/{usage_type_regex}/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonLightsail", "Lightsail Instance", region, attribute_filters
        )


class MQQueryBuilder(QueryBuilder):
    """Query builder for Amazon MQ."""
    
    @staticmethod
    def build_broker_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        instance_type = properties.get("HostInstanceType", "mq.t3.micro")
        engine_type = properties.get("EngineType", "ActiveMQ")
        deployment_mode = properties.get("DeploymentMode", "SINGLE_INSTANCE")
        
        # MQ Broker uses AmazonMQ service and Broker Instances product family per Go file
        # Determine deployment option
        is_multi_az = deployment_mode.lower() in ["active_standby_multi_az", "cluster_multi_az"]
        deployment_option = "Multi-AZ" if is_multi_az else "Single-AZ"
        
        attribute_filters = [
            {"key": "usagetype", "valueRegex": f"/{instance_type}/"},
            {"key": "brokerEngine", "valueRegex": f"/{engine_type}/"},
            {"key": "deploymentOption", "valueRegex": f"/{deployment_option}/"},
            {"key": "operation", "valueRegex": "/CreateBroker/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonMQ", "Broker Instances", region, attribute_filters
        )


class MSKQueryBuilder(QueryBuilder):
    """Query builder for MSK (Managed Streaming for Apache Kafka)."""
    
    @staticmethod
    def build_cluster_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        broker_node_group_info = properties.get("BrokerNodeGroupInfo", {})
        instance_type = broker_node_group_info.get("InstanceType", "kafka.t3.small")
        
        # MSK uses AmazonMSK service and specific product family per Go file
        attribute_filters = [
            {"key": "usagetype", "valueRegex": f"/{instance_type}/i"},
            {"key": "locationType", "value": "AWS Region"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonMSK", "Managed Streaming for Apache Kafka (MSK)", region, attribute_filters
        )


class ConfigQueryBuilder(QueryBuilder):
    """Query builder for AWS Config."""
    
    @staticmethod
    def build_rule_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Config uses AWSConfig service and Management Tools - AWS Config product family per Go file
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/ConfigurationItemRecorded$/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSConfig", "Management Tools - AWS Config", region, attribute_filters
        )
    
    @staticmethod
    def build_recorder_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Config Configuration Recorder uses AWSConfig service and Management Tools - AWS Config product family per Go file
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/ConfigurationItemRecorded$/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSConfig", "Management Tools - AWS Config", region, attribute_filters
        )


class DMSQueryBuilder(QueryBuilder):
    """Query builder for Database Migration Service."""
    
    @staticmethod
    def build_replication_instance_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        instance_class = properties.get("ReplicationInstanceClass", "dms.t3.micro")
        multi_az = properties.get("MultiAZ", False)
        
        # DMS uses AWSDatabaseMigrationSvc service with no ProductFamily per Go file
        # Parse instance type from the class (remove "dms." prefix)
        instance_type_parts = instance_class.split(".")
        if len(instance_type_parts) >= 3:
            instance_type = ".".join(instance_type_parts[1:])
        else:
            instance_type = instance_class
        
        availability_zone = "Multiple" if multi_az else "Single"
        
        attribute_filters = [
            {"key": "instanceType", "value": instance_type},
            {"key": "availabilityZone", "value": availability_zone}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSDatabaseMigrationSvc", "", region, attribute_filters
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
        
        # Directory Service uses AWSDirectoryService service and AWS Directory Service product family per Go file
        # Map region to region name for location attribute
        region_name_mapping = {
            "us-east-1": "US East (N. Virginia)",
            "us-east-2": "US East (Ohio)",
            "us-west-1": "US West (N. California)",
            "us-west-2": "US West (Oregon)",
            "ca-central-1": "Canada (Central)",
            "eu-west-1": "Europe (Ireland)",
            "eu-west-2": "Europe (London)",
            "eu-central-1": "Europe (Frankfurt)",
            "ap-southeast-1": "Asia Pacific (Singapore)",
            "ap-southeast-2": "Asia Pacific (Sydney)",
            "ap-northeast-1": "Asia Pacific (Tokyo)"
        }
        
        region_name = region_name_mapping.get(region, "US East (N. Virginia)")
        
        attribute_filters = [
            {"key": "directoryType", "value": "Microsoft AD"},
            {"key": "directorySize", "value": edition},
            {"key": "location", "value": region_name}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSDirectoryService", "AWS Directory Service", region, attribute_filters
        )
    
    @staticmethod
    def build_simple_ad_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        size = properties.get("Size", "Small")
        
        # Directory Service uses AWSDirectoryService service and AWS Directory Service product family per Go file
        # Map region to region name for location attribute
        region_name_mapping = {
            "us-east-1": "US East (N. Virginia)",
            "us-east-2": "US East (Ohio)",
            "us-west-1": "US West (N. California)",
            "us-west-2": "US West (Oregon)",
            "ca-central-1": "Canada (Central)",
            "eu-west-1": "Europe (Ireland)",
            "eu-west-2": "Europe (London)",
            "eu-central-1": "Europe (Frankfurt)",
            "ap-southeast-1": "Asia Pacific (Singapore)",
            "ap-southeast-2": "Asia Pacific (Sydney)",
            "ap-northeast-1": "Asia Pacific (Tokyo)"
        }
        
        region_name = region_name_mapping.get(region, "US East (N. Virginia)")
        
        attribute_filters = [
            {"key": "directoryType", "valueRegex": "/Simple AD/i"},
            {"key": "directorySize", "value": size},
            {"key": "location", "value": region_name}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSDirectoryService", "AWS Directory Service", region, attribute_filters
        )


class EC2AdvancedQueryBuilder(QueryBuilder):
    """Query builder for advanced EC2 services."""
    
    @staticmethod
    def build_client_vpn_endpoint_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Client VPN endpoint uses AmazonVPC service per Go file
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/ClientVPN-ConnectionHours/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonVPC", "", region, attribute_filters
        )
    
    @staticmethod
    def build_dedicated_host_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        instance_type = properties.get("InstanceType", "m5.large")
        
        # Extract instance family from instance type (e.g., "m5" from "m5.large")
        instance_family = instance_type.split(".")[0] if "." in instance_type else instance_type
        
        # EC2 dedicated host uses AmazonEC2 service and Dedicated Host product family per Go file
        attribute_filters = [
            {"key": "usagetype", "valueRegex": f"/HostUsage:{instance_family}$/"}
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
        
        # Transit Gateway uses AmazonVPC service per Go file
        # Use TransitGateway-Hours usage type for the gateway itself
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/TransitGateway-Hours/"},
            {"key": "operation", "value": "TransitGatewayVPC"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonVPC", "", region, attribute_filters
        )
    
    @staticmethod
    def build_transit_gateway_attachment_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Transit Gateway VPC attachment uses AmazonVPC service per Go file
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/TransitGateway-Hours/"},
            {"key": "operation", "value": "TransitGatewayVPC"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonVPC", "", region, attribute_filters
        )


class ECSQueryBuilder(QueryBuilder):
    """Query builder for ECS services."""
    
    @staticmethod
    def build_service_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        launch_type = properties.get("LaunchType", "EC2")
        
        if launch_type == "FARGATE":
            # Fargate launch type - use vCPU hours as primary cost component per Go file
            attribute_filters = [
                {"key": "usagetype", "valueRegex": "/Fargate-vCPU-Hours:perCPU/"}
            ]
            return QueryBuilder._build_base_query(
                "AmazonECS", "Compute", region, attribute_filters
            )
        else:
            # EC2 launch type - costs are from underlying EC2 instances, ECS itself is free
            # Return a query that will show no cost for ECS service itself
            attribute_filters = []
            return QueryBuilder._build_base_query(
                "AmazonECS", "Container Service", region, attribute_filters, purchase_option="on_demand"
            )


class EKSFargateQueryBuilder(QueryBuilder):
    """Query builder for EKS Fargate."""
    
    @staticmethod
    def build_fargate_profile_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # EKS Fargate Profile uses AmazonEKS service and Compute product family per Go file
        # Use vCPU hours as the primary cost component
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/Fargate-vCPU-Hours:perCPU/"}
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
        
        # EventBridge uses AWSEvents service and EventBridge product family per Go file
        # Use custom events as the primary cost component
        attribute_filters = [
            {"key": "eventType", "value": "Custom Event"},
            {"key": "usagetype", "valueRegex": "/Event-64K-Chunks/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSEvents", "EventBridge", region, attribute_filters
        )


class FSxQueryBuilder(QueryBuilder):
    """Query builder for FSx file systems."""
    
    @staticmethod
    def build_filesystem_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        filesystem_type = properties.get("FileSystemType", "WINDOWS")
        deployment_type = properties.get("DeploymentType", "SINGLE_AZ_1")
        
        # FSx uses AmazonFSx service with Storage product family per Go file
        # Map deployment type to deployment option
        deployment_option = "Multi-AZ" if "multi_az" in deployment_type.lower() else "Single-AZ"
        
        # Map filesystem type to correct case
        if filesystem_type.upper() == "WINDOWS":
            file_system_type = "Windows"
        elif filesystem_type.upper() == "LUSTRE":
            file_system_type = "Lustre"
        elif filesystem_type.upper() == "OPENZFS":
            file_system_type = "OpenZFS"
        else:
            file_system_type = "Windows"  # Default
        
        attribute_filters = [
            {"key": "deploymentOption", "value": deployment_option},
            {"key": "fileSystemType", "value": file_system_type}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonFSx", "Storage", region, attribute_filters
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
        
        # Global Accelerator Endpoint Group uses AWSGlobalAccelerator service with no ProductFamily per Go file
        # Use basic data transfer attributes
        attribute_filters = [
            {"key": "trafficDirection", "value": "In"},
            {"key": "operation", "value": "Dominant"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSGlobalAccelerator", "", region, attribute_filters
        )


class GlueQueryBuilder(QueryBuilder):
    """Query builder for AWS Glue."""
    
    @staticmethod
    def build_crawler_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Glue Crawler uses AWSGlue service and AWS Glue product family per Go file
        attribute_filters = [
            {"key": "operation", "valueRegex": "/^crawlerrun$/i"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSGlue", "AWS Glue", region, attribute_filters
        )
    
    @staticmethod
    def build_database_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Glue Catalog Database uses AWSGlue service and AWS Glue product family per Go file
        # Use storage cost component as primary cost
        attribute_filters = [
            {"key": "group", "valueRegex": "/^data catalog storage$/i"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSGlue", "AWS Glue", region, attribute_filters
        )
    
    @staticmethod
    def build_job_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Glue Job uses AWSGlue service and AWS Glue product family per Go file
        attribute_filters = [
            {"key": "group", "value": "ETL Job run"},
            {"key": "operation", "valueRegex": "/^jobrun$/i"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSGlue", "AWS Glue", region, attribute_filters
        )


class KinesisAdvancedQueryBuilder(QueryBuilder):
    """Query builder for advanced Kinesis services."""
    
    @staticmethod
    def build_analytics_application_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Kinesis Analytics uses AmazonKinesisAnalytics service and Kinesis Analytics product family per Go file
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/KPU-Hour-Java/i"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonKinesisAnalytics", "Kinesis Analytics", region, attribute_filters
        )
    
    @staticmethod
    def build_firehose_delivery_stream_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Kinesis Firehose uses AmazonKinesisFirehose service and Kinesis Firehose product family per Go file
        # Use data ingestion as the primary cost component
        attribute_filters = [
            {"key": "group", "value": "Event-by-Event Processing"},
            {"key": "sourcetype", "value": ""}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonKinesisFirehose", "Kinesis Firehose", region, attribute_filters
        )


class MWAAQueryBuilder(QueryBuilder):
    """Query builder for Managed Workflows for Apache Airflow."""
    
    @staticmethod
    def build_environment_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        environment_class = properties.get("EnvironmentClass", "mw1.small")
        
        # MWAA uses AmazonMWAA service with no ProductFamily per Go file
        # Parse environment class to get size (Small, Medium, Large)
        if "small" in environment_class.lower():
            size = "Small"
        elif "medium" in environment_class.lower():
            size = "Medium"
        elif "large" in environment_class.lower():
            size = "Large"
        else:
            size = "Small"  # Default
        
        attribute_filters = [
            {"key": "size", "valueRegex": f"/^{size}$/i"},
            {"key": "type", "value": "Environment"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonMWAA", "", region, attribute_filters
        )


class NetworkFirewallQueryBuilder(QueryBuilder):
    """Query builder for Network Firewall."""
    
    @staticmethod
    def build_firewall_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # NetworkFirewall uses AWSNetworkFirewall service and AWS Firewall product family per Go file
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/^[A-Z0-9]*-Endpoint-Hour$/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AWSNetworkFirewall", "AWS Firewall", region, attribute_filters
        )


class Route53AdvancedQueryBuilder(QueryBuilder):
    """Query builder for advanced Route 53 services."""
    
    @staticmethod
    def build_record_set_query(properties: Dict[str, Any]) -> str:
        # DNS queries are charged per query, not per record
        # Route53 is a global service, so no region filter needed
        attribute_filters = [
            {"key": "usagetype", "value": "DNS-Queries"}
        ]
        
        return QueryBuilder._build_global_query(
            "AmazonRoute53", "DNS Query", attribute_filters
        )


class Route53ResolverQueryBuilder(QueryBuilder):
    """Query builder for Route 53 Resolver."""
    
    @staticmethod
    def build_resolver_endpoint_query(properties: Dict[str, Any]) -> str:
        region = properties.get("Region", "us-east-1")
        
        # Route53 Resolver Endpoint uses AmazonRoute53 service and DNS Query product family per Go file
        attribute_filters = [
            {"key": "usagetype", "valueRegex": "/ResolverNetworkInterface$/"}
        ]
        
        return QueryBuilder._build_base_query(
            "AmazonRoute53", "DNS Query", region, attribute_filters
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