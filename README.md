# AWS CloudFormation Cost Estimator

A comprehensive Python-based solution to estimate costs of AWS CloudFormation stacks using the Infracost API, with support for all AWS resources documented by Infracost.

## 🚀 Features

- **Comprehensive Resource Support**: Supports 88 paid AWS resources (100% coverage) and 247+ free resources
- **Accurate Pricing**: Fixed query builders for all major AWS services with correct attribute filters
- **Dynamic Pricing**: Real-time pricing fetched from Infracost API for usage-based resources
- **Cost Breakdown Tables**: Clean, formatted cost breakdown tables for easy analysis
- **Template Comparison**: Compare costs between different CloudFormation templates
- **Single Template Analysis**: Analyze costs for new deployments (same template for old and new)
- **Modular Architecture**: Clean separation of concerns with dedicated modules for resource mappings, query builders, and cost estimation
- **Infracost API Integration**: Primary cost estimation using Infracost GraphQL API with optimized queries
- **AWS Pricing API Fallback**: Secondary cost estimation using AWS Pricing API
- **CloudFormation Template Parsing**: Full support for YAML and JSON CloudFormation templates
- **Detailed Cost Breakdown**: Resource-level cost analysis with hourly and monthly estimates
- **Free Resource Detection**: Automatic identification of free AWS resources
- **GitHub Actions Ready**: Built for CI/CD integration

## 🔧 Recent Improvements

### Cost Breakdown Tables (v4.0) 📊

**MAJOR UPDATE**: Complete redesign of output formatting with clean, professional cost breakdown tables.

**✅ NEW FEATURES**:
- **Clean Table Format**: Professional grid-based tables with clear cost information
- **Single Template Analysis**: Pass the same template twice to analyze new deployment costs
- **Cost Comparison**: Compare costs between different templates with impact analysis
- **Smart Resource Grouping**: Paid resources first, then usage-based, then free resources
- **Reduced Logging**: Clean output without verbose logging messages
- **Multiple Output Formats**: Table (default), GitHub comment, or full report formats

**📊 Example Usage**:
```bash
# Analyze costs for a new deployment
python3 src/main.py template.yaml template.yaml

# Compare costs between templates
python3 src/main.py old-template.yaml new-template.yaml

# Generate GitHub comment format
python3 src/main.py old.yaml new.yaml github
```

### Dynamic Pricing Revolution (v3.0) 🎯

**MAJOR UPDATE**: Completely redesigned how usage-based pricing is displayed and explained.

**❌ BEFORE**: Confusing $0.00 values for paid resources
```
SNS Topic: $0.00/month (misleading!)
KMS Key: $0.00/month (confusing!)
API Gateway: $0.00/month (unclear!)
VPC: Usage-based (wrong for free resources!)
```

**✅ AFTER**: Clear, informative pricing with detailed explanations
```
📊 SNS Topic: Usage-based - $0.50 per 1M requests + notification costs
💰 KMS Key: $1.00/month per key + $0.03 per 10K requests  
📊 API Gateway: Usage-based - $3.50 per 1M requests + data transfer
🆓 VPC: Free - This resource is free to use
```

### Key Improvements:

- **🎯 Smart Pricing Models**: Distinguishes between fixed, usage-based, and free resources
- **📊 Detailed Usage Information**: Shows actual pricing structure for usage-based resources
- **💡 Meaningful Cost Display**: Free resources show "Free", usage-based show "Usage-based" with details
- **🔄 Dynamic Pricing**: Real-time pricing fetched from Infracost API instead of hardcoded values
- **📈 Usage Estimation**: Provides estimated costs based on typical usage patterns
- **🎨 Better Visual Indicators**: Clear emojis and formatting for different pricing models
- **💾 Comprehensive Database**: JSON export of all 335 resources with pricing in multiple regions

## 📁 Project Structure

```
.
├── src/
│   ├── cost_estimator/
│   │   ├── __init__.py
│   │   ├── core.py                 # Core cost calculation interfaces
│   │   ├── infracost.py            # Infracost API integration
│   │   ├── aws_pricing.py          # AWS Pricing API integration
│   │   ├── resource_mappings.py    # Terraform to CloudFormation mappings
│   │   ├── query_builders.py       # GraphQL query builders by service
│   │   ├── pricing_models.py       # Pricing model definitions (no hardcoded values)
│   │   └── dynamic_pricing.py      # Real-time pricing fetcher
│   ├── stack_analyzer/
│   │   ├── __init__.py
│   │   ├── parser.py               # CloudFormation template parsing
│   │   └── diff.py                 # Stack diff analysis
│   └── formatter/
│       ├── __init__.py
│       └── output.py               # Output formatting with table support
├── templates/
│   ├── comprehensive-test-stack.yaml   # Basic test template
│   └── all-paid-resources-test.yaml    # Comprehensive paid resources test
├── tests/
|   ├── test_cost_estimation.py        # Comprehensive test suite
├── requirements.txt
└── README.md
```

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/aws-cfn-infra-cost-estimator.git
   cd aws-cfn-infra-cost-estimator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   # Required for Infracost API
   export INFRACOST_API_KEY="ico-your-api-key-here"
   
   # Optional: AWS credentials for AWS Pricing API fallback
   export AWS_ACCESS_KEY_ID="your-access-key"
   export AWS_SECRET_ACCESS_KEY="your-secret-key"
   export AWS_DEFAULT_REGION="us-east-1"
   ```

## 🔧 Usage

### Command Line Usage

```bash
# Analyze costs for a new deployment (same template for both parameters)
python3 src/main.py template.yaml template.yaml

# Compare costs between different templates
python3 src/main.py old-template.yaml new-template.yaml

# Generate different output formats
python3 src/main.py old.yaml new.yaml table    # Default: clean table format
python3 src/main.py old.yaml new.yaml github   # GitHub comment format
python3 src/main.py old.yaml new.yaml full     # Full detailed report
```

### Example Output

**Single Template Analysis:**
```
# 💰 CloudFormation Stack Cost Breakdown
============================================================

## 📊 Cost Summary
💰 Fixed Monthly Cost: $109.94
⏰ Fixed Hourly Cost: $0.1506
📊 Usage-Based Resources: 3 (costs depend on usage)
🆓 Free Resources: 19
💵 Paid Resources: 4

## 📋 Detailed Resource Breakdown
+----------------------------------------+-------------------------+----------------+
| Resource Type                          | Resource ID             | Monthly Cost   |
+========================================+=========================+================+
| 💰 EC2::Instance                        | WebServer               | $8.47/month    |
| 💰 RDS::DBInstance                      | Database                | $24.82/month   |
| 📊 S3::Bucket                           | DataBucket              | Usage-based    |
| 🆓 EC2::VPC                             | VPC                     | Free           |
+----------------------------------------+-------------------------+----------------+
```

**Template Comparison:**
```
# 💰 CloudFormation Stack Cost Comparison
============================================================

## 📊 Cost Impact Summary
💵 Current Monthly Cost: $109.94
💰 New Monthly Cost: $449.97
📈 Monthly Cost INCREASE: $+340.03 (+309.3%)

## 🔄 Resource Changes Summary
➕ Added: 25 resources
❌ Removed: 0 resources
🔄 Modified: 0 resources
```

### Programmatic Usage

```python
from src.main import CostEstimator

# Initialize the cost estimator
estimator = CostEstimator()

# Read template files
with open('old-template.yaml', 'r') as f:
    old_template = f.read()
with open('new-template.yaml', 'r') as f:
    new_template = f.read()

# Generate cost report
report = estimator.estimate_costs(old_template, new_template, "table")
print(report)
```

## 📊 Supported AWS Resources

### Paid Resources (88 types)

The estimator supports all major AWS services with cost implications:

- **Compute**: EC2 Instances, Auto Scaling Groups, ECS Services, EKS Clusters, Lambda Functions
- **Storage**: EBS Volumes, S3 Buckets, EFS File Systems
- **Database**: RDS Instances/Clusters, DynamoDB Tables, ElastiCache, Redshift, Neptune
- **Networking**: Load Balancers, NAT Gateways, VPN Connections, Direct Connect
- **Security**: KMS Keys, Secrets Manager, Certificate Manager (Private CAs)
- **Analytics**: Kinesis Streams, Glue Jobs, CloudWatch Logs/Dashboards
- **Integration**: SNS Topics, SQS Queues, API Gateway, Step Functions
- **And many more...**

### Free Resources (247 types)

Automatically identifies free AWS resources including:

- **IAM**: Roles, Policies, Users, Groups
- **VPC**: Subnets, Security Groups, Route Tables, Internet Gateways
- **Configuration**: CloudFormation metadata, Lambda permissions, S3 bucket policies
- **And many more...**

## 🧪 Testing

The project includes a comprehensive test suite that validates:

1. **Resource Mappings**: Terraform to CloudFormation resource type mappings
2. **Query Builders**: GraphQL query generation for different AWS services
3. **Infracost Integration**: API connectivity and response parsing
4. **CloudFormation Parsing**: Template parsing with intrinsic functions
5. **End-to-End Workflow**: Complete cost estimation pipeline
6. **Dynamic Pricing**: Real-time pricing fetcher validation
7. **Output Formatting**: Table generation and formatting

Run tests:
```bash
python3 tests/test_cost_estimation.py
```

Expected output:
```
🚀 Starting AWS CloudFormation Cost Estimation Tests
✅ Resource Mappings PASSED
✅ Query Builders PASSED  
✅ Infracost Estimator PASSED
✅ CloudFormation Parsing PASSED
✅ End-to-End PASSED
🎉 All tests passed!
```

## 📋 Test Templates

The project includes comprehensive test templates:

- **`comprehensive-test-stack.yaml`**: Basic multi-tier web application
- **`all-paid-resources-test.yaml`**: Comprehensive test with 40+ paid resources

## 🔑 API Keys

### Infracost API Key

1. Sign up at [Infracost](https://www.infracost.io/)
2. Get your API key (starts with `ico-`)
3. Set environment variable: `INFRACOST_API_KEY=ico-your-key`

### AWS Credentials (Optional)

For AWS Pricing API fallback:
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

## 🚀 GitHub Actions Integration

Example workflow for automated cost analysis:

```yaml
name: Cost Analysis
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  cost-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          
      - name: Install dependencies
        run: pip install -r requirements.txt
        
      - name: Run cost analysis
        env:
          INFRACOST_API_KEY: ${{ secrets.INFRACOST_API_KEY }}
        run: |
          python3 src/main.py old-template.yaml new-template.yaml github
```

## 🔧 Troubleshooting

### Understanding Pricing Results

**Understanding Pricing Models:**

The cost estimator clearly distinguishes between different pricing models:

- **Fixed Pricing** 💰: Resources with predictable hourly/monthly costs (EC2, RDS, etc.)
- **Usage-Based Pricing** 📊: Resources that charge based on actual usage
  - **SNS Topics**: Per request + notification delivery costs
  - **SQS Queues**: Per request with free tier
  - **KMS Keys**: Per key per month + per request charges
  - **API Gateway**: Per request + data transfer
  - **Lambda**: Per request + per GB-second
- **Free Resources** 🆓: No direct charges (IAM roles, VPC components, etc.)

### Common Issues

**"No products found" errors:**
- Verify your Infracost API key is valid
- Check if the resource type is supported
- Ensure the region is correctly specified

**Connection timeouts:**
- Check your internet connection
- Verify Infracost API is accessible
- Try increasing timeout values

**Incorrect pricing:**
- Verify resource properties match AWS specifications
- Check if you're using the correct region
- Some resources may have minimum billing requirements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and add tests
4. Run the test suite: `python3 tests/test_cost_estimation.py`
5. Commit your changes: `git commit -am 'Add new feature'`
6. Push to the branch: `git push origin feature/new-feature`
7. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Infracost](https://www.infracost.io/) for providing the cost estimation API
- AWS for comprehensive pricing data
- The CloudFormation community for template examples and best practices

## 📞 Support

- Create an issue for bug reports or feature requests
- Check the [Infracost documentation](https://www.infracost.io/docs/) for API details
- Review the test suite for usage examples 