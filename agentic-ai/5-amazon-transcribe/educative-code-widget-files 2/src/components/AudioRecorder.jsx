import React, {useState, useEffect} from 'react';
import { AudioRecorder } from 'react-audio-voice-recorder';
import './audioRecorder.css'
import AWS from 'aws-sdk';
import { PutObjectCommand, S3Client } from "@aws-sdk/client-s3";
export default function App() {
  const [redactedText, setRedactedText] = useState('');
  const bucketName = '<YOUR_S3_BUCKET>';
  const objectKey = 'AppOutput/redacted_text.txt';
  // eslint-disable-next-line
  let audioContent=null;

  // SECURITY: Do NOT put long-lived AWS credentials in browser code.
  // The previous version of this file hardcoded an AWS access key
  // in JSX, which meant it shipped to every user's browser. That key
  // was rotated; the new model is:
  //   1. The browser asks the backend (an API you control) for a
  //      *presigned URL* for the S3 object.
  //   2. The backend uses its IAM role to mint a presigned URL with
  //      a 5-15 minute expiry.
  //   3. The browser uses the presigned URL to upload / fetch, with
  //      no credentials in the JS at all.
  // See ../app.py and ../Amazon_Polly.py for the server-side code
  // that has been migrated to use os.environ['AWS_ACCESS_KEY_ID'].
  // The presigned-URL backend endpoint is out of scope for this
  // educational widget; until it ships, this UI is read-only and
  // cannot upload.

  useEffect(() => {
    // Fetch the existing redacted text via a backend endpoint that
    // returns the file contents (no S3 credentials in the browser).
    fetch('/api/redacted-text')
      .then((res) => res.text())
      .then((textContent) => {
        setRedactedText(textContent);
        console.log('Fetched redacted text via /api/redacted-text:', textContent);
      })
      .catch((err) => console.error('Error fetching /api/redacted-text:', err));
  }, []);
   const audio = document.createElement('audio');
   const addAudioElement = async (blob) => {
    audioContent = await fetch(blob)
        .then((res) => res.arrayBuffer());
    const url = URL.createObjectURL(blob);
    audio.src = url;
    audio.controls = true;
    audio.style.display = 'none';
    document.body.appendChild(audio);
    console.log("Before S3 upload (via presigned URL)", audio);
    if (audio) {
        console.log("Requesting presigned URL for upload", audio)
        // Step 1: ask the backend for a presigned PUT URL.
        // Step 2: PUT the blob to that URL.
        // (The previous version used a hardcoded S3Client here;
        //  that path is unsafe and is removed.)
        try {
            const presign = await fetch('/api/presigned-upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: 'AppData/myaudio.wav', contentType: 'audio/wav' }),
            }).then((r) => r.json());
            const putRes = await fetch(presign.url, {
                method: 'PUT',
                headers: { 'Content-Type': 'audio/wav' },
                body: blob,
            });
            if (!putRes.ok) throw new Error(`presigned PUT failed: ${putRes.status}`);
            console.log('Uploaded to S3 via presigned URL');
        } catch (err) {
            console.error('Upload via presigned URL failed:', err);
        }
    }
};
  return (
    <div className='recorder-container'>
    <div className= 'recorder'>
      <
      AudioRecorder
        onRecordingComplete={addAudioElement}
        audioTrackConstraints={{
          noiseSuppression: true,
          echoCancellation: true,
        }}
        onNotAllowedOrFound={(err) => console.table(err)}
        downloadFileExtension="wav"
        mediaRecorderOptions={{
          audioBitsPerSecond: 128000,
        }}
      />
      <br />
    </div>
    <h3 className='redactedText1'>Redacted Text: </h3>
    <p className='redactedText2'>{redactedText}</p>
    </div>
  );
}






