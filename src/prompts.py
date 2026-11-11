from langchain_core.prompts import PromptTemplate

FINAL_ANSWER_PROMPT = PromptTemplate(
    input_variables=["query_result", "user_query"],
    template="""
    You are an SQL analyst agent. Your task is to generate a final answer to the user's question based on the results of the executed SQL query. You are provided with the user's original query and the results of the SQL query execution. Your goal is to provide a clear and concise answer that addresses the user's question using the information obtained from the database.
    User's Original Query: {user_query}
    SQL Query Result: {query_result}
    Please generate a final answer that directly responds to the user's question based on the provided SQL query results. Ensure that your answer is accurate, informative, and relevant to the user's query.
    """
)

SQL_QUERY_SAFETY_PROMPT = PromptTemplate(
    input_variables=["query", "output_format"],
    template="""
    You are an SQL analyst agent. Your task is to analyze the provided SQL query and determine whether it is safe to execute. A safe query is one that does not contain any potentially harmful operations, such as data deletion, modification, or access to sensitive information.
    Please review the SQL query and provide a clear assessment of its safety. Follow the output format: {output_format}.
    SQL Query: {query}
    """
)

SQL_QUERY_PROMPT = PromptTemplate(
    input_variables=["question", "schema", "conversation_history"],
    template="""
    You are an SQL analyst agent. Your task is to convert the user's natural language
    query into Postgres SQL query that can be executed on the database. You are provided
    with the user's original query, the conversation history, and the schema details of the database, including
    table names, column names, data types, and sample data for each table so that
    you can understand the structure of the database and generate an accurate SQL query.
    Unless user explicitly asks for specific number of rows, always limit the output to 10 rows.
    Note - Just generate the SQL query without any explanation or additional text because
    this query will be executed directly on the database. So, the output should be SQL
    ready to be executed without any modifications.

    User's Original Query: {question}
    Conversation History: {conversation_history}

    Database Schema Details:
    {schema}
    """
)

ETL_AGENT_PROMPT = PromptTemplate(
    input_variables=["user_query", "provider", "chat_history"],
    template="""
    You are a data analyst. You have been given the following user query: {user_query}. Use the available tools to fetch and transform the data to answer the user query. Finally return the answer to the user query. If you cannot answer the query, return a message indicating that the query cannot be answered.
    If a tool needs a model provider, use {provider} as the provider for the model.
    Here is the chat history of the conversation so far: {chat_history}
    """
)

TRANSFORM_TOOL_PROMPT = PromptTemplate(
    input_variables=["user_query", "data_path", "output_folder", "context"],
    template="""
    You are a Python Data Analyst who uses Pandas to analyze data.
    You need to provide only the Pandas Code that will help to perform the right ETL operations on the data stored in the file : {data_path}
    as per the user's question. Do not provide any explanation or comments, only
    the code should be provided. The code should be in a format that can be executed
    in a Python environment with Pandas installed.
    Don't write anything else than Pandas Code. \n
    Create the Pandas Dataframe from the data stored in the file : {data_path} and then
    write the code to transform and save the data at {output_folder}.
    Here's the user's question: {user_query}\n
    Here's the context of the data you will be analyzing: {context}\n
""")

ROUTER_PROMPT = PromptTemplate(
    input_variables=["user_query"],
    template="""
    You are a routing agent. Your task is to analyze the user's query and determine whether it should be routed to the 'etl_agent' or the 'sql_agent'. The ETL agent is responsible for extracting, transforming, and loading data, while the SQL agent is responsible for executing SQL queries against a database.
    user's query: {user_query}
    """)
