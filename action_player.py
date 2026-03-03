import json
import time
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from input_manager import InputManager
from discord_sender import DiscordSender

logger = logging.getLogger(__name__)

class ActionPlayer:
    def __init__(self, game_title=None):
        try:
            load_dotenv(override=True)
            if game_title is not None:
                self.game_title = game_title
            else:
                self.game_title = os.getenv("game_title")
            self.actions = []
            self.repeat = int(os.getenv("repeat", "5"))
            
            self.manager = InputManager(self.game_title)
            self.sender = DiscordSender()
            
            logger.info("ActionPlayer 初始化成功")
        except Exception as e:
            logger.error(f"ActionPlayer 初始化失敗: {e}")
        
    def load_script(self, filename):
        try:
            path = Path.cwd() / "scripts" / filename
            logger.info(f"正在載入腳本: {filename}")
            
            with open(path, 'r') as f:
                self.actions = json.load(f)
            logger.info(f"腳本 {filename} 載入成功，總共 {len(self.actions)} 個動作")
        except Exception as e:
            err_msg = f"載入腳本 {filename} 失敗: {e}"
            logger.error(f"[X] {err_msg}")
            self.sender.send_status(err_msg, remind_user=True)
            raise FileNotFoundError(err_msg)

    def play(self):
        try:
            self.load_script("login.json")
            self.execute_action()
            logger.info("等待登入動畫完成...")
            
            logger.info("[*] 登入完成，準備進入遊戲")
            while self.manager.try_moving_test():
                logger.info("檢測到選單/彈窗，嘗試關閉...")
                self.manager.send_keys('esc')
                time.sleep(1)
            
            self.load_script("send_ship.json")
            self.execute_action()
            logger.info("傳送腳本執行完成")
            
            self.load_script("preprocess.json")
            self.execute_action()
            logger.info("預處裡腳本執行完成")
            
            logger.info(f"開始執行主腳本，預計重複 {self.repeat} 次")
            self.load_script("transfer.json")
            for i in range(self.repeat):
                logger.info(f">>> 正在執行第 {i+1} / {self.repeat} 次循環")
                self.execute_action()
            
            logger.info("主腳本執行完成，開始執行回報")
            for script in ["send_home.json", "show_resource.json"]:
                self.load_script(script)
                self.execute_action()
            
            self.execution_report()
            
        except Exception as e:
            logger.error(f"執行過程中發生錯誤: {e}")
            self.sender.send_status(f"執行過程中發生錯誤: {e}", remind_user=True)

    def execute_action(self):
        if not self.actions:
            msg = "腳本為空，無法執行"
            logger.warning(msg)
            self.sender.send_status(msg, remind_user=True)
            return
        
        actions = sorted(self.actions, key=lambda a: a.get("time", 0))
        start_time = time.perf_counter()
        for action in actions:
            target_time = action.get("time", 0)
            
            if not isinstance(target_time, (int, float)):
                continue
            elapsed = time.perf_counter() - start_time
            wait_time = target_time - elapsed
            if wait_time > 0:
                time.sleep(wait_time)
            try:
                self.manager.execute_action(action)
            except Exception as e:
                logger.warning(f"[X] 執行特定動作失敗: {action} | 錯誤: {e}")

    def execution_report(self):
        logger.info("[*] 資源截圖中")
        time.sleep(5)
        img = self.manager.snapshot()
        
        if img:
            self.sender.send_status("Endfield 資源狀況", img_bytes=img)
        else:
            err_msg = "無法截取遊戲畫面，請檢查遊戲視窗狀態"
            self.sender.send_status(err_msg, remind_user=True)
            logger.error(f"[X] {err_msg}")
            
        

if __name__ == "__main__":
    game_title = "未命名 - 小畫家"
    load_dotenv(override=True)
    player = ActionPlayer(game_title)
    player.load_script("preprocess.json")
    player.execute_action()