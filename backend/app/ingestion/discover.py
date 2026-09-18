"""
Document discovery module for finding supported files (.docx, .xlsx, .pdf).
"""

import os
from app.core.logging_config import logger


def discover_documents(base_folder: str) -> list[tuple[str, str, str]]:
    """
    Scans base_folder recursively for .docx, .xlsx, and .pdf files.
    Returns a list of tuples: (filepath, file_type, automation_name).
    """
    logger.info(f"Scanning base folder for documents: {base_folder}")
    if not os.path.exists(base_folder):
        logger.error(f"Directory '{base_folder}' does not exist.")
        return []

    discovered = []
    supported_exts = {".docx": "docx", ".xlsx": "xlsx", ".pdf": "pdf"}

    for root, _, files in os.walk(base_folder):
        for file in files:
            if file.startswith("~$"):
                continue  # Skip Office temporary lock files

            ext = os.path.splitext(file)[1].lower()
            if ext in supported_exts:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(root, base_folder)
                
                if rel_path == ".":
                    automation = "General"
                else:
                    parts = rel_path.split(os.sep)
                    automation = parts[0]

                discovered.append((filepath, supported_exts[ext], automation))

    logger.info(f"Discovered {len(discovered)} documents across workspace folders.")
    return discovered
