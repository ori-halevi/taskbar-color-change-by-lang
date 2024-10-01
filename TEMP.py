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
