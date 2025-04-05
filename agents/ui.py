from __future__ import annotations
from functools import partial

from typing import Literal, TypedDict, Callable
from enum import Enum

import streamlit as st

from pydantic_ai.messages import (
    ModelResponse,
    TextPart,
    UserPromptPart,
    ModelRequest,
)

from agents.ai_expert import PydanticAgent
from agents.tools.dependencies import PydanticAIDependencies


class ChatMessage(TypedDict):
    """Format of messages send to the browser/API"""

    role: Literal["user", "model"]
    timestamp: str
    content: str


def display_system_prompt(content):
    with st.chat_message("system"):
        st.markdown(f"**System**: {content}")


def display_user_prompt(content):
    with st.chat_message("user"):
        st.markdown(content)


def display_text(content):
    with st.chat_message("assistant"):
        st.markdown(content)


def display_default(content):
    pass


class MessagePartEnum(Enum):
    """enum for parsing the correct function to use to display a part_kind"""

    SYSTEM_PROMPT = partial(display_system_prompt)
    USER_PROMPT = partial(display_user_prompt)
    TEXT = partial(display_text)

    DEFAULT = partial(display_default)

    @classmethod
    def get_with_default(cls, value):
        try:
            return MessagePartEnum[value]

        except KeyError:
            return MessagePartEnum.DEFAULT


def display_message_part(part):
    """
    Display a single part of a message in the Streamlit UI.
    Customize how you display system prompts, user prompts,
    tool calls, tool returns, etc.
    """

    if not hasattr(part, "content"):
        return

    MessagePartEnum.get_with_default(part.part_kind.replace("-", "_").upper()).value(
        content=part.content
    )


async def run_agent_with_streaming(
    user_input: str,
    st,
    agent: PydanticAgent,
    dependencies: PydanticAIDependencies,
) -> None:
    """
    Run the agent with streaming text for the user_input prompt,
    while maintaining the entire conversation in `st.session_state.messages`.
    """

    async with agent.run_stream(
        user_prompt=user_input,
        deps=dependencies,
        message_history=st.session_state.messages[
            :-1
        ],  # pass entire conversation so far
    ) as result:
        # gather partial text to show streaming results incrementally

        partial_text = ""

        message_placeholder = st.empty()

        # render partial_text as it arrives
        async for chunk in result.stream_text(delta=True):
            partial_text += chunk
            message_placeholder.markdown(partial_text)

        # add new messages excluding initial user_prompt
        filtered_messages = [
            msg
            for msg in result.new_messages()
            if not (
                hasattr(msg, "parts")
                and any(part.part_kind == "user-prompt" for part in msg.parts)
            )
        ]
        st.session_state.messages.extend(filtered_messages)

        # Add the final response to the messages
        st.session_state.messages.append(
            ModelResponse(parts=[TextPart(content=partial_text)])
        )


async def streamlit_ui(
    title: str,
    description: str,
    default_chat_input: str,
    run_agent_with_streaming: Callable[[str]],
):
    st.title(title)
    st.write(description)

    # Initialize chat history in session state if not present
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display all messages from the conversation so far
    # Each message is either a ModelRequest or ModelResponse.
    # We iterate over their parts to decide how to display them.
    for msg in st.session_state.messages:
        if isinstance(msg, ModelRequest) or isinstance(msg, ModelResponse):
            for part in msg.parts:
                display_message_part(part)

    # Chat input for the user
    user_input = st.chat_input(default_chat_input)

    if user_input:
        # We append a new request to the conversation explicitly
        st.session_state.messages.append(
            ModelRequest(parts=[UserPromptPart(content=user_input)])
        )

        # Display user prompt in the UI
        with st.chat_message("user"):
            st.markdown(user_input)

        # Display the assistant's partial response while streaming
        with st.chat_message("assistant"):
            # Actually run the agent now, streaming the text
            await run_agent_with_streaming(user_input=user_input, st=st)
