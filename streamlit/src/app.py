from langchain import PromptTemplate
from langchain.prompts import ChatPromptTemplate
from langchain.chains import SQLDatabaseChain, LLMChain
import os
import streamlit as st
from langchain.llms import OpenAI

# default values
postgres_log = dict(st.secrets.db_credentials)
chat_model = 'GPT3.5'
API_KEY = st.secrets["apikey"]


def generate_llm(chat_model=chat_model, API_KEY=API_KEY):
    """generates llm"""
    model_name = 'gpt-4' if chat_model == 'GPT4' else 'gpt-3.5-turbo'
    print(f"Chat GPT Model is {model_name}.")
    from langchain.chat_models import ChatOpenAI
    # API_KEY = OPENAI_API_KEY
    llm = ChatOpenAI(
        openai_api_key=API_KEY,
        model_name=model_name,
        temperature=0)
    return llm


def connect_db(postgres_log):
    """connect to postgres SQL server using langchain and pyscopg"""
    host, port, username, password, database = postgres_log.values()
    from langchain.sql_database import SQLDatabase
    # post gres SQL setup
    db = None
    try:
        db = SQLDatabase.from_uri(
            f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}")
    except:
        st.error("Error connecting to the postgres SQL database")
    
    print(host, port, username, password, database)
    return db

# streamlit framework and state variables
st.title("SQL ChatBot")
# Initialize chat history and sidebar visibility
if "messages" not in st.session_state:
    st.session_state.messages = []
if "buffer_memory" not in st.session_state:
    st.session_state.buffer_memory= None
if "last_valid" not in st.session_state:
    st.session_state.last_valid = " "
if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False  
# initialize db
if 'postgres_log' not in st.session_state:
    st.session_state.postgres_log = postgres_log   
# initialize chat_gpt
if 'chat_model' not in st.session_state:
    st.session_state.chat_model = chat_model

# sidebar to change chatgpt and server settings
with st.sidebar:
    st.session_state.chat_model = st.selectbox('Select the Chat GPT Version',
                            ("GPT3.5", "GPT4"))
    st.checkbox("Check to use default server connection", key="disabled")

    with st.form("Postgres_Settings"):
        st.write("Postgres SQL Server settings")
        postgres_input = postgres_log.copy()
        for key in postgres_log.keys():
            postgres_input[key] = st.text_input(
                key, disabled=st.session_state.disabled)
        submitted = st.form_submit_button(
            "Submit", disabled=st.session_state.disabled)
        if submitted:
            st.session_state.postgres_log = postgres_input


# Setup the database chain
template = "Answer this question: {question}"

llm_prompt = PromptTemplate(template=template, input_variables=['question'])


db = connect_db(st.session_state.postgres_log)
llm = generate_llm(chat_model=st.session_state.chat_model)
# back up if db_chain has no answers
chain = LLMChain(llm=llm, prompt=llm_prompt)
db_chain = SQLDatabaseChain(
    llm=llm,
    database=db,
    verbose=True,
    memory=st.session_state.buffer_memory,)

# chatbot
print(st.session_state.buffer_memory)



# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Type in your SQL question here"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    try:
        response = db_chain.run(st.session_state.last_valid + prompt)
        st.session_state.last_valid = response + ' '
    except:
        response = f"""I cannot find a suitable answer from the SQLChat. But the main ChatBot thinks:\n
                    {chain.run(prompt)}"""
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append(
        {"role": "assistant", "content": response})
