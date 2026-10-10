#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { AppSyncSfnStack } from '../lib/app-sync-sfn-stack';

/**
 * CDK App entry point for the `app-sync-sfn` project.
 *
 * Instantiates a single stack that wires together:
 *   - 1 AppSync GraphQL API (schema-as-code)
 *   - 1 Lambda function (the GraphQL resolver)
 *   - 1 Step Functions state machine (orchestrates the workflow)
 */
const app = new cdk.App();

new AppSyncSfnStack(app, 'AppSyncSfnStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
  description: 'CDK v2 — AppSync + Step Functions + Lambda (Section 4).',
  tags: {
    Project: 'app-sync-sfn',
    Course: 'aws-cdk-v2-crash-course',
  },
});
