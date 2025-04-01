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
    # Initialize default message
    formatted_message = "An unknown error occurred"

    if exception:
        # Use exception message if no message was provided
        if message is None:
            formatted_message = str(exception)
        else:
            formatted_message = message

        # Add exception information
        type_name = 'unknown'
        if hasattr(exception, '__class__') and hasattr(exception.__class__,
                                                       '__name__'):
            type_name = exception.__class__.__name__

        template = f"An exception of type {type_name} occurred."

        # Add exception arguments if available
        if hasattr(exception, 'args') and exception.args:
            args_str = []
            for arg in exception.args:
                if arg is not None and str(arg):
                    args_str.append(str(arg))

            if args_str:
                template += f" Arguments: {','.join(args_str)}"

        formatted_message = f"{formatted_message}\n{template}"
    elif message is not None:
        formatted_message = message

    # Add skull emoji prefix if not already present
    if formatted_message and not formatted_message.startswith("💀"):
        formatted_message = "💀  " + formatted_message

    return formatted_message


class MafiaError(Exception):
    """
    Custom exception class for Mafia application.
    Automatically formats error messages using generate_error_message.
    
    Args:
        message (str, optional): The main error message.
        exception (Exception, optional): The original exception that was caught.
    """

    def __init__(self, message=None, exception=None):
        super().__init__(
            generate_error_message(message=message, exception=exception))
