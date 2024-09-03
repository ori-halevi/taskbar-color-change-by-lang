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

import ctypes
import multiprocessing
import time
import winreg
import logging
from pathlib import Path
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import threading
import sys
from worker_module import worker

DEBUG = False

# Set up logging
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Global flag to control the main loop
keep_checking = True

# This ensures the `multiprocessing` module finds the correct location for imports
sys.path.append(str(Path(__file__).resolve().parent))

multiprocessing.freeze_support()


class TaskbarManager:
    def __init__(self):
        # Load user32.dll
        self.user32 = ctypes.windll.user32
        # Get the handle of the taskbar
        self.taskbar_handle = self.user32.FindWindowW("Shell_TrayWnd", None)
        self.registry_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        self.value_name = "ColorPrevalence"

    def toggle_color_prevalence(self):
        """
        Changes the ColorPrevalence value in the system registry to turn the color on the taskbar on or off.
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
        self.user32.SendMessageW(self.taskbar_handle, 0x001A, 0, "ImmersiveColorSet")


def get_keyboard_layout_process():
    """
    Runs a separate process to get the current keyboard layout code and returns the result.
    """
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=worker, args=(queue,))
    process.start()
    process.join()
    return queue.get()


def main(taskbar_manager):
    """
    The main loop to check for keyboard layout changes and toggle taskbar color accordingly.
    """
    last_layout_id = get_keyboard_layout_process()

    while keep_checking:
        layout_id = get_keyboard_layout_process()
        if layout_id != last_layout_id:
            logging.debug("Language change detected")
            last_layout_id = layout_id
            taskbar_manager.toggle_color_prevalence()

        time.sleep(0.1)


def create_image(width, height, color1, color2):
    """
    Creates an image for the tray icon.
    """
    image = Image.new('RGB', (width, height), color1)
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, width, height // 2], fill=color2)
    return image


def on_quit(icon, _):
    """
    Callback to quit the application when the tray icon is clicked.
    """
    global keep_checking
    keep_checking = False
    icon.stop()


def setup_tray_icon(taskbar_manager):
    """
    Sets up the system tray icon with options to toggle color and quit the application.
    """
    try:
        icon_path = Path(__file__).resolve().parent / 'windows-11-change-taskbar-color.png'
        icon_image = Image.open(icon_path)
    except FileNotFoundError:
        icon_image = create_image(64, 64, 'purple', 'lightblue')

    menu = Menu(
        MenuItem('Toggle Color', lambda _: taskbar_manager.toggle_color_prevalence()),  # Adding the toggle color option
        MenuItem('Quit', on_quit)
    )

    icon = Icon("Language Toggle", icon_image, "Language Toggle", menu)
    threading.Thread(target=icon.run, daemon=True).start()


if __name__ == "__main__":
    taskbar_manager = TaskbarManager()
    setup_tray_icon(taskbar_manager)
    main(taskbar_manager)
