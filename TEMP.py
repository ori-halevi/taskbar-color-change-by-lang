import ctypes
import locale

# הטעינת הספרייה user32.dll
user32 = ctypes.windll.user32

def get_keyboard_layout_list():
    # קבלת מספר פריסות המקלדת (שפות הקלט) המותקנות במערכת
    n = user32.GetKeyboardLayoutList(0, None)
    if n == 0:
        return []

    # יצירת מערך לשמירת פריסות המקלדת
    klid_array = (ctypes.c_uint * n)()
    user32.GetKeyboardLayoutList(n, klid_array)

    # רשימה לשמירת שמות השפות
    languages = []

    # מעברים על הפריסות ומחפשים את שם השפה מה-LCID
    for klid in klid_array:
        lang_id = klid & 0xFFFF  # חילוץ ה-LANGID
        print(lang_id)
        language = locale.windows_locale.get(lang_id, f"Unknown (ID: {lang_id})")
        languages.append(language)

    return languages

# קריאה לפונקציה והדפסת התוצאה
input_languages = get_keyboard_layout_list()
print(f"Installed input languages: {input_languages}")
print(f"Number of input languages: {len(input_languages)}")




import locale

# פונקציה לתרגום מזהה LCID לשפה
def lcid_to_language(lcid):
    try:
        # שימוש במילון windows_locale לקבלת קוד השפה
        language_code = locale.windows_locale[lcid]
        return language_code
    except KeyError:
        return f"Unknown LCID: {lcid}"

# דוגמה לשימוש
lcids = [1033, 1037, 3073, 13313, 1061, 12300, 5132]
languages = [lcid_to_language(lcid) for lcid in lcids]

# הדפסת השפות
print(languages)
