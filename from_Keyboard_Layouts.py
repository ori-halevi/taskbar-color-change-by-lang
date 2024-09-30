import winreg


def read_keyboard_layouts() -> list[str]:
    """
    Reads the keyboard layouts from the Windows registry for the current user.

    Returns:
        list: A list of keyboard layout identifiers.
    """
    layouts = []

    try:
        # Open the registry key for keyboard layouts
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Keyboard Layout\Preload') as reg_key:
            i = 0
            while True:
                try:
                    # Get the value of the layout identifier
                    layout_value = winreg.EnumValue(reg_key, i)
                    layouts.append(layout_value[1])  # The identifier is in the first position of the value
                    i += 1
                except OSError:
                    break  # Exit when there are no more values

    except Exception as e:
        print(f"Error: {e}")

    return layouts


def get_layout_text(layout_id: str) -> str | None:
    """
    Retrieves the layout text for a given keyboard layout identifier from the registry.

    Args:
        layout_id (str): The identifier of the keyboard layout.

    Returns:
        str or None: The layout text if found, otherwise None.
    """
    try:
        # Open the registry key for the keyboard layout
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf'SYSTEM\CurrentControlSet\Control\Keyboard Layouts\{layout_id}') as reg_key:
            # Get the value of "Layout Text"
            layout_text = winreg.QueryValueEx(reg_key, "Layout Text")[0]
            return layout_text
    except FileNotFoundError:
        return None  # The key does not exist
    except Exception as e:
        print(f"Error reading {layout_id}: {e}")
        return None


def find_layout_texts(layout_ids: list[str]) -> list[str]:
    """
    Finds and filters layout texts for a list of keyboard layout identifiers.

    Args:
        layout_ids (list): A list of keyboard layout identifiers.

    Returns:
        list: A list of layout texts that are at least 3 characters long.
    """
    layout_texts = []

    for layout_id in layout_ids:
        text = get_layout_text(layout_id)
        # Filter texts with a length less than 3 characters
        if text and len(text) >= 3:
            layout_texts.append(text)

    return layout_texts


def get_keyboard_layout_texts() -> list[str]:
    """
    Retrieves and returns the layout texts for all keyboard layouts available for the current user.

    Returns:
        list: A list of keyboard layout texts.
    """
    keyboard_layouts = read_keyboard_layouts()  # Read the keyboard layouts
    result = find_layout_texts(keyboard_layouts)  # Find the texts for the keyboard layouts
    return result  # Return the final result


if __name__ == "__main__":
    # Using the function
    layout_texts = get_keyboard_layout_texts()
    print("Layout Texts Found:", layout_texts)
