# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.
# See LICENSE file in the project root for full license information.
from typing import Optional

import logging
import pydantic
import sys


def get_logger(name: str,
               log_level: int = logging.INFO,
               log_file_name: Optional[str] = None,
               log_to_console: bool=True) -> logging.Logger:
    """
    Return the logger, capable to log into file and/or to console.

    :param name: the name of the logger.
    :param log_level: The logging verbosity level.
    :param log_file_name: The file to be sed to write logs if any.
    :param log_to_console: Boolean showing if we want to log into the console.
    :returns: The logger object.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    if log_to_console:
        # Configure the stream handler (stdout)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        stream_handler.setFormatter(stream_formatter)
        logger.addHandler(stream_handler)
    
    if log_file_name:
        file_handler = logging.FileHandler(log_file_name)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    return logger


class FileAttachment(pydantic.BaseModel):
    """
    Represents a file attached to a chat message.
    
    Attributes:
        name: Original filename
        type: MIME type (e.g., 'image/jpeg', 'application/pdf')
        data: Base64-encoded file content
    """
    name: str
    type: str
    data: str  # Base64-encoded content


class Message(pydantic.BaseModel):
    """
    Represents a chat message with optional file attachments.
    
    Attributes:
        content: The text content of the message
        role: Either 'user' or 'assistant'
        attachments: Optional list of file attachments (images, documents)
    """
    content: str
    role: str = "user"
    attachments: list[FileAttachment] = []


class ChatRequest(pydantic.BaseModel):
    messages: list[Message]
