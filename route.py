from dotenv import load_dotenv
import os
import asyncio

from slack_bolt.async_app import AsyncApp as AsyncSlackApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler


from openai import AsyncOpenAI
from supabase import Client as SupabaseClient

from src import PydanticAIDependencies, pydantic_ai_expert


from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart,
)

load_dotenv()


openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

supabase: SupabaseClient = SupabaseClient(
    os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"]
)

message_history = []


async def run_streaming(user_prompt, message_history):

    message_history.append(ModelRequest(parts=[UserPromptPart(content=user_prompt)]))

    dependencies = PydanticAIDependencies(
        supabase=supabase, openai_client=openai_client
    )

    res = await pydantic_ai_expert.run(
        user_prompt=user_prompt, deps=dependencies, message_history=message_history[:-1]
    )

    print(res)

    filtered_messages = [
        msg
        for msg in res.new_messages()
        if not (
            hasattr(msg, "parts")
            and any(part.part_kind == "user-prompt" for part in msg.parts)
        )
    ]

    message_history.extend(filtered_messages)

    message_history.append(ModelResponse(parts=[TextPart(content=res.data)]))

    return res.data


# Initializes your app with your bot token and app token
app = AsyncSlackApp(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)


@app.event("app_mention")  # Listen for app mentions
async def handle_app_mention(event, say):
    """Handles app mentions and responds with a random yes/no."""

    user = event["user"]

    question = event["text"]  # Get the text of the message

    res = await run_streaming(question, message_history=message_history)

    # res = 123

    await say(
        f"You asked: {question}\nMy answer is: {res}"
    )  # Send the response back to Slack


async def main():
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())
