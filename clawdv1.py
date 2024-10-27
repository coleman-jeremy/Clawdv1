import io
import requests
import json
from google.cloud import speech
import speech_recognition as sr
import subprocess
from google.cloud import texttospeech
import os
import time
from mutagen.mp3 import MP3
from dotenv import load_dotenv  # Import to load .env variables

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
PROJECT_ID = os.getenv("PROJECT_ID")
MODEL = os.getenv("MODEL")
LOCATION = os.getenv("LOCATION")
ENDPOINT = os.getenv("ENDPOINT")

# Initialize Google Cloud Speech-to-Text client
client = speech.SpeechClient()

# Path to store memories in a file
memory_folder = 'memories'
memory_file = os.path.join(memory_folder, 'conversation_memory.json')

# Ensure the folder exists
if not os.path.exists(memory_folder):
    os.makedirs(memory_folder)

# Function to load conversation memory from a file
def load_conversation_memory():
    if os.path.exists(memory_file):
        with open(memory_file, 'r') as file:
            try:
                memory = json.load(file)
            except json.JSONDecodeError:
                memory = []
    else:
        memory = []
    return memory

# Function to save conversation memory to a file
def save_conversation_memory(memory):
    with open(memory_file, 'w') as file:
        json.dump(memory, file, indent=4)

# Function to prune memory to only keep the last N exchanges
def prune_memory(memory, limit=10):
    if len(memory) > limit:
        return memory[-limit:]  # Keep only the last N entries
    return memory

# Function to transcribe speech
def transcribe_speech():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 3.0  # 3 seconds of silence before considering input done

    with sr.Microphone() as source:
        print("Please speak...")

        try:
            audio = recognizer.listen(source, timeout=10)
            print("Audio captured from the microphone.")
        except sr.WaitTimeoutError:
            print("Listening timed out, waiting for input again...")
            return ""

    audio_data = io.BytesIO(audio.get_wav_data())
    audio_bytes = audio_data.read()

    print(f"Captured audio data length: {len(audio_bytes)} bytes")

    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code="en-US"
    )

    try:
        response = client.recognize(config=config, audio=audio)
        for result in response.results:
            return result.alternatives[0].transcript
    except Exception as e:
        print(f"Error during recognition: {e}")
        return ""

# Function to get a response from Claude
def get_claude_response(user_input):
    # Load conversation memory
    conversation_memory = load_conversation_memory()

    # Add the user's message to the memory
    conversation_memory.append({"role": "user", "content": user_input})

    # Prune memory to limit it to the last N messages
    conversation_memory = prune_memory(conversation_memory, limit=5)

    # Create the Claude request body with the pruned memory
    messages = [{"role": entry["role"], "content": [{"type": "text", "text": entry["content"]}]} for entry in conversation_memory]

    request_body = {
        "anthropic_version": "vertex-2023-10-16",  # Required for Claude 3.5
        "messages": messages,
        "max_tokens": 1256,
        "stream": False  # If you want the full response at once, set to False
    }

    print(f"Request body: {json.dumps(request_body, indent=4)}")

    # Get the auth token from gcloud
    try:
        auth_token = subprocess.getoutput("gcloud auth print-access-token")
        print(f"Auth token: {auth_token[:30]}...")  # Print part of the token for confirmation
    except Exception as e:
        print(f"Error fetching auth token: {e}")
        return "Error"

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    # Use the ENDPOINT variable loaded from .env
    endpoint_url = ENDPOINT

    # Send the request to Claude
    try:
        response = requests.post(endpoint_url, headers=headers, json=request_body)
        response.raise_for_status()
        response_data = response.json()

        print(f"Claude Response: {json.dumps(response_data, indent=4)}")

        # Extract the text response from Claude
        text_response = response_data.get('content', [{}])[0].get('text', "No response found")

        # Add the bot's response to the memory
        conversation_memory.append({"role": "assistant", "content": text_response})

        # Save updated conversation memory
        save_conversation_memory(conversation_memory)

        return text_response
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.content}")
        return "Error"
    except Exception as err:
        print(f"Error during Claude response generation: {err}")
        return "Error"

# Function to speak the text response
def speak_text(text):
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)

    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')

def play_audio(file_name="output.mp3"):
    os.system(f'start {file_name}')
    audio_duration = get_audio_duration(file_name)
    time.sleep(audio_duration)

def get_audio_duration(file_name):
    audio = MP3(file_name)
    duration = audio.info.length
    print(f"Audio duration: {duration} seconds")
    return duration

# Main function
def main():
    while True:
        user_input = transcribe_speech()

        if user_input:
            print(f"You said: {user_input}")

            # Get response from Claude
            bot_response = get_claude_response(user_input)
            print(f"Bot says: {bot_response}")

            # Speak and play the bot response
            speak_text(bot_response)
            play_audio()
        else:
            print("No input detected, waiting for speech...")

# Run main
if __name__ == "__main__":
    main()
