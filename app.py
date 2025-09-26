from flask import Flask, render_template, jsonify, request
from src.helper import download_embeddings
from langchain_pinecone import PineconeVectorStore
# from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM
from src.prompt import *

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from src.db import save_chat 
import os
from dotenv import load_dotenv
load_dotenv()  # this reads the .env file and sets os.environ

app= Flask(__name__)

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

embeddings = download_embeddings()

index_name = "medical-chatbot"

docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

retriever = docsearch.as_retriever(search_type="similarity",search_kwargs={"k":2})
# chatModel = ChatOpenAI(model="gpt-4o")

chatModel = OllamaLLM(model="mistral")  # max_tokens removed

# prompt = ChatPromptTemplate.from_messages(
#     [
#         ("system", system_prompt),
#         ("human", "{input}"),
#     ]
# )
prompt_style = "cot"  # "default", "few_shot", "cot", "role", "cot"

chosen_prompt = {
    "default": system_prompt,
    "few_shot": system_prompt_few_shot,
    "cot": system_prompt_cot,
    "role": system_prompt_role,
    "json": system_prompt_json
}[prompt_style]

prompt = ChatPromptTemplate.from_messages(
    [("system", chosen_prompt), ("human", "{input}")]
)

question_answer_chain = create_stuff_documents_chain(chatModel, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)



@app.route('/')
def index():
    return render_template('chat.html')


# @app.route("/get", methods=["GET", "POST"])
# def chat():
#     user_msg = request.form["msg"]
#     input = user_msg
#     print(input)
#     response = rag_chain.invoke({"input": user_msg})
#     print("Response : ", response["answer"])
#     bot_msg = response["answer"]
#     save_chat(user_msg,bot_msg)

#     return str(bot_msg)

@app.route("/get", methods=["GET", "POST"])
def chat():
    user_msg = request.form["msg"]
    print("User Input:", user_msg)
    
    # call RAG chain with max_output_tokens
    response = rag_chain.invoke(
        {"input": user_msg},
        llm_kwargs={"max_output_tokens": 512}
    )
    print("Raw RAG response:", response)
    
    bot_msg = response.get("answer", str(response))
    bot_msg = bot_msg.replace("\n", " ").strip()
    
    save_chat(user_msg, bot_msg)
    
    return str(bot_msg)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port= 8080, debug= True)