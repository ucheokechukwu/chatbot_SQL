from langchain.sql_database import SQLDatabase
from langchain.llms.openai import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import SQLDatabaseChain
import streamlit as st

# default values
postgres_log = dict(st.secrets.db_credentials)
chat_model = 'GPT3.5'
API_KEY = st.secrets["apikey"]



def generate_llm(chat_model=chat_model, API_KEY=API_KEY):
    """generates llm"""
    model_name = 'gpt-4' if chat_model == 'GPT4' else 'gpt-3.5-turbo'
    print(f"Chat GPT Model is {model_name}.")
    from langchain.chat_models import ChatOpenAI
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
    print("Connected to: ", host, port, username, password, database)
    return db

# streamlit framework and state variables
st.title("SQL ChatBot")
# Initialize chat history and sidebar visibility
if "messages" not in st.session_state:
    st.session_state.messages = []
if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False  
# initialize db
if 'postgres_log' not in st.session_state:
    st.session_state.postgres_log = postgres_log   
# initialize chat_gpt
if 'chat_model' not in st.session_state:
    st.session_state.chat_model = chat_model
# initialize memory
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = ""   
    
    
    
    

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
QUERY = """
Given an input question: {question}

use the previous chat history as the context to first create a syntactically correct postgresql query to run, 
then look at the results of the query and return the answer.

This is the chat history:
{chat_history}

Use the following format:

Question: Question here
SQLQuery: SQL Query to run
SQLResult: Result of the SQLQuery
Answer: Final answer here
"""
prompt = PromptTemplate(template=QUERY, 
                        input_variables=['question','chat_history'])
                        
db = connect_db(st.session_state.postgres_log)
llm = generate_llm(chat_model=st.session_state.chat_model)
db_chain = SQLDatabaseChain(
    llm=llm,
    database=db,
    verbose=True)

# chatbot



# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if query := st.chat_input("Type in your SQL question here"):
    # Display user message in chat message container
    st.chat_message("user").markdown(query)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": query})
    
    
    
    
    try:
        print(st.session_state.chat_history)
        response = db_chain.run(prompt.format(
                        question=query, 
                        chat_history=st.session_state.chat_history))
        st.session_state.chat_history += ('Human: '+query+'\nAI: '+response+'\n')
    except:
        response = f"""I cannot find a suitable answer from the SQLChat. Please rephrase and try again."""
                                  
                    
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append(
        {"role": "assistant", "content": response})
