import time
import win32gui, win32con, win32api, win32process
from pynput import keyboard

CLICK_OFFSET = (10, 10)   # x,y pixels inside the client rect to click
PAUSE = 0.003             # seconds to wait after bringing a window forward
BLACKLIST_TITLES = {
    "Program Manager",
    "Windows Input Experience",
    "Settings",
    "Realtek Audio Console",
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
    out = []
    def _enum(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            title = win32gui.GetWindowText(hwnd).strip()
            if title and title not in BLACKLIST_TITLES:
                out.append((hwnd, title))
    win32gui.EnumWindows(_enum, None)
    return out

def get_edit_control(hwnd):
    edit = win32gui.FindWindowEx(hwnd, 0, "Edit", None)
    if edit:
        return edit
    def _find(child, found):
        if "Edit" in win32gui.GetClassName(child):
            found.append(child)
    found = []
    win32gui.EnumChildWindows(hwnd, _find, found)
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

def click_inside(hwnd, offset=CLICK_OFFSET):
    x_client, y_client = win32gui.ClientToScreen(hwnd, (0, 0))
    x = x_client + offset[0]
    y = y_client + offset[1]
    win32api.SetCursorPos((x, y))
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

def make_on_press(targets):
    hwnds, edits = zip(*targets)
    attach_input(hwnds)

    def _on_press(key):
        original_hwnd = win32gui.GetForegroundWindow()
        original_edit = get_edit_control(original_hwnd)

        for hwnd, edit in targets:
            bring_forward(hwnd)
            click_inside(hwnd)
            post_key(edit, key)

        if win32gui.IsWindow(original_hwnd):
            bring_forward(original_hwnd)
            click_inside(original_hwnd)
            post_key(original_edit, key)

    return _on_press

def main():
    wins = list_windows()
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