from modules.from_Keyboard_Layouts import get_keyboard_layout_texts
from modules.from_User_Profile import get_language_with_meanings

def get_all_system_keyboard_layouts() -> list[str]:
    """
    Combines the language meanings and keyboard layouts into a single list.

    Returns:
        list[str]: A combined list of language meanings and keyboard layouts.
    """
    # Retrieve the contents of both functions
    languages = get_language_with_meanings()
    keyboard_layouts = get_keyboard_layout_texts()

    # Combine the two arrays into one array
    combined_array = languages + keyboard_layouts
    return combined_array

if __name__ == '__main__':
    # Print the result
    print(get_all_system_keyboard_layouts())
