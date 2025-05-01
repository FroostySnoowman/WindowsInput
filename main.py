import time
import win32gui, win32con, win32api, win32process
from pynput import keyboard

BLACKLIST_TITLES = {
    "Program Manager",
    "Windows Input Experience",
    "Settings",
    "Realtek Audio Console",
}

PAUSE = 0.15
MIN_KEY_INTERVAL = 0.12

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
    found = []
    def _find(child, _):
        if "Edit" in win32gui.GetClassName(child):
            found.append(child)
    win32gui.EnumChildWindows(hwnd, _find, None)
    return found[0] if found else hwnd


def attach_input(hwnds):
    my_tid = win32api.GetCurrentThreadId()
    seen = set()
    for h in hwnds:
        tid, _ = win32process.GetWindowThreadProcessId(h)
        if tid not in seen:
            win32process.AttachThreadInput(my_tid, tid, True)
            seen.add(tid)


def bring_forward(hwnd):
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    time.sleep(PAUSE)


def click_center(hwnd):
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    cx = (right - left) // 2
    cy = (bottom - top) // 2
    screen_x, screen_y = win32gui.ClientToScreen(hwnd, (cx, cy))
    win32api.SetCursorPos((screen_x, screen_y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,   0, 0, 0, 0)
    time.sleep(PAUSE)


def post_key(target_hwnd, key):
    try:
        win32api.PostMessage(target_hwnd, win32con.WM_CHAR, ord(key.char), 0)
    except (AttributeError, TypeError):
        vk = SPECIAL_KEYS.get(key)
        if vk is not None:
            win32api.PostMessage(target_hwnd, win32con.WM_KEYDOWN, vk, 0)
            win32api.PostMessage(target_hwnd, win32con.WM_KEYUP,   vk, 0)
    time.sleep(PAUSE)

def make_on_press(targets):
    hwnds, edits = zip(*targets)
    attach_input(hwnds)

    last_press_time = {}

    def _on_press(key):
        now = time.perf_counter()
        if (t := last_press_time.get(key)) is not None and now - t < MIN_KEY_INTERVAL:
            return
        last_press_time[key] = now

        original_hwnd = win32gui.GetForegroundWindow()
        original_edit = get_edit_control(original_hwnd) if win32gui.IsWindow(original_hwnd) else None

        for hwnd, edit in targets:
            bring_forward(hwnd)
            click_center(hwnd)
            post_key(edit, key)

        if win32gui.IsWindow(original_hwnd):
            bring_forward(original_hwnd)
            click_center(original_hwnd)
            if original_edit:
                post_key(original_edit, key)

    return _on_press

def main():
    wins = list_windows()
    if not wins:
        print("No broadcastable windows found.")
        return

    print("Available windows:")
    for i, (_, title) in enumerate(wins):
        print(f"  [{i}] {title}")

    sel = input("\nIndices to broadcast to (e.g. 0,2,3): ")
    try:
        idxs = [int(x) for x in sel.split(",") if x.strip()]
        targets = [(wins[i][0], get_edit_control(wins[i][0])) for i in idxs]
    except Exception:
        print("Bad selection.")
        return

    print(f"\nBroadcasting to {len(targets)} window(s).  Ctrl-C to quit.")
    listener = keyboard.Listener(on_press=make_on_press(targets))
    listener.start()
    listener.join()


if __name__ == "__main__":
    main()