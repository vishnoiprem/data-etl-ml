from json import dumps as json_encode
import boto3
import os


def _required_env(name: str) -> str:
    """Read a required env var or raise a clear error.

    The previous version of this file hardcoded an AWS access key
    in source (see README "Security" section for the rotation
    history). Never put credentials in source again.
    """
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. The previous version of this file "
            f"hardcoded an AWS access key in source — that key has been "
            f"rotated and the new value must be supplied via environment. "
            f"Set it in your shell or in a .env file (see .env.example)."
        )
    return value


aws_access_key_id = _required_env("AWS_ACCESS_KEY_ID")
aws_secret_access_key = _required_env("AWS_SECRET_ACCESS_KEY")
aws_region = os.environ.get("AWS_REGION", "us-east-1")

try:
    # Polly's client object
    polly = boto3.client(
        "polly",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region,
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