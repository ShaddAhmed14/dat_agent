from ..prompts import SQL_QUERY_PROMPT, FINAL_ANSWER_PROMPT
from ..schema import SQLAgentSchema
from ..pick_model import pick_model
from ..database import Database
from ..models.clef import ClefModel

from langgraph.graph import StateGraph
from langgraph.graph import START, END

# ----------------------- NODES -----------------------
def create_sql_query(state: SQLAgentSchema) -> SQLAgentSchema:
    '''
    This function generates a SQL query based on the user's natural language query and the database schema details.
    '''
    db_obj = Database()
    schema_info = db_obj.get_schema_details()  # Fetch schema details

    user_query = state.user_query
    prompt = SQL_QUERY_PROMPT.format(question=user_query, schema=schema_info, conversation_history=state.messages)

    llm = pick_model(provider=state.provider, complexity="simple")
    result = llm.invoke(prompt).content[0]['text'] # TODO is there a better way - do all llm return the same output format

    state.sql_query = result
    return state

def is_query_safe(state: SQLAgentSchema) -> SQLAgentSchema:
    '''
    This function checks the safety of the generated SQL query.
    '''
    print('is_query_safe called with messages:', state.messages)
    clef_model = ClefModel()
    response = clef_model.is_safe(state.sql_query)

    state.query_safe = response
    if not state.query_safe:
        state.rejection_reason = "The SQL query is potentially unsafe to execute. Our clef model has flagged it as such."
    return state

def reject_execution(state: SQLAgentSchema) -> SQLAgentSchema:
    '''
    This function handles the rejection of SQL query execution when the query is deemed unsafe. It updates the state with a rejection reason and prepares a message to inform the user about the rejection.
    '''
    print('reject_execution called with messages:', state.messages)

    rejection_reason = state.rejection_reason
    state.answer = f"Query execution rejected. Reason: {rejection_reason}"
    return state

def execute_sql_query(state: SQLAgentSchema) -> SQLAgentSchema:
    '''
    This function executes the SQL query against the database and retrieves the results. It uses the Database class to establish a connection, execute the query, and fetch the results. The results are then stored in the state for further processing.
    '''
    print('execute_sql_query called with messages:', state.messages)

    db_obj = Database()
    sql_query = state.sql_query

    result = db_obj.execute_query(sql_query)
    state.query_result = str(result)  # Convert result to string for storage
    return state

def generate_final_answer(state: SQLAgentSchema) -> SQLAgentSchema:
    '''
    This function generates the final answer to the user's question based on the results of the executed SQL query. It uses a language model to analyze the query results and provide a clear and concise answer that addresses the user's original question.
    '''
    print('generate_final_answer called with messages:', state.messages)

    user_query = state.user_query
    query_result = state.query_result

    prompt = FINAL_ANSWER_PROMPT.format(query_result=query_result, user_query=user_query)
    llm = pick_model(provider=state.provider, complexity="simple")
    result = llm.invoke(prompt).content
    state.answer = result[0]['text']  # Get the text content of the response
    return state

def error_node(state: SQLAgentSchema) -> SQLAgentSchema:
    '''
    This function handles any errors that occur during the execution of the SQL agent. It updates the state with an error message and prepares a message to inform the user about the error.
    '''
    error_message = state.error if state.error else "An unknown error occurred."
    state.answer = f"An error occurred during processing: {error_message}"
    return state

# ----------------------- CONDITIONAL NODES -----------------------
def check_query_safety(state: SQLAgentSchema) -> str:
    # return "safe" if state.query_safe else "unsafe"
    return "execute_sql_query" if state.query_safe else "reject_execution"

# ----------------------- GRAPH CREATION -----------------------

def create_agent_state(user_query: str, provider: str) -> SQLAgentSchema:
    return SQLAgentSchema(
        messages=[],
        provider=provider,
        user_query=user_query,
        sql_query="",
        query_safe=False,
        rejection_reason="",
        query_result="",
        answer=""
    )

def create_agent(render_graph: bool = False) -> SQLAgentSchema:
    graph = StateGraph(SQLAgentSchema)

    # NODES
    graph.add_node("create_sql_query", create_sql_query)
    graph.add_node("is_query_safe", is_query_safe)
    graph.add_node("reject_execution", reject_execution)
    graph.add_node("execute_sql_query", execute_sql_query)
    graph.add_node("generate_final_answer", generate_final_answer)
    # EDGES
    graph.add_edge(START, "create_sql_query")
    graph.add_edge("create_sql_query", "is_query_safe")
    graph.add_conditional_edges("is_query_safe", check_query_safety)
    graph.add_edge("reject_execution", END)
    graph.add_edge("execute_sql_query", "generate_final_answer")
    graph.add_edge("generate_final_answer", END)

    graph = graph.compile()
    if render_graph:
        graph.get_graph().draw_mermaid_png(output_file_path='sql_agent_graph.png')

    return graph

def run_sql_agent_detailed(user_query: str, provider: str, history: list | None = None):
    state = create_agent_state(user_query, provider)
    state.messages = history or []  # Set the initial message history
    agent_graph = create_agent()
    try:
        final_state = agent_graph.invoke(state) # returns dict
    except Exception as e:
        return {
            "provider": provider,
            "user_query": user_query,
            "error": f"An error occurred during processing: {e}",
            "answer": None
        }
    return final_state

def run_sql_agent(user_query: str, provider: str, history: list):
    final_state = run_sql_agent_detailed(user_query, provider, history=history)
    return {'answer': final_state.get('answer'), 'messages': final_state.get('messages', [])}

if __name__ == "__main__":
    user_query = "What are the unique vehicle makes?"
    provider = "google"
    response = run_sql_agent_detailed(user_query, provider)
    if response.get('error') is not None: # if present
        print(f"Received an error: {response.get('error')} \nFull output: {response}")
    else:
        print(f"Final Answer: {response.get('answer')}")
