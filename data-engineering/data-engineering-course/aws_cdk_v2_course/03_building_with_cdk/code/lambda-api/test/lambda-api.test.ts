import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { LambdaApiStack } from '../lib/lambda-api-stack';

/**
 * Tests for LambdaApiStack. Run with `npm test` (Jest + ts-jest).
 *
 * The patterns used here are covered in L22–L24:
 *   - resourceCountIs
 *   - hasResourceProperties
 *   - hasResource
 *   - objectLike / stringLikeRegexp
 */
describe('LambdaApiStack', () => {
  let template: Template;

  beforeAll(() => {
    const app = new cdk.App();
    const stack = new LambdaApiStack(app, 'TestStack');
    template = Template.fromStack(stack);
  });

  test('creates exactly one S3 bucket', () => {
    template.resourceCountIs('AWS::S3::Bucket', 1);
  });

  test('creates exactly one Lambda function', () => {
    template.resourceCountIs('AWS::Lambda::Function', 1);
  });

  test('creates exactly one REST API', () => {
    template.resourceCountIs('AWS::API::RESTApi', 1);
  });

  test('creates an IAM role for the Lambda', () => {
    template.resourceCountIs('AWS::IAM::Role', 1);
    template.hasResourceProperties('AWS::IAM::Role', {
      AssumeRolePolicyDocument: Match.objectLike({
        Statement: Match.arrayWith([
          Match.objectLike({
            Principal: { Service: 'lambda.amazonaws.com' },
          }),
        ]),
      }),
    });
  });

  test('Lambda runs Node 20 and uses the inline hello-world handler', () => {
    template.hasResourceProperties('AWS::Lambda::Function', {
      Runtime: 'nodejs20.x',
      Handler: 'index.handler',
      MemorySize: 256,
      Timeout: 10,
    });
  });

  test('Lambda has a permission for API Gateway to invoke it', () => {
    template.hasResourceProperties('AWS::Lambda::Permission', {
      Action: 'lambda:InvokeFunction',
      Principal: 'apigateway.amazonaws.com',
    });
  });

  test('API Gateway uses AWS_PROXY integration', () => {
    template.hasResourceProperties('AWS::ApiGateway::Method', {
      HttpMethod: 'ANY',
      Integration: Match.objectLike({ Type: 'AWS_PROXY' }),
    });
  });

  test('exposes ApiUrl, FunctionName, and AssetsBucketName outputs', () => {
    template.hasOutput('ApiUrl', {});
    template.hasOutput('FunctionName', {});
    template.hasOutput('AssetsBucketName', {});
  });
});
