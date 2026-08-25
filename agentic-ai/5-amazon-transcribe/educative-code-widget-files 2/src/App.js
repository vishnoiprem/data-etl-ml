import React from "react";
import AudioRecorder from "./components/AudioRecorder";
import "./App.css";
function App() {
    return (
		<div style={{height:"850px", backgroundColor:"rgb(25,31,44"}}>
		<header>
		<img style={{ width: '350px', height: '350px',position: 'absolute', marginLeft:'40%', marginTop: '0%'}}
		src="https://moattarzeest.github.io/ImageForApp/Record.png"
		alt="microphone"/>
        <h1 style={{ position: 'absolute', marginLeft:'42%', marginTop:'20%', textAlign: 'center', fontSize: '40px', fontFamily:"Papyrus", color:"white"}}>Audio Recorder</h1>
        <AudioRecorder/>
	    </header>
		</div>
	);
}
export default App;

