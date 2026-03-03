import logging
import os
from logging.handlers import TimedRotatingFileHandler

def init_logger():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "app.log")
    
    # 移除手動設定 suffix，改用預設或確認匹配
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when='D',      # 按天切換
        interval=1,
        backupCount=7,
        encoding='utf-8',
        atTime=None    # 可以設定在午夜切換，例如 datetime.time(0, 0, 0)
    )

    # 預設格式其實就是 .%Y-%m-%d，手動改 suffix 若沒對應 extMatch 會導致 backupCount 失效
    # 如果一定要改，建議連同 extMatch 一起改（較複雜），否則用預設即可

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s')
    file_handler.setFormatter(formatter)

    # 強制獲取根日誌並清除舊的 Handler，防止 basicConfig 失效
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 清除現有的 handlers (防止重複印出或設定失敗)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(file_handler)
    root_logger.addHandler(logging.StreamHandler())

    logging.info("Logger 系統初始化完成，當前寫入檔案: app.log")