import ctypes


def worker(queue):
    """
    A separate process that gets the current keyboard layout code and sends it to a queue.
    """
    layout_id = ctypes.windll.user32.GetKeyboardLayout(0)  # Gets the current keyboard layout code.
    queue.put(layout_id)  # Sends the result back to the main process
