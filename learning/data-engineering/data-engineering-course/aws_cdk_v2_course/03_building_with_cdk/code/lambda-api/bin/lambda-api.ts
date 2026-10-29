#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { LambdaApiStack } from '../lib/lambda-api-stack';

/**
 * CDK App entry point for the `lambda-api` project.
 *
 * Instantiates a single stack that wires together:
 *   - 1 Lambda function (Node 20, hello-world handler)
 *   - 1 API Gateway REST API (proxy integration to the Lambda)
 *   - 1 S3 bucket for the function's deployment asset
 *   - 1 IAM role for the Lambda (least-privilege)
 */
const app = new cdk.App();

new LambdaApiStack(app, 'LambdaApiStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
  description: 'CDK v2 — Lambda + API Gateway + S3 + IAM (Section 3).',
  tags: {
    Project: 'lambda-api',
    Course: 'aws-cdk-v2-crash-course',
  },
});
