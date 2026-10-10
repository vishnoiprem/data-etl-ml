import { PutObjectCommand, S3Client } from '@aws-sdk/client-s3';
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

const s3 = new S3Client({});
const BUCKET = process.env.BUCKET_NAME ?? '';

export const handler = async (
  event: APIGatewayProxyEvent,
): Promise<APIGatewayProxyResult> => {
  const key = event.pathParameters?.key;
  if (!key || event.body === null || event.body === undefined) {
    return {
      statusCode: 400,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'Missing path parameter: key or body' }),
    };
  }

  try {
    await s3.send(
      new PutObjectCommand({
        Bucket: BUCKET,
        Key: key,
        Body: event.body,
        ContentType: event.headers['content-type'] ?? 'application/octet-stream',
      }),
    );
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, bucket: BUCKET, message: 'Stored' }),
    };
  } catch (err) {
    console.error('put-object error', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'Internal server error' }),
    };
  }
};
