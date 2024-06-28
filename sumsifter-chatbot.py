from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from pydantic import BaseModel, ValidationError
import os
from dotenv import load_dotenv
from docx import Document
import openai

app = Flask(__name__)
cors = CORS(app, origins=["*"])

# Load environment variables
load_dotenv()
# Retrieve API keys from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key


# Define the file reading function for .docx files
def read_docx(file_path):
    document = Document(file_path)

    r = {
        "document": document,
        "sentencesSequence": [],
        "sentences": "",
    }

    cnt_sources = 0
    for p_cnt, para in enumerate(document.paragraphs):
        texts = list(filter(None, para.text.split(".")))
        # print(para.style.name)
        for text in texts:
            cnt_sources += 1
            r["sentencesSequence"].append({"id": f"S{cnt_sources}", "text": text})
            r["sentences"] += f"{text} (S{cnt_sources})."

        cnt_sources += 1
        r["sentencesSequence"].append({"id": f"S{cnt_sources}", "text": "\n"})
        r["sentences"] += "\n"

    return r


# Define the file path
# file_path = "./test_files/2024 Problem Book_sumsifter_short.docx"
file_path = "./test_files/2024 Problem Book_sumsifter_short_2.docx"

# Read the content of the file
file_content = read_docx(file_path)

# Define the additional prompt
additional_prompt = """
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


@app.route("/")
def home():
    return "API is running. Use POST /process_inquiry/ to interact with the chat agent."


@app.route("/summary/", methods=["POST"])
@cross_origin()
def request_summary():
    # return jsonify(
    #     {
    #         "source": [
    #             {"id": "S1", "text": " SCADS 2024 Problem Book"},
    #             {"id": "S2", "text": "\n"},
    #             {"id": "S3", "text": "Violet B"},
    #             {"id": "S4", "text": ", Susanna Bitters, John M"},
    #             {"id": "S5", "text": " Conroy, R"},
    #             {"id": "S6", "text": " Jordan Crouser, Sue Mi Kim, J"},
    #             {"id": "S7", "text": " Bowman Light, Neil P"},
    #             {
    #                 "id": "S8",
    #                 "text": " Molino, Amanda Peterson, Elizabeth Richerson, Stephen Shauger, Ben Strickson, Aaron W",
    #             },
    #             {"id": "S9", "text": ", Julia S"},
    #             {"id": "S10", "text": " Yang"},
    #             {"id": "S11", "text": "\n"},
    #             {"id": "S12", "text": "April 2024"},
    #             {"id": "S13", "text": "\n"},
    #             {"id": "S14", "text": "1 Introduction"},
    #             {"id": "S15", "text": "\n"},
    #             {
    #                 "id": "S16",
    #                 "text": "The Summer Conference on Applied Data Science (SCADS) is an annual eight-week summer research program held at the Laboratory for Analytic Sciences (LAS) that is focused on the research and development of Artificial Intelligence (AI) to assist US Intelligence Community (IC) data analysts",
    #             },
    #             {
    #                 "id": "S17",
    #                 "text": " SCADS identifies a multi-year Grand Challenge to focus the research toward solving a current mission challenge",
    #             },
    #             {
    #                 "id": "S18",
    #                 "text": "  SCADS brings together approximately fifty personnel each year, including faculty, graduate students, industry professionals, researchers at National Laboratories and Federally Funded Research and Development Centers (FFRDCs), and government employees from the IC, to advance the research on the current Grand Challenge",
    #             },
    #             {"id": "S19", "text": "\n"},
    #             {
    #                 "id": "S20",
    #                 "text": "Grand Challenge: Generate tailored daily reports for knowledge workers that capture information relevant to their individual objectives and interests",
    #             },
    #             {"id": "S21", "text": " "},
    #             {"id": "S22", "text": "\n"},
    #             {
    #                 "id": "S23",
    #                 "text": "The SCADS grand challenge is intended to be a multi-year unifying research goal of creating Tailored Daily Reports (TLDRs) for individual knowledge workers within the IC",
    #             },
    #             {
    #                 "id": "S24",
    #                 "text": " These reports would be similar in some sense to the well-known President’s Daily Brief or to established commercial news aggregators, but would include a mix of classified and unclassified material, combine information from a variety of modes and formats, and be tailored to the interests and responsibilities of the individual IC worker",
    #             },
    #             {"id": "S25", "text": " "},
    #             {"id": "S26", "text": "\n"},
    #         ],
    #         "summary": [
    #             {
    #                 "sources": ["S16"],
    #                 "text": "The Summer Conference on Applied Data Science (SCADS) is an annual research program done at the Laboratory for Analytic Sciences (LAS) to assist US Intelligence Community (IC) data analysts.",
    #             },
    #             {
    #                 "sources": ["S17"],
    #                 "text": "SCADS identifies a multi-year Grand Challenge to focus the research toward solving a current mission challenge.",
    #             },
    #             {
    #                 "sources": ["S18"],
    #                 "text": "SCADS brings around fifty personnel each year, including faculty, students, professionals, researchers, and government employees from IC, for its research.",
    #             },
    #             {
    #                 "sources": ["S20"],
    #                 "text": "The Grand Challenge is focused on creating daily reports for knowledge workers that capture information relevant to their individual objectives and interests.",
    #             },
    #             {
    #                 "sources": ["S24"],
    #                 "text": "These tailored daily reports would include classified and unclassified material, information from a variety of modes, and be customized to the interests of the individual IC worker.",
    #             },
    #         ],
    #     }
    # )

    try:
        inquiry_data = request.get_json()
        inquiry = Inquiry(
            **inquiry_data
        )  # Validate the input data using the Inquiry model
    except ValidationError as e:
        return jsonify(e.errors()), 400

    # Append the additional prompt and file content to the inquiry question
    inquiry_with_prompt = f"{additional_prompt}\n\nOriginal Document Content:\n----------\n{file_content["sentences"]}\n----------\n{inquiry.question}"

    # Get the response from the chat agent
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": inquiry_with_prompt},
        ],
    )

    response_text = response["choices"][0]["message"]["content"].strip()

    # Extract JSON from the response text
    try:
        start_index = response_text.find("{")
        end_index = response_text.rfind("}") + 1
        json_response = response_text[start_index:end_index]
        json_response = eval(json_response)  # Convert string to dict for JSON response
    except Exception as e:
        return jsonify({"error": "Failed to parse response", "details": str(e)}), 500

    json_response["source"] = file_content["sentencesSequence"]
    return jsonify(json_response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
