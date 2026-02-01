# -*- coding: utf-8 -*-
"""
LOF基金溢价监控程序 - 计算模块
"""


def calculate_premium_discount(market_price, nav_price):
    """
    计算溢价率和折价率
    
    Args:
        market_price: 场内价格 (X)
        nav_price: 场外净值 (Y)
        
    Returns:
        tuple: (溢价率, 折价率) 百分比形式
               溢价率 Z1 = (X - Y) / Y * 100%
               折价率 Z2 = (Y - X) / Y * 100%
    """
    if market_price is None or nav_price is None:
        return None, None
    
    if nav_price == 0 or market_price == 0:
        return None, None
    
    # 溢价率: 场内价格高于场外净值的比例
    premium_rate = (market_price - nav_price) / nav_price * 100
    
    # 折价率: 场外净值高于场内价格的比例
    discount_rate = (nav_price - market_price) / nav_price * 100
    
    # 互斥显示逻辑：如果溢价率>0，则显示溢价率，折价率为None（N/A）
    # 反之如果折价率>0，则显示折价率，溢价率为None
    if premium_rate > 0:
        return round(premium_rate, 2), None
    elif discount_rate > 0:
        return None, round(discount_rate, 2)
    else:
        # 两者都未超过0（极其罕见的情况），保留原值或都为0
        return 0, 0


def get_status(premium_rate, discount_rate, premium_threshold, discount_threshold):
    """
    判断基金状态
    
    Args:
        premium_rate: 溢价率
        discount_rate: 折价率
        premium_threshold: 溢价阈值
        discount_threshold: 折价阈值
        
    Returns:
        str: 'premium_alert' | 'discount_alert' | 'premium' | 'discount' | 'normal'
    """
    if premium_rate is None:
        premium_rate = 0
    if discount_rate is None:
        discount_rate = 0
    
    if premium_rate >= premium_threshold:
        return 'premium_alert'  # 溢价超过阈值，需要告警
    elif discount_rate >= discount_threshold:
        return 'discount_alert'  # 折价超过阈值，需要告警
    elif premium_rate > 0:
        return 'premium'  # 正常溢价
    elif discount_rate > 0:
        return 'discount'  # 正常折价
    else:
        return 'normal'
