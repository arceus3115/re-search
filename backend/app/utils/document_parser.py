"""
Document parser for extracting text from TXT files.
"""

import os
import logging
from pathlib import Path
from typing import Optional

from .exceptions import DocumentParsingError

logger = logging.getLogger(__name__)


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from a TXT file.

    Args:
        file_path: Path to the TXT file

    Returns:
        Extracted text as string

    Raises:
        Exception: If file reading fails
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(file_path, "r", encoding="latin-1") as file:
                return file.read()
        except Exception as e:
            logger.error(
                f"Error reading TXT file {file_path} with alternate encoding: {e}",
                exc_info=True,
            )
            raise DocumentParsingError(f"Failed to read TXT file: {e}") from e
    except Exception as e:
        logger.error(f"Error reading TXT file {file_path}: {e}", exc_info=True)
        raise DocumentParsingError(f"Failed to read TXT file: {e}") from e


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from a TXT file.

    Args:
        file_path: Path to the TXT file

    Returns:
        Extracted text as string

    Raises:
        FileNotFoundError: If file doesn't exist
        DocumentParsingError: If file format is not supported or extraction fails
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_ext = Path(file_path).suffix.lower()

    logger.info(f"Extracting text from {file_ext} file: {file_path}")

    if file_ext != ".txt":
        raise DocumentParsingError(
            f"Unsupported file format: {file_ext}. Only .txt files are supported."
        )

    return extract_text_from_txt(file_path)


def get_file_type(file_path: str) -> Optional[str]:
    """
    Get the file type based on extension.

    Args:
        file_path: Path to the file

    Returns:
        File type ('txt') or None if not supported
    """
    file_ext = Path(file_path).suffix.lower()

    if file_ext == ".txt":
        return "txt"
    else:
        return None
