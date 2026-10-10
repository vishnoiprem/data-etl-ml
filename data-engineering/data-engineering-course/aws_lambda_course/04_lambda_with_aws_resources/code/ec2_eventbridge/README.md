# ec2_eventbridge — EventBridge schedule that runs the EC2 lifecycle Lambda (L17)

> Companion code for L17 — AWS Lambda Automation Use Case (EC2, Lambda, EventBridge).

## Files

- `eventbridge_scheduled_start_stop.py` — the wrapper Lambda module
  that normalizes the EventBridge event shape and delegates to the
  L16 EC2 lifecycle handler.
- `test_script.py` — `moto`-based tests of the wrapper.

## What this code does (and does not do)

The `script.py` in this directory is the **wrapper Lambda**. The
EventBridge *rules*, the Lambda *invoke permission*, and the IAM
*role* are documented as comments at the top of the file and as a
canonical CloudFormation snippet below. `moto`'s EventBridge support
is partial, so we test the wrapper's event-shape normalization and
delegate the actual rule creation to manual setup or CFN.

## CloudFormation (for real AWS deploys)

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Resources:
  StartStopLambda:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: ec2-start-stop
      Role: !GetAtt LambdaRole.Arn
      Runtime: python3.11
      Handler: eventbridge_scheduled_start_stop.handler
      Code:
        S3Bucket: my-lambda-bucket
        S3Key:    lambdas/eventbridge_scheduled_start_stop.zip
      Environment:
        Variables:
          AWS_REGION: us-east-1

  LambdaRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal: { Service: lambda.amazonaws.com }
            Action: sts:AssumeRole
      Policies:
        - PolicyName: EC2Lifecycle
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - ec2:DescribeInstances
                  - ec2:StartInstances
                  - ec2:StopInstances
                Resource: "*"
              - Effect: Allow
                Action: [logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents]
                Resource: arn:aws:logs:*:*:*

  StartRule:
    Type: AWS::Events::Rule
    Properties:
      ScheduleExpression: "cron(0 8 ? * MON-FRI *)"
      Targets:
        - Id: StartEC2Target
          Arn: !GetAtt StartStopLambda.Arn
          Input: '{"action": "start", "instance_id": "i-0123456789abcdef0"}'

  StopRule:
    Type: AWS::Events::Rule
    Properties:
      ScheduleExpression: "cron(0 20 ? * MON-FRI *)"
      Targets:
        - Id: StopEC2Target
          Arn: !GetAtt StartStopLambda.Arn
          Input: '{"action": "stop", "instance_id": "i-0123456789abcdef0"}'

  StartInvokePermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref StartStopLambda
      Action: lambda:InvokeFunction
      Principal: events.amazonaws.com
      SourceArn: !GetAtt StartRule.Arn

  StopInvokePermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref StartStopLambda
      Action: lambda:InvokeFunction
      Principal: events.amazonaws.com
      SourceArn: !GetAtt StopRule.Arn
```

## Run the tests

```bash
cd 04_lambda_with_aws_resources/code/ec2_eventbridge
pytest test_script.py -v
```

The tests assert the wrapper's event-shape normalization. They do
not (and cannot, without a richer `moto` shim) assert the schedule
fires.
