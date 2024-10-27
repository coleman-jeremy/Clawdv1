Clawdv1
Speech-to-speech AI using Anthropics Claude 3.0.

Features
Voice Interaction: Communicate with Clawdv1 using voice input and get responses through synthesized speech.
Memory Persistence: Saves conversation history to allow for contextual memory, making conversations feel more continuous and personalized.
Google Cloud Integration: Uses Google Cloud's Speech-to-Text and Text-to-Speech APIs for accurate voice recognition and realistic responses.
How to Use
Install Dependencies: Make sure you have the required Python packages installed. You can do this by running:

pip install -r requirements.txt

Set Up Environment Variables: You need to provide your own Google Cloud credentials. Add them to a .env file in the root directory:

makefile
Copy code
PROJECT_ID=your_project_id
MODEL=your_model
LOCATION=your_location
ENDPOINT=your_endpoint
Run the Program: Start the program with:

python clawdv1.py

Conversation Memory: The AI saves conversation history to keep track of past interactions, which enhances the flow of dialogue by allowing it to remember key details across sessions.
