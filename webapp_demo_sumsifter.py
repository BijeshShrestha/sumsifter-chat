from CQA import *
import streamlit as st

# Streamlit user interface setup
# st.set_page_config(layout="wide", page_title="Chart Question Answering", page_icon="📊")

# st.title('SumSifter: Summary to Source Document Attribution')

# Ensure conversation and response history are part of session state
if 'conversation' not in st.session_state:
    st.session_state['conversation'] = []
if 'response_history' not in st.session_state:
    st.session_state['response_history'] = []

# Display the conversation history dynamically
def display_conversation_history():
    if 'conversation' not in st.session_state:
        st.session_state['conversation'] = []
    if 'response_history' not in st.session_state:
        st.session_state['response_history'] = []

    for i in range(len(st.session_state['conversation'])):
        st.write(f"User: {st.session_state['conversation'][i]}")
        if i < len(st.session_state['response_history']):
            st.write(f"{st.session_state['response_history'][i]}")

        # Additionally check for image responses and display them
        if i < len(st.session_state['response_history']) and isinstance(st.session_state['response_history'][i], str) and st.session_state['response_history'][i].endswith('.png'):
            st.image(st.session_state['response_history'][i], caption="Generated Chart")

# Display the conversation history and any images first
display_conversation_history()

def send_message():
    user_message = st.session_state['current_message']
    if user_message:
        # Append message to conversation
        st.session_state['conversation'].append(user_message)

        # Add the prompt before sending the message to the agent
        prompt = """
        
        The document will be in the following format so that it is easier to attribute the summary to the source document and its sentences:
            id,text
            S1,<h2>SCADS 2024 Problem Book.</h2>
            S2,"Violet B., Susanna Bitters, John M. Conroy, Jordan Crouser, Sue Mi Kim, Amanda Peterson Molino, Elizabeth Richerson, Stephen Shauger, Ben Strickson, Aaron W., Julia S. Yang, April 2024"
            S3,
            S4,
            S5,
            S6,
            S7,
            S8,
            S9,<h3>1 Introduction. </h3>
            S10,The Summer Conference on Applied Data Science (SCADS) is an annual eight-week summer research program held at the Laboratory for Analytic Sciences (LAS) that is focused on the research and development of Artificial Intelligence (AI) to assist US Intelligence Community (IC) data analysts.
            S11,SCADS identifies a multi-year Grand Challenge to focus the research toward solving a current mission challenge
            S12,"SCADS brings together approximately fifty personnel each year, including faculty, graduate students, industry professionals, researchers at National Laboratories and Federally Funded Research and Development Centers (FFRDCs), and government employees from the IC, to advance the research on the current Grand Challenge."
            S13,Grand Challenge: Generate tailored daily reports for knowledge workers that capture information relevant to their individual objectives and interests.
            S14,The SCADS grand challenge is intended to be a multi-year unifying research goal of creating Tailored Daily Reports (TLDRs) for individual knowledge workers within the IC.
            S15,"These reports would be similar in some sense to the well-known President’s Daily Brief or to established commercial news aggregators, but would include a mix of classified and unclassified material, combine information from a variety of modes and formats, and be tailored to the interests and responsibilities of the individual IC worker ."
            S16,"In 2024, we continue working toward creating TLDRs and directed research efforts will fall under the broad areas of Automatic Summarization, Recommendation Systems, and Human-Machine Interaction."
            S17,"Each of these areas will also include a special emphasis on explainability and contextualization, as well as knowledge representation and dataset creation and curation."
            S18,Efforts will also include development projects that are aimed at bringing together the different areas into a demonstration application to model how the individual research projects come together to support a TLDR.
            S19,"In this document we present relevant critical challenges and research questions that address various aspects of the grand challenge, briefly discuss the motivation for those challenges and questions, and provide references and other resources for further exploration."
            S20,"We have organized this document by focus areas, and note that some challenges and questions presented might span multiple focus areas."
            S21,"For each critical challenge and research question, we attempt to identify the scope (short, medium, or long-term) of the challenge or question, and also which other challenges and questions are related."
            S22,Throughout this document we attempt to identify research areas which may be served by use of Large Language Models (LLMs) which have been an area of great focus in the field recently.
            S23,"Two ubiquitous LLMs are GPT-3.5 and GPT-4, versions of which are incorporated into ChatGPT."
            S24,<h3>2 Automatic Summarization. </h3>
        The reply for summary will always have to cite the original document and its sentences in the following format:
            id,text,sources
            1,"The Summer Conference on Applied Data Science (SCADS) focuses on AI for assisting US Intelligence Community data analysts, identifying multi-year Grand Challenges.","S10,S11"
            2,"The 2024 Grand Challenge is creating tailored daily reports for individual knowledge workers, combining classified and unclassified materials.","S13,S14"
            3,"Research areas include Automatic Summarization, Recommendation Systems, and Human-Machine Interaction, with an emphasis on explainability and contextualization.","S16,S17"
            4,"Multi-modal summarization and development projects for demonstration applications are also included.","S18,S27"
            5,"In the document, the importance of accurately summarizing multi-modal content is highlighted.","S188,S189"
            6,"Critical challenges include personalized summaries, Retrieval Augmented Generation (RAG), and handling dynamic data sources.","S46,S78,S100"
            7,"The document stresses the need for contextual citations in summaries.","S43,S44"
            8,"A groundbreaking method for summarizing complex network diagrams was introduced (S206).","S206"
            9,"For future research, the incorporation of reinforcement learning in recommendation systems is proposed.","S539"
            10,"The SCADS program will develop an AI capable of predicting geopolitical events with 90% accuracy.","S100"
            11,"Researchers are required to publish their findings in a dedicated SCADS journal for transparency.","S43"

        """
        full_message = prompt + "\n" + user_message

        # Generate a response using the agent, which might include generating an image
        latest_image_path = process_inquiry_and_show_latest_image(full_message)
        if latest_image_path:
            # If an image is generated, use the image path as the response to display
            st.session_state['response_history'].append(latest_image_path)
            st.image(latest_image_path, caption="Latest Generated Chart")

        # Otherwise, generate a text response using the agent
        else:
            response = agent.chat(full_message)
            st.session_state['response_history'].append(response)

        # Clear the current message to reset the text input box
        st.session_state['current_message'] = ""

        # # Optionally rerun to update the UI
        # st.rerun()

if 'current_message' not in st.session_state:
    st.session_state['current_message'] = ""

# Input and send buttons are defined after displaying the images
message_input = st.text_input("Enter your message here", key='current_message')
send_button = st.button("Send", on_click=send_message)

if send_button:
    st.rerun()
