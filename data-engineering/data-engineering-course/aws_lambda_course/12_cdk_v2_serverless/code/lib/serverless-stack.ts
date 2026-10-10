import { join } from 'path';
import { CfnOutput, Duration, RemovalPolicy, Stack, StackProps } from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

/**
 * The complete serverless CRUD stack.
 *
 * Resources:
 *   - 1 S3 bucket (versioned + SSE-S3, public access blocked)
 *   - 1 IAM role assumed by both Lambdas (least-privilege S3 Get/Put)
 *   - 2 Lambda functions (Node 20, 256 MB, 30 s)
 *   - 1 REST API (API Gateway) with GET + PUT on /objects/{key}
 */
export class ServerlessStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    // --------------------------------------------------------------
    // S3 bucket — versioned + encrypted, public access blocked
    // --------------------------------------------------------------
    const objectsBucket = new s3.Bucket(this, 'ObjectsBucket', {
      bucketName: `serverless-objects-${this.account}-${this.region}`,

      // Keep every prior version of an object.
      versioned: true,

      // SSE-S3 (AES-256). Free, no KMS permissions required.
      encryption: s3.BucketEncryption.S3_MANAGED,

      // Defense in depth: refuse any public ACL or public policy.
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,

      // Enforce TLS on every request.
      enforceSSL: true,

      // Empty the bucket before destroying the stack.
      autoDeleteObjects: true,

      // Delete the bucket itself on stack destroy.
      removalPolicy: RemovalPolicy.DESTROY,
    });

    new CfnOutput(this, 'ObjectsBucketName', {
      value: objectsBucket.bucketName,
      description: 'Name of the S3 bucket that holds objects',
      exportName: 'ServerlessObjectsBucketName',
    });

    // --------------------------------------------------------------
    // IAM role — assumed by both Lambdas
    // --------------------------------------------------------------
    const lambdaExecutionRole = new iam.Role(this, 'LambdaExecutionRole', {
      roleName: 'ServerlessStack-LambdaExecutionRole',
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Execution role for the get-object and put-object Lambdas.',

      // Inline policy = least privilege, co-located with the role.
      inlinePolicies: {
        S3ObjectsAccess: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: ['s3:GetObject', 's3:PutObject'],
              // Scope to the bucket we just created. Never use '*' here.
              resources: [objectsBucket.arnForObjects('*')],
            }),
          ],
        }),
      },
    });

    // --------------------------------------------------------------
    // Lambda functions — get-object and put-object
    // --------------------------------------------------------------
    const commonLambdaProps = {
      runtime: lambda.Runtime.NODEJS_20_X,
      role: lambdaExecutionRole,
      memorySize: 256,
      timeout: Duration.seconds(30),
      environment: {
        BUCKET_NAME: objectsBucket.bucketName,
      },
      // Bundle from the local `lambda/` directory. esbuild is the default
      // bundler in CDK v2 and produces a tiny zip with only the deps we
      // actually import.
      code: lambda.Code.fromAsset(join(__dirname, '..', 'lambda')),
      logRetention: logs.RetentionDays.ONE_WEEK,
    };

    const getObjectFn = new lambda.Function(this, 'GetObjectFn', {
      ...commonLambdaProps,
      handler: 'get-object.handler',
      description: 'GET /objects/{key} — reads an S3 object and returns its body',
    });

    const putObjectFn = new lambda.Function(this, 'PutObjectFn', {
      ...commonLambdaProps,
      handler: 'put-object.handler',
      description: 'PUT /objects/{key} — stores the request body as an S3 object',
    });

    // --------------------------------------------------------------
    // REST API — exposes the two Lambdas as /objects/{key}
    // --------------------------------------------------------------
    const api = new apigateway.RestApi(this, 'ObjectsApi', {
      restApiName: 'Serverless Objects API',
      description: 'API Gateway in front of the get-object and put-object Lambdas.',

      deployOptions: {
        stageName: 'prod',
        description: 'Production stage',
      },

      // Default CORS for the whole API. The L2 auto-creates the
      // preflight OPTIONS handlers when this is set.
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: ['GET', 'PUT', 'OPTIONS'],
        allowHeaders: ['Content-Type', 'Authorization'],
      },
    });

    // /objects
    const objectsResource = api.root.addResource('objects');
    // /objects/{key}
    const keyResource = objectsResource.addResource('{key}');

    // GET /objects/{key}  ->  getObjectFn
    keyResource.addMethod(
      'GET',
      new apigateway.LambdaIntegration(getObjectFn, { proxy: true }),
    );

    // PUT /objects/{key}  ->  putObjectFn
    keyResource.addMethod(
      'PUT',
      new apigateway.LambdaIntegration(putObjectFn, { proxy: true }),
    );

    new CfnOutput(this, 'ApiUrl', {
      value: api.url,
      description: 'Invoke URL of the REST API (prod stage)',
      exportName: 'ServerlessApiUrl',
    });
  }
}
