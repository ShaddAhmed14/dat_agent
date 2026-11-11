from dotenv import load_dotenv
from typing import Literal
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

MODEL_OPTIONS = {
    'openai': {
        'simple': 'gpt-6-luna',
        'medium': 'gpt-6-sol',
        'complex': 'gpt-6-astra'
    },
    'anthropic': {
        'simple': 'claude-haiku-4-5',
        'medium': 'claude-sonnet-5-5',
        'complex': 'claude-opus-5-5'
    },
    'google': {
        'simple': 'gemini-3.5-flash-lite',
        'medium': 'gemini-3.5-flash',
        'complex': 'gemini-3.1-pro-preview'
    },
    'ollama': {
        'simple': 'llama3.2:3b',
        'medium': 'qwen3:8b',
        'complex': 'qwen3:30b-instruct'
    }
}

def pick_model(
    provider: Literal["openai", "anthropic", "google", "ollama"],
    complexity: Literal["simple", "medium", "complex"]
    )-> object:
    """
    Pick a language model based on the provider and complexity.
    """
    models = MODEL_OPTIONS.get(provider, {})
    if not models:
        raise ValueError(f"No models available for provider '{provider}'.")

    model_name = models.get(complexity)
    if model_name is None:
        raise ValueError(f"No model found for provider '{provider}' with complexity '{complexity}'.")

    match provider:
        case "openai":
            return ChatOpenAI(model=model_name)
        case "anthropic":
            return ChatAnthropic(model=model_name)
        case "google":
            return ChatGoogleGenerativeAI(model=model_name)
        case "ollama":
            return ChatOllama(model=model_name)
        case _:
            raise ValueError(f"Unsupported provider: {provider}")
