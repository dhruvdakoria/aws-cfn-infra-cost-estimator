"""
Resource mappings from Terraform to CloudFormation equivalents.
Based on Infracost supported resources documentation.
"""

from typing import Dict, Set

# Mapping of CloudFormation resource types to Infracost service information
PAID_RESOURCE_MAPPINGS = {
    # API Gateway
    "AWS::ApiGateway::RestApi": {
        "service": "AmazonApiGateway",
        "productFamily": "API Gateway",
        "terraform_equivalent": "aws_api_gateway_rest_api"
    },
    "AWS::ApiGateway::Stage": {
        "service": "AmazonApiGateway", 
        "productFamily": "API Gateway",
        "terraform_equivalent": "aws_api_gateway_stage"
    },
    "AWS::ApiGatewayV2::Api": {
        "service": "AmazonApiGateway",
        "productFamily": "API Gateway",
        "terraform_equivalent": "aws_apigatewayv2_api"
    },
    
    # Application Auto Scaling
    "AWS::ApplicationAutoScaling::ScalableTarget": {
        "service": "AmazonEC2",
        "productFamily": "Auto Scaling",
        "terraform_equivalent": "aws_appautoscaling_target"
    },
    
    # Backup
    "AWS::Backup::BackupVault": {
        "service": "AWSBackup",
        "productFamily": "Backup Storage",
        "terraform_equivalent": "aws_backup_vault"
    },
    
    # Certificate Manager (ACM)
    "AWS::ACMPCA::CertificateAuthority": {
        "service": "AWSCertificateManager",
        "productFamily": "Certificate Authority",
        "terraform_equivalent": "aws_acmpca_certificate_authority"
    },
    "AWS::CertificateManager::Certificate": {
        "service": "AWSCertificateManager",
        "productFamily": "Certificate",
        "terraform_equivalent": "aws_acm_certificate",
        "notes": "Private certificates are paid, public SSL/TLS certificates are free"
    },
    
    # CloudFormation
    "AWS::CloudFormation::Stack": {
        "service": "AWSCloudFormation",
        "productFamily": "CloudFormation",
        "terraform_equivalent": "aws_cloudformation_stack"
    },
    "AWS::CloudFormation::StackSet": {
        "service": "AWSCloudFormation",
        "productFamily": "CloudFormation",
        "terraform_equivalent": "aws_cloudformation_stack_set"
    },
    
    # CloudFront
    "AWS::CloudFront::Distribution": {
        "service": "AmazonCloudFront",
        "productFamily": "Content Delivery",
        "terraform_equivalent": "aws_cloudfront_distribution"
    },
    "AWS::CloudFront::Function": {
        "service": "AmazonCloudFront",
        "productFamily": "CloudFront Functions",
        "terraform_equivalent": "aws_cloudfront_function"
    },
    
    # CloudTrail
    "AWS::CloudTrail::Trail": {
        "service": "AWSCloudTrail",
        "productFamily": "CloudTrail",
        "terraform_equivalent": "aws_cloudtrail"
    },
    
    # CloudWatch
    "AWS::CloudWatch::Dashboard": {
        "service": "AmazonCloudWatch",
        "productFamily": "Dashboard",
        "terraform_equivalent": "aws_cloudwatch_dashboard"
    },
    "AWS::Logs::LogGroup": {
        "service": "AmazonCloudWatch",
        "productFamily": "Log Group",
        "terraform_equivalent": "aws_cloudwatch_log_group"
    },
    "AWS::CloudWatch::Alarm": {
        "service": "AmazonCloudWatch",
        "productFamily": "Alarm",
        "terraform_equivalent": "aws_cloudwatch_metric_alarm"
    },
    
    # CodeBuild
    "AWS::CodeBuild::Project": {
        "service": "AWSCodeBuild",
        "productFamily": "Build",
        "terraform_equivalent": "aws_codebuild_project"
    },
    
    # Config
    "AWS::Config::ConfigRule": {
        "service": "AWSConfig",
        "productFamily": "Config Rule",
        "terraform_equivalent": "aws_config_config_rule"
    },
    "AWS::Config::ConfigurationRecorder": {
        "service": "AWSConfig",
        "productFamily": "Configuration Recorder",
        "terraform_equivalent": "aws_config_configuration_recorder"
    },
    
    # Database Migration Service (DMS)
    "AWS::DMS::ReplicationInstance": {
        "service": "AWSDatabaseMigrationService",
        "productFamily": "Database Migration",
        "terraform_equivalent": "aws_dms_replication_instance"
    },
    
    # Direct Connect
    "AWS::DirectConnect::Connection": {
        "service": "AWSDirectConnect",
        "productFamily": "Direct Connect",
        "terraform_equivalent": "aws_dx_connection"
    },
    "AWS::DirectConnect::VirtualInterface": {
        "service": "AWSDirectConnect",
        "productFamily": "Virtual Interface",
        "terraform_equivalent": "aws_dx_gateway_association"
    },
    
    # Directory Service
    "AWS::DirectoryService::MicrosoftAD": {
        "service": "AWSDirectoryService",
        "productFamily": "Directory Service",
        "terraform_equivalent": "aws_directory_service_directory"
    },
    "AWS::DirectoryService::SimpleAD": {
        "service": "AWSDirectoryService",
        "productFamily": "Directory Service",
        "terraform_equivalent": "aws_directory_service_directory"
    },
    
    # DocumentDB
    "AWS::DocDB::DBCluster": {
        "service": "AmazonDocDB",
        "productFamily": "Database Cluster",
        "terraform_equivalent": "aws_docdb_cluster"
    },
    "AWS::DocDB::DBInstance": {
        "service": "AmazonDocDB",
        "productFamily": "Database Instance",
        "terraform_equivalent": "aws_docdb_cluster_instance"
    },
    
    # DynamoDB
    "AWS::DynamoDB::Table": {
        "service": "AmazonDynamoDB",
        "productFamily": "Database Storage",
        "terraform_equivalent": "aws_dynamodb_table"
    },
    
    # EC2
    "AWS::EC2::Instance": {
        "service": "AmazonEC2",
        "productFamily": "Compute Instance",
        "terraform_equivalent": "aws_instance"
    },
    "AWS::EC2::Volume": {
        "service": "AmazonEC2",
        "productFamily": "Storage",
        "terraform_equivalent": "aws_ebs_volume"
    },
    "AWS::EC2::Snapshot": {
        "service": "AmazonEC2",
        "productFamily": "Storage Snapshot",
        "terraform_equivalent": "aws_ebs_snapshot"
    },
    "AWS::AutoScaling::AutoScalingGroup": {
        "service": "AmazonEC2",
        "productFamily": "Compute Instance",
        "terraform_equivalent": "aws_autoscaling_group"
    },
    "AWS::EC2::EIP": {
        "service": "AmazonEC2",
        "productFamily": "IP Address",
        "terraform_equivalent": "aws_eip"
    },
    "AWS::EC2::DedicatedHost": {
        "service": "AmazonEC2",
        "productFamily": "Dedicated Host",
        "terraform_equivalent": "aws_ec2_host"
    },
    "AWS::EC2::SpotFleet": {
        "service": "AmazonEC2",
        "productFamily": "Compute Instance",
        "terraform_equivalent": "aws_spot_instance_request"
    },
    
    # ECR
    "AWS::ECR::Repository": {
        "service": "AmazonECR",
        "productFamily": "Container Registry",
        "terraform_equivalent": "aws_ecr_repository"
    },
    
    # ECS
    "AWS::ECS::Service": {
        "service": "AmazonECS",
        "productFamily": "Container Service",
        "terraform_equivalent": "aws_ecs_service"
    },
    
    # EFS
    "AWS::EFS::FileSystem": {
        "service": "AmazonEFS",
        "productFamily": "Storage",
        "terraform_equivalent": "aws_efs_file_system"
    },
    
    # EKS
    "AWS::EKS::Cluster": {
        "service": "AmazonEKS",
        "productFamily": "Kubernetes Cluster",
        "terraform_equivalent": "aws_eks_cluster"
    },
    "AWS::EKS::FargateProfile": {
        "service": "AmazonEKS",
        "productFamily": "Fargate",
        "terraform_equivalent": "aws_eks_fargate_profile"
    },
    "AWS::EKS::Nodegroup": {
        "service": "AmazonEKS",
        "productFamily": "Node Group",
        "terraform_equivalent": "aws_eks_node_group"
    },
    
    # ElastiCache
    "AWS::ElastiCache::CacheCluster": {
        "service": "AmazonElastiCache",
        "productFamily": "Cache Instance",
        "terraform_equivalent": "aws_elasticache_cluster"
    },
    "AWS::ElastiCache::ReplicationGroup": {
        "service": "AmazonElastiCache",
        "productFamily": "Cache Instance",
        "terraform_equivalent": "aws_elasticache_replication_group"
    },
    
    # Elasticsearch
    "AWS::Elasticsearch::Domain": {
        "service": "AmazonES",
        "productFamily": "Search Instance",
        "terraform_equivalent": "aws_elasticsearch_domain"
    },
    
    # Elastic Beanstalk
    "AWS::ElasticBeanstalk::Environment": {
        "service": "AWSElasticBeanstalk",
        "productFamily": "Environment",
        "terraform_equivalent": "aws_elastic_beanstalk_environment"
    },
    
    # Elastic Load Balancing
    "AWS::ElasticLoadBalancing::LoadBalancer": {
        "service": "AWSELB",
        "productFamily": "Load Balancer",
        "terraform_equivalent": "aws_elb"
    },
    "AWS::ElasticLoadBalancingV2::LoadBalancer": {
        "service": "AWSELB",
        "productFamily": "Load Balancer",
        "terraform_equivalent": "aws_lb"
    },
    
    # EventBridge
    "AWS::Events::EventBus": {
        "service": "AmazonEventBridge",
        "productFamily": "Event Bus",
        "terraform_equivalent": "aws_cloudwatch_event_bus"
    },
    
    # FSx
    "AWS::FSx::FileSystem": {
        "service": "AmazonFSx",
        "productFamily": "File System",
        "terraform_equivalent": "aws_fsx_windows_file_system"
    },
    
    # Global Accelerator
    "AWS::GlobalAccelerator::Accelerator": {
        "service": "AWSGlobalAccelerator",
        "productFamily": "Accelerator",
        "terraform_equivalent": "aws_globalaccelerator_accelerator"
    },
    "AWS::GlobalAccelerator::EndpointGroup": {
        "service": "AWSGlobalAccelerator",
        "productFamily": "Endpoint Group",
        "terraform_equivalent": "aws_globalaccelerator_endpoint_group"
    },
    
    # Glue
    "AWS::Glue::Database": {
        "service": "AWSGlue",
        "productFamily": "Data Catalog",
        "terraform_equivalent": "aws_glue_catalog_database"
    },
    "AWS::Glue::Crawler": {
        "service": "AWSGlue",
        "productFamily": "Crawler",
        "terraform_equivalent": "aws_glue_crawler"
    },
    "AWS::Glue::Job": {
        "service": "AWSGlue",
        "productFamily": "Job",
        "terraform_equivalent": "aws_glue_job"
    },
    
    # KMS
    "AWS::KMS::Key": {
        "service": "awskms",
        "productFamily": "Key Management",
        "terraform_equivalent": "aws_kms_key"
    },
    
    # Kinesis
    "AWS::Kinesis::Stream": {
        "service": "AmazonKinesis",
        "productFamily": "Kinesis Streams",
        "terraform_equivalent": "aws_kinesis_stream"
    },
    "AWS::KinesisAnalytics::Application": {
        "service": "AmazonKinesis",
        "productFamily": "Kinesis Analytics",
        "terraform_equivalent": "aws_kinesis_analytics_application"
    },
    "AWS::KinesisFirehose::DeliveryStream": {
        "service": "AmazonKinesis",
        "productFamily": "Kinesis Firehose",
        "terraform_equivalent": "aws_kinesis_firehose_delivery_stream"
    },
    
    # Lambda
    "AWS::Lambda::Function": {
        "service": "AWSLambda",
        "productFamily": "Serverless Compute",
        "terraform_equivalent": "aws_lambda_function"
    },
    
    # Lightsail
    "AWS::Lightsail::Instance": {
        "service": "AmazonLightsail",
        "productFamily": "Instance",
        "terraform_equivalent": "aws_lightsail_instance"
    },
    
    # MSK (Managed Streaming for Apache Kafka)
    "AWS::MSK::Cluster": {
        "service": "AmazonMSK",
        "productFamily": "Kafka Cluster",
        "terraform_equivalent": "aws_msk_cluster"
    },
    
    # MWAA (Managed Workflows for Apache Airflow)
    "AWS::MWAA::Environment": {
        "service": "AmazonMWAA",
        "productFamily": "Airflow Environment",
        "terraform_equivalent": "aws_mwaa_environment"
    },
    
    # MQ
    "AWS::MQ::Broker": {
        "service": "AmazonMQ",
        "productFamily": "Message Broker",
        "terraform_equivalent": "aws_mq_broker"
    },
    
    # Neptune
    "AWS::Neptune::DBCluster": {
        "service": "AmazonNeptune",
        "productFamily": "Database Cluster",
        "terraform_equivalent": "aws_neptune_cluster"
    },
    "AWS::Neptune::DBInstance": {
        "service": "AmazonNeptune",
        "productFamily": "Database Instance",
        "terraform_equivalent": "aws_neptune_cluster_instance"
    },
    
    # Network Firewall
    "AWS::NetworkFirewall::Firewall": {
        "service": "AWSNetworkFirewall",
        "productFamily": "Firewall",
        "terraform_equivalent": "aws_networkfirewall_firewall"
    },
    
    # RDS
    "AWS::RDS::DBCluster": {
        "service": "AmazonRDS",
        "productFamily": "Database Cluster",
        "terraform_equivalent": "aws_rds_cluster"
    },
    "AWS::RDS::DBInstance": {
        "service": "AmazonRDS",
        "productFamily": "Database Instance",
        "terraform_equivalent": "aws_db_instance"
    },
    
    # Redshift
    "AWS::Redshift::Cluster": {
        "service": "AmazonRedshift",
        "productFamily": "Compute Instance",
        "terraform_equivalent": "aws_redshift_cluster"
    },
    
    # Route 53
    "AWS::Route53::RecordSet": {
        "service": "AmazonRoute53",
        "productFamily": "DNS Query",
        "terraform_equivalent": "aws_route53_record"
    },
    "AWS::Route53::HostedZone": {
        "service": "AmazonRoute53",
        "productFamily": "Hosted Zone",
        "terraform_equivalent": "aws_route53_zone"
    },
    "AWS::Route53Resolver::ResolverEndpoint": {
        "service": "AmazonRoute53",
        "productFamily": "Resolver Endpoint",
        "terraform_equivalent": "aws_route53_resolver_endpoint"
    },
    "AWS::Route53::HealthCheck": {
        "service": "AmazonRoute53",
        "productFamily": "Health Check",
        "terraform_equivalent": "aws_route53_health_check"
    },
    
    # S3
    "AWS::S3::Bucket": {
        "service": "AmazonS3",
        "productFamily": "Storage",
        "terraform_equivalent": "aws_s3_bucket"
    },
    
    # Secrets Manager
    "AWS::SecretsManager::Secret": {
        "service": "AWSSecretsManager",
        "productFamily": "Secret",
        "terraform_equivalent": "aws_secretsmanager_secret"
    },
    
    # SNS
    "AWS::SNS::Topic": {
        "service": "AmazonSNS",
        "productFamily": "Notification",
        "terraform_equivalent": "aws_sns_topic"
    },
    "AWS::SNS::Subscription": {
        "service": "AmazonSNS",
        "productFamily": "Notification",
        "terraform_equivalent": "aws_sns_topic_subscription"
    },
    
    # SQS
    "AWS::SQS::Queue": {
        "service": "AmazonSQS",
        "productFamily": "Queue",
        "terraform_equivalent": "aws_sqs_queue"
    },
    
    # SSM
    "AWS::SSM::Parameter": {
        "service": "AmazonSSM",
        "productFamily": "Parameter Store",
        "terraform_equivalent": "aws_ssm_parameter"
    },
    "AWS::SSM::Activation": {
        "service": "AmazonSSM",
        "productFamily": "Activation",
        "terraform_equivalent": "aws_ssm_activation"
    },
    
    # Step Functions
    "AWS::StepFunctions::StateMachine": {
        "service": "AWSStepFunctions",
        "productFamily": "State Machine",
        "terraform_equivalent": "aws_sfn_state_machine"
    },
    
    # Transfer Family
    "AWS::Transfer::Server": {
        "service": "AWSTransfer",
        "productFamily": "Transfer Server",
        "terraform_equivalent": "aws_transfer_server"
    },
    
    # VPC/Network
    "AWS::EC2::ClientVpnEndpoint": {
        "service": "AmazonVPC",
        "productFamily": "VPN Connection",
        "terraform_equivalent": "aws_ec2_client_vpn_endpoint"
    },
    "AWS::EC2::NatGateway": {
        "service": "AmazonVPC",
        "productFamily": "NAT Gateway",
        "terraform_equivalent": "aws_nat_gateway"
    },
    "AWS::EC2::VPNConnection": {
        "service": "AmazonVPC",
        "productFamily": "VPN Connection",
        "terraform_equivalent": "aws_vpn_connection"
    },
    "AWS::EC2::VPCEndpoint": {
        "service": "AmazonVPC",
        "productFamily": "VPC Endpoint",
        "terraform_equivalent": "aws_vpc_endpoint"
    },
    "AWS::EC2::TransitGateway": {
        "service": "AmazonVPC",
        "productFamily": "Transit Gateway",
        "terraform_equivalent": "aws_ec2_transit_gateway_peering_attachment"
    },
    "AWS::EC2::TransitGatewayVpcAttachment": {
        "service": "AmazonVPC",
        "productFamily": "Transit Gateway",
        "terraform_equivalent": "aws_ec2_transit_vpc_attachment"
    },
    
    # WAF
    "AWS::WAF::WebACL": {
        "service": "AWSWAF",
        "productFamily": "Web ACL",
        "terraform_equivalent": "aws_waf_web_acl"
    },
    "AWS::WAFv2::WebACL": {
        "service": "AWSWAF",
        "productFamily": "Web ACL",
        "terraform_equivalent": "aws_wafv2_web_acl"
    }
}

# Free resources that don't incur charges
FREE_RESOURCES: Set[str] = {
    # Access Analyzer
    "AWS::AccessAnalyzer::Analyzer",
    
    # ACM (Public certificates are free)
    "AWS::CertificateManager::Certificate",  # Note: Private certificates are paid
    
    # API Gateway (Configuration resources are free, usage is paid)
    "AWS::ApiGateway::Account",
    "AWS::ApiGateway::ApiKey",
    "AWS::ApiGateway::Authorizer",
    "AWS::ApiGateway::BasePathMapping",
    "AWS::ApiGateway::ClientCertificate",
    "AWS::ApiGateway::Deployment",
    "AWS::ApiGateway::DocumentationPart",
    "AWS::ApiGateway::DocumentationVersion",
    "AWS::ApiGateway::DomainName",
    "AWS::ApiGateway::GatewayResponse",
    "AWS::ApiGateway::Method",
    "AWS::ApiGateway::MethodResponse",
    "AWS::ApiGateway::Model",
    "AWS::ApiGateway::RequestValidator",
    "AWS::ApiGateway::Resource",
    "AWS::ApiGateway::UsagePlan",
    "AWS::ApiGateway::UsagePlanKey",
    "AWS::ApiGateway::VpcLink",
    
    # API Gateway V2
    "AWS::ApiGatewayV2::ApiMapping",
    "AWS::ApiGatewayV2::Authorizer",
    "AWS::ApiGatewayV2::Deployment",
    "AWS::ApiGatewayV2::DomainName",
    "AWS::ApiGatewayV2::Integration",
    "AWS::ApiGatewayV2::IntegrationResponse",
    "AWS::ApiGatewayV2::Model",
    "AWS::ApiGatewayV2::Route",
    "AWS::ApiGatewayV2::RouteResponse",
    "AWS::ApiGatewayV2::Stage",
    "AWS::ApiGatewayV2::VpcLink",
    
    # Application Auto Scaling
    "AWS::ApplicationAutoScaling::ScalingPolicy",
    
    # App Config
    "AWS::AppConfig::Extension",
    "AWS::AppConfig::ExtensionAssociation",
    "AWS::AppConfig::HostedConfigurationVersion",
    
    # App Flow
    "AWS::AppFlow::ConnectorProfile",
    
    # App Integrations
    "AWS::AppIntegrations::EventIntegration",
    
    # App Mesh
    "AWS::AppMesh::GatewayRoute",
    "AWS::AppMesh::Mesh",
    "AWS::AppMesh::Route",
    "AWS::AppMesh::VirtualGateway",
    "AWS::AppMesh::VirtualNode",
    "AWS::AppMesh::VirtualRouter",
    "AWS::AppMesh::VirtualService",
    
    # Auto Scaling
    "AWS::AutoScaling::LifecycleHook",
    "AWS::AutoScaling::NotificationConfiguration",
    "AWS::AutoScaling::ScalingPolicy",
    "AWS::AutoScaling::ScheduledAction",
    
    # Backup
    "AWS::Backup::BackupPlan",
    "AWS::Backup::BackupSelection",
    "AWS::Backup::BackupVaultNotifications",
    "AWS::Backup::BackupVaultPolicy",
    
    # CloudFormation
    "AWS::CloudFormation::Type",
    
    # CloudFront
    "AWS::CloudFront::OriginAccessIdentity",
    "AWS::CloudFront::PublicKey",
    
    # CloudWatch
    "AWS::Events::Rule",
    "AWS::Events::Target",
    "AWS::Logs::Destination",
    "AWS::Logs::DestinationPolicy",
    "AWS::Logs::LogStream",
    "AWS::Logs::MetricFilter",
    "AWS::Logs::ResourcePolicy",
    "AWS::Logs::SubscriptionFilter",
    
    # CodeBuild
    "AWS::CodeBuild::ReportGroup",
    "AWS::CodeBuild::SourceCredential",
    
    # Config
    "AWS::Config::AggregationAuthorization",
    "AWS::Config::ConfigurationAggregator",
    "AWS::Config::DeliveryChannel",
    "AWS::Config::RemediationConfiguration",
    
    # Direct Connect
    "AWS::DirectConnect::BGPPeer",
    "AWS::DirectConnect::CustomerGateway",
    "AWS::DirectConnect::DirectConnectGateway",
    "AWS::DirectConnect::DirectConnectGatewayAssociation",
    
    # DMS
    "AWS::DMS::ReplicationSubnetGroup",
    "AWS::DMS::ReplicationTask",
    
    # DocumentDB
    "AWS::DocDB::DBClusterParameterGroup",
    "AWS::DocDB::DBSubnetGroup",
    
    # DynamoDB
    "AWS::DynamoDB::Table",  # Table items are free, storage and throughput are paid
    
    # EBS
    "AWS::EC2::EBSEncryptionByDefault",
    
    # EC2
    "AWS::EC2::ClientVpnAuthorizationRule",
    "AWS::EC2::ClientVpnRoute",
    "AWS::EC2::CustomerGateway",
    "AWS::EC2::EgressOnlyInternetGateway",
    "AWS::EC2::FlowLog",
    "AWS::EC2::InternetGateway",
    "AWS::EC2::KeyPair",
    "AWS::EC2::NetworkAcl",
    "AWS::EC2::NetworkAclEntry",
    "AWS::EC2::NetworkInterface",
    "AWS::EC2::NetworkInterfaceAttachment",
    "AWS::EC2::PlacementGroup",
    "AWS::EC2::Route",
    "AWS::EC2::RouteTable",
    "AWS::EC2::SecurityGroup",
    "AWS::EC2::SecurityGroupEgress",
    "AWS::EC2::SecurityGroupIngress",
    "AWS::EC2::Subnet",
    "AWS::EC2::SubnetRouteTableAssociation",
    "AWS::EC2::TrafficMirrorFilter",
    "AWS::EC2::TrafficMirrorFilterRule",
    "AWS::EC2::TrafficMirrorTarget",
    "AWS::EC2::TransitGatewayRoute",
    "AWS::EC2::TransitGatewayRouteTable",
    "AWS::EC2::TransitGatewayRouteTableAssociation",
    "AWS::EC2::TransitGatewayRouteTablePropagation",
    "AWS::EC2::VPC",
    "AWS::EC2::VPCDHCPOptions",
    "AWS::EC2::VPCDHCPOptionsAssociation",
    "AWS::EC2::VPCEndpointConnectionNotification",
    "AWS::EC2::VPCEndpointRouteTableAssociation",
    "AWS::EC2::VPCEndpointService",
    "AWS::EC2::VPCEndpointServicePermissions",
    "AWS::EC2::VPCEndpointSubnetAssociation",
    "AWS::EC2::VPCGatewayAttachment",
    "AWS::EC2::VPCPeeringConnection",
    "AWS::EC2::VPNConnectionRoute",
    "AWS::EC2::VPNGateway",
    "AWS::EC2::VPNGatewayAttachment",
    "AWS::EC2::VPNGatewayRoutePropagation",
    "AWS::EC2::VolumeAttachment",
    
    # ECR
    "AWS::ECR::LifecyclePolicy",
    "AWS::ECR::RepositoryPolicy",
    
    # ECS
    "AWS::ECS::CapacityProvider",
    "AWS::ECS::Cluster",
    "AWS::ECS::TaskDefinition",
    
    # EFS
    "AWS::EFS::AccessPoint",
    "AWS::EFS::FileSystemPolicy",
    "AWS::EFS::MountTarget",
    
    # EIP
    "AWS::EC2::EIPAssociation",
    
    # EKS
    "AWS::EKS::Addon",
    "AWS::EKS::IdentityProviderConfig",
    
    # ElastiCache
    "AWS::ElastiCache::ParameterGroup",
    "AWS::ElastiCache::SecurityGroup",
    "AWS::ElastiCache::SubnetGroup",
    "AWS::ElastiCache::User",
    "AWS::ElastiCache::UserGroup",
    
    # Elasticsearch
    "AWS::Elasticsearch::DomainPolicy",
    
    # Elastic Beanstalk
    "AWS::ElasticBeanstalk::Application",
    
    # ELB
    "AWS::ElasticLoadBalancing::LoadBalancer",  # Attachments only
    "AWS::ElasticLoadBalancingV2::Listener",
    "AWS::ElasticLoadBalancingV2::ListenerCertificate",
    "AWS::ElasticLoadBalancingV2::ListenerRule",
    "AWS::ElasticLoadBalancingV2::TargetGroup",
    "AWS::ElasticLoadBalancingV2::TargetGroupBinding",
    
    # Glue
    "AWS::Glue::Classifier",
    "AWS::Glue::Connection",
    "AWS::Glue::DataCatalogEncryptionSettings",
    "AWS::Glue::Partition",
    "AWS::Glue::Registry",
    "AWS::Glue::Schema",
    "AWS::Glue::SecurityConfiguration",
    "AWS::Glue::Table",
    "AWS::Glue::Trigger",
    "AWS::Glue::UserDefinedFunction",
    "AWS::Glue::Workflow",
    
    # IAM
    "AWS::IAM::AccessKey",
    "AWS::IAM::AccountAlias",
    "AWS::IAM::AccountPasswordPolicy",
    "AWS::IAM::Group",
    "AWS::IAM::GroupPolicy",
    "AWS::IAM::InstanceProfile",
    "AWS::IAM::ManagedPolicy",
    "AWS::IAM::OIDCProvider",
    "AWS::IAM::Policy",
    "AWS::IAM::Role",
    "AWS::IAM::RolePolicy",
    "AWS::IAM::SAMLProvider",
    "AWS::IAM::ServerCertificate",
    "AWS::IAM::ServiceLinkedRole",
    "AWS::IAM::User",
    "AWS::IAM::UserPolicy",
    "AWS::IAM::UserToGroupAddition",
    
    # IoT
    "AWS::IoT::Policy",
    
    # KMS
    "AWS::KMS::Alias",
    
    # Lambda
    "AWS::Lambda::Alias",
    "AWS::Lambda::CodeSigningConfig",
    "AWS::Lambda::EventSourceMapping",
    "AWS::Lambda::LayerVersion",
    "AWS::Lambda::LayerVersionPermission",
    "AWS::Lambda::Permission",
    "AWS::Lambda::Version",
    
    # Launch Configuration/Template
    "AWS::AutoScaling::LaunchConfiguration",
    "AWS::EC2::LaunchTemplate",
    
    # Lightsail
    "AWS::Lightsail::Domain",
    "AWS::Lightsail::KeyPair",
    "AWS::Lightsail::StaticIp",
    "AWS::Lightsail::StaticIpAttachment",
    
    # MQ
    "AWS::MQ::Configuration",
    
    # MSK
    "AWS::MSK::Configuration",
    
    # Neptune
    "AWS::Neptune::DBClusterParameterGroup",
    "AWS::Neptune::DBParameterGroup",
    "AWS::Neptune::DBSubnetGroup",
    "AWS::Neptune::EventSubscription",
    
    # Network Firewall
    "AWS::NetworkFirewall::FirewallPolicy",
    "AWS::NetworkFirewall::LoggingConfiguration",
    "AWS::NetworkFirewall::RuleGroup",
    
    # RAM
    "AWS::RAM::PrincipalAssociation",
    "AWS::RAM::ResourceAssociation",
    "AWS::RAM::ResourceShare",
    
    # RDS
    "AWS::RDS::DBClusterParameterGroup",
    "AWS::RDS::DBParameterGroup",
    "AWS::RDS::DBSubnetGroup",
    "AWS::RDS::EventSubscription",
    "AWS::RDS::OptionGroup",
    
    # Resource Groups
    "AWS::ResourceGroups::Group",
    
    # Route 53
    "AWS::Route53Resolver::ResolverDNSSECConfig",
    "AWS::Route53Resolver::ResolverQueryLoggingConfig",
    "AWS::Route53Resolver::ResolverQueryLoggingConfigAssociation",
    "AWS::Route53Resolver::ResolverRule",
    "AWS::Route53Resolver::ResolverRuleAssociation",
    
    # S3
    "AWS::S3::AccessPoint",
    "AWS::S3::AccountPublicAccessBlock",
    "AWS::S3::BucketNotification",
    "AWS::S3::BucketPolicy",
    
    # Secrets Manager
    "AWS::SecretsManager::ResourcePolicy",
    "AWS::SecretsManager::RotationSchedule",
    "AWS::SecretsManager::SecretTargetAttachment",
    
    # Service Discovery
    "AWS::ServiceDiscovery::Service",
    
    # SES
    "AWS::SES::ConfigurationSet",
    "AWS::SES::ReceiptFilter",
    "AWS::SES::ReceiptRule",
    "AWS::SES::ReceiptRuleSet",
    
    # SNS
    "AWS::SNS::TopicPolicy",
    
    # SQS
    "AWS::SQS::QueuePolicy",
    
    # SSM
    "AWS::SSM::Association",
    "AWS::SSM::Document",
    "AWS::SSM::MaintenanceWindow",
    "AWS::SSM::MaintenanceWindowTarget",
    "AWS::SSM::MaintenanceWindowTask",
    "AWS::SSM::PatchBaseline",
    "AWS::SSM::ResourceDataSync",
    
    # Transfer
    "AWS::Transfer::Access",
    "AWS::Transfer::User",
    
    # WAF
    "AWS::WAF::ByteMatchSet",
    "AWS::WAF::GeoMatchSet",
    "AWS::WAF::IPSet",
    "AWS::WAF::RateBasedRule",
    "AWS::WAF::Rule",
    "AWS::WAF::RuleGroup",
    "AWS::WAF::SizeConstraintSet",
    "AWS::WAF::SqlInjectionMatchSet",
    "AWS::WAF::XssMatchSet",
    
    # WAFv2
    "AWS::WAFv2::IPSet",
    "AWS::WAFv2::RegexPatternSet",
    "AWS::WAFv2::RuleGroup",
    "AWS::WAFv2::WebACLAssociation",
    "AWS::WAFv2::WebACLLoggingConfiguration"
}

def get_paid_resources() -> Dict[str, Dict[str, str]]:
    """Get all paid resource mappings."""
    return PAID_RESOURCE_MAPPINGS

def get_free_resources() -> Set[str]:
    """Get all free resource types."""
    return FREE_RESOURCES

def is_paid_resource(resource_type: str) -> bool:
    """Check if a resource type is a paid resource."""
    return resource_type in PAID_RESOURCE_MAPPINGS

def is_free_resource(resource_type: str) -> bool:
    """Check if a resource type is a free resource."""
    return resource_type in FREE_RESOURCES

def get_resource_mapping(resource_type: str) -> Dict[str, str]:
    """Get the service mapping for a specific resource type."""
    return PAID_RESOURCE_MAPPINGS.get(resource_type, {}) 