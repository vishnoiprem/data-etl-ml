#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { HelloCdkStack } from '../lib/hello-cdk-stack';

/**
 * CDK App entry point for the `hello-cdk` project.
 *
 * This is the *root* of the construct tree (see diagram
 * `diagrams/cdk_construct_tree.mmd`). The `App` is the only place where
 * the AWS account and region are bound to the stack via `env`.
 *
 * Run with:
 *     npx cdk synth
 *     npx cdk deploy
 *     npx cdk diff
 *     npx cdk destroy
 */
const app = new cdk.App();

new HelloCdkStack(app, 'HelloCdkStack', {
  // Use the AWS account/region from the CLI profile unless overridden
  // by `-c env=...` or environment variables.
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },

  // Stack-level tags applied to every resource in the stack.
  description: 'Minimal CDK v2 stack — 1 S3 bucket + CfnOutput (Section 2).',
  tags: {
    Project: 'hello-cdk',
    Course: 'aws-cdk-v2-crash-course',
  },
});
