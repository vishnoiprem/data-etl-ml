import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';

/**
 * HelloCdkStack — the simplest possible useful CDK v2 stack.
 *
 * It provisions:
 *   - 1 S3 bucket (private, versioned, with public-access block on)
 *   - 1 CfnOutput that exports the bucket name
 *
 * This is the L1/L2 split illustrated in lecture L06:
 *   - We *could* write `new s3.CfnBucket(this, 'Bucket', { ... })` (L1)
 *   - We *instead* write `new s3.Bucket(this, 'Bucket', { ... })` (L2)
 *   The L2 form is one line shorter and gives us sane defaults
 *   (encryption, public-access block) for free.
 */
export class HelloCdkStack extends cdk.Stack {
  /** The bucket this stack creates. Exposed so other stacks (or tests) can use it. */
  public readonly bucket: s3.Bucket;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ----- L2 construct: s3.Bucket --------------------------------------
    this.bucket = new s3.Bucket(this, 'HelloBucket', {
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // for demo only; use RETAIN in prod
      autoDeleteObjects: true,                   // for demo only
    });

    // ----- CfnOutput ----------------------------------------------------
    // The `description` shows up in the CloudFormation console; the
    // `exportName` would let another stack import this value by name.
    new cdk.CfnOutput(this, 'BucketName', {
      value: this.bucket.bucketName,
      description: 'Name of the S3 bucket created by HelloCdkStack',
      exportName: `${id}-BucketName`,
    });
  }
}
