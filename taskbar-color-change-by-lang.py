"""
Created by: Ori Halevi
GitHub: https://github.com/ori-halevi
python 3.12

Description: This script toggles the ColorPrevalence setting in the Windows registry when a keyboard language change
is detected, and refreshes the taskbar to apply the change and thus causes the color of the taskbar to change when
the language changes.

for future developers, this is the value that get changed in the registry when user changes the keyboard language layout:
"InputLocale"
inside the key:
"SOFTWARE/Microsoft/Input/Locales"
"""
import os
import json
from pynput import keyboard
import webbrowser
import requests
import ctypes
import time
import winreg
import logging
import threading
from PIL import Image, ImageDraw
from pathlib import Path
from pystray import Icon, MenuItem, Menu
from pystray import MenuItem as item, Menu, Icon
from Find_out_installd_keyboard_layout import get_all_system_keyboard_layouts

__version__ = 'v1.1.3'

DEBUG = False
# Set up logging
logging.basicConfig(level=logging.DEBUG if DEBUG else None,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Defining the constants for registry notifications and wait statuses
REG_NOTIFY_CHANGE_LAST_SET = 0x00000004  # Notifies when the last write time of the key or value is changed
KEY_NOTIFY = 0x00000010  # Allows a registry key to be monitored for changes

# Loads the Windows API libraries
advapi32 = ctypes.WinDLL('advapi32')  # Windows API for registry functions
kernel32 = ctypes.WinDLL('kernel32')  # Core Windows API

# Defining ctypes types for function calls
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

# Creating a registry key
hkey = winreg.HKEY_LOCAL_MACHINE
subkey = r"SOFTWARE\WOW6432Node\Microsoft\Input\Locales"  # Path to registry key for input locales


# This section is for monitor the current lang.
# Load Windows API libraries
advapi32 = ctypes.WinDLL('advapi32')  # Windows API for registry functions
kernel32 = ctypes.WinDLL('kernel32')  # Core Windows API
user32 = ctypes.WinDLL('user32')  # Windows API for user interactions

# Function to get the current keyboard layout
GetKeyboardLayout = user32.GetKeyboardLayout
GetKeyboardLayout.argtypes = [ctypes.c_ulong]
GetKeyboardLayout.restype = ctypes.c_ulong

# Function to get the handle of the foreground window
GetForegroundWindow = user32.GetForegroundWindow
GetForegroundWindow.restype = ctypes.c_void_p


class TaskbarManager:
    def __init__(self):
        # Load user32.dll to interact with the Windows GUI elements
        self.user32 = ctypes.windll.user32
        # Get the handle of the taskbar
        self.taskbar_handle = self.user32.FindWindowW("Shell_TrayWnd", None)
        # Registry path and value name for taskbar color settings
        self.registry_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        self.value_name = "ColorPrevalence"

    def toggle_color_prevalence(self):
        """
        Changes the ColorPrevalence value in the system registry to toggle the color on the taskbar.
        """
        try:
            # Opens the registry key
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0,
                                winreg.KEY_READ | winreg.KEY_WRITE) as key:
                # Read the current value
                current_value = winreg.QueryValueEx(key, self.value_name)[0]
                # Change the current value to the opposite value
                new_value = 0 if current_value == 1 else 1
                # Set the new value
                winreg.SetValueEx(key, self.value_name, 0, winreg.REG_DWORD, new_value)
                self.refresh_taskbar()

                logging.debug(f"Changed ColorPrevalence from {current_value} to {new_value}")
        except FileNotFoundError:
            logging.error("Registry path or value not found.")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def refresh_taskbar(self):
        """
        Refreshes the taskbar by sending a settings change notification to the taskbar.
        """
        self.user32.SendMessageW(self.taskbar_handle, 0x001A, 0, "ImmersiveColorSet")  # Refresh command to taskbar

    def get_is_ColorPrevalence_on_or_off(self):
        """
        :return: 1 if ColorPrevalence is on, and 0 otherwise.
        """
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0,
                                winreg.KEY_READ | winreg.KEY_WRITE) as key:
                # Read the current value
                current_value = winreg.QueryValueEx(key, self.value_name)[0]
                return current_value
        except FileNotFoundError:
            logging.error(f"something went wrong!")


# Global stop event to control the monitoring thread
stop_event = threading.Event()


def check_for_updates(current_version):
    """
    Checks the latest release version from GitHub and compares it with the current version.
    """
    github_api_url = "https://api.github.com/repos/ori-halevi/taskbar-color-change-by-lang/releases/latest"
    try:
        response = requests.get(github_api_url)
        response.raise_for_status()
        latest_version = response.json()["tag_name"]
        if latest_version != current_version:
            return latest_version
    except requests.RequestException as e:
        logging.error(f"Error checking for updates: {e}")
    return None


def open_git_releases():
    """
    Opens the GitHub releases page in the default web browser when the user selects the 'Check for Updates' menu item.
    """
    github_releases_url = "https://github.com/ori-halevi/taskbar-color-change-by-lang/releases"
    webbrowser.open(github_releases_url)


###
def get_preferences_file():
    appdata_path = os.getenv('LOCALAPPDATA')  # מקבל את הנתיב לתיקיית AppData המקומית
    app_folder = os.path.join(appdata_path, "taskbar-color-change-by-lang")
    os.makedirs(app_folder, exist_ok=True)  # יוצר את התיקייה אם היא לא קיימת
    return os.path.join(app_folder, "user_preferences.json")

def load_user_preferences():
    preferences_file = get_preferences_file()
    if not os.path.exists(preferences_file):
        save_user_preferences("English")
        return "English"  # ברירת מחדל - אנגלית אם הקובץ לא קיים
    try:
        with open(preferences_file, 'r') as f:
            return json.load(f)["preferred_language"]
    except:
        save_user_preferences("English")
        return "English"

def save_user_preferences(preferred_language):
    preferences = {"preferred_language": preferred_language}
    preferences_file = get_preferences_file()
    with open(preferences_file, 'w') as f:
        json.dump(preferences, f)


###



# def is_caps_lock_on():
#     """
#     Checks if the user has the caps lock on.
#     :return: True or False
#     """
#     return ctypes.WinDLL("User32.dll").GetKeyState(0x14) & 0xffff != 0


def sync_taskbar_color_with_preference_lang(taskbar_manager):
    """
    Synchronize the taskbar color with the preferred lang.
    """
    if load_user_preferences() == get_current_language().split()[0] and taskbar_manager.get_is_ColorPrevalence_on_or_off():
        taskbar_manager.toggle_color_prevalence()
        logging.info("taskbar color changed!")
    elif load_user_preferences() != get_current_language().split()[0] and not taskbar_manager.get_is_ColorPrevalence_on_or_off():
        taskbar_manager.toggle_color_prevalence()
        logging.info("taskbar color changed!")

def get_current_language():
    """
    Returns the current keyboard layout language of the foreground window.
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


def monitor_registry_key(hkey, subkey, taskbar_manager):
    """
    Monitors changes to a specific registry key and toggles taskbar color when changes are detected.
    """
    # Opens the registry key
    reg_key = winreg.OpenKey(hkey, subkey, 0, KEY_NOTIFY)

    # Convert the key to the format expected by ctypes
    reg_key_handle = ctypes.c_void_p(reg_key.handle)

    # Creates an event object to signal when a change occurs
    event = CreateEventW(None, True, False, None)

    # Registers a change to the registry key
    result = RegNotifyChangeKeyValue(
        reg_key_handle,
        False,
        REG_NOTIFY_CHANGE_LAST_SET,
        event,
        True
    )

    if result != 0:
        logging.error("Error setting up registry change notification.")
        return

    logging.info("Monitoring keyboard language layout changes.")

    try:
        while not stop_event.is_set():
            print("ya")
            # Wait for event or until stopped
            wait_result = WaitForSingleObject(event, -1)  # Wait for -1 ms (infinity)
            if wait_result == 0:  # 0 indicates that the event occurred
                logging.info("Registry key has been modified.")

                if not is_caps_lock_on_BOOL:
                    taskbar_manager.toggle_color_prevalence()  # Toggle color on taskbar
                    print(is_caps_lock_on_BOOL)
                    print("heRe1")
                elif is_caps_lock_on_BOOL:
                    print(is_caps_lock_on_BOOL)
                    print("heRe2")
                    if load_user_preferences() == "English" and taskbar_manager.get_is_ColorPrevalence_on_or_off():
                        # if the user prefer that on English will there not be color and now there is
                        taskbar_manager.toggle_color_prevalence()

                        #TODO here we need to listen to when the Caps get off again and when it does to do sync_taskbar_color_with_preference_lang()
                        continue


                # Register again to continue receiving notifications
                result = RegNotifyChangeKeyValue(
                    reg_key_handle,
                    False,
                    REG_NOTIFY_CHANGE_LAST_SET,
                    event,
                    True
                )
                if result != 0:
                    logging.error("Error re-registering registry change notification.")
                    break
            else:
                logging.error("Error waiting for registry change event.")
                break
    except KeyboardInterrupt:
        logging.info("Stopped monitoring.")
    finally:
        # Clean up
        winreg.CloseKey(reg_key)  # Close the registry key handle
        kernel32.CloseHandle(event)  # Close the event handle


def create_image(width, height, color1, color2):
    """
    Creates an image for the tray icon.
    """
    image = Image.new('RGB', (width, height), color1)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, height // 2), fill=color2)  # Use a tuple instead of a list
    return image


def on_quit(icon):
    """
    Callback to quit the application when the tray icon is clicked.
    """
    stop_event.set()  # Signal all threads to stop
    logging.info("Exiting application.")
    kernel32.CloseHandle(taskbar_manager.taskbar_handle)  # Close the taskbar handle
    icon.stop()  # Stop the tray icon
    time.sleep(2)  # Short delay before exit
    os._exit(0)


def setup_tray_icon(taskbar_manager) -> 'Icon':
    """
    Sets up the system tray icon with options to toggle color and quit the application.
    It also provides a sub-menu for changing the preferred language.

    Args:
        taskbar_manager: An object responsible for managing the taskbar appearance.

    Returns:
        Icon: The created system tray icon.
    """

    # Function to be executed when clicking an item in the sub-menu
    def select_sub_item(icon, menu_item) -> None:
        """
        Handles the selection of a sub-menu item, updates user preferences,
        and refreshes the icon's menu.

        Args:
            icon: The tray icon object.
            menu_item: The selected menu item.
        """
        # Save the user's preference for the selected item
        save_user_preferences(str(menu_item))

        # Refresh the menu to display changes
        icon.update_menu()

        # Sync the taskbar color with the selected language preference
        sync_taskbar_color_with_preference_lang(taskbar_manager)

    # Function to check if an item is selected and mark it with a check
    def is_selected(menu_item) -> bool:
        """
        Checks if the given menu item is the currently selected one.

        Args:
            menu_item: The menu item to check.

        Returns:
            bool: True if the menu item is selected, False otherwise.
        """
        return menu_item.text == str(load_user_preferences())

    def sub_menu() -> 'Menu':
        """
        Creates a sub-menu for selecting a preferred language.

        Returns:
            Menu: The language selection sub-menu.
        """
        # Create menu items from the all_OS_keyboard_layouts array
        menu_items = [
            item(layout, select_sub_item, checked=is_selected)
            for layout in all_OS_keyboard_layouts
        ]

        # Return a menu with the items
        return Menu(*menu_items)

    # Create the main menu with an item that leads to the sub-menu
    menu = Menu(
        item('Change Preferred Language', sub_menu()),  # Language menu
        item('Toggle Color', lambda: taskbar_manager.toggle_color_prevalence()),  # Option to toggle taskbar color
        item('Check out more versions', lambda: open_git_releases()),  # Option to check for updates
        item('Quit', lambda: on_quit(icon))  # Option to quit the application
    )

    try:
        # Attempt to load an existing icon image
        icon_path = Path(__file__).resolve().parent / 'windows-11-change-taskbar-color.png'
        icon_image = Image.open(icon_path)
    except FileNotFoundError:
        # Create a default icon if the file is not found
        icon_image = create_image(64, 64, 'purple', 'lightblue')

    # Create the tray icon (must provide some image for the icon)
    icon = Icon("Language Toggle", icon_image, "Language Toggle", menu)

    # Start the tray icon in a separate thread
    threading.Thread(target=icon.run, daemon=True).start()

    return icon

def show_update_notification(icon, latest_version):
    """
    Shows a popup notification in the tray icon if a new version is available.
    """
    icon.notify(f"גרסה חדשה זמינה: {latest_version}!", title="עדכון זמין")
















# This function checks the actual state of CapsLock
def is_caps_lock_on():
    hll_dll = ctypes.WinDLL("User32.dll")
    vk_caps_lock = 0x14  # Virtual key code for CapsLock
    # GetKeyState returns 1 if CapsLock is on, otherwise 0
    return hll_dll.GetKeyState(vk_caps_lock) & 0x0001 != 0

# This function is called when the key state changes
def on_press(key):
    global is_caps_lock_on_BOOL
    try:
        if key == keyboard.Key.caps_lock:
            # Check the actual state of CapsLock
            caps_state = is_caps_lock_on()
            if caps_state:
                print("CapsLock is ON.")
                is_caps_lock_on_BOOL = True
                if load_user_preferences() == "English" and taskbar_manager.get_is_ColorPrevalence_on_or_off():
                    # if the user prefer that on English will there not be color and now there is
                    taskbar_manager.toggle_color_prevalence()
                elif not load_user_preferences() == "English" and not taskbar_manager.get_is_ColorPrevalence_on_or_off():
                    taskbar_manager.toggle_color_prevalence()
            else:
                print("CapsLock is OFF.")
                is_caps_lock_on_BOOL = False
                sync_taskbar_color_with_preference_lang(taskbar_manager)
    except AttributeError:
        pass

def listen_to_caps_lock():
    # Create a listener that waits for keyboard events
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()




































if __name__ == "__main__":

    is_caps_lock_on_BOOL = bool(is_caps_lock_on())
    print(is_caps_lock_on_BOOL)

    threading.Thread(target=listen_to_caps_lock).start()


    taskbar_manager = TaskbarManager()  # Initialize the taskbar manager

    all_OS_keyboard_layouts = list()
    for keyboard_layout in get_all_system_keyboard_layouts():
        all_OS_keyboard_layouts.append(keyboard_layout.split()[0])
    print(all_OS_keyboard_layouts)

    sync_taskbar_color_with_preference_lang(taskbar_manager)

    tray_icon = setup_tray_icon(taskbar_manager)  # Set up the system tray icon

    # Check for updates when the program starts
    latest_version = check_for_updates(__version__)
    if latest_version:
        show_update_notification(tray_icon, latest_version)

    monitor_registry_key(hkey, subkey, taskbar_manager)  # Start monitoring registry key changes
