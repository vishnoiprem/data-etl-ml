import boto3
import json
import time
import uuid
import urllib.request

bucket_name='transcription-bucket-prem'
s3 = boto3.client('s3', region_name='us-east-1')
transcribe = boto3.client('transcribe', region_name='us-east-1')

def lambda_handler(event, context):
    try:
        job_name = f'transcription_job_{int(time.time())}_{uuid.uuid4()}'
        media_file_uri = f's3://{bucket_name}/AppData/myaudio.wav'
        # Transcription job starts
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': media_file_uri},
            LanguageCode='en-US'
        )
        while True:
            result = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            if result['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
                break
            elif result['TranscriptionJob']['TranscriptionJobStatus'] == 'FAILED':
                print("Transcription job failed")
                print(result['TranscriptionJob'])
                return
            else:
                time.sleep(5)
        transcript_file_uri = result['TranscriptionJob']['Transcript']['TranscriptFileUri']
        with urllib.request.urlopen(transcript_file_uri) as response:
            transcript_data = json.loads(response.read().decode('utf-8'))
        transcript = transcript_data['results']['transcripts'][0]['transcript']

        # Transcript uploads to S3 bucket
        text_to_analyze = transcript
        s3_object_key = 'AppOutput/redacted_text.txt'
        try:
            response = s3.put_object(
                Bucket=bucket_name,
                Key=s3_object_key,
                Body=text_to_analyze
            )
            print("Transcripted text uploaded successfully to S3. S3 Object URL:", response['ObjectURL'])
        except Exception as e:
            print("Error uploading redacted text to S3:", str(e))
    except Exception as e:
        print("Error transcribing audio", str(e))