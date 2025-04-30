import win32gui
import win32con
import win32api
from pynput import keyboard

BLACKLIST_TITLES = {
    "Program Manager",
    "Windows Input Experience",
    "Settings",
    "Realtek Audio Console"
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

def send_char(hwnd, ch: str):
    win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(ch), 0)

def send_special(hwnd, vk_code: int):
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, 0)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP,   vk_code, 0)

def on_press_factory(target_hwnds):
    def _on_press(key):
        for hwnd in target_hwnds:
            try:
                ch = key.char
                send_char(hwnd, ch)
            except AttributeError:
                vk = None
                if key == keyboard.Key.enter:
                    vk = win32con.VK_RETURN
                elif key == keyboard.Key.tab:
                    vk = win32con.VK_TAB
                elif key == keyboard.Key.backspace:
                    vk = win32con.VK_BACK
                elif key == keyboard.Key.space:
                    vk = win32con.VK_SPACE
                elif key == keyboard.Key.esc:
                    vk = win32con.VK_ESCAPE
                elif key == keyboard.Key.up:
                    vk = win32con.VK_UP
                elif key == keyboard.Key.down:
                    vk = win32con.VK_DOWN
                elif key == keyboard.Key.left:
                    vk = win32con.VK_LEFT
                elif key == keyboard.Key.right:
                    vk = win32con.VK_RIGHT
                if vk:
                    send_special(hwnd, vk)
    return _on_press

def main():
    windows = list_windows()
    print("Available Windows:")
    for idx, (hwnd, title) in enumerate(windows):
        print(f"  [{idx}] {title} (HWND={hwnd})")

    sel = input("\nEnter comma-separated window indices to broadcast to (e.g. 0,2,5): ")
    try:
        indices = [int(x.strip()) for x in sel.split(",") if x.strip()!='']
        target_hwnds = [ windows[i][0] for i in indices ]
    except Exception:
        print("Invalid selection. Exiting.")
        return

    print(f"\nBroadcasting every keystroke to {len(target_hwnds)} window(s). Press Ctrl+C to stop.")
    listener = keyboard.Listener(on_press=on_press_factory(target_hwnds))
    listener.start()
    listener.join()

if __name__ == "__main__":
    main()