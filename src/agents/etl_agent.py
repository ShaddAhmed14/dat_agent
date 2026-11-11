import requests
import pandas as pd
from pathlib import Path
from langchain.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END

from ..schema import ETLAgentSchema
from ..pick_model import pick_model
from ..prompts import ETL_AGENT_PROMPT, TRANSFORM_TOOL_PROMPT

@tool
def load_data_tool(url: str, output_folder:str, format: str) -> str:
    '''
    This tool is used to load data from a URL and save it in the specified format in specified folder.
    Args:
        url (str): The URL from which to fetch the data.
        output_folder (str): The folder where the data will be saved.
        format (str): The format in which to save the data. Supported formats are 'csv', 'json', and 'parquet'.
    Returns:
        str: A message indicating the success or failure of the operation.
    '''
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()['results']  # Assuming the data is in the 'results' key of the JSON response
    except (requests.exceptions.RequestException, ValueError)  as e:
        return f"Error occurred while fetching data from {url}: {e}"

    df = pd.json_normalize(data)  # Normalize semi-structured JSON data into a flat table
    output_file = output_folder / f'data.{format}'
    try:
        if format == 'csv':
            df.to_csv(output_file, index=False)
        elif format == 'json':
            df.to_json(output_file, orient='records', lines=True)
        elif format == 'parquet':
            df.to_parquet(output_file, index=False)
        else:
            return f"Unsupported format: {format}. Supported formats are 'csv', 'json', and 'parquet'."
    except Exception as e:
        return f"Error occurred while saving data to {output_file}: {e}"

    return f"Data successfully loaded from {url} and saved to {output_file} in {format} format."

@tool
def transform_data_tool(data_path: str, output_folder: str, user_question: str, provider: str) -> str:
    '''
    Gets context from the data file at the specified path and format.
    Transforms the data based on user query and returns the transformed data.
    Args:
        data_path (str): The path to the data file.
        output_folder (str): The folder where the data will be saved.
        user_question (str): The question posed by the user.
        provider (str): The provider to use for the LLM.
    Returns:
        str: A message indicating the success or failure of the operation.
    '''
    format = Path(data_path).suffix
    if format == '.csv':
        df = pd.read_csv(data_path)
    elif format == '.json':
        df = pd.read_json(data_path, lines=True)
    elif format == '.parquet':
        df = pd.read_parquet(data_path)
    else:
        return f"Unsupported format: {format}. Supported formats are 'csv', 'json', and 'parquet'."

    context = str(df.head(5))  # Get the first 5 rows of the dataframe as context

    prompt = TRANSFORM_TOOL_PROMPT.format(user_query=user_question, data_path=data_path, output_folder=output_folder, context=context)
    llm = pick_model(provider=provider, complexity="simple")
    response = llm.invoke(prompt).content[0]['text']  # Get the text content of the response
    pandas_code = response.strip().strip('```').strip().lstrip('python').strip()

    # Execute the Pandas code
    try:
        exec(pandas_code)
        return f"Pandas code executed successfully. Transformed data saved to {output_folder}."
    except Exception as e:
        return f"Error executing Pandas code: {e}"

def llm_node(state: ETLAgentSchema) -> ETLAgentSchema:
    user_query = state.user_query
    tools = state.tools
    llm = pick_model(provider=state.provider, complexity="simple")
    llm = llm.bind_tools(tools)

    prompt = ETL_AGENT_PROMPT.format(user_query=user_query, provider=state.provider, chat_history=state.messages)

    result = llm.invoke(prompt) # we need full message - including content and tool_calls
    state.messages = [result] # appends automatically
    if not result.tool_calls: # final answer
        state.answer = result.content[0]['text']

    return state

def tool_node(state: ETLAgentSchema) -> ETLAgentSchema:
    """
    This node is responsible for invoking the appropriate tool based on the user's question and the context provided by the LLM.
    Returns the tool execution result and sends it back to the LLM for further processing.
    """
    tools = state.tools
    tools_by_name = {tool.name: tool for tool in tools}
    tool_calls = state.messages[-1].tool_calls # Get the list of tool calls, if any

    tools_results = []
    for tool_call in tool_calls:
        tool = tools_by_name[tool_call['name']]
        observation = tool.invoke(tool_call['args']) # result of the tool execution
        tools_results.append(ToolMessage(content=observation, tool_call_id = tool_call['id']))

    state.messages = tools_results
    return state

def is_tool(state: ETLAgentSchema) -> str:
    """
    Determines if the last message (LLM response) contains a tool call.
    """
    tool_calls = state.messages[-1].tool_calls
    return "tool_node" if tool_calls else END

def create_agent():
    graph = StateGraph(ETLAgentSchema)
    # NODES
    graph.add_node("llm_node", llm_node)
    graph.add_node("tool_node", tool_node)
    # EDGES
    graph.add_edge(START, "llm_node")
    graph.add_conditional_edges("llm_node", is_tool)
    graph.add_edge("tool_node", "llm_node")

    graph = graph.compile()
    graph.get_graph().draw_mermaid_png(output_file_path='etl_agent_graph.png')

    return graph

def create_state(user_query: str, provider: str) -> ETLAgentSchema:
    tools = [load_data_tool, transform_data_tool]
    return ETLAgentSchema(
        provider=provider,
        messages=[HumanMessage(content=user_query)],
        user_query=user_query,
        tools=tools,
        answer=""
    )

def run_etl_agent(user_query: str, provider: str):
    agent = create_agent()
    state = create_state(user_query, provider)
    final_state = agent.invoke(state) # returns dict
    return final_state['answer']

if __name__ == "__main__":
    user_query = "I want to extract the data from the API endpoint 'https://pokeapi.co/api/v2/pokemon' and save it to output/extract folder in the csv folder"
    provider = "google"
    answer = run_etl_agent(user_query, provider)
    print(answer)
