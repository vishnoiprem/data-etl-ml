#!/usr/bin/env node
import 'source-map-support/register';
import { App, DefaultStackSynthesizer } from 'aws-cdk-lib';
import { ServerlessStack } from '../lib/serverless-stack';

/**
 * The CDK application entry point.
 *
 * Instantiates a single stack. Environment defaults to whatever the AWS CLI
 * credentials + region resolve to (typically `us-east-1`). Override by
 * passing `--context env=...` or by setting `CDK_DEFAULT_ACCOUNT` /
 * `CDK_DEFAULT_REGION` environment variables.
 */
const app = new App();

new ServerlessStack(app, 'ServerlessStack', {
  // Use the default CDK synthesizer (asset bucket + roles created by
  // `cdk bootstrap`).
  synthesizer: new DefaultStackSynthesizer(),

  // Description shown in the CloudFormation console.
  description: 'Serverless Use Case 2 (API Gateway + Lambda + S3) via AWS CDK v2.',

  // Tags applied to every taggable resource in the stack.
  tags: {
    Project: 'aws-lambda-course',
    Section: '12-cdk-v2-serverless',
    ManagedBy: 'cdk',
  },
});
