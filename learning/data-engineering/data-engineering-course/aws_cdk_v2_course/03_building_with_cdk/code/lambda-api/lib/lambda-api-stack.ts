import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigw from 'aws-cdk-lib/aws-apigateway';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as path from 'path';

/**
 * LambdaApiStack — minimal "API Gateway → Lambda" stack.
 *
 * Resources:
 *   - 1 S3 bucket (for the function code asset)
 *   - 1 Lambda function (Node 20, reads from the bucket)
 *   - 1 IAM role for the Lambda (auto-created by the L2 construct)
 *   - 1 API Gateway REST API (proxy integration to the Lambda)
 */
export class LambdaApiStack extends cdk.Stack {
  /** The Lambda function. */
  public readonly handler: lambda.Function;
  /** The API Gateway REST API. */
  public readonly api: apigw.RestApi;
  /** The S3 bucket the function code lives in. */
  public readonly assetsBucket: s3.Bucket;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ----- S3 bucket for the function code asset -----------------------
    this.assetsBucket = new s3.Bucket(this, 'AssetsBucket', {
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // ----- Lambda function ---------------------------------------------
    // We use `lambda.Code.fromInline` for the smallest possible demo
    // (no separate asset directory). In production, prefer
    // `lambda.Code.fromAsset(path.join(__dirname, '../lambda'))`.
    this.handler = new lambda.Function(this, 'HelloHandler', {
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'index.handler',
      code: lambda.Code.fromInline(`
        exports.handler = async (event) => ({
          statusCode: 200,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: 'Hello from CDK v2!',
            path: event.path,
            method: event.httpMethod,
          }),
        });
      `),
      memorySize: 256,
      timeout: cdk.Duration.seconds(10),
      environment: {
        BUCKET_NAME: this.assetsBucket.bucketName,
      },
    });

    // ----- Allow the Lambda to read its asset bucket --------------------
    this.assetsBucket.grantRead(this.handler);

    // ----- API Gateway REST API ----------------------------------------
    // `LambdaRestApi` is the L3 pattern: it gives you a proxy
    // integration for every path with one line of code.
    this.api = new apigw.LambdaRestApi(this, 'HelloApi', {
      handler: this.handler,
      restApiName: 'hello-api',
      description: 'Hello API served by the Lambda above',
      deployOptions: {
        stageName: 'prod',
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigw.Cors.ALL_ORIGINS,
        allowMethods: apigw.Cors.ALL_METHODS,
      },
    });

    // ----- Outputs -----------------------------------------------------
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: this.api.url,
      description: 'Invoke URL of the API Gateway stage',
    });
    new cdk.CfnOutput(this, 'FunctionName', {
      value: this.handler.functionName,
      description: 'Name of the Lambda function',
    });
    new cdk.CfnOutput(this, 'AssetsBucketName', {
      value: this.assetsBucket.bucketName,
      description: 'Name of the S3 bucket holding the function code',
    });
  }
}
