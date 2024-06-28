from flask import Flask, request, jsonify
from pydantic import BaseModel, ValidationError
import os
from dotenv import load_dotenv
from docx import Document
import openai

app = Flask(__name__)

# Load environment variables
load_dotenv()
# Retrieve API keys from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key

# Define the file reading function for .docx files
def read_docx(file_path):
    document = Document(file_path)
    return '\n'.join([para.text for para in document.paragraphs])

# Define the file path
file_path = "./test_files/2024 Problem Book_sumsifter_short.docx"

# Read the content of the file
file_content = read_docx(file_path)

# Define the additional prompt
additional_prompt = """
Please provide a 100-word summary of the article. 
Each sentence in the original article ends with a sentence ID in the form of "(S1)", "(S2)", and so on. 
Each sentence in the summary must be attributed to sentences in the original article by citing the sentence IDs. 
Use the following json format to answer. 
{
    "summary": [
        {"text": "Sentence 1", "sources": ["S1", "S2"]},
        {"text": "Sentence 22", "sources": ["S3", "S4"]},
        {"text": "Sentence 33", "sources": ["S5", "S6"]},
        {"text": "Sentence 44", "sources": ["S7", "S8"]},
        {"text": "Sentence 55", "sources": ["S9", "S10"]}
    ]
}
Do not include any text outside of the JSON format.
"""

class Inquiry(BaseModel):
    question: str

@app.route('/')
def home():
    return "API is running. Use POST /process_inquiry/ to interact with the chat agent."

@app.route('/process_inquiry/', methods=['POST'])
def process_inquiry():
    try:
        inquiry_data = request.get_json()
        inquiry = Inquiry(**inquiry_data)  # Validate the input data using the Inquiry model
    except ValidationError as e:
        return jsonify(e.errors()), 400

    # Append the additional prompt and file content to the inquiry question
    inquiry_with_prompt = f"{additional_prompt}\n\nOriginal Document Content:\n{file_content}\n\n{inquiry.question}"
    
    # Get the response from the chat agent
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": inquiry_with_prompt}
        ]
    )
    
    response_text = response['choices'][0]['message']['content'].strip()
    
    # Extract JSON from the response text
    try:
        start_index = response_text.find('{')
        end_index = response_text.rfind('}') + 1
        json_response = response_text[start_index:end_index]
        json_response = eval(json_response)  # Convert string to dict for JSON response
    except Exception as e:
        return jsonify({"error": "Failed to parse response", "details": str(e)}), 500
    
    return jsonify(json_response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
