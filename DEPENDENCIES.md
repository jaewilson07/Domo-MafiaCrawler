# Dependencies

## Overview

This library relies on several tools and libraries to provide robust web crawling and data processing functionality. Below is an overview of the key dependencies:

### 1. `crawl4ai`

- **Purpose**: Provides the core crawling functionality, including browser automation, rate limiting, and advanced crawling strategies.
- **Features**:
  - Supports multiple browser types (e.g., Chromium, Firefox).
  - Includes built-in strategies like BFS and domain filtering.
  - Handles dynamic content loading with configurable delays.

### 2. `supabase`

- **Purpose**: Used for storing and managing crawled data in a cloud-based database.
- **Features**:
  - Provides a scalable backend for data storage.
  - Includes APIs for querying and managing data.

### 3. `openai`

- **Purpose**: Used for generating text embeddings and summaries of crawled documents.
- **Features**:
  - Generates embeddings for semantic search and similarity tasks.
  - Creates concise summaries of crawled content for better understanding and storage.

### 4. Other Dependencies

- **`asyncio`**: Enables asynchronous operations for efficient crawling.
- **`logging`**: Used for progress and error logging.
- **`json`**: Handles serialization of logs and responses.
- **`argparse`**: Supports command-line argument parsing for flexibility.

## Installation

All dependencies are listed in the `requirements.txt` file. Install them using:

```bash
pip install -r requirements.txt
```

### Post-Installation Setup

1. Run the following command to set up `crawl4ai`:

   ```bash
   crawl4ai-setup
   ```

2. Verify your installation:

   ```bash
   crawl4ai-doctor
   ```

3. Ensure your OpenAI API key is set in the environment variables:
   ```plaintext
   OPENAI_API_KEY=<your-openai-api-key>
   ```
