import winreg
import json
import os
import shutil
import sys
import logging

# Condition to toggle to see DEBUG logging
DEBUG = False

# Set up logging
logging.basicConfig(level=logging.DEBUG if DEBUG else None,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_languages_from_user_profile() -> list[str]:
    """
    Retrieves the languages from the user's profile in the Windows registry.

    Returns:
        list: A list of language codes that are at least 3 characters long.
    """
    languages = []

    try:
        # Open the registry key for the user profile
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Control Panel\International\User Profile') as reg_key:
            # Get the value of "Languages"
            languages_list = winreg.QueryValueEx(reg_key, "Languages")[0]

            # Filter data with a length less than 3 characters
            for lang in languages_list:
                lang = lang.strip()  # Remove whitespace
                if len(lang) >= 3:
                    languages.append(lang)

    except FileNotFoundError:
        logging.info("The 'Languages' key was not found.")
    except Exception as e:
        logging.info(f"Error reading Languages: {e}")

    return languages


def get_meanings(country_codes: list[str]) -> list[str]:
    """
    Retrieves the meanings of the provided country codes from a JSON file.

    Args:
        country_codes (list): A list of country codes to retrieve meanings for.

    Returns:
        list: A list of meanings corresponding to the provided country codes.
    """
    ensure_json_installed()

    meanings = []

    # Getting the path to the local AppData folder
    appdata_path = os.getenv('LOCALAPPDATA')
    app_folder = os.path.join(appdata_path, "taskbar-color-change-by-lang")

    # Setting the JSON file path
    json_file_path = os.path.join(app_folder, 'language_data.json')

    # Reading JSON data from the file
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        logging.info(f"Error: The file {json_file_path} was not found.")
    except json.JSONDecodeError:
        logging.info(f"Error: Failed to decode the file {json_file_path}.")
    except Exception as e:
        logging.info(f"Error: {str(e)}")

    # Create a dictionary of codes and meanings
    code_to_meaning = {item['Country code']: item['Meaning'] for item in data}

    for code in country_codes:
        # If the country code is not found in the dictionary, skip it
        meaning = code_to_meaning.get(code)
        if meaning:
            meanings.append(meaning)

    return meanings


def get_language_with_meanings() -> list[str]:
    """
    Combines the retrieval of languages from the user's profile and their meanings.

    Returns:
        list: A list of meanings corresponding to the user's languages.
    """
    return get_meanings(get_languages_from_user_profile())




def ensure_json_installed():
    """
    Ensures that the JSON file exists in the local AppData folder.
    If the folder does not exist, it creates it.
    If the JSON file is missing, it copies it from the source directory.
    """
    # Getting the path to the AppData\Local directory
    local_app_data = os.getenv('LOCALAPPDATA')
    target_folder = os.path.join(local_app_data, 'taskbar-color-change-by-lang')
    json_file_name = 'language_data.json'  # Name of your JSON file
    target_file_path = os.path.join(target_folder, json_file_name)

    # Checking if the folder exists, and if not, creating it
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    # Checking if the file already exists
    if not os.path.exists(target_file_path):
        # Determine the source path for the JSON file
        if hasattr(sys, '_MEIPASS'):
            # When running as a bundled executable
            source_json_path = os.path.join(sys._MEIPASS, json_file_name)
        else:
            # When running in a development environment
            source_json_path = json_file_name

        # Copying the file from the source directory
        shutil.copyfile(source_json_path, target_file_path)
        logging.info(f"{json_file_name} copied to {target_file_path}")
    else:
        logging.info(f"{json_file_name} already exists at {target_file_path}")


if __name__ == "__main__":
    # Example call to the function
    country_codes = ["zh-CHS", "ar-SA", "en-US"]  # Add country codes as desired
    meanings = get_meanings(country_codes)
    print(meanings)
    print(get_meanings(get_languages_from_user_profile()))
