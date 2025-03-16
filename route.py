import os
from dotenv import load_dotenv
import random
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()


# Initializes your app with your bot token and app token
if "SLACK_BOT_TOKEN" not in os.environ:
    raise ValueError("SLACK_BOT_TOKEN environment variable is required")

app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)


@app.message("hello")
def message_hello(message, say):
    user = message["user"]

    print("hello")

    say(f"hey there <@{user}>!")


@app.event("app_mention")  # Listen for app mentions
def handle_app_mention(event, say):
    """Handles app mentions and responds with a random yes/no."""

    question = event["text"]  # Get the text of the message
    response = random.choice(["Yes", "No"])  # Generate a random response

    say(
        f"You asked: {question}\nMy answer is: {response}"
    )  # Send the response back to Slack


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
