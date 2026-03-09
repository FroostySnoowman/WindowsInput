# Windows Input Broadcaster

Broadcast keyboard input to multiple Windows application windows at once.

This script enumerates visible windows, lets you choose target windows by index, and then mirrors key presses to all selected targets while preserving focus back to your original window.

## Features

- Lists currently visible, enabled windows.
- Lets you select multiple target windows (for example: `0,2,3`).
- Sends regular character keys and several special keys (`Enter`, `Tab`, arrows, etc.).
- Tries to focus each target window/edit control before posting input.
- Restores focus to your original window after broadcasting.

## Requirements

- Windows OS
- Python 3.10+ (recommended)
- Dependencies from `requirements.txt`:
  - `pynput==1.8.1`
  - `pywin32==310`

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Run:

```bash
python main.py
```

Workflow:

1. The script prints available window titles.
2. Enter comma-separated indices for windows you want to broadcast to.
3. Start typing. Keystrokes are sent to all selected windows.
4. Press `Ctrl+C` to stop.

Example selection:

```text
Indices to broadcast to (e.g. 0,2,3): 0,2,3
```

## Notes and Limitations

- This project is Windows-specific and uses Win32 APIs (`pywin32` + `ctypes`).
- Some windows are excluded by title via `BLACKLIST_TITLES` in `main.py`.
- Delivery reliability depends on target app behavior (some apps ignore posted messages or require elevated privileges).
- Rapid duplicate presses are rate-limited by `MIN_KEY_INTERVAL` to reduce repeats.
- Mouse movement/click simulation is used to focus controls and may briefly move pointer focus.

## Safety

- Test with non-critical apps first.
- Avoid using this where unintended input could cause data loss.
- If needed, run apps and Python with matching privilege level (e.g., all normal user or all admin).
