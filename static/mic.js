  //const downloadLink = document.getElementById('download');
  const stopButton = document.getElementById('stop');

function uploadAudioBlob(audioBlob)
     fetch('YOUR_API_ENDPOINT', { method: 'POST', body: audioBlob }) .then(response =>response.json()) .then(response => 
        {   //The response will contain the whisper-transcribed text 
            //audioUrl = response.url; 
        })
function playUploadedAudio(url) 
        const audio = document.createElement('audio'); audio.src = url; audio.play()
  const handleSuccess = function(stream) {
    const options = {mimeType: 'audio/webm'};
    const recordedChunks = [];
    const mediaRecorder = new MediaRecorder(stream, options);

    mediaRecorder.addEventListener('dataavailable', function(e) {
      if (e.data.size > 0) recordedChunks.push(e.data);
    });

    mediaRecorder.addEventListener('stop', function() {
      downloadLink.href = URL.createObjectURL(new Blob(recordedChunks));
      downloadLink.download = 'acetest.wav';
    });

    stopButton.addEventListener('click', function() {
      mediaRecorder.stop();
    });

    mediaRecorder.start();
  };

  navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      .then(handleSuccess);
