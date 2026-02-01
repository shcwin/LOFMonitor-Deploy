# -*- coding: utf-8 -*-
"""
LOF基金溢价监控程序 - 钉钉通知模块
"""

from config import config
import requests
import json
import time
import hmac
import hashlib
import base64
import urllib.parse


def generate_sign(secret):
    """
    生成钉钉机器人签名
    
    Args:
        secret: 加签密钥
        
    Returns:
        tuple: (timestamp, sign)
    """
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode('utf-8')
    string_to_sign = f'{timestamp}\n{secret}'
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def send_dingtalk_alert(webhook_url, secret, message, title="LOF基金告警", fund_code=None):
    """
    发送钉钉告警消息
    
    Args:
        webhook_url: 钉钉机器人Webhook URL
        secret: 加签密钥（可选）
        message: 告警消息内容
        title: 消息标题
        fund_code: 基金代码（用于去重）
        
    Returns:
        bool: 是否发送成功
    """
    if not webhook_url:
        print("钉钉Webhook URL未配置，跳过发送")
        return False
    
    # 检查是否已告警（如果提供了fund_code）
    if fund_code and config.is_fund_alerted(fund_code):
        print(f"基金 {fund_code} 今日已发送过告警，跳过")
        return False
    
    try:
        # 构造请求URL
        if secret:
            timestamp, sign = generate_sign(secret)
            url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
        else:
            url = webhook_url
        
        # 构造Markdown消息
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": message
            }
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        
        result = response.json()
        if result.get('errcode') == 0:
            # print("钉钉消息发送成功")
            # 标记已告警
            if fund_code:
                config.mark_fund_alerted(fund_code)
            return True
        else:
            print(f"钉钉消息发送失败: {result}")
            return False
            
    except Exception as e:
        print(f"发送钉钉消息异常: {e}")
        return False


def format_alert_message(fund_code, fund_name, alert_type, rate, market_price, nav_price, fund_state=""):
    """
    格式化告警消息
    
    Args:
        fund_code: 基金代码
        fund_name: 基金名称
        alert_type: 告警类型
        rate: 比率
        market_price: 场内价格
        nav_price: 场外净值
        
    Returns:
        str: 格式化的Markdown消息
    """
    if alert_type == 'premium':
        alert_title = "🔴 溢价告警"
        rate_text = f"溢价率: **{rate:.2f}%**"
    else:
        alert_title = "🟢 折价告警"
        rate_text = f"折价率: **{rate:.2f}%**"
    
    message = f"""## {alert_title}

**基金名称:** {fund_name}

**基金代码:** {fund_code}

**基金状态:** {fund_state}

**场内价格:** {market_price:.4f}

**场外净值:** {nav_price:.4f}

**{rate_text}**

---
*LOF基金溢价监控系统*
"""
    return message
