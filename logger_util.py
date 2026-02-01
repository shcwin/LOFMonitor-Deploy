# -*- coding: utf-8 -*-
"""
LOF基金溢价监控程序 - 日志模块
"""

import os
from datetime import datetime
from config import ALERTS_LOG_FILE


def log_alert(fund_code, fund_name, alert_type, rate, threshold):
    """
    记录告警日志
    
    Args:
        fund_code: 基金代码
        fund_name: 基金名称
        alert_type: 告警类型 ('premium' 或 'discount')
        rate: 当前比率
        threshold: 阈值
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if alert_type == 'premium':
        message = f"[溢价告警] {fund_name}({fund_code}) 溢价率: {rate:.2f}% (阈值: {threshold}%)"
    else:
        message = f"[折价告警] {fund_name}({fund_code}) 折价率: {rate:.2f}% (阈值: {threshold}%)"
    
    log_line = f"[{timestamp}] {message}\n"
    
    try:
        with open(ALERTS_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_line)
        # print(f"告警已记录: {message}")
    except Exception as e:
        print(f"写入日志失败: {e}")


def get_recent_alerts(limit=100):
    """
    获取最近的告警记录
    
    Args:
        limit: 返回的最大记录数
        
    Returns:
        list: 告警记录列表
    """
    if not os.path.exists(ALERTS_LOG_FILE):
        return []
    
    try:
        with open(ALERTS_LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return lines[-limit:][::-1]  # 返回最新的记录，倒序排列
    except Exception as e:
        print(f"读取日志失败: {e}")
        return []
