import os
import uuid
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage
from .schema import RouterAgentSchema
from .agents.sql_agent import run_sql_agent
from .agents.etl_agent import run_etl_agent
from .models.clef import ClefModel

# NODES
def route_node(state: RouterAgentSchema) -> str:
    clef_model = ClefModel()
    response = clef_model.route_to(state.user_query)
    if response is None:
        raise ValueError("Clef model did not return a valid response for routing.")
    state.route_to = response
    return state

def etl_node(state: RouterAgentSchema) -> RouterAgentSchema:
    result = run_etl_agent(state.user_query, state.provider)
    state.answer = result
    return state

def sql_node(state: RouterAgentSchema) -> RouterAgentSchema:
    result = run_sql_agent(state.user_query, state.provider, history=state.messages)
    state.answer = result.get('answer')
    return state

# Conditional Node
def next_node(state: RouterAgentSchema) -> str:
    route_to = state.route_to
    if route_to == "etl_agent":
        return 'etl_node'
    elif route_to == "sql_agent":
        return 'sql_node'
    else:
        raise ValueError(f"Invalid route_to value: {route_to}. Expected 'etl_agent' or 'sql_agent'.")

def create_state(user_query: str, provider: str) -> RouterAgentSchema:
    return RouterAgentSchema(
        messages=[],
        provider=provider,
        user_query=user_query,
        route_to=None,
        answer=""
    )

def create_router_agent(render_graph: bool = False) -> StateGraph:
    graph = StateGraph(RouterAgentSchema)

    # NODES
    graph.add_node("route_node", route_node)
    graph.add_node("etl_node", etl_node)
    graph.add_node("sql_node", sql_node)

    # EDGES
    graph.add_edge(START, "route_node")
    graph.add_conditional_edges("route_node", next_node)
    graph.add_edge("etl_node", END)
    graph.add_edge("sql_node", END)

    checkpointer = InMemorySaver()
    graph = graph.compile(checkpointer=checkpointer)
    if render_graph:
        graph.get_graph().draw_mermaid_png(output_file_path='router_agent_graph.png')
    return graph

if __name__ == "__main__":
    '''Sample Questions
        # ETL
        # user_query = "I want to extract the data from the API endpoint 'https://pokeapi.co/api/v2/pokemon' and save it to output/extract folder in the csv folder"
        user_query = "I want to transform the data stored in the 'output/extract/data.csv' file and save the transformed data in the 'output/transform' folder in the csv format. The transformation should filter the data to show bulbasaur pokemon only."

        # SQL
        # user_query = "What are the unique vehicle makes?"
    '''
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    provider = os.getenv("provider")
    graph = create_router_agent()

    state = create_state(user_query="", provider=provider)
    while True:
        user_input = input("Enter your query (or type 'q' to quit): ")
        if user_input.lower() == 'q':
            break
        state.user_query = user_input
        state.messages = [HumanMessage(content=user_input)]
        result = graph.invoke(state, config=config)
        answer = result.get('answer')
        print(f"Answer: {answer}")