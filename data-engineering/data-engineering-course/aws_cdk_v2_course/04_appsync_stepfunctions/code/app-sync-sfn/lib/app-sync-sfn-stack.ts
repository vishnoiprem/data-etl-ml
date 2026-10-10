import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as appsync from 'aws-cdk-lib/aws-appsync';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as tasks from 'aws-cdk-lib/aws-stepfunctions-tasks';

/**
 * AppSyncSfnStack — AppSync + Step Functions + Lambda.
 *
 * GraphQL schema (L16):
 *
 *     type Order { id: String!  status: String! }
 *     type Query  { getOrder(id: String!): Order }
 *     type Mutation { startOrder(id: String!): Order }
 *
 * The `getOrder` resolver is the resolver Lambda below.
 * The `startOrder` mutation kicks off the Step Functions state machine.
 */
export class AppSyncSfnStack extends cdk.Stack {
  public readonly api: appsync.GraphqlApi;
  public readonly resolverFn: lambda.Function;
  public readonly stateMachine: sfn.StateMachine;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ----- Lambda resolver for AppSync ---------------------------------
    this.resolverFn = new lambda.Function(this, 'ResolverFn', {
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'index.handler',
      code: lambda.Code.fromInline(`
        exports.handler = async (event) => {
          const id = event.arguments?.id ?? 'unknown';
          return { id, status: 'PENDING' };
        };
      `),
      memorySize: 256,
      timeout: cdk.Duration.seconds(10),
    });

    // ----- AppSync GraphQL API -----------------------------------------
    // We use the modern `definition` field (Schema.fromString) so the
    // schema lives next to the stack code. In production move the
    // schema into a separate `schema.graphql` file and use
    // `SchemaFile.fromAsset(path.join(__dirname, 'schema.graphql'))`.
    this.api = new appsync.GraphqlApi(this, 'Api', {
      name: 'orders-api',
      definition: appsync.Schema.fromString(`
        type Order {
          id: String!
          status: String!
        }
        type Query {
          getOrder(id: String!): Order
        }
        type Mutation {
          startOrder(id: String!): Order
        }
        schema {
          query: Query
          mutation: Mutation
        }
      `),
      authorizationConfig: {
        defaultAuthorization: {
          authorizationType: appsync.AuthorizationType.API_KEY,
        },
      },
    });

    // ----- Data source: Lambda -----------------------------------------
    const lambdaDs = this.api.addLambdaDataSource('LambdaDataSource', this.resolverFn);

    // Resolver: Query.getOrder
    lambdaDs.createResolver('GetOrderResolver', {
      typeName: 'Query',
      fieldName: 'getOrder',
    });

    // ----- Step Functions state machine --------------------------------
    // A simple 2-state machine: a Lambda invoke → a "Done" pass state.
    const invokeOrderTask = new tasks.LambdaInvoke(this, 'InvokeOrder', {
      lambdaFunction: this.resolverFn,
      payload: sfn.TaskInput.fromObject({
        'arguments.$': '$',
      }),
    });

    const definition = invokeOrderTask.next(
      new sfn.Pass(this, 'Done', {
        result: sfn.Result.fromObject({ status: 'COMPLETED' }),
      })
    );

    this.stateMachine = new sfn.StateMachine(this, 'OrderStateMachine', {
      definitionBody: sfn.DefinitionBody.fromChainable(definition),
      timeout: cdk.Duration.minutes(5),
    });

    // Mutation: Mutation.startOrder → start the state machine
    // For brevity the resolver uses the Lambda data source (a real
    // implementation would use an HttpDataSource targeting SFN's
    // StartExecution API). The point of this demo is the schema + the
    // state machine existing in the same stack.
    lambdaDs.createResolver('StartOrderResolver', {
      typeName: 'Mutation',
      fieldName: 'startOrder',
    });

    // ----- Outputs -----------------------------------------------------
    new cdk.CfnOutput(this, 'GraphqlUrl', {
      value: this.api.graphqlUrl,
      description: 'GraphQL endpoint URL',
    });
    new cdk.CfnOutput(this, 'ApiKey', {
      value: this.api.apiKey ?? '',
      description: 'AppSync API key (read from the console in production)',
    });
    new cdk.CfnOutput(this, 'StateMachineArn', {
      value: this.stateMachine.stateMachineArn,
      description: 'ARN of the Step Functions state machine',
    });
  }
}
