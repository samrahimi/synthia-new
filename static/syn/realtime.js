//one day i'll make gpt4 cause a million telephones to ring at once
//via this pipe. guess how and name the movie
const socket = new WebSocket('ws://localhost:8888');


document.getElementById('docurl').addEventListener('input', function () {
    const textareaContent = this.value;
    const iframe = document.getElementById('iframe');
    iframe.src = textareaContent
    setTimeout(() => {
        //it may be dumb to update the context this way, rather than just dumping outerhtml when a request is sent
        //but somehow it seems cleaner... the effect is the same, assuming the code works
        const d = getLatestDOM()
        const data = { type: 'updatecontext', userId: 'sammy', sessionId: window.sessionId, contextDocument: d }
        socket.send(JSON.stringify(data))
    }, 3000)
});

// document.getElementById('textarea').addEventListener('input', function () {
//     const textareaContent = this.value;
//     const iframe = document.getElementById('iframe');
//     const iframeDocument = iframe.contentWindow.document;

//     iframeDocument.open();
//     iframeDocument.write(textareaContent);
//     iframeDocument.close();

//     //it may be dumb to update the context this way, rather than just dumping outerhtml when a request is sent
//     //but somehow it seems cleaner... the effect is the same, assuming the code works
//     const data = { type: 'updatecontext', userId: 'sammy', sessionId: window.sessionId, contextDocument: textareaContent }
//     socket.send(JSON.stringify(data))
// });
function executeScriptInIframe(scriptString) {
    const iframe = document.getElementById('iframe');
    const iframeDocument = iframe.contentWindow.document;

    const script = iframeDocument.createElement('script');
    script.type = 'text/javascript';
    script.text = scriptString;

    iframeDocument.body.appendChild(script);
}

function evalInIframe(expression) {
    
}


//dom snapshot of the iframe
function getLatestDOM(opts) {
    const iframe = document.getElementById('iframe');
    const iframeDocument = iframe.contentWindow.document.documentElement;
    return iframeDocument.outerHTML

    const script = iframeDocument.createElement('script');
    script.type = 'text/javascript';
    script.text = scriptString;

}

socket.addEventListener('open', () => {
    console.log('Connected to server');

    const data = {
        type: 'initialize',
        userId: 'sammy',
        contextDocument: "[No Context Document Selected]"
    };

    socket.send(JSON.stringify(data));
});


socket.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'sessionCreated') {
        window.sessionId = data.sessionId;
        console.log('Session created:', sessionId);
    } else if (data.type === 'response') {
        const responseContent = data.response.content;
        console.log('Received response:', responseContent);

        // Display response content in the messages container
        const messagesContainer = document.getElementById('messages');
        const messageElement = document.createElement('p');
        messageElement.textContent = responseContent;
        messagesContainer.appendChild(messageElement);

        // Inject and execute response content as JavaScript in the iframe
        executeScriptInIframe(responseContent); // Assuming you have the executeScriptInIframe function
    }
});

askGptRealtime = (inputBox) => {
        //event.preventDefault(); // Prevent default behavior (new line)

        const query = inputBox.value.trim();
        if (query) {
            const queryData = {
                type: 'query',
                sessionId: sessionId, // Make sure to store the sessionId when it's received
                query: query
            };
            socket.send(JSON.stringify(queryData));
            inputBox.value = ''; // Clear the input box

            //display the sent message
            // Display response content in the messages container
            const messagesContainer = document.getElementById('messages');
            const messageElement = document.createElement('p');
            messageElement.className = "sent-message"
            messageElement.textContent = queryData.query;
            messagesContainer.appendChild(messageElement);

        }
    }



const inputBox = document.getElementById('inputBox'); // Add an ID to the input box in HTML
inputBox.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault()
        askGptRealtime(inputBox)
    }
});








/*** Purpose: records a user's voice, transcribes to text via our API and whisper-1, passes result onwards ***/
let mediaRecorder;
const startRecording = async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.start();
        console.log('Recording started');
    } catch (err) {
        console.error('Error starting recording:', err);
    }
};
const stopRecording = (uploadTo, onTranscriptionAvailable) => {
    if (!mediaRecorder) {
        console.error('No recording in progress');
        return;
    }
    mediaRecorder.stop();
    console.log('Recording stopped');

    mediaRecorder.ondataavailable = function (e) {
        // create a new FormData object and append the audio data to it
        const formData = new FormData();
        formData.append('audio', e.data, 'recording.wav');
        fetch(uploadTo, {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                console.log("transcription result: " + data)

                if (onTranscriptionAvailable) {
                    onTranscriptionAvailable(data);
                }
            })

    };
}


socket.addEventListener('close', () => {
    console.log('Disconnected from server');
});

socket.addEventListener('error', (error) => {
    console.error('WebSocket error:', error);
});




/*** UI  ***/
function sendMessage(message) {
    $("#inputBox").val(message);
    askGptRealtime(document.getElementById("inputBox"))
    //const d = getLatestDOM()
    //const data = { type: 'updatecontext', userId: 'sammy', sessionId: window.sessionId, contextDocument: d }
    //socket.send(JSON.stringify(data))
}

async function requestFileSystemPermission() {
    const handle = await window.showDirectoryPicker();
    return handle
}

// Save the current DOM state to index2.html
async function saveDOMToFile(filename) {
    const synthDir = await requestFileSystemPermission();
    const fileHandle = await synthDir.getFileHandle(filename, { create: true });
    const writableStream = await fileHandle.createWritable();
    await writableStream.write(new Blob([document.documentElement.outerHTML], { type: "text/html" }));
    await writableStream.close();
    console.log("File saved successfully");
}

// Add click event to the save button to call saveDOMToFile()
$("#saveButton").on("click", function () {
    filename = prompt("Save As...", "new.html")
    saveDOMToFile();
});

$("#toggleMicButton").on("click", function () {
    const micIcon = $("#micIcon");
    if (micIcon.hasClass("fa-microphone")) {
        micIcon.removeClass("fa-microphone").addClass("fa-stop");
        startRecording();
    } else {
        micIcon.removeClass("fa-stop").addClass("fa-microphone");
        stopRecording('/transcribe', x => sendMessage(x.text));
    }
});
