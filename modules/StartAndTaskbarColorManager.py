import ctypes
import logging
import winreg

# Condition to toggle to see DEBUG logging
DEBUG = False

# Set up logging
logging.basicConfig(level=logging.DEBUG if DEBUG else None,
                    format='%(asctime)s - %(levelname)s - %(message)s')
class StartAndTaskbarColorManager:
    def __init__(self):
        # Load user32.dll to interact with the Windows GUI elements
        self.user32 = ctypes.windll.user32
        # Get the handle of the taskbar
        self.taskbar_handle = self.user32.FindWindowW("Shell_TrayWnd", None)
        # Registry path and value name for taskbar color settings
        self.registry_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        self.color_prevalence_value_name = "ColorPrevalence"

    def toggle_color_prevalence(self) -> None:
        """
        Changes the ColorPrevalence value in the system registry to toggle the color on the taskbar.
        """
        try:
            # Opens the registry key
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0,
                                winreg.KEY_READ | winreg.KEY_WRITE) as registry_key:
                # Read the current value
                current_color_prevalence = winreg.QueryValueEx(registry_key, self.color_prevalence_value_name)[0]
                # Change the current value to the opposite value
                new_color_prevalence = 0 if current_color_prevalence == 1 else 1
                # Set the new value
                winreg.SetValueEx(registry_key, self.color_prevalence_value_name, 0, winreg.REG_DWORD, new_color_prevalence)
                self._refresh_taskbar()

                logging.debug(f"Changed ColorPrevalence from {current_color_prevalence} to {new_color_prevalence}")
        except FileNotFoundError:
            logging.error("Registry path or value not found.")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def _refresh_taskbar(self) -> None:
        """
        Refreshes the taskbar by sending a settings change notification to the taskbar.
        """
        self.user32.SendMessageW(self.taskbar_handle, 0x001A, 0, "ImmersiveColorSet")  # Refresh command to taskbar

    def get_color_prevalence_status(self) -> int | None:
        """
        :return: 1 if ColorPrevalence is on, and 0 otherwise.
        """
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0,
                                winreg.KEY_READ | winreg.KEY_WRITE) as registry_key:
                # Read the current value
                current_color_prevalence = winreg.QueryValueEx(registry_key, self.color_prevalence_value_name)[0]
                return current_color_prevalence
        except FileNotFoundError:
            logging.error("something went wrong!")
            return None  # Make sure to return None in case of error


if __name__ == "__main__":
    object1 = StartAndTaskbarColorManager()
    object1.toggle_color_prevalence()
    print(object1.get_color_prevalence_status())
