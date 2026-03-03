import time
import os
import psutil
import ctypes
import win32gui
import schedule
import subprocess
import logging
import sys

from action_player import ActionPlayer
from discord_sender import DiscordSender
from dotenv import load_dotenv
from logger import init_logger

logger = logging.getLogger(__name__)

def env_generator():
    if os.path.isfile('.env'):
        return
    os.rename("env.copy", ".env")

class GameScheduler:
    def __init__(self):
        try:
            init_logger()
            load_dotenv(override=True)
            self.current_interval = int(os.getenv("time_interval"))
            self.current_job = schedule.every(self.current_interval).minutes.do(self.start_automation_flow)
            self.game_path = os.getenv("game_path")
            self.game_exe_name = os.path.basename(self.game_path)
            self.game_title = os.getenv("game_title")
            
            logger.info(f"[*] Scheduler initialized for {self.game_title} at path: {self.game_path}")
            self.sender = DiscordSender()
        except Exception as e:
            logger.error(f"Scheduler initialization failed: {e}")
            raise
            
    def is_game_open(self):
        procs = [proc.info['name'] for proc in psutil.process_iter(['name'])]
        return any(self.game_title in proc for proc in procs)

    def check_game_status(self):
        hwnd = win32gui.FindWindow(None, self.game_title)
        return not hwnd or ctypes.windll.user32.IsHungAppWindow(hwnd)
        
    def launch_game(self):
        try:
            if self.is_game_open():
                self.stop_game()
                time.sleep(10)
            logger.info(f"[*] 正在啟動 {self.game_title}...")
            subprocess.Popen(
                [self.game_path], 
                creationflags=subprocess.HIGH_PRIORITY_CLASS
            )
            time.sleep(60)
            try_count = 0
            while self.check_game_status() and try_count < 5:
                logger.info("[*] 等待遊戲啟動中...")
                time.sleep(30)
                try_count += 1
            if try_count >= 5:
                self.stop_game()
                self.diagnostic_report()
                logger.warning("[*] 遊戲啟動失敗，已嘗試多次，請檢查遊戲狀態。")
                self.sender.send_status(f"遊戲啟動失敗，已嘗試多次，請檢查遊戲狀態。", remind_user=True)
                sys.exit(0)
        except Exception as e:
            self.sender.send_status(f"遊戲啟動遇到問題: {e}", remind_user=True)
    
    def stop_game(self):
        try:
            for proc in psutil.process_iter(['name']):
                if self.game_title in proc.info['name']:
                    proc.kill()
                    logger.info(f"{self.game_title} has been terminated.")
        except Exception as e:
            self.sender.send_status(f"遊戲關閉遇到問題: {e}", remind_user=True)

    def start_automation_flow(self):
        load_dotenv(override=True)
        self.launch_game()
        player = ActionPlayer()
        player.play()
        self.stop_game()
        
    def load_config(self):
        load_dotenv(override=True)
        new_interval = int(os.getenv("time_interval"))

        if new_interval != self.current_interval:
            logger.info(f"[*] 偵測到配置變更：{self.current_interval} -> {new_interval} 分鐘")
            self.reschedule(new_interval)

    def reschedule(self, new_interval):
        if self.current_job:
            schedule.cancel_job(self.current_job)
            logger.info(f"[-] 已取消舊的排程任務 : {self.current_interval} 分")

        self.current_interval = new_interval
        self.current_job = schedule.every(new_interval).minutes.do(self.start_automation_flow)
        logger.info(f"[+] 新排程已生效：每 {new_interval} 分鐘執行一次")

    def diagnostic_report(self):
        cpu_usage = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        disk_usage = psutil.disk_io_counters()
        
        logger.error(f"--- 啟動失敗診斷報告 ---")
        logger.error(f"CPU 使用率: {cpu_usage}%")
        logger.error(f"記憶體剩餘: {memory_info.available / (1024**3):.2f} GB")
        logger.error(f"磁碟狀態: {disk_usage}")

def keep_awake():
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000002 | 0x00000001)
    
if __name__ == "__main__":
    scheduler = GameScheduler()
    keep_awake()
    env_generator()
    
    while True:
        scheduler.load_config()
        schedule.run_pending()
        time.sleep(10)