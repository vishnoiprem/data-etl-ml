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
  useEffect(() => {
    AWS.config.update({
      credentials: {
        accessKeyId: 'AKIASEXCXLFDMUEP3TJI',
        secretAccessKey: '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',
      },
      region: 'us-east-1',
    });
    const s3 = new AWS.S3();
    const params = {
      Bucket: bucketName,
      Key: objectKey,
    };
    s3.getObject(params, (err, data) => {
      if (err) {
        console.error('Error fetching object from S3:', err);
      } 
      else {
        const textContent = data.Body.toString('utf-8');
        setRedactedText(textContent);
        console.log('Fetched content from S3:', textContent);
      }
    });
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
    console.log("Before S3 uploading", audio);
    if (audio) {
        console.log("In S3", audio)
        const client = new S3Client({
            region: "us-east-1",
            credentials: {
                accessKeyId: 'AKIASEXCXLFDMUEP3TJI',
                secretAccessKey: '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',
            }
        });
        const command = new PutObjectCommand({
            Bucket: bucketName,
            Key: 'AppData/myaudio.wav',
            Body: blob,
        });
        try {
            const response = await client.send(command);
            console.log('Uploaded to S3', response);
        } catch (err) {
            console.error(err);
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






