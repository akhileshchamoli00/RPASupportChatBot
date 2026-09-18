"""
Utility module for safe file handling in Windows environments with file locking.
"""

import os
import ctypes
from ctypes import wintypes
from app.core.logging_config import logger


def read_file_bytes_safely(filepath: str) -> bytes:
    """
    Reads file bytes safely. If standard open fails due to Windows file locking
    (e.g. file is open in MS Word or Excel), uses Win32 CreateFileW share-read fallback.
    """
    try:
        with open(filepath, "rb") as f:
            return f.read()
    except Exception as e:
        if os.name == "nt":
            logger.warning(f"Standard read failed for '{filepath}' ({e}). Attempting Win32 share-read fallback...")
            GENERIC_READ = 0x80000000
            FILE_SHARE_READ = 0x00000001
            FILE_SHARE_WRITE = 0x00000002
            FILE_SHARE_DELETE = 0x00000004
            OPEN_EXISTING = 3
            FILE_ATTRIBUTE_NORMAL = 0x80

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.CreateFileW(
                filepath, GENERIC_READ,
                FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None
            )

            if handle != -1 and handle != 0xFFFFFFFF:
                buffer_size = 65536
                buffer = ctypes.create_string_buffer(buffer_size)
                bytes_read = wintypes.DWORD()
                file_bytes = bytearray()
                while True:
                    res = kernel32.ReadFile(handle, buffer, buffer_size, ctypes.byref(bytes_read), None)
                    if not res or bytes_read.value == 0:
                        break
                    file_bytes.extend(buffer.raw[:bytes_read.value])
                kernel32.CloseHandle(handle)
                logger.info(f"Successfully read {len(file_bytes)} bytes via Win32 share-read handle for '{filepath}'.")
                return bytes(file_bytes)
        raise e
