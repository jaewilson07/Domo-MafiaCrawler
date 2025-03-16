from dotenv import load_dotenv
import os
import asyncio

from typing import Callable

from slack_bolt.async_app import AsyncApp as AsyncSlackApp


app = AsyncSlackApp(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)


async def reply_to_message(body, say, get_response_fn: Callable):
    """
    Replies to a message in the same thread.

    Args:
        body (dict): The event payload from Slack.
        say (callable): A function to send messages to Slack.
    """
    event = body["event"]
    # channel_id = event["channel"]
    user_msg = event.get("text")  # Get the text of the message.
    thread_ts = event.get("ts")  # Get the timestamp of the message, to reply to it.

    if user_msg:  # make sure there is a message.
        reply_text = await get_response_fn(user_msg)

        await say(
            reply_text, thread_ts=thread_ts
        )  # reply to the message using the thread_ts.
    else:
        print("message did not contain text")


### requires App
async def update_slack_message(channel_id, timestamp, new_text, app: AsyncSlackApp):
    """
    Updates an existing Slack message.

    Args:
        channel_id (str): The ID of the channel where the message is located.
        timestamp (str): The timestamp of the message to update.
        new_text (str): The new text content for the message.
    """
    try:
        await app.client.chat_update(channel=channel_id, ts=timestamp, text=new_text)

        print(f"Message updated successfully in channel {channel_id} at {timestamp}")

    except Exception as e:
        print(f"Error updating message: {e}")


async def post_initial_message(channel_id, initial_text, app: AsyncSlackApp):
    try:
        result = await app.client.chat_postMessage(
            channel=channel_id, text=initial_text
        )

        return result["ts"]  # return timestamp.

    except Exception as e:
        print(f"Error posting initial message: {e}")
        return None
