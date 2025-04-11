# UI to Code Generator - CDK Deployment

This directory contains the AWS CDK code for deploying the UI to Code Generator application to AWS.

## Architecture

The deployment creates the following AWS resources:

- VPC with public and private subnets
- EC2 instances in an Auto Scaling Group (ASG)
- Application Load Balancer (ALB) with HTTPS support
- IAM roles with permissions to access AWS Bedrock
- Security groups following AWS best practices

## Prerequisites

- AWS CLI configured with appropriate credentials
- Node.js 14.x or later
- AWS CDK v2 installed globally (`npm install -g aws-cdk`)
- AWS account with access to Bedrock service

## Deployment Steps

1. Install dependencies:
   ```bash
   npm install
   ```

2. Build the CDK app:
   ```bash
   npm run build
   ```

3. Deploy the stack with a specific deployment ID:
   ```bash
   ./deploy.sh my-deployment-id
   ```

   If no deployment ID is provided, "default" will be used:
   ```bash
   ./deploy.sh
   ```

4. After deployment, the ALB DNS name will be displayed in the outputs.

## Multiple Deployments

This CDK project supports multiple deployments by using deployment IDs. Each deployment will have unique resource names based on the deployment ID, allowing you to deploy multiple instances of the application in the same AWS account.

To deploy multiple instances:

```bash
./deploy.sh deployment-1
./deploy.sh deployment-2
```

## Security Features

- EC2 instances are placed in private subnets
- ALB is the only entry point, placed in public subnets
- HTTPS is enforced with automatic HTTP to HTTPS redirection
- Security groups follow the principle of least privilege
- EC2 instances have only the necessary IAM permissions to call Bedrock APIs

## Customization

You can modify the following aspects of the deployment:

- EC2 instance type in `code-gen-stack.ts`
- Auto Scaling Group capacity settings
- VPC CIDR and subnet configuration
- Certificate domain name (currently using a self-signed certificate)

## Cleanup

To remove a specific deployment:

```bash
cdk destroy CodeGenStack-my-deployment-id
```
