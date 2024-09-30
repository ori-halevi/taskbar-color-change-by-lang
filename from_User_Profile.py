import winreg
import json


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
        print("The 'Languages' key was not found.")
    except Exception as e:
        print(f"Error reading Languages: {e}")

    return languages


def get_meanings(country_codes: list[str]) -> list[str]:
    """
    Retrieves the meanings of the provided country codes from a JSON file.

    Args:
        country_codes (list): A list of country codes to retrieve meanings for.

    Returns:
        list: A list of meanings corresponding to the provided country codes.
    """
    meanings = []

    # Assume your JSON data is in a file named "language_data.json"
    with open('language_data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

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


if __name__ == "__main__":
    # Example call to the function
    country_codes = ["zh-CHS", "ar-SA", "en-US"]  # Add country codes as desired
    meanings = get_meanings(country_codes)
    print(meanings)
    print(get_meanings(get_languages_from_user_profile()))
