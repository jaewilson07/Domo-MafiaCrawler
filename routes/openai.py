# Standard library imports
import json
from dataclasses import dataclass
from typing import Union, Dict, List, Literal

# Third-party imports
from openai import AsyncClient as AsyncOpenaiClient

# Local application imports
from client.ResponseGetData import ResponseGetDataOpenAi


def generate_openai_client(
    api_key: str, base_url: str = None, is_ollama: bool = False
) -> AsyncOpenaiClient:

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
        return {"role": self.role, "content": self.content, "timestamp": self.timestamp}


async def generate_openai_chat(
    async_client: AsyncOpenaiClient,
    messages: List[ChatMessage],
    model: str = None,
    response_format: Union[Dict[str, str], None] = None,
    return_raw: bool = False,
):
    # Convert all messages to the proper format expected by OpenAI
    clean_message = [
        msg.to_json() if isinstance(msg, ChatMessage) else msg for msg in messages
    ]

    # Make the API call to OpenAI
    res = await async_client.chat.completions.create(
        model=model, messages=clean_message, response_format=response_format
    )

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
