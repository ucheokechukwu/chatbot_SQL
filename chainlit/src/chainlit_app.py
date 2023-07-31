import chainlit as cl
from chainlit import user_session
from langchain import PromptTemplate
# API Key
import os
from apikey import OPENAI_API_KEY

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = '5432'
DEFAULT_USERNAME = 'student'
DEFAULT_PASSWORD = 'student'
DEFAULT_DATABASE = 'postgres'

# reading postgres server login details
try:
    f = open('../data/postgres_login', 'r')
    postgres_log_params = f.read().splitlines()
    f.close()
except:
    postgres_log_params = None
    print("could not find new postgres login details. using default params")

# reading chat_model version
try:
    f = open('../data/chat_gpt_', 'r')
    chat_model = f.read()
    f.close()
except:
    chat_model = 'GPT3.5'

model_name = 'gpt-4' if chat_model == 'GPT4' else 'gpt-3.5-turbo'
print(f"Chat GPT Model is {model_name}.")


def generate_llm(model_name=model_name, API_KEY=OPENAI_API_KEY):
    # generates the LLM, only implemented with OpenAI for now

    from langchain.chat_models import ChatOpenAI
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model_name=model_name,
        temperature=0)

    # # or HuggingFace
    # from langchain import HuggingFaceHub
    # repo_id = "google/flan-t5-xxl"
    # HUGGINGFACEHUB_API_TOKEN = getpass('HUGGINGFACEHUB_API_TOKEN')
    # llm_hugging = HuggingFaceHub(
    #     repo_id=repo_id,
    #     model_kwargs={"temperature": 0.5, "max_length": 64},
    #     huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN)

    return llm


def connect_db(host=DEFAULT_HOST,
               port=DEFAULT_PORT,
               username=DEFAULT_USERNAME,
               password=DEFAULT_PASSWORD,
               database=DEFAULT_DATABASE):

    # post gres SQL setup
    from langchain.sql_database import SQLDatabase
    db = SQLDatabase.from_uri(
        f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}")
    return db


@cl.author_rename
# rename the chatbot
def rename(orig_author: str):
    rename_dict = {"Chatbot": "SQL Assistant"}
    return rename_dict.get(orig_author, orig_author)


@cl.on_chat_start
def main():
    # Instantiate the chain for that user session
    # set up database chain
    from langchain.chains import SQLDatabaseChain
    from langchain.prompts import ChatPromptTemplate
    if postgres_log_params:
        db = connect_db(*postgres_log_params)
    else:
        db = connect_db()
    llm = generate_llm()

    # Setup the database chain
    from langchain.memory import ConversationBufferMemory

    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True)
    db_chain = SQLDatabaseChain(
        llm=llm,
        database=db,
        verbose=False,
        memory=memory,
    )
    # Store the chain in the user session
    cl.user_session.set("db_chain", db_chain)


@cl.on_message
async def main(message: str):
    # Retrieve the chain from the user session
    db_chain = cl.user_session.get("db_chain")
    # Call the chain asynchronously

    res = await cl.make_async(db_chain)(message,
                                        callbacks=[cl.LangchainCallbackHandler(
                                            stream_final_answer=True,
                                        )])

    # Send the response
    await cl.Message(content=res["result"]).send()
