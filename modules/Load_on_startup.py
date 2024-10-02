import os
import logging
import winreg as reg

key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'

# Condition to toggle to see DEBUG logging
DEBUG = False

# Set up logging
logging.basicConfig(level=logging.DEBUG if DEBUG else None,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def load_on_startup(app_absolute_path_with_extension: str):
    """
    Adds the application to the Windows startup registry so it will run when the system starts.

    Args:
        app_absolute_path_with_extension (str): The full path of the application, including the file extension.
    """
    # Get the file name from the full path without the extension
    app_name = os.path.splitext(os.path.basename(app_absolute_path_with_extension))[0]
    # Wrap the full path in quotes
    quoted_path = f'"{app_absolute_path_with_extension}"'

    try:
        # Open the key for writing; if it doesn't exist, it will be created
        with reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_SET_VALUE) as key:
            # Add a value to the registry: the app name as the 'key' and the quoted path as the 'value'
            reg.SetValueEx(key, app_name, 0, reg.REG_SZ, quoted_path)
            logging.info(f"Created registry entry for '{app_name}' with path: {quoted_path}")
    except Exception as e:
        logging.error(f"Error creating registry key for '{app_name}': {e}")


def remove_load_on_startup(app_absolute_path_with_extension: str):
    """
    Removes the application from the Windows startup registry.

    Args:
        app_absolute_path_with_extension (str): The full path of the application, including the file extension.
    """
    # Get the file name from the full path without the extension
    app_name = os.path.splitext(os.path.basename(app_absolute_path_with_extension))[0]

    try:
        # Open the key for deletion
        with reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_SET_VALUE) as key:
            reg.DeleteValue(key, app_name)
            logging.info(f"Removed registry entry for '{app_name}'")
    except FileNotFoundError:
        logging.warning(f"Registry key for '{app_name}' not found")
    except Exception as e:
        logging.error(f"Error deleting registry key for '{app_name}': {e}")


def is_load_on_startup(app_absolute_path_with_extension: str) -> bool:
    """
    Checks if the application is set to load on startup in the Windows registry.

    Args:
        app_absolute_path_with_extension (str): The full path of the application, including the file extension.

    Returns:
        bool: True if the application is set to load on startup, False otherwise.
    """
    # Get the file name from the full path without the extension
    app_name = os.path.splitext(os.path.basename(app_absolute_path_with_extension))[0]

    try:
        # Open the key for reading
        with reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_READ) as key:
            # Check if the value exists
            value, _ = reg.QueryValueEx(key, app_name)
            return value == f'"{app_absolute_path_with_extension}"'
    except FileNotFoundError:
        return False
    except Exception as e:
        logging.error(f"Error checking registry key for '{app_name}': {e}")
        return False


if __name__ == '__main__':

    load_on_startup("C:\\path\\to\\your\\file\\example.txt")
    input("1")
    print(is_load_on_startup("C:\\path\\to\\your\\file\\example.txt"))
    input("2")
    remove_load_on_startup("C:\\path\\to\\your\\file\\example.txt")
    input("3")
    print(is_load_on_startup("C:\\path\\to\\your\\file\\example.txt"))
