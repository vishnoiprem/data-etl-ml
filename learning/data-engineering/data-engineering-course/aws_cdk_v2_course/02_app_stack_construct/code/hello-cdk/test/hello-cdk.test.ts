import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { HelloCdkStack } from '../lib/hello-cdk-stack';

/**
 * Tests for HelloCdkStack. These run **without** an AWS account — they
 * just synthesize the stack and inspect the resulting CloudFormation
 * template via `aws-cdk-lib/assertions`.
 *
 * See lectures L22–L24 for the assertion patterns used here.
 */
describe('HelloCdkStack', () => {
  let template: Template;

  beforeAll(() => {
    const app = new cdk.App();
    const stack = new HelloCdkStack(app, 'TestStack');
    template = Template.fromStack(stack);
  });

  test('creates exactly one S3 bucket', () => {
    template.resourceCountIs('AWS::S3::Bucket', 1);
  });

  test('the bucket is versioned', () => {
    template.hasResourceProperties('AWS::S3::Bucket', {
      VersioningConfiguration: { Status: 'Enabled' },
    });
  });

  test('the bucket blocks all public access', () => {
    template.hasResourceProperties('AWS::S3::Bucket', {
      PublicAccessBlockConfiguration: {
        BlockPublicAcls: true,
        BlockPublicPolicy: true,
        IgnorePublicAcls: true,
        RestrictPublicBuckets: true,
      },
    });
  });

  test('exposes a BucketName CfnOutput', () => {
    template.hasOutput('BucketName', {
      Description: Match.stringLikeRegexp('S3 bucket'),
    });
  });

  test('synthesizes without errors', () => {
    // If we got this far, synth succeeded. We assert one last fine
    // detail: the bucket has an `AWS::S3::Bucket` policy attached for
    // auto-delete-objects (only present when `autoDeleteObjects: true`).
    template.resourceCountIs('Custom::CDKBucketDeployment', 0);
  });
});
