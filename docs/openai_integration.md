# OpenAI Integration Guide

This document provides a comprehensive guide to using OpenAI's API with the crawler application. The integration supports both text generation (chat completions) and embedding generation for text processing and analysis.

## Overview

The OpenAI integration allows the crawler to:

1. **Process crawled content**: Summarize, extract key information, and analyze crawled website content
2. **Generate embeddings**: Create vector representations of text for semantic search and similarity comparisons
3. **Handle structured data**: Parse websites into structured formats like JSON using OpenAI's JSON mode

## Prerequisites

To use the OpenAI integration, you'll need:

- An OpenAI API key (get one at [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys))
- The OpenAI Python library installed: `pip install openai`
- Optional: For local testing, you can use an Ollama instance with OpenAI-compatible models

## Configuration

The OpenAI client needs to be configured before use:

```python
from routes.openai import generate_openai_client

# Standard OpenAI configuration
client = generate_openai_client(api_key="your-openai-key")

# Alternative: configure for Ollama (local open-source alternative)
ollama_client = generate_openai_client(
    api_key="ollama",  # Can be any string for Ollama
    base_url="http://localhost:11434/v1",
    is_ollama=True
)
```

## Environment Variables

For security, it's recommended to store your API keys as environment variables:

```python
import os
from routes.openai import generate_openai_client

# Get API key from environment
api_key = os.environ.get("OPENAI_API_KEY")
client = generate_openai_client(api_key=api_key)
```

## Chat Completions

Chat completions are used to generate text responses based on conversation history:

```python
import asyncio
from routes.openai import generate_openai_client, ChatMessage, generate_openai_chat

async def summarize_article(url, content):
    client = generate_openai_client(api_key="your-openai-key")
    
    messages = [
        ChatMessage(role="user", content=f"""
        URL: {url}
        
        Please summarize the following article in 3-5 sentences:
        
        {content[:2000]}...  # Send the first 2000 characters
        """)
    ]
    
    response = await generate_openai_chat(
        async_client=client,
        messages=messages,
        model="gpt-3.5-turbo"  # Or your preferred model
    )
    
    return response.response  # Access the text response

# Run the async function
summary = asyncio.run(summarize_article("https://example.com", "Article content..."))
print(summary)
```

### JSON Mode

You can request structured responses in JSON format:

```python
async def extract_structured_data(content):
    client = generate_openai_client(api_key="your-openai-key")
    
    messages = [
        ChatMessage(role="user", content=f"""
        Extract the following information from this article:
        - title
        - author
        - publication date
        - main topics (as a list)
        - summary
        
        Content:
        {content[:3000]}...
        """)
    ]
    
    response = await generate_openai_chat(
        async_client=client,
        messages=messages,
        model="gpt-4",
        response_format={"type": "json_object"}  # Request JSON response
    )
    
    # Response is automatically parsed as a dictionary
    structured_data = response.response
    return structured_data
```

## Embeddings

Embeddings convert text into numerical vector representations that capture semantic meaning:

```python
import asyncio
from routes.openai import generate_openai_client, generate_openai_embedding

async def compare_text_similarity(text1, text2):
    client = generate_openai_client(api_key="your-openai-key")
    
    # Generate embeddings for both texts
    embedding1 = await generate_openai_embedding(
        text=text1,
        async_client=client,
        model="text-embedding-3-small"
    )
    
    embedding2 = await generate_openai_embedding(
        text=text2,
        async_client=client,
        model="text-embedding-3-small"
    )
    
    # Calculate cosine similarity (you'd need to implement this function)
    similarity = calculate_cosine_similarity(embedding1, embedding2)
    return similarity
```

## Error Handling

The integration includes error handling, but you should implement additional error handling in your application:

```python
import asyncio
from routes.openai import generate_openai_client, generate_openai_chat, ChatMessage

async def safe_generate_text(prompt):
    try:
        client = generate_openai_client(api_key="your-openai-key")
        
        messages = [ChatMessage(role="user", content=prompt)]
        
        response = await generate_openai_chat(
            async_client=client,
            messages=messages,
            model="gpt-3.5-turbo"
        )
        
        return response.response
        
    except Exception as e:
        print(f"Error generating text: {str(e)}")
        return f"An error occurred: {str(e)}"
```

## Best Practices

1. **Prompt engineering**: Create clear, specific prompts for best results
2. **Token management**: Be aware of model token limits (e.g., 4096 tokens for gpt-3.5-turbo)
3. **Cost control**: Implement rate limiting and monitoring to control API usage costs
4. **Backup plans**: Have fallback behavior when API calls fail
5. **Model selection**: Choose the appropriate model for your task (balance cost vs. quality)

## Available Models

### Text Generation Models

- `gpt-4o`: Most advanced model, best quality but highest cost
- `gpt-4-turbo`: High quality with good performance
- `gpt-3.5-turbo`: Good balance of quality and cost for many applications

### Embedding Models

- `text-embedding-3-small`: 1536 dimensions, good balance of quality and cost
- `text-embedding-3-large`: 3072 dimensions, highest quality but more expensive
- `text-embedding-ada-002`: Legacy model, 1536 dimensions

## Security Considerations

1. Never hardcode API keys in your application code
2. Be cautious about what data you send to OpenAI's API
3. Implement rate limiting to prevent accidental excessive usage
4. Consider using Azure OpenAI Service for additional security and compliance features
5. Validate and sanitize model outputs before using them in your application

## Resources

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [OpenAI Python Library](https://github.com/openai/openai-python)
- [OpenAI Cookbook](https://github.com/openai/openai-cookbook)