"""
OpenAI Integration Module

This module provides a set of utilities for interacting with OpenAI's language models and embeddings API.
It abstracts away the complexity of direct API calls and provides a consistent interface for AI model interactions.

The module includes functions for:
- Creating OpenAI API clients with appropriate configuration
- Generating text completions using OpenAI's chat models
- Creating embeddings for text using OpenAI's embedding models

This integration is designed to work with async APIs for better performance in web applications.
All functions are designed to handle errors gracefully and provide standardized response formats.

Requirements:
- OpenAI Python SDK: pip install openai
- Valid OpenAI API key or compatible service (like Ollama with OpenAI-compatible API)

Usage examples are provided in the docstrings for each function.
"""

# Standard library imports
import json
from dataclasses import dataclass
from typing import Union, Dict, List, Literal

# Third-party imports
from openai import AsyncClient as AsyncOpenaiClient

# Local application imports
from client.ResponseGetData import ResponseGetDataOpenAi


def generate_openai_client(api_key: str,
                           base_url: str = None,
                           is_ollama: bool = False) -> AsyncOpenaiClient:
    """
    Creates an asynchronous OpenAI client with the appropriate configuration.
    
    This function generates a properly configured client for interacting with OpenAI's API
    or compatible alternatives like Ollama. It handles the configuration differences
    between standard OpenAI API and self-hosted alternatives.
    
    Args:
        api_key (str): The API key for authentication with OpenAI or compatible service
        base_url (str, optional): The base URL for API calls, required for self-hosted
            alternatives or non-standard OpenAI endpoints
        is_ollama (bool, optional): Flag indicating if connecting to Ollama instead of OpenAI,
            which may require different configuration settings
            
    Returns:
        AsyncOpenaiClient: A configured async client for making API calls
        
    Raises:
        ImportError: If the OpenAI package is not installed
        
    Example:
        ```python
        # Standard OpenAI client
        client = generate_openai_client(api_key="your-openai-key")
        
        # Ollama client
        ollama_client = generate_openai_client(
            api_key="ollama", 
            base_url="http://localhost:11434/v1",
            is_ollama=True
        )
        ```
    """

    if is_ollama:
        return AsyncOpenaiClient(
            api_key=api_key,
            base_url=base_url,
        )

    return AsyncOpenaiClient(api_key=api_key)


@dataclass
class ChatMessage:
    """
    Data class representing a message in a chat conversation.
    """

    role: Literal["user", "model", "system", "ai"]
    content: str
    timestamp: str = None

    def to_json(self):
        """
        Converts the ChatMessage to a dictionary format suitable for JSON serialization.
        
        This method is particularly useful when preparing messages for OpenAI API calls
        which expect messages in a specific JSON structure.
        
        Returns:
            dict: A dictionary with role, content, and optional timestamp
        """
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }


async def generate_openai_chat(
    async_client: AsyncOpenaiClient,
    messages: List[ChatMessage],
    model: str = None,
    response_format: Union[Dict[str, str], None] = None,
    return_raw: bool = False,
):
    """
    Generates a completion response from OpenAI's chat models.
    
    This asynchronous function sends a series of messages to an OpenAI chat model and
    receives a response. It supports structured JSON responses and can return either
    processed or raw API responses based on the parameters.
    
    Args:
        async_client (AsyncOpenAI): The configured OpenAI client to use for API calls
        messages (List[ChatMessage]): A list of messages representing the conversation history
        model (str, optional): The OpenAI model to use (e.g., "gpt-4", "gpt-3.5-turbo")
        response_format (Dict[str, str], optional): Specifies the format of the response,
            e.g., {"type": "json_object"} to get JSON responses
        return_raw (bool, optional): If True, returns the raw API response instead of
            processing it
            
    Returns:
        ResponseGetDataOpenAi: A standardized response object containing the model's reply
            and additional metadata
            
    Raises:
        ImportError: If the OpenAI package is not installed
            
    Example:
        ```python
        import asyncio
        from openai import AsyncOpenAI
        
        async def example():
            client = AsyncOpenAI(api_key="your-api-key")
            
            messages = [
                ChatMessage(role="user", content="What's the weather like today?")
            ]
            
            response = await generate_openai_chat(
                async_client=client,
                messages=messages,
                model="gpt-4",
                response_format={"type": "json_object"}
            )
            
            print(response.response)  # Access the processed response
            
        asyncio.run(example())
        ```
    """
    # Convert all messages to the proper format expected by OpenAI
    clean_message = [
        msg.to_json() if isinstance(msg, ChatMessage) else msg
        for msg in messages
    ]

    # Make the API call to OpenAI
    res = await async_client.chat.completions.create(
        model=model, messages=clean_message, response_format=response_format)

    # Convert the raw response to our standardized format
    rgd = ResponseGetDataOpenAi.from_res(res)

    # Return the raw response if requested
    if return_raw:
        return rgd

    # Extract and process the content from the response
    content = res.choices[0].message.content
    rgd.response = content

    # Parse JSON if the response is in JSON format
    if response_format and response_format.get("type") == "json_object":
        rgd.response = json.loads(content)

    return rgd


async def generate_openai_embedding(
    text: str,
    async_client: AsyncOpenaiClient,
    model: str = "text-embedding-3-small",
    return_raw: bool = False,
    debug_prn: bool = False,
) -> List[float]:
    """
    Generates vector embeddings for text using OpenAI's embedding models.
    
    This asynchronous function converts text into high-dimensional vector representations
    that capture semantic meaning. These embeddings can be used for semantic search,
    clustering, classification, and other NLP tasks.
    
    Args:
        text (str): The text to convert into embeddings
        async_client (AsyncOpenAI): The configured OpenAI client to use for API calls
        model (str, optional): The embedding model to use, defaults to "text-embedding-3-small"
        return_raw (bool, optional): If True, returns the raw API response instead of
            just the embedding vector
        debug_prn (bool, optional): If True, prints debug information during execution
            
    Returns:
        List[float]: A vector of floating-point numbers representing the text embedding,
            or the raw API response if return_raw is True
            
    Raises:
        ImportError: If the OpenAI package is not installed
            
    Example:
        ```python
        import asyncio
        from openai import AsyncOpenAI
        
        async def example():
            client = AsyncOpenAI(api_key="your-api-key")
            
            # Generate embedding for a text
            embedding = await generate_openai_embedding(
                text="This is a sample text to embed",
                async_client=client
            )
            
            # Print the dimensionality of the embedding
            print(f"Embedding dimension: {len(embedding)}")
            
        asyncio.run(example())
        ```
        
    Note:
        Different embedding models have different vector dimensions:
        - text-embedding-3-small: 1536 dimensions
        - text-embedding-3-large: 3072 dimensions
        - text-embedding-ada-002: 1536 dimensions
    """

    # Print debug information if requested
    if debug_prn:
        print("📚 - starting LLM embedding generation")

    # Generate embeddings via the OpenAI API
    res = await async_client.embeddings.create(model=model, input=text)

    # Return the raw response if requested
    if return_raw:
        return res

    # Otherwise, extract and return just the embedding vector
    return res.data[0].embedding
