import requests
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class DiscordSender:
    def __init__(self):
        load_dotenv(override=True)
        self.webhook_url = os.getenv("discord_webhook_url")
        self.user_tag = os.getenv("user_tag")

    def send_status(self, content, remind_user=False, img_bytes=None):
        
        if remind_user and self.user_tag:
            payload = {"content": f"{self.user_tag} \n {content}"}
        else:
            payload = {"content": content}
            
        files = {}
        if img_bytes:
            # Discord 的 Webhook 接收檔案時，欄位名稱通常設為 'file'
            files = {
                "file": ("screenshot.png", img_bytes, "image/png")
            }
        try:
            response = requests.post(self.webhook_url, data=payload, files=files)
            if response.status_code == 200 or response.status_code == 204:
                logger.info(f"Discord 發送成功: {content}")
            else:
                logger.warning(f"Discord 發送失敗，狀態碼: {response.status_code}, 內容: {response.text}")
        except Exception as e:
            logger.error(f"發送 Discord 時發生網路錯誤: {e}")
            
if __name__ == "__main__":
    sender = DiscordSender()
    sender.send_status("這是一則測試訊息", remind_user=False)
    