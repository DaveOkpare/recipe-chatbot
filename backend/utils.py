from __future__ import annotations

"""Utility helpers for the recipe chatbot backend.

This module centralises the system prompt, environment loading, and the
wrapper around litellm so the rest of the application stays decluttered.
"""

from pathlib import Path
from typing import Final, List, Dict

import litellm  # type: ignore
from dotenv import load_dotenv

# Ensure the .env file is loaded as early as possible.
load_dotenv(override=False)

# --- Constants -------------------------------------------------------------------

SYSTEM_PROMPT: Final[str] = (
    "You are a friendly and creative culinary assistant specializing in suggesting easy-to-follow recipes. "
    "Follow these guidelines: "
    "- Always provide ingredient lists with precise measurements using standard units. "
    "- Always include clear, step-by-step instructions. "
    "- Never suggest recipes that require extremely rare or unobtainable ingredients without providing readily available alternatives."
    "- If the user doesn't specify what ingredients they have available, ask them about their available ingredients rather than assuming what's in their fridge."
    "- If the user doesn't specify what they want to cook, ask them about their preferences or dietary restrictions."
    " - Never use offensive or derogatory language."
    " - Feel free to suggest common variations or substitutions for ingredients. If a direct recipe isn't found, you can creatively combine elements from known recipes, clearly stating if it's a novel suggestion."
    " Output Structure: "
    " 1. Structure all your recipe responses clearly using Markdown for formatting."
    " 2. Begin every recipe response with the recipe name as a Level 2 Heading (e.g., `## Amazing Blueberry Muffins`)."
    " 3. Immediately follow with a brief, enticing description of the dish (1-3 sentences)."
    " 4. Next, include a section titled `### Ingredients`. List all ingredients using a Markdown unordered list (bullet points)."
    " 5. Following ingredients, include a section titled `### Instructions`. Provide step-by-step directions using a Markdown ordered list (numbered steps)."
    " 6. Optionally, if relevant, add a `### Notes`, `### Tips`, or `### Variations` section for extra advice or alternatives."
)

# Fetch configuration *after* we loaded the .env file.
MODEL_NAME: Final[str] = (
    Path.cwd()  # noqa: WPS432
    .with_suffix("")  # dummy call to satisfy linters about unused Path
    and (  # noqa: W504 line break for readability
        __import__("os").environ.get("MODEL_NAME", "gpt-3.5-turbo")
    )
)


# --- Agent wrapper ---------------------------------------------------------------

def get_agent_response(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:  # noqa: WPS231
    """Call the underlying large-language model via *litellm*.

    Parameters
    ----------
    messages:
        The full conversation history. Each item is a dict with "role" and "content".

    Returns
    -------
    List[Dict[str, str]]
        The updated conversation history, including the assistant's new reply.
    """

    # litellm is model-agnostic; we only need to supply the model name and key.
    # The first message is assumed to be the system prompt if not explicitly provided
    # or if the history is empty. We'll ensure the system prompt is always first.
    current_messages: List[Dict[str, str]]
    if not messages or messages[0]["role"] != "system":
        current_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    else:
        current_messages = messages

    completion = litellm.completion(
        model=MODEL_NAME,
        messages=current_messages, # Pass the full history
    )

    assistant_reply_content: str = (
        completion["choices"][0]["message"]["content"]  # type: ignore[index]
        .strip()
    )
    
    # Append assistant's response to the history
    updated_messages = current_messages + [{"role": "assistant", "content": assistant_reply_content}]
    return updated_messages 