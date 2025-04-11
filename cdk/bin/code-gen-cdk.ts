#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { CodeGenStack } from '../lib/code-gen-stack';

const app = new cdk.App();

// Get environment variables or use defaults
const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION || 'us-east-1'
};

// Get deployment ID from context or use default
const deploymentId = app.node.tryGetContext('deploymentId') || 'default';

new CodeGenStack(app, `CodeGenStack-${deploymentId}`, {
  env,
  description: `UI to Code Generator application stack - Deployment ID: ${deploymentId}`,
  stackName: `code-gen-stack-${deploymentId}`,
  terminationProtection: false,
});
