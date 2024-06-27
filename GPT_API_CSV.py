from flask import Flask, request, jsonify
from pydantic import BaseModel, ValidationError
import os
import datetime
import csv
from dotenv import load_dotenv
from docx import Document
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import ReActAgent, FunctionCallingAgentWorker, AgentRunner
from llama_index.core.tools import FunctionTool, QueryEngineTool, ToolMetadata
from llama_index.core import VectorStoreIndex, StorageContext, SimpleDirectoryReader, load_index_from_storage
from llama_index.core.objects import ObjectIndex

app = Flask(__name__)

# Load environment variables
load_dotenv()
# Retrieve API keys from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

# Define the response text saving tool
def save_response_text(response_text, filename_prefix="response"):
    directory = "temp"
    if not os.path.exists(directory):
        os.makedirs(directory)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{directory}/{filename_prefix}_{current_time}.txt"
    with open(filename, "w") as file:
        file.write(response_text)
    return filename

response_text_tool = FunctionTool.from_defaults(
    fn=save_response_text,
    name="response_text_saver",
    description="Saves the response text to a file in the temp directory."
)

# Define the file reading tool for .docx files
def read_docx(file_path):
    document = Document(file_path)
    return '\n'.join([para.text for para in document.paragraphs])

read_file_tool = FunctionTool.from_defaults(
    fn=read_docx,
    name="file_reader",
    description="Reads the content of the .docx file at the given location."
)

# Define the CSV saving tool
def save_summary_to_csv(summary, filename="summary.csv"):
    directory = "temp"
    if not os.path.exists(directory):
        os.makedirs(directory)
    filepath = os.path.join(directory, filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["id", "text", "sources"])
        for idx, entry in enumerate(summary, 1):
            text, sources = entry
            writer.writerow([idx, text, sources])
    
    return filepath

try:
    storage_context = StorageContext.from_defaults(persist_dir="./test_files/textdata")
    text_index = load_index_from_storage(storage_context)
    index_loaded = True
except:
    index_loaded = False

if not index_loaded:
    text_docs = SimpleDirectoryReader(input_files=["./test_files/2024 Problem Book_sumsifter_short.docx"]).load_data()
    text_index = VectorStoreIndex.from_documents(text_docs)
    text_index.storage_context.persist(persist_dir="./test_files/textdata")

text_engine = text_index.as_query_engine(similarity_top_k=3)

query_engine_tools = [
    QueryEngineTool(
        query_engine=text_engine,
        metadata=ToolMetadata(
            name="textdata",
            description="Provides information about text in the document. Use a detailed plain text question as input to the tool.",
        ),
    ),
    response_text_tool,
    read_file_tool,  # Add the file reading tool to the list
]

obj_index = ObjectIndex.from_objects(
    query_engine_tools,
    index_cls=VectorStoreIndex,
)

# llm = OpenAI(model="gpt-3.5-turbo")
llm = OpenAI(model="gpt-4")
agent_worker = FunctionCallingAgentWorker.from_tools(
    tool_retriever=obj_index.as_retriever(similarity_top_k=5),
    llm=llm,
    verbose=True,
    allow_parallel_tool_calls=True,
)
agent = AgentRunner(agent_worker)

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

    additional_prompt = """
    Please add 'Namaste!' before every response. Please provide a 100-word summary of the article. 
    Each sentence in the original article ends with a sentence ID in the form of "(S1)", "(S2)", and so on. 
    Each sentence in the summary must be attributed to sentences in the original article by citing the sentence IDs, 
    Use the following json format to answer. 
            {
        "id": "doc1",
        "summary": [
            {
            "sentence": "The Summer Conference on Applied Data Science (SCADS) is an annual research program focused on the development of AI to assist the US Intelligence Community (IC) data analysts, identifying a multi-year Grand Challenge to guide the research.",
            "sources": ["S10", "S11"]
            },
            {
            "sentence": "The Grand Challenge for SCADS is to create Tailored Daily Reports (TLDRs) for individual knowledge workers within the IC, combining classified and unclassified material from various modes and formats.",
            "sources": ["S13", "S14", "S15"]
            },
            {
            "sentence": "The research efforts in 2024 will focus on Automatic Summarization, Recommendation Systems, and Human-Machine Interaction, with an emphasis on explainability, contextualization, and knowledge representation.",
            "sources": ["S16", "S17"]
            },
            {
            "sentence": "The document presents critical challenges and research questions related to the grand challenge, and identifies Large Language Models (LLMs) like GPT-3.5 and GPT-4 as potential tools for the research.",
            "sources": ["S19", "S22", "S23"]
            },
            {
            "sentence": "Automatic summarization, a key to creating a TLDR, involves both extractive and abstractive summarization, and the document encourages research in multi-modal summarization techniques.",
            "sources": ["S24", "S25", "S26", "S27"]
            }
        ]
        }

        Do not populate any summary sentence without a reference to the original sentences as S1 and so on. 
        file_path = "./test_files/2024 Problem Book_sumsifter_short.docx"

    """

    # Read the content of the file
    file_path = "./test_files/2024 Problem Book_sumsifter_short.docx"
    file_content = read_docx(file_path)

    # Append the additional prompt and file content to the inquiry question
    inquiry_with_prompt = f"{additional_prompt}\n\nOriginal Document Content:\n{file_content}\n\n{inquiry.question}"
    
    response = agent.chat(inquiry_with_prompt)  # Get the response from the chat agent
    
    # Ensure response is a string
    response_text = str(response)
    
    # Save the response text
    response_file = save_response_text(response_text)

    # Process response to extract summary sentences and their sources
    summary = []
    for line in response_text.split('\n'):
        if line.strip() and 'Namaste!' in line:  # Skip empty lines and ensure it's a summary line
            parts = line.split('Namaste!')[1].strip().split(' (S')
            text = parts[0].strip()
            sources = ', '.join(f'S{part.strip()[:-1]}' for part in parts[1:] if part.strip())
            summary.append((text, sources))
    
    # Save the summary to a CSV file
    csv_file_path = save_summary_to_csv(summary)
    
    return jsonify({"response": response_text, "file_path": response_file, "csv_file_path": csv_file_path})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
