/**
 * Snapshot-style test for the `HelloCdkStack`.
 *
 * Companion to the fine-grained assertions in
 * `02_app_stack_construct/code/hello-cdk/test/hello-cdk.test.ts`.
 * Copy this file into that test/ directory if you want to compare
 * the two styles side by side.
 *
 * Run with:
 *   npx jest test/hello-cdk.snapshot.test.ts
 *   npx jest -u test/hello-cdk.snapshot.test.ts   # update snapshot
 */
import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { HelloCdkStack } from '../../../02_app_stack_construct/code/hello-cdk/lib/hello-cdk-stack';

describe('HelloCdkStack — snapshot', () => {
  test('matches the stored CloudFormation snapshot', () => {
    const app = new cdk.App();
    const stack = new HelloCdkStack(app, 'TestStack');
    const template = Template.fromStack(stack);
    expect(template.toJSON()).toMatchSnapshot();
  });
});
