# -*- coding: utf-8 -*-
"""
LOF基金溢价监控程序 - 配置模块
"""

import os
import json
from datetime import datetime

# 文件路径
LOF_FUNDS_FILE = "lof_funds.csv"
ALERTS_LOG_FILE = "alerts.log"
CONFIG_FILE = "config.json"

# UI配置常量
WINDOW_TITLE = "LOF基金溢价监控系统"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

# 颜色配置
COLOR_PREMIUM = "#00C853"   # 溢价颜色 - 绿色
COLOR_DISCOUNT = "#FF5252"  # 折价颜色 - 红色
COLOR_NORMAL = "#FFFFFF"    # 正常颜色 - 白色
COLOR_BG_DARK = "#1E1E2E"   # 深色背景
COLOR_BG_CARD = "#2D2D3F"   # 卡片背景
COLOR_ACCENT = "#7C3AED"    # 主题色 - 紫色

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance
    
    def load_config(self):
        """加载配置"""
        self.default_config = {
            "premium_threshold": 30.0,
            "discount_threshold": 40.0,
            "dingtalk_webhook": "",
            "dingtalk_secret": "",
            "last_alert_date": "",
            "alerted_funds": [],  # 当日已告警的基金代码列表
            "mode": "ui"  # "ui" or "terminal"
        }
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # 合并配置，确保新字段存在
                    self.config = self.default_config.copy()
                    self.config.update(saved_config)
            except Exception as e:
                print(f"读取配置文件失败: {e}，使用默认配置")
                self.config = self.default_config.copy()
        else:
            self.config = self.default_config.copy()
            self.save_config()
        
        # 从环境变量覆盖配置 (用于GitHub Actions)
        env_mapping = {
            "DINGTALK_WEBHOOK": "dingtalk_webhook",
            "DINGTALK_SECRET": "dingtalk_secret",
            "PREMIUM_THRESHOLD": "premium_threshold",
            "DISCOUNT_THRESHOLD": "discount_threshold"
        }
        for env_key, config_key in env_mapping.items():
            env_val = os.environ.get(env_key)
            if env_val:
                try:
                    if config_key.endswith("_threshold"):
                        self.config[config_key] = float(env_val)
                    else:
                        self.config[config_key] = env_val
                except ValueError:
                    print(f"环境变量 {env_key} 格式错误: {env_val}")
            
    def save_config(self):
        """保存配置"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            
    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """设置配置项并保存"""
        self.config[key] = value
        self.save_config()
        
    def check_reset_daily_alerts(self):
        """检查并重置每日告警记录"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.config.get("last_alert_date") != today:
            self.config["last_alert_date"] = today
            self.config["alerted_funds"] = []
            self.save_config()
            return True
        return False
    
    def is_fund_alerted(self, code):
        """检查基金今日是否已告警"""
        self.check_reset_daily_alerts()
        return code in self.config.get("alerted_funds", [])
        
    def mark_fund_alerted(self, code):
        """标记基金今日已告警"""
        self.check_reset_daily_alerts()
        alerted_funds = self.config.get("alerted_funds", [])
        if code not in alerted_funds:
            alerted_funds.append(code)
            self.config["alerted_funds"] = alerted_funds
            self.save_config()

# 全局单例
config = ConfigManager()
