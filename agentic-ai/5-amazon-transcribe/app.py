import datetime
import time
import urllib.request
import json
import boto3

current_date_time = datetime.datetime.now()
import uuid
import os

aws_access_key_id = 'AKIASEXCXLFDMUEP3TJI'
aws_secret_access_key = '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'

try:
    # Transcribe the client object
    transcribe = boto3.client('transcribe',
                              aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key,
                              region_name='us-east-1')


    def detect_PII():
        audio_file_name = '<Audio_file_name>'
        job_uri = f's3://transcription-bucket-prem/{audio_file_name}'
        job_name = f'transcription_job_{int(time.time())}_{uuid.uuid4()}'
        file_format = audio_file_name.split('.')[1]
        # Choose a unique transcription job name
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': job_uri},
            LanguageCode='en-US')

        result = poll_transcription_job(job_name)
        # Start the transcription job
        if result['TranscriptionJob']['TranscriptionJobStatus'] == "COMPLETED":
            transcript_file_uri = result['TranscriptionJob']['Transcript']['TranscriptFileUri']
            response = urllib.request.urlopen(transcript_file_uri)
            transcript_data = json.loads(response.read().decode('utf-8'))
            transcript = transcript_data['results']['transcripts'][0]['transcript']
            print("Transcript is: ", transcript)


    def poll_transcription_job(job_name):
        while True:
            result = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            job_status = result['TranscriptionJob']['TranscriptionJobStatus']
            if job_status in ['COMPLETED', 'FAILED']:
                print("Transcription job status:", job_status)
                return result
            time.sleep(5)


    def main():
        print("Starting transcription job...")
        detect_PII()


    if __name__ == "__main__":
        main()
except Exception as e:
    print('Error occurred:', e)