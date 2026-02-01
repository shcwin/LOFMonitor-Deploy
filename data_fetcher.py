# -*- coding: utf-8 -*-
"""
LOF基金溢价监控程序 - 数据获取模块
"""

import os
import pandas as pd
import akshare as ak
import requests
from bs4 import BeautifulSoup
from config import LOF_FUNDS_FILE


def get_lof_fund_list_with_price():
    """
    获取LOF基金列表及最新场内价格（实时数据）
    
    通过 fund_etf_category_sina 接口同时获取基金列表和最新价格
    
    Returns:
        DataFrame: 包含 market, code, name, market_price 字段的DataFrame
    """
    # print("从akshare获取LOF基金列表及最新价格...")
    try:
        raw_df = ak.fund_etf_category_sina(symbol="LOF基金")
        
        # 处理数据 - 剥离代码前缀，同时保存最新价格
        result = []
        for _, row in raw_df.iterrows():
            code_with_prefix = row['代码']
            # 剥离 sz 或 sh 前缀
            if code_with_prefix.startswith('sz'):
                market = 'sz'
                code = code_with_prefix[2:]
            elif code_with_prefix.startswith('sh'):
                market = 'sh'
                code = code_with_prefix[2:]
            else:
                market = ''
                code = code_with_prefix
            
            # 获取最新价格
            try:
                market_price = float(row['最新价']) if pd.notna(row['最新价']) else None
            except (ValueError, TypeError):
                market_price = None
            
            result.append({
                'market': market,
                'code': code,
                'name': row['名称'],
                'market_price': market_price
            })
        
        df = pd.DataFrame(result)
        
        # 保存基金列表到本地文件
        #save_df = df[['market', 'code', 'name']].copy()
        #save_df.to_csv(LOF_FUNDS_FILE, index=False, encoding='utf-8-sig')
        # print(f"LOF基金列表已保存到 {LOF_FUNDS_FILE}，共 {len(df)} 只基金")
        
        return df
        
    except Exception as e:
        print(f"获取LOF基金列表失败: {e}")
        return pd.DataFrame(columns=['market', 'code', 'name', 'market_price'])



def get_nav_price(code):
    """
    获取单个LOF基金的场外净值及日期
    
    Args:
        code: 基金代码
        
    Returns:
        tuple: (nav_price, nav_date)
            nav_price (float): 最新净值
            nav_date (str): 净值日期 (YYYY-MM-DD)
            失败返回 (None, None)
    """
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        
        if df is not None and not df.empty:
            # 使用iloc按位置获取，避免编码问题导致的列名匹配失败
            # 通常列顺序为: 净值日期, 单位净值, 日增长率...
            nav_date = df.iloc[-1, 0]
            nav_val = df.iloc[-1, 1]
            
            # 格式化日期
            if hasattr(nav_date, 'strftime'):
                nav_date_str = nav_date.strftime('%Y-%m-%d')
            else:
                nav_date_str = str(nav_date)
                
            return float(nav_val), nav_date_str
            
        return None, None
        
    except Exception as e:
        # 静默处理错误，避免日志刷屏
        return None, None


def get_all_fund_data(progress_callback=None, data_callback=None):
    """
    获取所有LOF基金的完整数据（场内价格和场外净值）
    
    Args:
        progress_callback: 可选的进度回调函数 (current, total, name) -> None
        data_callback: 可选的数据回调函数 (fund_data) -> None
    
    Returns:
        list: 包含所有基金数据的列表
    """
    # 批量获取基金列表和场内价格
    fund_df = get_lof_fund_list_with_price()
    
    if fund_df.empty:
        return []
    
    result = []
    total = len(fund_df)
    
    # 获取当前时间作为场内价格时间（因为是实时接口）
    import datetime
    market_time = datetime.datetime.now().strftime('%H:%M:%S')
    
    for idx, row in fund_df.iterrows():
        code = row['code']
        name = row['name']
        market_price = row['market_price']
        
        # 回调进度
        if progress_callback:
            progress_callback(idx + 1, total, name)
        
        # 获取场外净值
        nav_price, nav_date = get_nav_price(code)
        
        # 获取基金状态
        fund_state = parse_fund_state(code)
        
        fund_data = {
            'code': code,
            'name': name,
            'market': row['market'],
            'market_price': market_price,
            'market_time': market_time,  # 新增: 场内价格时间
            'nav_price': nav_price,
            'nav_date': nav_date,         # 新增: 净值日期
            'fund_state': fund_state      # 新增: 基金状态
        }
        
        # 实时回调每个基金数据
        if data_callback:
            data_callback(fund_data)
        
        result.append(fund_data)
    
    return result


def parse_fund_state(code):
    url = "https://fund.eastmoney.com/" + code +".html"
    ret = ""
    
    try:
        response = requests.get(url, timeout=10)
        response.encoding = response.apparent_encoding 
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            target_div = None
            items = soup.find_all("div", class_="staticItem")
            for item in items:
                if "交易状态" in item.text:
                    target_div = item
                    break 
            if target_div:
                raw_text = target_div.get_text(strip=True)
                clean_text = raw_text.replace('\xa0', ' ')
                
                ret = clean_text.replace("交易状态：", "")
    except Exception as e:
        pass
    
    return ret