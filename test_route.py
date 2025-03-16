
import pytest
from route import app, message_hello, handle_app_mention
from unittest.mock import MagicMock

def test_message_hello():
    # Mock message and say function
    message = {"user": "U123ABC"}
    mock_say = MagicMock()
    
    # Test the message_hello function
    message_hello(message, mock_say)
    mock_say.assert_called_once_with("hey there <@U123ABC>!")

def test_app_mention():
    # Mock event and say function
    event = {"text": "Is this working?"}
    mock_say = MagicMock()
    
    # Test the app_mention handler
    handle_app_mention(event, mock_say)
    mock_say.assert_called_once()
    
def test_app_mention_empty_text():
    # Test handling of empty text
    event = {"text": ""}
    mock_say = MagicMock()
    
    handle_app_mention(event, mock_say)
    mock_say.assert_called_once()

def test_app_initialization():
    # Test if app is initialized correctly
    assert app is not None
    assert hasattr(app, 'token')
