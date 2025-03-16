
import pytest
from route import app, message_hello, handle_app_mention

def test_message_hello():
    # Mock message and say function
    message = {"user": "U123ABC"}
    mock_say = lambda x: None
    
    # Test the message_hello function
    message_hello(message, mock_say)

def test_app_mention():
    # Mock event and say function
    event = {"text": "Is this working?"}
    mock_say = lambda x: None
    
    # Test the app_mention handler
    handle_app_mention(event, mock_say)

def test_app_initialization():
    # Test if app is initialized correctly
    assert app is not None
    assert app.token == "SLACK_BOT_TOKEN"
