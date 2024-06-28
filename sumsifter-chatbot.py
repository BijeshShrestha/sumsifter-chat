# from flask import Flask, request, jsonify
# from pydantic import BaseModel, ValidationError
# import os
# from dotenv import load_dotenv
# from docx import Document
# import openai

# app = Flask(__name__)

# # Load environment variables
# load_dotenv()
# # Retrieve API keys from environment variables
# openai_api_key = os.getenv("OPENAI_API_KEY")
# openai.api_key = openai_api_key

# # Define the file reading function for .docx files
# def read_docx(file_path):
#     document = Document(file_path)
#     return '\n'.join([para.text for para in document.paragraphs])

# # Define the file path
# file_path = "./test_files/2024 Problem Book_sumsifter_short.docx"

# # Read the content of the file
# file_content = read_docx(file_path)

# # Define the additional prompt
# additional_prompt = """
# Please add 'Namaste!' before every response. Please provide a 100-word summary of the article. 
# Each sentence in the original article ends with a sentence ID in the form of "(S1)", "(S2)", and so on. 
# Each sentence in the summary must be attributed to sentences in the original article by citing the sentence IDs. 
# Use the following json format to answer. 
# {
#     "id": "doc1",
#     "summary": [
#         {
#         "sentence": "The Summer Conference on Applied Data Science (SCADS) is an annual research program focused on the development of AI to assist the US Intelligence Community (IC) data analysts, identifying a multi-year Grand Challenge to guide the research.",
#         "sources": ["S10", "S11"]
#         },
#         {
#         "sentence": "The Grand Challenge for SCADS is to create Tailored Daily Reports (TLDRs) for individual knowledge workers within the IC, combining classified and unclassified material from various modes and formats.",
#         "sources": ["S13", "S14", "S15"]
#         },
#         {
#         "sentence": "The research efforts in 2024 will focus on Automatic Summarization, Recommendation Systems, and Human-Machine Interaction, with an emphasis on explainability, contextualization, and knowledge representation.",
#         "sources": ["S16", "S17"]
#         },
#         {
#         "sentence": "The document presents critical challenges and research questions related to the grand challenge, and identifies Large Language Models (LLMs) like GPT-3.5 and GPT-4 as potential tools for the research.",
#         "sources": ["S19", "S22", "S23"]
#         },
#         {
#         "sentence": "Automatic summarization, a key to creating a TLDR, involves both extractive and abstractive summarization, and the document encourages research in multi-modal summarization techniques.",
#         "sources": ["S24", "S25", "S26", "S27"]
#         }
#     ]
# }
# Do not populate any summary sentence without a reference to the original sentences as S1 and so on.
# """

# class Inquiry(BaseModel):
#     question: str

# @app.route('/')
# def home():
#     return "API is running. Use POST /process_inquiry/ to interact with the chat agent."

# @app.route('/process_inquiry/', methods=['POST'])
# def process_inquiry():
#     try:
#         inquiry_data = request.get_json()
#         inquiry = Inquiry(**inquiry_data)  # Validate the input data using the Inquiry model
#     except ValidationError as e:
#         return jsonify(e.errors()), 400

#     # Append the additional prompt and file content to the inquiry question
#     inquiry_with_prompt = f"{additional_prompt}\n\nOriginal Document Content:\n{file_content}\n\n{inquiry.question}"
    
#     # Get the response from the chat agent
#     response = openai.ChatCompletion.create(
#         model="gpt-4",
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant."},
#             {"role": "user", "content": inquiry_with_prompt}
#         ]
#     )
    
#     response_text = response['choices'][0]['message']['content']
    
#     return jsonify({"response": response_text})

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)



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
        {"text": "Sentence 1", "sources": ["s1", "s2"]},
        {"text": "Sentence 22", "sources": ["s3", "s4"]},
        {"text": "Sentence 33", "sources": ["s5", "s6"]},
        {"text": "Sentence 44", "sources": ["s7", "s8"]},
        {"text": "Sentence 55", "sources": ["s9", "s10"]}
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
