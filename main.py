import time
import win32gui, win32con, win32api, win32process
from pynput import keyboard

MODE = 'focus'   # 'direct' (no UI focus, fastest) or 'focus' (SetFocus each time)
DELAY = 0.005    # small pause after SetForegroundWindow / SetFocus

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

def attach_input_threads(hwnds):
    my_tid = win32api.GetCurrentThreadId()
    seen = set()
    for hwnd in hwnds:
        their_tid, _ = win32process.GetWindowThreadProcessId(hwnd)
        if their_tid not in seen:
            win32process.AttachThreadInput(my_tid, their_tid, True)
            seen.add(their_tid)

def focus_and_set(hwnd, target_hwnd):
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    time.sleep(DELAY)
    try:
        win32gui.SetFocus(target_hwnd)
    except Exception:
        pass
    time.sleep(DELAY)

def on_press_factory(hwnds, edits):
    def _on_press(key):
        for hwnd, edit in zip(hwnds, edits):
            if MODE == 'focus':
                focus_and_set(hwnd, edit)

            try:
                ch = key.char
                win32api.PostMessage(edit, win32con.WM_CHAR, ord(ch), 0)
            except (AttributeError, TypeError):
                vk = SPECIAL_KEYS.get(key)
                if vk is not None:
                    win32api.PostMessage(edit, win32con.WM_KEYDOWN, vk, 0)
                    win32api.PostMessage(edit, win32con.WM_KEYUP,   vk, 0)
    return _on_press

def main():
    windows = list_windows()
    print("Available Windows:")
    for i, (_hwnd, title) in enumerate(windows):
        print(f"  [{i}] {title}")

    sel = input("\nEnter comma-separated indices to broadcast to (e.g. 0,2): ")
    try:
        idxs = [int(x) for x in sel.split(",") if x.strip()!='']
        hwnds = [windows[i][0] for i in idxs]
    except Exception:
        print("Invalid selection. Exiting.")
        return

    edits = [get_edit_control(h) for h in hwnds]

    attach_input_threads(hwnds)

    mode_desc = "direct to controls" if MODE=='direct' else "focus+SetFocus"
    print(f"\nBroadcasting keystrokes to {len(hwnds)} window(s) ({mode_desc}).")
    print("Hold any key or type normally; press Ctrl+C to stop.")

    listener = keyboard.Listener(on_press=on_press_factory(hwnds, edits))
    listener.start()
    listener.join()

if __name__ == "__main__":
    main()