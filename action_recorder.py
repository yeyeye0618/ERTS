from pynput import mouse, keyboard
import json
import time
import win32gui

def get_rect(game_window_title):
    hwnd = win32gui.FindWindow(None, game_window_title)
    if not hwnd:
        return
    
    point = win32gui.ClientToScreen(hwnd, (0, 0))
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    return (point[0], point[1], right - left, bottom - top)


class ActionRecorder:
    def __init__(self, game_title, file_name="script.json"):
        self.file_name = file_name
        self.game_title = game_title
        self.actions = []
        self.start_time = None
        self.abs_x, self.abs_y, self.width, self.height = get_rect(game_title)
        
        # 用於追蹤目前哪些按鍵被按住了
        self.current_modifiers = {
            'ctrl': False,
            'shift': False,
            'alt': False
        }

    def _get_relative_pos(self, x, y):
        rel_x = (x - self.abs_x) / self.width if self.width > 0 else 0
        rel_y = (y - self.abs_y) / self.height if self.height > 0 else 0
        return rel_x, rel_y

    def on_click(self, x, y, button, pressed):
        # 我們只紀錄「按下」的那一刻
        if pressed:
            rel_x, rel_y = self._get_relative_pos(x, y)
            elapsed = time.time() - self.start_time
            
            self.actions.append({
                'type': 'click',
                'rel_pos': (rel_x, rel_y),
                'button': str(button),
                'modifiers': self.current_modifiers.copy(), # 紀錄當下 Ctrl/Shift 是否被按住
                'time': elapsed
            })
            print(f"錄製點擊: {rel_x:.3f}, {rel_y:.3f} | Modifiers: {self.current_modifiers}")

    def on_press(self, key):
        elapsed = time.time() - self.start_time
        k = self._parse_key(key)

        if k in ['Key.ctrl_l', 'Key.ctrl_r', 'ctrl']:
            self.current_modifiers['ctrl'] = True
        elif k in ['Key.shift_l', 'Key.shift_r', 'shift']:
            self.current_modifiers['shift'] = True
        elif k in ['Key.alt_l', 'Key.alt_r', 'alt']:
            self.current_modifiers['alt'] = True

        if not any(a.get('key') == k and a.get('type') == 'keydown' and (elapsed - a['time'] < 0.1) for a in self.actions[-5:]):
            self.actions.append({
                'type': 'keydown',
                'key': k,
                'time': elapsed
            })

    def on_release(self, key):
        elapsed = time.time() - self.start_time
        k = self._parse_key(key)

        if k in ['Key.ctrl_l', 'Key.ctrl_r', 'ctrl']:
            self.current_modifiers['ctrl'] = False
        elif k in ['Key.shift_l', 'Key.shift_r', 'shift']:
            self.current_modifiers['shift'] = False
        elif k in ['Key.alt_l', 'Key.alt_r', 'alt']:
            self.current_modifiers['alt'] = False
        
        if k == 'p':
            return False

        self.actions.append({
            'type': 'keyup',
            'key': k,
            'time': elapsed
        })

    def _parse_key(self, key):
        try:
            return key.char # 普通字元
        except AttributeError:
            return str(key) # 特殊鍵

    def start(self):
        print(f"正在錄製 '{self.game_title}'... 按 ESC 停止")
        self.start_time = time.time()
        # 加上 on_release 監聽
        with mouse.Listener(on_click=self.on_click) as m_lsn, \
             keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as k_lsn:
            k_lsn.join()
        
        self.save_to_file()

    def save_to_file(self):
        with open(self.file_name, 'w') as f:
            json.dump(self.actions, f, indent=2) 
        print(f"腳本已儲存至 {self.file_name}")

if __name__ == "__main__":
    game_window_title = "Endfield"
    recorder = ActionRecorder(game_window_title, "preprocess.json")
    recorder.start()