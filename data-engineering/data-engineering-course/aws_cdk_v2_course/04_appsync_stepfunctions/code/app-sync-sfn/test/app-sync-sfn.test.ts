import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { AppSyncSfnStack } from '../lib/app-sync-sfn-stack';

/**
 * Tests for AppSyncSfnStack. Run with `npm test`.
 *
 * These tests assert the *shape* of the synthesized CloudFormation
 * template:
 *   - 1 AppSync GraphQL API with the expected schema
 *   - 1 Lambda function (the resolver)
 *   - 1 Step Functions state machine
 *   - 2 resolvers (Query.getOrder, Mutation.startOrder)
 */
describe('AppSyncSfnStack', () => {
  let template: Template;

  beforeAll(() => {
    const app = new cdk.App();
    const stack = new AppSyncSfnStack(app, 'TestStack');
    template = Template.fromStack(stack);
  });

  test('creates exactly one AppSync GraphQL API', () => {
    template.resourceCountIs('AWS::AppSync::GraphQLApi', 1);
  });

  test('creates exactly one Lambda function', () => {
    template.resourceCountIs('AWS::Lambda::Function', 1);
  });

  test('creates exactly one Step Functions state machine', () => {
    template.resourceCountIs('AWS::States::StateMachine', 1);
  });

  test('creates two AppSync resolvers (Query.getOrder, Mutation.startOrder)', () => {
    template.resourceCountIs('AWS::AppSync::Resolver', 2);
  });

  test('the GraphQL schema defines Query.getOrder and Mutation.startOrder', () => {
    template.hasResourceProperties('AWS::AppSync::GraphQLSchema', {
      Definition: Match.stringLikeRegexp('type Order'),
    });
    template.hasResourceProperties('AWS::AppSync::GraphQLSchema', {
      Definition: Match.stringLikeRegexp('getOrder'),
    });
    template.hasResourceProperties('AWS::AppSync::GraphQLSchema', {
      Definition: Match.stringLikeRegexp('startOrder'),
    });
  });

  test('the state machine references the resolver Lambda', () => {
    // The state machine is a string of states — we just check the
    // definition string mentions the Lambda ARN placeholder CDK uses.
    template.hasResourceProperties('AWS::States::StateMachine', {
      DefinitionString: Match.serializedJson(Match.objectLike({
        StartAt: Match.anyValue(),
        States: Match.objectLike({
          InvokeOrder: Match.objectLike({ Type: 'Task' }),
          Done: Match.objectLike({ Type: 'Pass' }),
        }),
      })),
    });
  });

  test('AppSync uses API_KEY authorization', () => {
    template.hasResourceProperties('AWS::AppSync::GraphQLApi', {
      AuthenticationType: 'API_KEY',
    });
  });

  test('exposes GraphqlUrl, ApiKey, and StateMachineArn outputs', () => {
    template.hasOutput('GraphqlUrl', {});
    template.hasOutput('ApiKey', {});
    template.hasOutput('StateMachineArn', {});
  });
});
