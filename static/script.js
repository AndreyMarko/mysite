let recognition;
const startButton = document.getElementById('startButton');
const submitButton = document.getElementById('submitButton');
const textInput = document.getElementById('textInput');
const errorDiv = document.getElementById('error');
const responseDiv = document.getElementById('response');
let responseContainer;

console.log('Script loaded'); // Отладочное сообщение

startButton.addEventListener('click', () => {
    console.log('Start button clicked');
    requestMicrophoneAccess();
});

submitButton.addEventListener('click', () => {
    console.log('Submit button clicked'); // Отладочное сообщение
    const text = textInput.value.trim();
    if (text) {
        stopSpeech();
        sendToServer(text);
    } else {
        showError('Пожалуйста, введите текст.');
    }
});

function requestMicrophoneAccess() {
    console.log('Requesting microphone access...');
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error('getUserMedia is not supported in this browser');
        showError('Ваш браузер не поддерживает доступ к микрофону.');
        return;
    }
    
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {
            console.log('Microphone access granted');
            stream.getTracks().forEach(track => track.stop());
            startSpeechRecognition();
        })
        .catch(function(err) {
            console.error('Error accessing microphone:', err);
            showError('Не удалось получить доступ к микрофону. Пожалуйста, разрешите доступ в настройках браузера.');
        });
}

function startSpeechRecognition() {
    errorDiv.textContent = '';
    stopSpeech();
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'ru-RU';

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            console.log('Speech recognized:', transcript); // Отладочное сообщение
            sendToServer(transcript);
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error); // Отладочное сообщение
            if (event.error === 'no-speech') {
                showError('Не удалось распознать речь. Пожалуйста, попробуйте снова.');
            } else {
                showError('Ошибка распознавания речи: ' + event.error);
            }
        };

        recognition.onend = function() {
            console.log('Speech recognition ended'); // Отладочное сообщение
            setButtonState(false);
        };

        recognition.onstart = function() {
            console.log('Speech recognition started'); // Отладочное сообщение
            setButtonState(true);
        };

        recognition.start();
    } else {
        showError('Распознавание речи не поддерживается в этом браузере.');
    }
}

function sendToServer(text) {
    console.log('Sending to server:', text);
    fetch('/process_audio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: text }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Server response:', data);
        if (data.response) {
            displayResponse(data.response);
            speakResponse(data.response);
        } else {
            console.error('No response data from server');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function speakResponse(text) {
    console.log('Speaking response:', text);
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ru-RU';
    speechSynthesis.speak(utterance);
}

function stopSpeech() {
    console.log('Stopping speech'); // Отладочное сообщение
    speechSynthesis.cancel();
}

function showError(message) {
    console.error('Error:', message);
    if (errorDiv) {
        errorDiv.textContent = message;
    } else {
        console.error('Error div not found');
    }
}

function setButtonState(isListening) {
    console.log('Setting button state:', isListening); // Отладочное сообщение
    startButton.style.backgroundColor = isListening ? 'green' : 'red';
    startButton.textContent = isListening ? 'Говорите...' : 'Начать говорить';
    startButton.disabled = isListening;
}

function displayResponse(response) {
    console.log('Attempting to display response:', response);
    if (responseContainer) {
        responseContainer.textContent = response;
        console.log('Response set to container');
    } else {
        console.error('Response container not found');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    responseContainer = document.getElementById('response-container');
    console.log('Response container found:', !!responseContainer);
});
