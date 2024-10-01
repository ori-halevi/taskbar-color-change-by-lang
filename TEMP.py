from pystray import MenuItem as item, Menu, Icon
from PIL import Image  # pystray דורש תמונה לאייקון

# משתנה גלובלי לשמירת הפריט הנבחר
selected_item = None

# פונקציה שתופעל בעת לחיצה על פריט בתפריט הבן
def select_sub_item(icon, menu_item):
    global selected_item
    # עדכון הפריט הנבחר
    selected_item = menu_item.text
    # רענון התפריט כדי להציג את השינוי
    icon.update_menu()

# פונקציה שבודקת אם פריט נבחר ומסמנת אותו עם V
def is_selected(menu_item):
    return menu_item.text == selected_item

def sub_menu():
    # יצירת תפריט בן עם אפשרות לבחירה
    sub_menu = Menu(
        item('Sub Item 1', select_sub_item, checked=is_selected),
        item('Sub Item 2', select_sub_item, checked=is_selected)
    )
    return sub_menu

# יצירת תפריט ראשי עם פריט שמוביל לתת-תפריט
menu = Menu(
    item('Main Item', sub_menu()),  # זהו הפריט שמוביל לתת-תפריט
    item('Exit', lambda icon, item: icon.stop())  # פריט ליציאה
)

# יצירת אייקון (חובה לספק תמונה כלשהי לאייקון)
icon_image = Image.new('RGB', (64, 64), color=(73, 109, 137))

# יצירת אייקון והפעלתו עם התפריט
icon = Icon('test', icon_image, menu=menu)
icon.run()



































# רשימת השפות הנתמכות
supported_languages = all_OS_keyboard_layouts


def is_selected(menu_item):
    print(menu_item, "sss")
    return menu_item.text == load_user_preferences()


# יצירת תפריט עם רשימת השפות
def set_preferred_language(language):
    print("Setting preferred language", language)

    save_user_preferences(language)

    print(f"Preferred language set to: {language}")
    # לאחר שינוי השפה יש לעדכן את התפריט כולו


# פונקציה ליצירת פריט תפריט עבור כל שפה
def create_language_item(language):
    print("here", load_user_preferences())
    return item(
        f"{language} {'✔' if language == load_user_preferences() else ''}",
        lambda: set_preferred_language(language)
    )


# יצירת תפריט השפות
def language_menu():
    # יצירת פריטי תפריט מתוך רשימת פריסות המקלדת
    menu_items = [
        item(layout, load_user_preferences, checked=is_selected)
        for layout in all_OS_keyboard_layouts
    ]

    # יצירת תפריט עם הפריטים
    return Menu(*menu_items)


try:
    # נסיון לטעון אייקון קיים
    icon_path = Path(__file__).resolve().parent / 'windows-11-change-taskbar-color.png'
    icon_image = Image.open(icon_path)
except FileNotFoundError:
    # יצירת אייקון ברירת מחדל במקרה שהקובץ לא נמצא
    icon_image = create_image(64, 64, 'purple', 'lightblue')

# הגדרת התפריט עבור אייקון המגש
menu = Menu(
    item('Change Preferred Language', language_menu()),  # תפריט השפות
    item('Toggle Color', lambda: taskbar_manager.toggle_color_prevalence()),  # אפשרות להחליף צבע
    item('Check out more versions', lambda: open_git_releases()),  # אפשרות לבדוק עדכונים
    item('Quit', lambda: icon.stop())  # אפשרות לצאת
)

# יצירת אייקון המגש
icon = Icon("Language Toggle", icon_image, "Language Toggle", menu)

# הפעלת אייקון המגש עם חוט נפרד
threading.Thread(target=icon.run, daemon=True).start()

return icon