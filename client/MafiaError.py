"""
Error handling utilities for Mafia application.
Provides consistent error formatting and a custom exception class.
"""

__all__ = ['generate_error_message', 'MafiaError']

def generate_error_message(message=None, exception=None):
    """
    Formats error messages with consistent styling and additional exception information.
    
    Args:
        message (str, optional): The main error message to display.
        exception (Exception, optional): The exception that was raised.
        
    Returns:
        str: A formatted error message string with skull emoji prefix.
    """
    if exception:
        if message is None:
            message = str(exception)

        template = f"An exception of type {type(exception).__name__ if type(exception) else 'unknown'} occurred."

        if exception.args:
            template += f" Arguments: {','.join(str(arg) for arg in exception.args if arg and str(arg))}"

        message = f"{message}\n{template}"

    if message and not message.startswith("💀"):
        message = "💀  " + message

    return message


class MafiaError(Exception):
    """
    Custom exception class for Mafia application.
    Automatically formats error messages using generate_error_message.
    
    Args:
        message (str, optional): The main error message.
        exception (Exception, optional): The original exception that was caught.
    """
    def __init__(self, message=None, exception=None):
        super().__init__(generate_error_message(message=message, exception=exception))
