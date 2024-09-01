import streamlit as st
from langchain_community.chat_models import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.output_parsers import StrOutputParser

from dotenv import load_dotenv
load_dotenv()

def get_llminfo():
    st.sidebar.header("Options", divider='rainbow')
    tip1="Select a model you want to use."
    model = st.sidebar.radio("Choose LLM:",
                                  ("gemini-1.5-flash",
                                   "gemini-1.5-pro",
                                   "llama3","mixtral-8x7b-32768",
                                   ), help=tip1)
    
    return model

llm1 = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
llm2 = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0)
llm3 = ChatOllama(model="llama3", temperature=0)
llm4 = ChatGroq(model="mixtral-8x7b-32768", temperature=0)

def connectDatabase(username, port, host, password, database):
    mysql_uri = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
    st.session_state.db = SQLDatabase.from_uri(mysql_uri)

def getDatabaseSchema():
    return st.session_state.db.get_table_info() if st.session_state.db else "Please connect to database"

def getQueryFromLLM(question,model):
    template = """below is the schema of MYSQL database, read the schema carefully about the table and column names. Also take care of table or column name case sensitivity.
    Finally answer user's question in the form of SQL query.

    {schema}
    
    please only provide the SQL query and nothing else

    for example:
    question: how many albums we have in database
    SQL query: SELECT COUNT(*) FROM album;
    
    question: How many customers are from Brazil in the database ?
    SQL query: SELECT COUNT(*) FROM customer WHERE country= "Brazil";
    
    question: What are the titles of all albums and their corresponding artists?
    SQL query: SELECT Album.Title, Artist.Name FROM Album JOIN Artist ON Album.ArtistId = Artist.ArtistId;
    question:Show the top 10 most expensive tracks
    SQL query: SELECT Name, UnitPrice FROM Track ORDER BY UnitPrice DESC LIMIT 10;
    
    question: Find the most popular genre based on the number of tracks?
    SQL query: SELECT Genre.Name, COUNT(*) AS TrackCount FROM Genre JOIN Track ON Genre.GenreId = Track.GenreId  GROUP BY Genre.Name ORDER BY TrackCount DESC LIMIT 1;
    
    question: Retrieve all tracks in a specific album titled 'Jagged Little Pill'.
    SQL query: SELECT Track.Name FROM Track JOIN Album ON Track.AlbumId = Album.AlbumId 
    WHERE Album.Title = 'Jagged Little Pill';
    
    question: What are the details of all tracks that are longer than 300000 milliseconds?
    SQL query: SELECT Name, Milliseconds FROM Track WHERE Milliseconds > 300000;

    your turn :
    question: {question}
    SQL query :
    please only provide the SQL query and nothing else
    """
       
    prompt = ChatPromptTemplate.from_template(template)
    if model== "gemini-1.5-flash":
     llm = llm1
    if model== "gemini-1.5-pro":   #gemini-1.5-pro
     llm = llm2
    if model== "llama3":
     llm = llm3
    if model== "mixtral-8x7b-32768":
     llm = llm4
    
    chain = prompt | llm | StrOutputParser()

    response1 = chain.invoke({
        "question": question,
        "schema": getDatabaseSchema()
    })
    #in google gemini model output is found with '''sql\n . so we use strip('''sql\n') method
    if model== "gemini-1.5-flash" or model== "gemini-1.5-pro":
        return response1.strip('```sql\n').strip('\n```') 
    if model== "llama3" or model== "mixtral-8x7b-32768":
        return response1

def runQuery(query):
    return st.session_state.db.run(query) if st.session_state.db else "Please connect to database"

def getResponseForQueryResult(question, query,model, result):
    template2 = """below is the schema of MYSQL database, read the schema carefully about the table and column names of each table.
    Also look into the conversation if available
    Finally write a response in natural language by looking into the conversation and result.

    {schema}

    Here are some example for you:
    question: how many albums we have in database
    SQL query: SELECT COUNT(*) FROM album;
    Result : [(34,)]
    Response: There are 34 albums in the database.

    question: how many users we have in database
    SQL query: SELECT COUNT(*) FROM customer;
    Result : [(59,)]
    Response: There are 59  users in the database.

    question: how many users above are from india we have in database
    SQL query: SELECT COUNT(*) FROM customer WHERE country=india;
    Result : [(4,)]
    Response: There are 4  users in the database.

    your turn to write response in natural language from the given result :
    question: {question}
    SQL query : {query}
    Result : {result}
    Response:
    """
  
    prompt2 = ChatPromptTemplate.from_template(template2)
    if model== "gemini-1.5-flash":
     llm = llm1
    if model== "gemini-1.5-pro":   #gemini-1.5-pro
     llm = llm2
    if model== "llama3":
     llm = llm3
    if model== "mixtral-8x7b-32768":
     llm = llm4
    chain2 = prompt2 | llm 

    response2 = chain2.invoke({
        "question": question,
        "schema": getDatabaseSchema(),
        "query": query,
        "result": result
    })

    return response2.content

st.set_page_config(
    page_icon=":speech_balloon:",
    page_title="Chat with MYSQL DB",
    layout="centered"
)
st.title('Ask Questions To Your Database')
model = get_llminfo()


with st.sidebar:
    st.title('Connect to database')
    st.text_input(label="Host", key="host", value="localhost")
    st.text_input(label="Port", key="port", value="3306")
    st.text_input(label="Username", key="username", value="root")
    st.text_input(label="Password", key="password", value="root123", type="password")
    st.text_input(label="Database", key="database", value="rag_test")
    connectBtn = st.button("Connect")
   

if connectBtn:
    with st.spinner("Connecting to database .."):
        connectDatabase(
            username=st.session_state.username,
            port=st.session_state.port,
            host=st.session_state.host,
            password=st.session_state.password,
            database=st.session_state.database,
        )
        x =st.success("Database connected")
        if x:
            st.chat_message('assistant').markdown("Hello! I'm a SQL assistant. Ask me anything about your database")
            
question = st.chat_input('Chat with your mysql database')

if "chat" not in st.session_state:
    st.session_state.chat = []

if question:
    if "db" not in st.session_state:
        st.error('Please connect database first.')
    else:
        st.session_state.chat.append({
            "role": "user",
            "content": question
        })

        query = getQueryFromLLM(question, model)    
        print(query)
        result = runQuery(query)
        print(result)
        response = getResponseForQueryResult(question, query,model, result)
        st.session_state.chat.append({
            "role": "assistant",
            "content": response
        })
   
for chat in st.session_state.chat:
    st.chat_message(chat['role']).markdown(chat['content'])
    
