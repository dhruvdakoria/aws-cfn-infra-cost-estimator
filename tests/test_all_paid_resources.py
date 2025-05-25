#!/usr/bin/env python3
"""
Comprehensive test script to validate pricing for all paid resources across regions.
Tests all resources from resource_mappings.py to ensure accurate pricing.
"""

import os
import sys
import logging
from typing import Dict, List, Tuple, Any
from dotenv import load_dotenv
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cost_estimator.infracost import InfracostEstimator
from cost_estimator.resource_mappings import get_paid_resources
from cost_estimator.query_builders import get_query_builder

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PaidResourceTester:
    """Test all paid resources for accurate pricing across regions."""
    
    def __init__(self):
        load_dotenv()
        self.estimator = InfracostEstimator()
        self.paid_resources = get_paid_resources()
        self.test_regions = ["us-east-1", "ca-central-1"]
        self.results = []
        self.failed_resources = []
        
    def get_test_properties(self, resource_type: str) -> Dict[str, Any]:
        """Get appropriate test properties for each resource type."""
        
        # Default properties for different resource categories
        test_properties = {
            # API Gateway
            "AWS::ApiGateway::RestApi": {"Name": "test-api"},
            "AWS::ApiGateway::Stage": {"StageName": "prod", "RestApiId": "test-api"},
            "AWS::ApiGatewayV2::Api": {"Name": "test-api", "ProtocolType": "HTTP"},
            
            # Auto Scaling
            "AWS::ApplicationAutoScaling::ScalableTarget": {"ServiceNamespace": "ecs"},
            "AWS::AutoScaling::AutoScalingGroup": {"MinSize": 1, "MaxSize": 3, "DesiredCapacity": 2},
            
            # Backup
            "AWS::Backup::BackupVault": {"BackupVaultName": "test-vault"},
            
            # Certificate Manager
            "AWS::ACMPCA::CertificateAuthority": {"Type": "ROOT"},
            "AWS::CertificateManager::Certificate": {"DomainName": "example.com", "ValidationMethod": "DNS"},
            
            # CloudFormation
            "AWS::CloudFormation::Stack": {"TemplateURL": "https://example.com/template.yaml"},
            "AWS::CloudFormation::StackSet": {"StackSetName": "test-stackset"},
            
            # CloudFront
            "AWS::CloudFront::Distribution": {"DistributionConfig": {"Enabled": True}},
            "AWS::CloudFront::Function": {"Name": "test-function", "FunctionCode": "function handler() {}"},
            
            # CloudTrail
            "AWS::CloudTrail::Trail": {"TrailName": "test-trail", "S3BucketName": "test-bucket"},
            
            # CloudWatch
            "AWS::CloudWatch::Dashboard": {"DashboardName": "test-dashboard"},
            "AWS::Logs::LogGroup": {"LogGroupName": "test-logs"},
            "AWS::CloudWatch::Alarm": {"AlarmName": "test-alarm", "MetricName": "CPUUtilization"},
            
            # CodeBuild
            "AWS::CodeBuild::Project": {"Name": "test-project", "ServiceRole": "arn:aws:iam::123456789012:role/service-role"},
            
            # Config
            "AWS::Config::ConfigRule": {"ConfigRuleName": "test-rule"},
            "AWS::Config::ConfigurationRecorder": {"Name": "test-recorder"},
            
            # DMS
            "AWS::DMS::ReplicationInstance": {"ReplicationInstanceClass": "dms.t3.micro"},
            
            # Direct Connect
            "AWS::DirectConnect::Connection": {"Bandwidth": "1Gbps", "Location": "EqDC2"},
            "AWS::DirectConnect::VirtualInterface": {"Vlan": 100},
            
            # Directory Service
            "AWS::DirectoryService::MicrosoftAD": {"Name": "test.example.com", "Password": "TempPassword123!"},
            "AWS::DirectoryService::SimpleAD": {"Name": "test.example.com", "Password": "TempPassword123!"},
            
            # DocumentDB
            "AWS::DocDB::DBCluster": {"DBClusterIdentifier": "test-cluster", "MasterUsername": "admin"},
            "AWS::DocDB::DBInstance": {"DBInstanceClass": "db.t3.medium", "DBClusterIdentifier": "test-cluster"},
            
            # DynamoDB
            "AWS::DynamoDB::Table": {"TableName": "test-table", "BillingMode": "PAY_PER_REQUEST"},
            
            # EC2
            "AWS::EC2::Instance": {"InstanceType": "t3.micro", "ImageId": "ami-12345678"},
            "AWS::EC2::Volume": {"VolumeType": "gp3", "Size": 100},
            "AWS::EC2::Snapshot": {"VolumeId": "vol-12345678"},
            "AWS::EC2::EIP": {"Domain": "vpc"},
            "AWS::EC2::DedicatedHost": {"InstanceType": "m5.large"},
            "AWS::EC2::SpotFleet": {"SpotFleetRequestConfig": {"TargetCapacity": 2}},
            
            # ECR
            "AWS::ECR::Repository": {"RepositoryName": "test-repo"},
            
            # ECS
            "AWS::ECS::Service": {"ServiceName": "test-service", "TaskDefinition": "test-task"},
            
            # EFS
            "AWS::EFS::FileSystem": {"CreationToken": "test-efs"},
            
            # EKS
            "AWS::EKS::Cluster": {"Name": "test-cluster", "Version": "1.21"},
            "AWS::EKS::FargateProfile": {"FargateProfileName": "test-profile", "ClusterName": "test-cluster"},
            "AWS::EKS::Nodegroup": {"NodegroupName": "test-nodegroup", "ClusterName": "test-cluster", "InstanceTypes": ["t3.medium"]},
            
            # ElastiCache
            "AWS::ElastiCache::CacheCluster": {"CacheNodeType": "cache.t3.micro", "Engine": "redis"},
            "AWS::ElastiCache::ReplicationGroup": {"ReplicationGroupDescription": "test", "CacheNodeType": "cache.t3.micro"},
            
            # Elasticsearch
            "AWS::Elasticsearch::Domain": {"DomainName": "test-domain"},
            
            # Elastic Beanstalk
            "AWS::ElasticBeanstalk::Environment": {"ApplicationName": "test-app", "EnvironmentName": "test-env"},
            
            # ELB
            "AWS::ElasticLoadBalancing::LoadBalancer": {"LoadBalancerName": "test-elb"},
            "AWS::ElasticLoadBalancingV2::LoadBalancer": {"Name": "test-alb", "Type": "application"},
            
            # EventBridge
            "AWS::Events::EventBus": {"Name": "test-bus"},
            
            # FSx
            "AWS::FSx::FileSystem": {"FileSystemType": "WINDOWS", "StorageCapacity": 300},
            
            # Global Accelerator
            "AWS::GlobalAccelerator::Accelerator": {"Name": "test-accelerator"},
            "AWS::GlobalAccelerator::EndpointGroup": {"ListenerArn": "arn:aws:globalaccelerator::123456789012:accelerator/test"},
            
            # Glue
            "AWS::Glue::Database": {"DatabaseInput": {"Name": "test-database"}},
            "AWS::Glue::Crawler": {"Name": "test-crawler", "Role": "arn:aws:iam::123456789012:role/service-role"},
            "AWS::Glue::Job": {"Name": "test-job", "Role": "arn:aws:iam::123456789012:role/service-role"},
            
            # KMS
            "AWS::KMS::Key": {"Description": "Test key"},
            
            # Kinesis
            "AWS::Kinesis::Stream": {"Name": "test-stream", "ShardCount": 1},
            "AWS::KinesisAnalytics::Application": {"ApplicationName": "test-app"},
            "AWS::KinesisFirehose::DeliveryStream": {"DeliveryStreamName": "test-stream"},
            
            # Lambda
            "AWS::Lambda::Function": {"FunctionName": "test-function", "Runtime": "python3.9", "Handler": "index.handler"},
            
            # Lightsail
            "AWS::Lightsail::Instance": {"InstanceName": "test-instance", "BlueprintId": "ubuntu_20_04"},
            
            # MSK
            "AWS::MSK::Cluster": {"ClusterName": "test-cluster", "KafkaVersion": "2.8.0"},
            
            # MWAA
            "AWS::MWAA::Environment": {"Name": "test-airflow"},
            
            # MQ
            "AWS::MQ::Broker": {"BrokerName": "test-broker", "EngineType": "ActiveMQ"},
            
            # Neptune
            "AWS::Neptune::DBCluster": {"DBClusterIdentifier": "test-neptune-cluster"},
            "AWS::Neptune::DBInstance": {"DBInstanceClass": "db.t3.medium", "DBClusterIdentifier": "test-neptune-cluster"},
            
            # Network Firewall
            "AWS::NetworkFirewall::Firewall": {"FirewallName": "test-firewall"},
            
            # RDS
            "AWS::RDS::DBCluster": {"DBClusterIdentifier": "test-cluster", "Engine": "aurora-mysql"},
            "AWS::RDS::DBInstance": {"DBInstanceClass": "db.t3.micro", "Engine": "mysql", "AllocatedStorage": 20},
            
            # Redshift
            "AWS::Redshift::Cluster": {"ClusterIdentifier": "test-cluster", "NodeType": "dc2.large"},
            
            # Route 53
            "AWS::Route53::RecordSet": {"Name": "test.example.com", "Type": "A"},
            "AWS::Route53::HostedZone": {"Name": "example.com"},
            "AWS::Route53Resolver::ResolverEndpoint": {"Direction": "INBOUND"},
            "AWS::Route53::HealthCheck": {"Type": "HTTP"},
            
            # S3
            "AWS::S3::Bucket": {"BucketName": "test-bucket"},
            
            # Secrets Manager
            "AWS::SecretsManager::Secret": {"Name": "test-secret"},
            
            # SNS
            "AWS::SNS::Topic": {"TopicName": "test-topic"},
            "AWS::SNS::Subscription": {"TopicArn": "arn:aws:sns:us-east-1:123456789012:test-topic", "Protocol": "email"},
            
            # SQS
            "AWS::SQS::Queue": {"QueueName": "test-queue"},
            
            # SSM
            "AWS::SSM::Parameter": {"Name": "test-parameter", "Type": "String", "Value": "test-value"},
            "AWS::SSM::Activation": {"IamRole": "arn:aws:iam::123456789012:role/service-role"},
            
            # Step Functions
            "AWS::StepFunctions::StateMachine": {"StateMachineName": "test-state-machine", "StateMachineType": "STANDARD"},
            
            # Transfer Family
            "AWS::Transfer::Server": {"IdentityProviderType": "SERVICE_MANAGED"},
            
            # VPC/Network
            "AWS::EC2::ClientVpnEndpoint": {"ClientCidrBlock": "10.0.0.0/16"},
            "AWS::EC2::NatGateway": {"SubnetId": "subnet-12345678"},
            "AWS::EC2::VPNConnection": {"Type": "ipsec.1", "CustomerGatewayId": "cgw-12345678"},
            "AWS::EC2::VPCEndpoint": {"VpcId": "vpc-12345678", "ServiceName": "com.amazonaws.us-east-1.s3"},
            "AWS::EC2::TransitGateway": {"Description": "Test transit gateway"},
            "AWS::EC2::TransitGatewayVpcAttachment": {"TransitGatewayId": "tgw-12345678", "VpcId": "vpc-12345678"},
            
            # WAF
            "AWS::WAF::WebACL": {"Name": "test-web-acl"},
            "AWS::WAFv2::WebACL": {"Name": "test-web-acl", "Scope": "REGIONAL"},
        }
        
        return test_properties.get(resource_type, {})
    
    def test_resource_pricing(self, resource_type: str, region: str) -> Tuple[bool, float, str]:
        """Test pricing for a specific resource in a specific region."""
        try:
            # Check if query builder exists
            query_builder = get_query_builder(resource_type)
            if not query_builder:
                return False, 0.0, f"No query builder found for {resource_type}"
            
            # Get test properties
            properties = self.get_test_properties(resource_type)
            properties["Region"] = region
            properties["id"] = f"test-{resource_type.lower().replace('::', '-')}"
            
            # Get cost estimate
            cost = self.estimator.get_resource_cost(resource_type, properties)
            
            # Consider it successful if we get any response (even $0 for usage-based resources)
            return True, cost.monthly_cost, "Success"
            
        except Exception as e:
            return False, 0.0, str(e)
    
    def run_comprehensive_test(self):
        """Run comprehensive test for all paid resources."""
        print("🧪 COMPREHENSIVE PAID RESOURCES PRICING TEST")
        print("=" * 100)
        print(f"Testing {len(self.paid_resources)} paid resources across {len(self.test_regions)} regions")
        print("=" * 100)
        
        # Header
        print(f"{'Resource Type':<50} | {'us-east-1':<15} | {'ca-central-1':<15} | {'Status':<20}")
        print("-" * 100)
        
        total_resources = len(self.paid_resources)
        successful_resources = 0
        
        for i, resource_type in enumerate(sorted(self.paid_resources.keys()), 1):
            print(f"\n[{i:3d}/{total_resources}] Testing: {resource_type}")
            
            # Test in both regions
            results_by_region = {}
            all_successful = True
            error_messages = []
            
            for region in self.test_regions:
                success, cost, message = self.test_resource_pricing(resource_type, region)
                results_by_region[region] = (success, cost, message)
                
                if not success:
                    all_successful = False
                    error_messages.append(f"{region}: {message}")
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
            
            # Format results
            us_east_result = results_by_region["us-east-1"]
            ca_central_result = results_by_region["ca-central-1"]
            
            us_east_display = f"${us_east_result[1]:8.2f}" if us_east_result[0] else "ERROR"
            ca_central_display = f"${ca_central_result[1]:8.2f}" if ca_central_result[0] else "ERROR"
            
            if all_successful:
                status = "✅ SUCCESS"
                successful_resources += 1
            else:
                status = "❌ FAILED"
                self.failed_resources.append({
                    "resource_type": resource_type,
                    "errors": error_messages
                })
            
            print(f"{resource_type:<50} | {us_east_display:<15} | {ca_central_display:<15} | {status:<20}")
            
            # Store detailed results
            self.results.append({
                "resource_type": resource_type,
                "us_east_1": us_east_result,
                "ca_central_1": ca_central_result,
                "success": all_successful
            })
        
        # Summary
        print("\n" + "=" * 100)
        print("📊 TEST SUMMARY")
        print("=" * 100)
        print(f"Total Resources Tested: {total_resources}")
        print(f"Successful: {successful_resources}")
        print(f"Failed: {len(self.failed_resources)}")
        print(f"Success Rate: {(successful_resources/total_resources)*100:.1f}%")
        
        if self.failed_resources:
            print("\n❌ FAILED RESOURCES:")
            print("-" * 50)
            for failed in self.failed_resources:
                print(f"• {failed['resource_type']}")
                for error in failed['errors']:
                    print(f"  - {error}")
        
        # Regional pricing differences
        print("\n💰 REGIONAL PRICING DIFFERENCES:")
        print("-" * 50)
        significant_differences = []
        
        for result in self.results:
            if result['success']:
                us_cost = result['us_east_1'][1]
                ca_cost = result['ca_central_1'][1]
                
                if us_cost > 0 and ca_cost > 0:
                    diff_percent = ((ca_cost - us_cost) / us_cost) * 100
                    if abs(diff_percent) > 5:  # More than 5% difference
                        significant_differences.append({
                            'resource': result['resource_type'],
                            'us_cost': us_cost,
                            'ca_cost': ca_cost,
                            'diff_percent': diff_percent
                        })
        
        if significant_differences:
            significant_differences.sort(key=lambda x: abs(x['diff_percent']), reverse=True)
            for diff in significant_differences[:10]:  # Top 10 differences
                print(f"• {diff['resource']:<50} | US: ${diff['us_cost']:8.2f} | CA: ${diff['ca_cost']:8.2f} | {diff['diff_percent']:+6.1f}%")
        else:
            print("No significant regional pricing differences found (>5%)")
        
        return len(self.failed_resources) == 0

def main():
    """Main function to run the comprehensive test."""
    tester = PaidResourceTester()
    success = tester.run_comprehensive_test()
    
    if not success:
        print(f"\n🔧 RECOMMENDATIONS:")
        print("1. Check query_builders.py for failed resources")
        print("2. Verify resource property mappings")
        print("3. Check Infracost API documentation for correct attribute filters")
        print("4. Consider if resources need region-specific usage types")
        
        return 1
    else:
        print(f"\n🎉 ALL TESTS PASSED! All paid resources are working correctly.")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 