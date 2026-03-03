import pydirectinput
import time
import random
import win32process
import win32gui
import win32con
import win32com.client
import io
import logging
from mss import mss
from PIL import Image

logger = logging.getLogger(__name__)

def is_focus(func):
    def wrapper(self, *args, **kwargs):
        title = getattr(self, 'game_window_title', None)
        if title:
            active_hwnd = win32gui.GetForegroundWindow()
            window_text = win32gui.GetWindowText(active_hwnd)
            
            if title not in window_text:
                logger.info(f"檢測到視窗失去焦點，嘗試切換回: {title}")
                force_focus(title)
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            logger.error(f"執行操作 {func.__name__} 失敗: {e}")
    return wrapper


def force_focus(game_window_title):
    hwnd = win32gui.FindWindow(None, game_window_title)
    if not hwnd:
        return
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        try:
            win32gui.SetForegroundWindow(hwnd)
        except:
            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys('%')
            win32gui.SetForegroundWindow(hwnd)
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        
    except Exception as e:
        logger.error(f"無法強制聚焦視窗: {e}")

def update_window_rect(func):
    def wrapper(self, *args, **kwargs):
        self._refresh_window_rect()
        return func(self, *args, **kwargs)
    return wrapper

class InputManager:
    def __init__(self, game_window_title):
        self.game_window_title = game_window_title
        self._refresh_window_rect()
    
    def _refresh_window_rect(self):
        hwnd = win32gui.FindWindow(None, self.game_window_title)
        if hwnd:
            point = win32gui.ClientToScreen(hwnd, (0, 0))
            left, top, right, bottom = win32gui.GetClientRect(hwnd)
            self.abs_x, self.abs_y = point[0], point[1]
            self.width, self.height = right - left, bottom - top
        else:
            logger.error(f"找不到視窗: {self.game_window_title}")
    
    @is_focus
    @update_window_rect
    def click(self, r_x, r_y):
        x = self.abs_x + int(r_x * self.width)
        y = self.abs_y + int(r_y * self.height)        
        pydirectinput.moveTo(x, y, duration=random.uniform(0.1, 0.3))
        pydirectinput.mouseDown()
        time.sleep(random.uniform(0.05, 0.1))
        pydirectinput.mouseUp()

    @is_focus
    @update_window_rect
    def send_keys(self, keys):
        pydirectinput.press(keys)
        time.sleep(random.uniform(0.1, 0.3))
        pydirectinput.release(keys)
    
    @is_focus
    @update_window_rect
    def execute_action(self, action):
        if action['type'] == 'click':
            mods = action.get('modifiers', {})
            
            if mods.get('ctrl'): pydirectinput.keyDown('ctrl')
            if mods.get('shift'): pydirectinput.keyDown('shift')
            
            self.click(action['rel_pos'][0], action['rel_pos'][1])
            
            if mods.get('ctrl'): pydirectinput.keyUp('ctrl')
            if mods.get('shift'): pydirectinput.keyUp('shift')

        elif action['type'] == 'keydown':
            pydirectinput.keyDown(action['key'])
        elif action['type'] == 'keyup':
            pydirectinput.keyUp(action['key'])
        elif action['type'] == 'nop':
            pass

    @is_focus
    @update_window_rect
    def snapshot(self):
        with mss() as sct:
            monitor = {"top": self.abs_y, "left": self.abs_x, "width": self.width, "height": self.height}
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
    
    @is_focus
    @update_window_rect
    def try_moving_test(self):
        pydirectinput.moveTo(self.abs_x + self.width // 2, self.abs_y + self.height // 2)
        mouse_pos = win32gui.GetCursorPos()
        pydirectinput.moveRel(100, 0, duration=0.5)
        new_mouse_pos = win32gui.GetCursorPos()
        distance = ((new_mouse_pos[0] - mouse_pos[0]) ** 2 + (new_mouse_pos[1] - mouse_pos[1]) ** 2) ** 0.5
        return distance > 50
        
if __name__ == "__main__":
    game_window_title = "剪取工具"
    manager = InputManager(game_window_title)
    print(manager.click(0.5, 0.5))
    time.sleep(5)
    print(manager.click(0.1, 0.9))
    