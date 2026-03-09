import time
import ctypes
import win32gui
import win32con
import win32api
import win32process
from ctypes import wintypes
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

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx",       wintypes.LONG),
        ("dy",       wintypes.LONG),
        ("mouseData",wintypes.DWORD),
        ("dwFlags",  wintypes.DWORD),
        ("time",     wintypes.DWORD),
        ("dwExtraInfo", wintypes.ULONG_PTR),
    ]

class INPUT(ctypes.Structure):
    class _INPUT_UNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("union",)
    _fields_ = [
        ("type",  wintypes.DWORD),
        ("union", _INPUT_UNION),
    ]

def send_input(mi):
    ctypes.windll.user32.SendInput(1, ctypes.byref(mi), ctypes.sizeof(mi))

def click_center(hwnd):
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    cx = (right - left) // 2
    cy = (bottom - top) // 2
    sx, sy = win32gui.ClientToScreen(hwnd, (cx, cy))
    sw = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    sh = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    ax = int(sx * 65535 / (sw - 1))
    ay = int(sy * 65535 / (sh - 1))
    mi = INPUT(type=0, mi=MOUSEINPUT(ax, ay, 0, win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, 0, 0))
    send_input(mi)
    time.sleep(0.01)
    down = INPUT(type=0, mi=MOUSEINPUT(ax, ay, 0, win32con.MOUSEEVENTF_LEFTDOWN | win32con.MOUSEEVENTF_ABSOLUTE, 0, 0))
    up   = INPUT(type=0, mi=MOUSEINPUT(ax, ay, 0, win32con.MOUSEEVENTF_LEFTUP   | win32con.MOUSEEVENTF_ABSOLUTE, 0, 0))
    send_input(down)
    send_input(up)
    time.sleep(PAUSE)

def list_windows():
    wins = []
    def _enum(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            t = win32gui.GetWindowText(hwnd).strip()
            if t and t not in BLACKLIST_TITLES:
                wins.append((hwnd, t))
    win32gui.EnumWindows(_enum, None)
    return wins

def get_edit_control(hwnd):
    e = win32gui.FindWindowEx(hwnd, 0, "Edit", None)
    if e:
        return e
    found = []
    def _find(c, _):
        if "Edit" in win32gui.GetClassName(c):
            found.append(c)
    win32gui.EnumChildWindows(hwnd, _find, None)
    return found[0] if found else hwnd

def attach_input(hwnds):
    tid = win32api.GetCurrentThreadId()
    s = set()
    for h in hwnds:
        t, _ = win32process.GetWindowThreadProcessId(h)
        if t not in s:
            win32process.AttachThreadInput(tid, t, True)
            s.add(t)

def bring_forward(hwnd):
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except:
        pass
    time.sleep(PAUSE)

def post_key(hwnd, key):
    try:
        win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(key.char), 0)
    except:
        vk = SPECIAL_KEYS.get(key)
        if vk is not None:
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
            win32api.PostMessage(hwnd, win32con.WM_KEYUP,   vk, 0)
    time.sleep(PAUSE)

def make_on_press(targets):
    hwnds, edits = zip(*targets)
    attach_input(hwnds)
    last = {}
    def _on_press(key):
        now = time.perf_counter()
        if (t := last.get(key)) and now - t < MIN_KEY_INTERVAL:
            return
        last[key] = now
        orig = win32gui.GetForegroundWindow()
        oe = get_edit_control(orig) if win32gui.IsWindow(orig) else None
        for h, e in targets:
            bring_forward(h)
            try: win32gui.SetFocus(e)
            except: pass
            click_center(e)
            post_key(e, key)
        if win32gui.IsWindow(orig) and oe:
            bring_forward(orig)
            click_center(oe)
            post_key(oe, key)
    return _on_press

def main():
    wins = list_windows()
    if not wins:
        print("No broadcastable windows found.")
        return
    print("Available windows:")
    for i, (_, t) in enumerate(wins):
        print(f"  [{i}] {t}")
    sel = input("\nIndices to broadcast to (e.g. 0,2,3): ")
    try:
        idxs = [int(x) for x in sel.split(",") if x.strip()]
        targets = []
        for i in idxs:
            h = wins[i][0]
            targets.append((h, get_edit_control(h)))
    except:
        print("Bad selection.")
        return
    print(f"\nBroadcasting to {len(targets)} window(s). Ctrl-C to quit.")
    listener = keyboard.Listener(on_press=make_on_press(targets))
    listener.start()
    listener.join()

if __name__ == "__main__":
    main()