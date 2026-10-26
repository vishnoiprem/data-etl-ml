import { GetObjectCommand, NoSuchKey, S3Client } from '@aws-sdk/client-s3';
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

// Reuse the client across invocations — Lambda freezes the module graph
// after the first call, so this client lives for the lifetime of the
// execution environment.
const s3 = new S3Client({});
const BUCKET = process.env.BUCKET_NAME ?? '';

export const handler = async (
  event: APIGatewayProxyEvent,
): Promise<APIGatewayProxyResult> => {
  const key = event.pathParameters?.key;
  if (!key) {
    return {
      statusCode: 400,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'Missing path parameter: key' }),
    };
  }

  try {
    const out = await s3.send(new GetObjectCommand({ Bucket: BUCKET, Key: key }));
    const body = await out.Body!.transformToString('utf-8');
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body,
    };
  } catch (err) {
    if (err instanceof NoSuchKey || (err as { name?: string }).name === 'NoSuchKey') {
      return {
        statusCode: 404,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: `Object ${key} not found` }),
      };
    }
    console.error('get-object error', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'Internal server error' }),
    };
  }
};
