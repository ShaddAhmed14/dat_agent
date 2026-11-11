from pydantic import BaseModel, Field
from typing import Annotated, Literal
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages # adds messages by id. ensures no duplicates

models = Literal["openai", "anthropic", "google", "ollama"]

class SQLAgentSchema(BaseModel):
    provider: Literal[models] = Field(..., description="The provider of the language model to be used by the SQL agent. This field determines which language model will be utilized for generating SQL queries and processing user input.")
    messages: Annotated[list[AnyMessage], add_messages] = Field(..., description="A list of messages exchanged between the user and the SQL agent.")
    user_query: str = Field(..., description="The uncrated question provided by the user.")
    sql_query: str = Field(..., description="The final SQL query that will be executed against the database. This query may include additional modifications or optimizations made by the SQL agent.")
    query_safe: Literal[True, False] = Field(..., description="A boolean flag indicating whether the final SQL query is safe to execute. This flag is determined based on various safety checks and validations performed on the query.")
    rejection_reason: str = Field(default="", description="If the SQL query is deemed unsafe, this field provides a brief explanation of the potential risks associated with the query. It may include information about why the query is considered unsafe and suggestions for modifications to make it safe.")
    query_result: str = Field(..., description="SQL query result.")
    answer: str = Field(..., description="The final answer to the user's question, derived from the results of the SQL query.")
    error: str | None = Field(None, description="An optional field that captures any errors encountered during the execution of the SQL query or the processing of the user's request. If an error occurs, this field will contain a descriptive message detailing the nature of the error and any relevant information for troubleshooting.")

class SQLSafetySchema(BaseModel):
    query_safe: Literal[True, False] = Field(..., description="A boolean flag indicating whether the final SQL query is safe to execute. This flag is determined based on various safety checks and validations performed on the query.")
    explanation: str = Field(..., description="A brief explanation of the potential risks associated with the SQL query if it is deemed unsafe. This field provides insights into why the query may be considered unsafe and suggests modifications to make it safe.")

class ETLAgentSchema(BaseModel):
    provider: Literal[models] = Field(..., description="The provider of the language model to be used by the ETL agent. This field determines which language model will be utilized for generating SQL queries and processing user input.")
    messages: Annotated[list[AnyMessage], add_messages] = Field(..., description="A list of messages exchanged between the user and the ETL agent.")
    user_query: str = Field(..., description="The uncrated question provided by the user.")
    tools: list = Field(..., description="A list of tools available to the ETL agent for data extraction, transformation, and loading tasks. These tools may include functions or methods for data manipulation, cleaning, and analysis.")
    answer: str = Field(..., description="The final answer to the user's question, derived from the results of the ETL process. This answer may include insights, summaries, or conclusions based on the data processed by the ETL agent.")
    error : str | None = Field(None, description="An optional field that captures any errors encountered during the execution of the ETL process or the processing of the user's request. If an error occurs, this field will contain a descriptive message detailing the nature of the error and any relevant information for troubleshooting.")

class RouterAgentSchema(BaseModel):
    provider: Literal[models] = Field(..., description="The provider of the language model to be used by the Router agent. This field determines which language model will be utilized for analyzing the user's query and determining the appropriate routing to either the ETL agent or the SQL agent.")
    messages: Annotated[list[AnyMessage], add_messages] = Field(..., description="A list of messages exchanged between the user and the Router agent.")
    user_query: str = Field(..., description="The uncrated question provided by the user.")
    route_to: Literal["etl_agent", "sql_agent"] | None = Field(..., description="The determined route for the user's query, indicating whether it should be handled by the ETL agent or the SQL agent based on the analysis of the query's content and context.")
    answer: str = Field(..., description="The final answer to the user's question, derived from the results of the ETL or SQL process. This answer may include insights, summaries, or conclusions based on the data processed by the respective agent.")
    error : str | None = Field(None, description="An optional field that captures any errors encountered during the execution of the routing process or the processing of the user's request. If an error occurs, this field will contain a descriptive message detailing the nature of the error and any relevant information for troubleshooting.")

class RouteToSchema(BaseModel):
    route_to: Literal["etl_agent", "sql_agent"] = Field(..., description="The determined route for the user's query, indicating whether it should be handled by the ETL agent or the SQL agent based on the analysis of the query's content and context.")
