"""
Created by: Ori Halevi
GitHub: https://github.com/ori-halevi
Python 3.12

Description: This script monitors changes to a specific registry key related to input locales and detects when
the keyboard language layout is changed. When a change is detected, the script logs the current keyboard language
layout.

The script sets up a registry change notification on the key:
"SOFTWARE/WOW6432Node/Microsoft/Input/Locales"

It also retrieves and prints the current keyboard layout language of the foreground window before and after monitoring
for changes.

Note: The script uses Windows API functions via ctypes to interact with the registry and handle system events.
"""
from __future__ import annotations

import ctypes
import winreg
import logging

# Debugging flag
DEBUG = False

# Set up logging
logging.basicConfig(level=logging.DEBUG if DEBUG else None,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for registry notifications and wait statuses
REG_NOTIFY_CHANGE_LAST_SET = 0x00000004  # Notifies when the last write time of the key or value is changed
KEY_NOTIFY = 0x00000010  # Allows a registry key to be monitored for changes

# Load Windows API libraries
advapi32 = ctypes.WinDLL('advapi32')  # Windows API for registry functions
kernel32 = ctypes.WinDLL('kernel32')  # Core Windows API
user32 = ctypes.WinDLL('user32')  # Windows API for user interactions

# Define ctypes types for function calls
HKEY = ctypes.c_void_p  # Handle type for registry keys
DWORD = ctypes.c_ulong  # Unsigned long type for various parameters

# Define functions from the Windows API
RegNotifyChangeKeyValue = advapi32.RegNotifyChangeKeyValue
RegNotifyChangeKeyValue.argtypes = [HKEY, ctypes.c_bool, DWORD, HKEY, ctypes.c_bool]
RegNotifyChangeKeyValue.restype = ctypes.c_long

CreateEventW = kernel32.CreateEventW
CreateEventW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_bool, ctypes.c_wchar_p]
CreateEventW.restype = HKEY

WaitForSingleObject = kernel32.WaitForSingleObject
WaitForSingleObject.argtypes = [HKEY, DWORD]
WaitForSingleObject.restype = DWORD

# Function to get the current keyboard layout
GetKeyboardLayout = user32.GetKeyboardLayout
GetKeyboardLayout.argtypes = [ctypes.c_ulong]
GetKeyboardLayout.restype = ctypes.c_ulong

# Registry path for input locales
hkey = winreg.HKEY_LOCAL_MACHINE
subkey = r"SOFTWARE\WOW6432Node\Microsoft\Input\Locales"

# Function to get the handle of the foreground window
GetForegroundWindow = user32.GetForegroundWindow
GetForegroundWindow.restype = ctypes.c_void_p


def get_current_language() -> str | None:
    """
    Returns the current keyboard layout language of the foreground window.

    Returns:
        str | None: The current keyboard layout language as a string, or None if it cannot be retrieved.
    """
    hwnd = GetForegroundWindow()
    layout = GetKeyboardLayout(ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None))
    language_id = layout & 0xFFFF  # Extract the low-order word (language ID)

    buffer = ctypes.create_unicode_buffer(100)
    if ctypes.windll.kernel32.GetLocaleInfoW(language_id, 0x00000002, buffer, len(buffer)):
        return buffer.value
    else:
        logging.error("Could not retrieve the current keyboard layout language.")
        return None


def start_monitor_language_in_registry_key(duration: int = -1, user_function: callable = None) -> str | bool | None:
    """
    Monitors changes to a specific registry key and logs when changes are detected.
    :param duration: How long to wait for changes in milliseconds. If negative (-1) or empty - it will wait forever.
    :param user_function: An optional user-defined function to execute when a change is detected.
    :return: The current keyboard language if a change is detected; False if no change occurred; None in case of error.
    """
    event = None
    try:
        with winreg.OpenKey(hkey, subkey, 0, KEY_NOTIFY) as reg_key:
            reg_key_handle = ctypes.c_void_p(reg_key.handle)

            event = CreateEventW(None, True, False, None)
            if not event:
                logging.error("Error creating event handle.")
                return None

            result = RegNotifyChangeKeyValue(
                reg_key_handle,
                False,
                REG_NOTIFY_CHANGE_LAST_SET,
                event,
                True
            )

            if result != 0:
                logging.error(f"Error setting up registry change notification. Error code: {ctypes.get_last_error()}")
                return None

            logging.info("Monitoring keyboard language layout changes.")

            wait_result = WaitForSingleObject(event, duration)
            if wait_result == 0:  # Event occurred
                logging.info("Registry key has been modified.")

                # Here the user function will run (if entered)
                if user_function is not None and callable(user_function):
                    user_function()
                    logging.info("Function executed successfully.")

                return get_current_language()
            else:
                return False

    except KeyboardInterrupt:
        logging.info("Stopped monitoring.")
    except Exception as e:
        logging.error("Unexpected error:", e)
    finally:
        if event:
            kernel32.CloseHandle(event)


if __name__ == "__main__":

    def example():
        print("Hello")

    old_lang = get_current_language()
    print(f"Current language: {old_lang}")
    new_lang = start_monitor_language_in_registry_key(duration=2000, user_function=example)  # Start monitoring registry key changes
    print(f"Result after monitoring: {new_lang}")
