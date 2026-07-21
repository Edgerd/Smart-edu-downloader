---
name: "ai-computer-control"
description: "Controls the computer by taking screenshots, analyzing the screen, and performing mouse/keyboard/terminal/browser actions. Invoke when the user asks to control the PC, move/click the mouse, automate desktop operations, click something on screen, or perform multi-step GUI tasks."
---

# AI Computer Control

This skill enables autonomous computer control through a see-think-act loop. It supports both mouse and keyboard automation, with a strong preference for mouse actions when the user explicitly asks to control or click the mouse.

## When to Invoke

- User says "control my computer", "帮我操作电脑", "控制电脑", "控制鼠标", "点击屏幕".
- User asks to move/click/drag/scroll the mouse.
- User describes a GUI task: "open XXX and click YYY", "fill in the form", "take a screenshot and tell me what's wrong".
- User wants desktop automation beyond a single command.

## Workflow

Always follow this loop until the task is complete or the user stops you:

### 1. Observe
- Use the `screenshot` skill to capture the current screen.
- Describe what you see: active window, controls, buttons, input fields, cursor position, coordinates of relevant UI elements.
- When coordinates matter, estimate them from the screenshot or use `pyautogui.position()` to read the current cursor location.

### 2. Reason
- Compare the current state with the user's goal.
- Identify the next single action needed.
- Prefer mouse actions when the user asked for mouse control; use keyboard only as a fallback or for text input.
- Prefer safe, reversible actions. Avoid destructive actions without explicit confirmation.

### 3. Act
Choose the appropriate tool:

| Goal | Tool / Method |
|------|---------------|
| Move/click/drag/scroll the mouse | `RunCommand` to execute a Python script using `pyautogui`. |
| Type text or press keys | `RunCommand` to execute a Python script using `pyautogui`. |
| Execute shell commands, open apps | `RunCommand` directly. |
| Interact with web pages | `browser_*` tools (navigate, click, type, evaluate, etc.). |
| Read screen content | `screenshot` skill + vision analysis. |

### 4. Confirm
- After each action, take another screenshot if needed.
- Verify the expected change occurred before proceeding.

## Mouse Control Reference

Create and run a temporary Python script when you need to control the mouse.

### Get current cursor position

```python
import pyautogui
print(pyautogui.position())
```

### Move the cursor

```python
import pyautogui
pyautogui.moveTo(500, 500, duration=0.3)
```

### Click

```python
import pyautogui
pyautogui.click(500, 500)          # left click
pyautogui.click(500, 500, clicks=2) # double click
pyautogui.rightClick(500, 500)      # right click
pyautogui.middleClick(500, 500)     # middle click
```

### Drag

```python
import pyautogui
pyautogui.moveTo(500, 500)
pyautogui.dragTo(700, 500, duration=0.5)
```

### Scroll

```python
import pyautogui
pyautogui.scroll(500)   # scroll up
pyautogui.scroll(-500)  # scroll down
```

### Click and hold / release

```python
import pyautogui
pyautogui.mouseDown()
pyautogui.moveTo(700, 500, duration=0.5)
pyautogui.mouseUp()
```

Save the script to a temporary file (e.g. `runtime/temp/computer_use_action.py`) and run it with `RunCommand`.

## How to Find Element Coordinates Precisely

**Never guess coordinates from a screenshot by eye.** Human visual estimation is unreliable. Always use one of the programmatic methods below, ordered from most to least reliable.

### Priority 1: Windows UI Automation (most reliable for native apps)

Use `pywinauto` or `uiautomation` to query the OS accessibility tree and get exact control rectangles. This is the preferred method on Windows because it is independent of screen resolution and window position.

```bash
pip install pywinauto
```

```python
from pywinauto import Desktop
import pyautogui

# List all visible windows
for w in Desktop(backend="uia").windows():
    print(w.window_text(), w.rectangle())

# Example: click a control by its accessible name
start = Desktop(backend="uia").window(title="启动")
start.wait('visible')
chrome = start.child_window(title="Google Chrome", control_type="ListItem")
rect = chrome.rectangle()
center = (rect.left + rect.width() // 2, rect.top + rect.height() // 2)
pyautogui.click(*center)
```

Useful `pywinauto` tools:
- `print_control_identifiers()` to dump the control tree.
- `Inspect.exe` (from Windows SDK) for manual inspection.

### Priority 2: Image template matching

When UI Automation cannot find the control, save a small cropped image of the target and use `pyautogui.locateOnScreen` or `locateCenterOnScreen`. Requires OpenCV for confidence support.

```bash
pip install opencv-python
```

```python
import pyautogui

# Returns Box(left, top, width, height) or raises ImageNotFoundException
box = pyautogui.locateOnScreen('runtime/temp/target_button.png', confidence=0.9)
center = pyautogui.center(box)
pyautogui.click(center.x, center.y)
```

Tips:
- Use `confidence=0.9`.
- Keep templates small and unique.
- The template must match the current theme/scale exactly.
- Restrict the search region for speed: `region=(left, top, width, height)`.

For faster or more robust matching, use OpenCV directly:

```python
import cv2
import numpy as np
from PIL import ImageGrab

screen = np.array(ImageGrab.grab())
template = cv2.imread('runtime/temp/target_button.png')
result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
if max_val >= 0.8:
    h, w = template.shape[:2]
    center = (max_loc[0] + w // 2, max_loc[1] + h // 2)
    pyautogui.click(*center)
```

### Priority 3: OCR text localization

Use OCR when the target has visible text and no stable image/template or accessible name.

```bash
pip install easyocr
```

```python
import pyautogui
import numpy as np
import easyocr

screenshot = pyautogui.screenshot()
img = np.array(screenshot)
reader = easyocr.Reader(['ch_sim', 'en'])
results = reader.readtext(img)

for bbox, text, conf in results:
    if "登录" in text:
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        cx = int(sum(xs) / len(xs))
        cy = int(sum(ys) / len(ys))
        pyautogui.click(cx, cy)
        break
```

OCR is slower and may miss short labels; prefer UI Automation or image matching when possible.

### Priority 4: AI vision model

If a multimodal LLM or vision API is available, send the screenshot and ask it to return the bounding box or center coordinates of the target element. Validate the returned coordinates with a follow-up screenshot before clicking.

### Last Resort: Manual cursor position

Move the mouse to the target and run:

```python
import pyautogui
print(pyautogui.position())
```

This only works when a human is present to position the cursor. Do not use visual estimation from static screenshots.

## Keyboard Control Reference

Use keyboard only when mouse is not practical (e.g., text input, shortcuts).

```python
# Type text into the active field
import pyautogui
pyautogui.typewrite("hello world", interval=0.01)
```

```python
# Press a key combination
import pyautogui
pyautogui.hotkey("win", "r")
```

## Safety Rules

1. **Confirm destructive actions**: Do not delete files, format drives, send emails, or make purchases without explicit user confirmation.
2. **One action at a time**: Perform one small action per step, then verify with a screenshot.
3. **Escape safely**: If the screen does not change as expected after 3 attempts, stop and ask the user for help.
4. **Respect focus**: When typing, ensure the correct input field is focused first (click it, then type).
5. **Privacy**: Do not capture or describe sensitive information (passwords, private messages) unless the task explicitly requires it.

## Example Session (Mouse-Based)

User: "Open the calculator and calculate 123 + 456 using the mouse."

1. Screenshot -> desktop visible.
2. RunCommand: open calculator via `start calc` or `pyautogui.hotkey('win','r')` + type `calc` + `enter`.
3. Screenshot -> calculator window open at coordinates around (760, 400).
4. RunCommand: click calculator buttons with the mouse.
   ```python
   import pyautogui, time
   pyautogui.click(820, 690)  # 1
   time.sleep(0.1)
   pyautogui.click(920, 690)  # 2
   time.sleep(0.1)
   pyautogui.click(1020, 690) # 3
   time.sleep(0.1)
   pyautogui.click(1020, 620) # +
   time.sleep(0.1)
   pyautogui.click(820, 760)  # 4
   time.sleep(0.1)
   pyautogui.click(920, 760)  # 5
   time.sleep(0.1)
   pyautogui.click(1020, 760) # 6
   time.sleep(0.1)
   pyautogui.click(1020, 890) # =
   ```
5. Screenshot -> result 579 shown.
6. Report completion.
