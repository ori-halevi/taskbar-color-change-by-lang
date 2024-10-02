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
import shutil
import json
import sys
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
from pystray import MenuItem as item, Menu, Icon
from modules.Find_out_installd_keyboard_layout import get_all_system_keyboard_layouts
from modules.Load_on_startup import *
from modules.Language_change_monitor import *
from modules.StartAndTaskbarColorManager import StartAndTaskbarColorManager

# Version of this release
__version__ = 'v2.0.0'

# Condition to toggle to see DEBUG logging
DEBUG = False

# Set up logging
logging.basicConfig(level=logging.DEBUG if DEBUG else None,
                    format='%(asctime)s - %(levelname)s - %(message)s')


#
# Section for local simple functions:

def get_current_app_path():
    # Getting the full path of the currently running software
    app_path = os.path.abspath(sys.argv[0])
    return app_path


def show_update_notification(icon, latest_version):
    """
    Shows a popup notification in the tray icon if a new version is available.

    Args:
        icon: The tray icon instance that will display the notification.
        latest_version (str): The latest available version to notify the user about.
    """
    icon.notify(f"A new and better version is available: {latest_version}!", title="Update Available")


def sync_taskbar_color_with_preference_lang():
    """
    Synchronize the taskbar color with the preferred lang.
    """
    if load_user_preferences() == get_current_language().split()[0] and taskbar_manager.get_color_prevalence_status():
        taskbar_manager.toggle_color_prevalence()
        logging.info("taskbar color changed!")
    elif load_user_preferences() != get_current_language().split()[0] and not taskbar_manager.get_color_prevalence_status():
        taskbar_manager.toggle_color_prevalence()
        logging.info("taskbar color changed!")


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


#
#
# This section is responsible for monitoring the user's preferred language:
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


#
#
# This section is responsible for the tray icon display:
def setup_tray_icon() -> 'Icon':
    """
    Sets up the system tray icon with options to toggle color and quit the application.
    It also provides a sub-menu for changing the preferred language.

    Args:
        taskbar_manager: An object responsible for managing the taskbar appearance.

    Returns:
        Icon: The created system tray icon.
    """

    def quit_application():
        """
        Callback to quit the application when the tray icon is clicked.
        """
        stop_event.set()  # Signal all threads to stop
        logging.info("Exiting application.")
        kernel32.CloseHandle(taskbar_manager.taskbar_handle)  # Close the taskbar handle
        icon.stop()  # Stop the tray icon
        time.sleep(2)  # Short delay before exit
        os._exit(0)

    def generate_icon_image(width, height, top_color, bottom_color):
        """
        Creates an image for the tray icon.

        Args:
            width: The width of the icon.
            height: The height of the icon.
            top_color: Color for the top half of the icon.
            bottom_color: Color for the bottom half of the icon.
        """
        image = Image.new('RGB', (width, height), top_color)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, width, height // 2), fill=bottom_color)  # Use a tuple instead of a list
        return image

    def handle_menu_selection(icon_object, selected_menu_item) -> None:
        """
        Handles the selection of a sub-menu item, updates user preferences,
        and refreshes the icon's menu.

        Args:
            icon_object: The tray icon object.
            selected_menu_item: The selected menu item.
        """
        # Save the user's preference for the selected item
        save_user_preferences(str(selected_menu_item))

        # Refresh the menu to display changes
        icon_object.update_menu()

        # Sync the taskbar color with the selected language preference
        sync_taskbar_color_with_preference_lang()

    def is_currently_selected(menu_item) -> bool:
        """
        Checks if the given menu item is the currently selected one.

        Args:
            menu_item: The menu item to check.

        Returns:
            bool: True if the menu item is selected, False otherwise.
        """
        return menu_item.text == str(load_user_preferences())

    def create_language_sub_menu() -> 'Menu':
        """
        Creates a sub-menu for selecting a preferred language.

        Returns:
            Menu: The language selection sub-menu.
        """
        # Get array with all the keyboard layouts on the OS
        available_keyboard_layouts = list()
        for keyboard_layout in get_all_system_keyboard_layouts():
            available_keyboard_layouts.append(keyboard_layout.split()[0])

        # Create menu items from the available_keyboard_layouts array
        menu_items = [
            item(layout, handle_menu_selection, checked=is_currently_selected)
            for layout in available_keyboard_layouts
        ]

        # Return a menu with the items
        return Menu(*menu_items)

    def toggle_startup_on_boot(icon_object):
        """
        Toggles whether the application should load on startup.
        """
        app_path = get_current_app_path()
        if is_load_on_startup(app_path):
            remove_load_on_startup(app_path)
        else:
            load_on_startup(app_path)
        # Refresh the menu to display changes
        icon_object.update_menu()

    def is_startup_on_boot_enabled(_) -> bool:
        """
        Checks if the application is set to load on startup.

        Returns:
            bool: True if set to load on startup, False otherwise.
        """
        app_path = get_current_app_path()
        return is_load_on_startup(app_path)

    # Create the main menu with an item that leads to the sub-menu
    menu = Menu(
        item('Load on Startup', toggle_startup_on_boot, checked=is_startup_on_boot_enabled),  # Load on startup option
        item('━ ━━ ━━━ ━━━━ ━━━━━ ━━━━━━ ━━━━', lambda: None),  # A fake separator
        item('Change Preferred Language', create_language_sub_menu()),  # Language menu
        item('Toggle Taskbar Color (Temporary)', lambda: taskbar_manager.toggle_color_prevalence()),    # Taskbar color toggle
        item('Check for Updates', lambda: open_git_releases()),  # Option to check for updates
        item('Quit', lambda: quit_application())  # Option to quit the application
    )

    try:
        # Attempt to load an existing icon image
        icon_path = Path(__file__).resolve().parent / 'windows-11-change-taskbar-color.png'
        icon_image = Image.open(icon_path)
    except FileNotFoundError:
        # Create a default icon if the file is not found
        icon_image = generate_icon_image(64, 64, 'purple', 'lightblue')

    # Create the tray icon (must provide some image for the icon)
    icon = Icon("Language Toggle", icon_image, "Language Toggle", menu)

    # Start the tray icon in a separate thread
    threading.Thread(target=icon.run, daemon=True).start()

    return icon


#
# This section is responsible for CapsLock related code:

# This function checks the actual state of CapsLock
def is_caps_lock_on():
    hll_dll = ctypes.WinDLL("User32.dll")
    vk_caps_lock = 0x14  # Virtual key code for CapsLock
    # GetKeyState returns 1 if CapsLock is on, otherwise 0
    return hll_dll.GetKeyState(vk_caps_lock) & 0x0001 != 0


# This function is called when the key state changes
def on_press(key):
    try:
        if key == keyboard.Key.caps_lock:
            # Check the actual state of CapsLock
            caps_state = is_caps_lock_on()
            if caps_state:
                logging.info("CapsLock is ON.")
                if load_user_preferences() == "English" and taskbar_manager.get_color_prevalence_status():
                    # if the user prefer that on English will there not be color and now there is
                    taskbar_manager.toggle_color_prevalence()
                elif not load_user_preferences() == "English" and not taskbar_manager.get_color_prevalence_status():
                    taskbar_manager.toggle_color_prevalence()
            else:
                logging.info("CapsLock is OFF")
                sync_taskbar_color_with_preference_lang()
    except AttributeError:
        pass

# This function starts the listener to CapsLock changes
def listen_to_caps_lock():
    # Create a listener that waits for keyboard events
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


#
#
#
# This is the main function that starts the magic:
def main():

    sync_taskbar_color_with_preference_lang()

    tray_icon = setup_tray_icon()  # Set up the system tray icon

    # Check for updates when the program starts
    latest_version = check_for_updates(__version__)
    if latest_version:
        show_update_notification(tray_icon, latest_version)

    threading.Thread(target=listen_to_caps_lock).start()

    def main_toggle_taskbar_color_condition():
        if not is_caps_lock_on():
            taskbar_manager.toggle_color_prevalence()  # Toggle color on taskbar
        elif is_caps_lock_on():
            if load_user_preferences() == "English" and taskbar_manager.get_color_prevalence_status():
                # if the user prefer that on English will there not be color and now there is
                taskbar_manager.toggle_color_prevalence()

    while not stop_event.is_set():
        start_monitor_language_in_registry_key(-1, main_toggle_taskbar_color_condition)


if __name__ == "__main__":

    # Global stop event to control the monitoring thread
    stop_event = threading.Event()

    # Building an object of StartAndTaskbarColorManager
    taskbar_manager = StartAndTaskbarColorManager()  # Initialize the taskbar manager

    # Start the engine
    main()
