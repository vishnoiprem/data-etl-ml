from json import dumps as json_encode
import boto3
import os

aws_access_key_id = "AKIASEXCXLFDMUEP3TJI"
aws_secret_access_key = "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"

try:
    # Polly’s client object
    polly = boto3.client(
        "polly",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name="us-east-1",
    )

    text = "Hi, my name is John Doe, and I live in Seattle."

    # Starting the Polly synthesis task
    response = polly.start_speech_synthesis_task(
        Text=text,
        Engine="neural",
        VoiceId="Joanna",
        TextType="text",
        OutputS3BucketName="transcription-bucket-prem",
        OutputFormat="mp3",
    )
    response = response["SynthesisTask"]
    print("Successfully converted text to speech using Amazon Polly!")
except Exception as e:
    print("Error occurred:", e)