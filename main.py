import time
import win32gui
import win32con
import win32api
import win32process
from pynput import keyboard

# 'focus'  = restore & foreground each window before sending (caret, IME, hotkeys all live)
# 'direct' = never touch your desktop; just blast messages into the Edit control
MODE = 'focus'  # or 'direct'

BLACKLIST_TITLES = {
    "Program Manager",
    "Windows Input Experience",
    "Settings",
    "Realtek Audio Console"
}

SPECIAL_KEYS = {
    keyboard.Key.enter:     win32con.VK_RETURN,
    keyboard.Key.tab:       win32con.VK_TAB,
    keyboard.Key.backspace: win32con.VK_BACK,
    keyboard.Key.space:     win32con.VK_SPACE,
    keyboard.Key.esc:       win32con.VK_ESCAPE,
    keyboard.Key.up:        win32con.VK_UP,
    keyboard.Key.down:      win32con.VK_DOWN,
    keyboard.Key.left:      win32con.VK_LEFT,
    keyboard.Key.right:     win32con.VK_RIGHT,
}

def list_windows():
    wins = []
    def _enum(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            title = win32gui.GetWindowText(hwnd).strip()
            if title and title not in BLACKLIST_TITLES:
                wins.append((hwnd, title))
    win32gui.EnumWindows(_enum, None)
    return wins

def get_edit_control(hwnd):
    edit = win32gui.FindWindowEx(hwnd, 0, "Edit", None)
    if edit:
        return edit

    children = []
    def _enum_child(c, _):
        cls = win32gui.GetClassName(c)
        children.append((c, cls))
    win32gui.EnumChildWindows(hwnd, _enum_child, None)
    for c, cls in children:
        if "Edit" in cls:
            return c
    return hwnd

def focus_window(hwnd):
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    except Exception:
        pass

    try:
        my_tid = win32api.GetCurrentThreadId()
        their_tid, _ = win32process.GetWindowThreadProcessId(hwnd)
        win32process.AttachThreadInput(my_tid, their_tid, True)
        win32gui.SetForegroundWindow(hwnd)
        win32process.AttachThreadInput(my_tid, their_tid, False)
    except Exception:
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass

    time.sleep(0.02)

def send_char_to(edit_hwnd, ch):
    win32api.PostMessage(edit_hwnd, win32con.WM_CHAR, ord(ch), 0)

def send_special_to(edit_hwnd, vk):
    win32api.PostMessage(edit_hwnd, win32con.WM_KEYDOWN, vk, 0)
    win32api.PostMessage(edit_hwnd, win32con.WM_KEYUP,   vk, 0)

def on_press_factory(target_hwnds):
    def _on_press(key):
        for hwnd in target_hwnds:
            if MODE == 'focus':
                focus_window(hwnd)

            edit = get_edit_control(hwnd)

            try:
                ch = key.char
                send_char_to(edit, ch)
            except AttributeError:
                vk = SPECIAL_KEYS.get(key)
                if vk is not None:
                    send_special_to(edit, vk)
    return _on_press

def main():
    windows = list_windows()
    print("Available Windows:")
    for idx, (_hwnd, title) in enumerate(windows):
        print(f"  [{idx}] {title}")

    sel = input("\nEnter comma-separated indices to broadcast to (e.g. 0,2): ")
    try:
        indices = [int(x.strip()) for x in sel.split(",") if x.strip()]
        target_hwnds = [windows[i][0] for i in indices]
    except Exception:
        print("Invalid selection. Exiting.")
        return

    mode_desc = "direct to Edit control" if MODE=='direct' else "focusing each window"
    print(f"\nBroadcasting keystrokes to {len(target_hwnds)} window(s) ({mode_desc}).")
    print("Press Ctrl+C to stop.")

    listener = keyboard.Listener(on_press=on_press_factory(target_hwnds))
    listener.start()
    listener.join()

if __name__ == "__main__":
    main()