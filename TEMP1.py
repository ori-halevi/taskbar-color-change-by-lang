import ctypes
from ctypes import wintypes

# קביעת מבנה למידע על שפות הקלט
class LANGID(ctypes.Structure):
    _fields_ = [("lang_id", wintypes.WORD)]

def get_installed_languages():
    languages = []
    # קריאה לפונקציה שמחזירה את שפות הקלט המותקנות
    lang_ids = ctypes.windll.user32.GetKeyboardLayoutList(0, None)
    layout_list = (LANGID * lang_ids)()
    ctypes.windll.user32.GetKeyboardLayoutList(lang_ids, ctypes.byref(layout_list))

    for i in range(lang_ids):
        lang_id = layout_list[i].lang_id & 0xFFFF
        languages.append(lang_id)

    return languages

def main():
    installed_languages = get_installed_languages()
    for lang in installed_languages:
        print(f"Installed Language ID: {lang}")

if __name__ == "__main__":
    main()
