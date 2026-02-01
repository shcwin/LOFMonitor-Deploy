# -*- coding: utf-8 -*-
"""
LOF基金溢价监控程序 - UI界面模块
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime

from config import (
    config,  # 引入ConfigManager实例
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_PREMIUM, COLOR_DISCOUNT, COLOR_BG_DARK, COLOR_BG_CARD, COLOR_ACCENT
)
from data_fetcher import get_all_fund_data
from calculator import calculate_premium_discount, get_status
from notifier import send_dingtalk_alert, format_alert_message
from logger_util import log_alert


class LOFMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=COLOR_BG_DARK)
        
        # 配置变量 - 从config读取
        self.premium_threshold = tk.DoubleVar(value=config.get("premium_threshold"))
        self.discount_threshold = tk.DoubleVar(value=config.get("discount_threshold"))
        self.webhook_url = tk.StringVar(value=config.get("dingtalk_webhook"))
        self.webhook_secret = tk.StringVar(value=config.get("dingtalk_secret"))
        
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="all")
        
        # 数据存储
        self.fund_data = []
        self.is_loading = False
        self.sort_column = None  # 当前排序列
        self.sort_reverse = False  # 是否降序
        
        # 监听配置变更并保存
        self.premium_threshold.trace("w", self.save_thresholds)
        self.discount_threshold.trace("w", self.save_thresholds)
        
        # 配置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 绑定搜索事件
        self.search_var.trace('w', self.refresh_table_view)
        self.filter_var.trace('w', self.refresh_table_view)
    
    def save_thresholds(self, *args):
        """保存阈值配置到文件"""
        try:
            config.set("premium_threshold", self.premium_threshold.get())
            config.set("discount_threshold", self.discount_threshold.get())
            self.recalculate_status() # 阈值变化后重新计算状态并刷新表格
        except tk.TclError:
            pass  # 输入非法时忽略
            
    def save_webhook_config(self):
        """保存Webhook配置"""
        config.set("dingtalk_webhook", self.webhook_url.get())
        config.set("dingtalk_secret", self.webhook_secret.get())
    
    def on_threshold_change(self, *args):
        """阈值变化回调"""
        # 此方法已不再直接绑定到trace，而是通过save_thresholds调用recalculate_status
        pass
        
    def recalculate_status(self):
        """重新计算所有基金的状态"""
        if not self.fund_data:
            return
            
        try:
            p_threshold = self.premium_threshold.get()
            d_threshold = self.discount_threshold.get()
        except tk.TclError:
            return  # 输入框可能为空或非法字符
            
        for fund in self.fund_data:
            premium_rate = fund['premium_rate']
            discount_rate = fund['discount_rate']
            
            # 重新判断状态
            status = get_status(premium_rate, discount_rate, p_threshold, d_threshold)
            fund['status'] = status
            
        # 刷新表格显示
        self.refresh_table()
        # 更新统计信息
        self.update_completion_status()
    
    def setup_styles(self):
        """配置自定义样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置Treeview样式
        style.configure("Custom.Treeview",
                       background=COLOR_BG_CARD,
                       foreground="white",
                       fieldbackground=COLOR_BG_CARD,
                       rowheight=30,
                       font=('Microsoft YaHei UI', 10))
        
        style.configure("Custom.Treeview.Heading",
                       background=COLOR_ACCENT,
                       foreground="white",
                       font=('Microsoft YaHei UI', 10, 'bold'))
        
        style.map("Custom.Treeview",
                 background=[('selected', COLOR_ACCENT)])
        
        # 配置按钮样式
        style.configure("Accent.TButton",
                       background=COLOR_ACCENT,
                       foreground="white",
                       font=('Microsoft YaHei UI', 10),
                       padding=(15, 8))
        
        style.map("Accent.TButton",
                 background=[('active', '#9B59B6')])
        
        # 配置Entry样式
        style.configure("Custom.TEntry",
                       fieldbackground=COLOR_BG_CARD,
                       foreground="white",
                       insertcolor="white")
        
        # 配置Label样式
        style.configure("Title.TLabel",
                       background=COLOR_BG_DARK,
                       foreground="white",
                       font=('Microsoft YaHei UI', 24, 'bold'))
        
        style.configure("Subtitle.TLabel",
                       background=COLOR_BG_DARK,
                       foreground="#888888",
                       font=('Microsoft YaHei UI', 10))
        
        style.configure("Card.TFrame",
                       background=COLOR_BG_CARD)
        
        style.configure("Dark.TFrame",
                       background=COLOR_BG_DARK)
        
        style.configure("White.TLabel",
                       background=COLOR_BG_CARD,
                       foreground="white",
                       font=('Microsoft YaHei UI', 10))
        
    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, style="Dark.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题区域
        self.create_header(main_frame)
        
        # 配置和筛选区域
        self.create_config_panel(main_frame)
        
        # 数据表格区域
        self.create_table(main_frame)
        
        # 状态栏
        self.create_status_bar(main_frame)
    
    def create_header(self, parent):
        """创建标题区域"""
        header_frame = ttk.Frame(parent, style="Dark.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="📊 LOF基金溢价监控", style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(header_frame, 
                                   text="实时监控 • 极简模式 (仅显示关注数据)", 
                                   style="Subtitle.TLabel")
        subtitle_label.pack(side=tk.LEFT, padx=(20, 0), pady=(10, 0))
    
    def create_config_panel(self, parent):
        """创建配置和筛选面板"""
        config_frame = ttk.Frame(parent, style="Card.TFrame")
        config_frame.pack(fill=tk.X, pady=(0, 20))
        
        inner_frame = ttk.Frame(config_frame, style="Card.TFrame")
        inner_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # 左侧 - 阈值配置
        left_frame = ttk.Frame(inner_frame, style="Card.TFrame")
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 溢价阈值
        premium_label = ttk.Label(left_frame, text="溢价阈值 (%):", style="White.TLabel")
        premium_label.pack(side=tk.LEFT, padx=(0, 5))
        
        premium_entry = ttk.Entry(left_frame, textvariable=self.premium_threshold, 
                                  width=8, style="Custom.TEntry")
        premium_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # 折价阈值
        discount_label = ttk.Label(left_frame, text="折价阈值 (%):", style="White.TLabel")
        discount_label.pack(side=tk.LEFT, padx=(0, 5))
        
        discount_entry = ttk.Entry(left_frame, textvariable=self.discount_threshold,
                                   width=8, style="Custom.TEntry")
        discount_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # 搜索框
        search_label = ttk.Label(left_frame, text="🔍 搜索:", style="White.TLabel")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = ttk.Entry(left_frame, textvariable=self.search_var,
                                 width=20, style="Custom.TEntry")
        search_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # 筛选下拉框
        filter_label = ttk.Label(left_frame, text="筛选:", style="White.TLabel")
        filter_label.pack(side=tk.LEFT, padx=(0, 5))
        
        filter_combo = ttk.Combobox(left_frame, textvariable=self.filter_var, 
                                    values=["all", "溢价告警", "折价告警", "溢价", "折价"],
                                    width=10, state="readonly")
        filter_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # 右侧 - 操作按钮
        right_frame = ttk.Frame(inner_frame, style="Card.TFrame")
        right_frame.pack(side=tk.RIGHT)
        
        refresh_btn = ttk.Button(right_frame, text="🔄 刷新数据", 
                                 command=self.refresh_data, style="Accent.TButton")
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        config_btn = ttk.Button(right_frame, text="⚙️ 钉钉配置",
                               command=self.show_dingtalk_config, style="Accent.TButton")
        config_btn.pack(side=tk.LEFT)
    
    def create_table(self, parent):
        """创建数据表格"""
        table_frame = ttk.Frame(parent, style="Card.TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建表格
        columns = ("code", "name", "market_price", "nav_price",
                   "premium_rate", "discount_rate", "status", "fund_state")
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                  style="Custom.Treeview", yscrollcommand=scrollbar.set)
        
        # 配置列（添加点击排序）
        columns_config = [
            ("code", "基金代码", 80),
            ("name", "基金名称", 200),
            ("market_price", "场内价格", 80),
            ("nav_price", "场外净值", 80),
            ("premium_rate", "溢价率 (%)", 90),
            ("discount_rate", "折价率 (%)", 90),
            ("status", "状态", 100),
            ("fund_state", "基金状态", 150)
        ]
        
        for col_id, col_text, col_width in columns_config:
            self.tree.heading(col_id, text=col_text, 
                             command=lambda c=col_id: self.sort_by_column(c))
            anchor = tk.W if col_id == "name" else tk.CENTER
            self.tree.column(col_id, width=col_width, anchor=anchor)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.config(command=self.tree.yview)
        
        
        # 配置行标签颜色
        # 溢价告警 -> 绿色
        self.tree.tag_configure('premium_alert', foreground=COLOR_PREMIUM, 
                                font=('Microsoft YaHei UI', 10, 'bold'))
        # 折价告警 -> 红色
        self.tree.tag_configure('discount_alert', foreground=COLOR_DISCOUNT,
                                font=('Microsoft YaHei UI', 10, 'bold'))
        
        # 正常状态（未超过阈值的溢价或折价） -> 白色
        self.tree.tag_configure('premium', foreground='white')
        self.tree.tag_configure('discount', foreground='white')
        self.tree.tag_configure('normal', foreground='white')
        self.tree.tag_configure('unknown', foreground='#888888')
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent, style="Dark.TFrame")
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, 
                                      text="就绪 - 点击'刷新数据'开始监控",
                                      style="Subtitle.TLabel")
        self.status_label.pack(side=tk.LEFT)
        
        self.count_label = ttk.Label(status_frame, text="", style="Subtitle.TLabel")
        self.count_label.pack(side=tk.RIGHT)
    
    def show_dingtalk_config(self):
        """显示钉钉配置对话框"""
        config_window = tk.Toplevel(self.root)
        config_window.title("钉钉配置")
        config_window.geometry("500x200")
        config_window.configure(bg=COLOR_BG_DARK)
        config_window.transient(self.root)
        config_window.grab_set()
        
        frame = ttk.Frame(config_window, style="Card.TFrame")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Webhook URL
        webhook_label = ttk.Label(frame, text="Webhook URL:", style="White.TLabel")
        webhook_label.grid(row=0, column=0, pady=10, sticky=tk.W)
        
        webhook_entry = ttk.Entry(frame, textvariable=self.webhook_url, width=50)
        webhook_entry.grid(row=0, column=1, pady=10, padx=(10, 0))
        
        # Secret
        secret_label = ttk.Label(frame, text="加签密钥:", style="White.TLabel")
        secret_label.grid(row=1, column=0, pady=10, sticky=tk.W)
        
        secret_entry = ttk.Entry(frame, textvariable=self.webhook_secret, width=50, show="*")
        secret_entry.grid(row=1, column=1, pady=10, padx=(10, 0))
        
        # 保存按钮
        def save_and_close():
            self.save_webhook_config()
            config_window.destroy()
            
        save_btn = ttk.Button(frame, text="保存", style="Accent.TButton",
                             command=save_and_close)
        save_btn.grid(row=2, column=1, pady=20, sticky=tk.E)
    
    def refresh_data(self):
        """刷新数据（异步）"""
        if self.is_loading:
            return
        
        self.is_loading = True
        self.status_label.config(text="正在加载数据...")
        
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 启动后台线程加载数据
        thread = threading.Thread(target=self.load_data_async)
        thread.daemon = True
        thread.start()
    
    
    def load_data_async(self):
        """异步加载数据"""
        try:
            self.fund_data = [] # Reset data list
            
            # 定义进度回调
            def progress_callback(current, total, name):
                self.root.after(0, lambda c=current, t=total, n=name: 
                               self.status_label.config(text=f"正在获取场外净值 {n} ({c}/{t})..."))
            
            # 定义数据回调（实时处理单个基金数据）
            def on_fund_data_received(fund):
                code = fund['code']
                name = fund['name']
                market_price = fund['market_price']
                nav_price = fund['nav_price']
                
                # 计算溢价/折价率
                premium_rate, discount_rate = calculate_premium_discount(market_price, nav_price)
                
                # 判断状态
                status = get_status(premium_rate, discount_rate,
                                   self.premium_threshold.get(),
                                   self.discount_threshold.get())
                
                # 构造包含状态的完整信息
                fund_info = {
                    'code': code,
                    'name': name,
                    'market_price': market_price,
                    # 'market_time': fund.get('market_time', ''), # 移除
                    'nav_price': nav_price,
                    # 'nav_date': fund.get('nav_date', ''), # 移除
                    'premium_rate': premium_rate,
                    'discount_rate': discount_rate,
                    'status': status,
                    'fund_state': fund.get('fund_state', '')
                }
                
                # 添加到内部列表（注意线程安全，虽然append是原子的，但这里在回调中）
                self.fund_data.append(fund_info)
                
                # 在主线程更新UI
                self.root.after(0, lambda f=fund_info: self.add_single_row_and_alert(f))

            
            self.root.after(0, lambda: self.status_label.config(text="正在获取LOF基金数据..."))
            
            # 调用数据获取函数，传入data_callback
            get_all_fund_data(progress_callback=progress_callback, data_callback=on_fund_data_received)
            
            # 完成后更新状态栏（表格行已经在回调中添加了）
            self.root.after(0, self.update_completion_status)
            
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"加载失败: {e}"))
        finally:
            self.is_loading = False
            
    def add_single_row_and_alert(self, fund_info):
        """添加单行数据并检查告警（主线程执行）"""
        # 如果当前有激活的排序，则重新排序并刷新整个表格
        if self.sort_column:
            # 添加到列表（已在load_data_async中添加，这里不需要再添）
            # 直接排序并刷新
            self.apply_sort_data()
            self.refresh_table()
        else:
            # 否则直接追加到表格末尾
            self.add_table_row(fund_info)
        
        # 检查是否需要告警
        status = fund_info['status']
        if status in ['premium_alert', 'discount_alert']:
            alert_type = 'premium' if status == 'premium_alert' else 'discount'
            rate = fund_info['premium_rate'] if alert_type == 'premium' else fund_info['discount_rate']
            
            # 每日去重逻辑
            if not config.is_fund_alerted(fund_info['code']):
                self.trigger_alert(fund_info, alert_type, rate)
                config.mark_fund_alerted(fund_info['code'])
            
    def refresh_table_view(self, *args):
        """仅刷新表格视图（搜索/筛选触发）"""
        self.refresh_table()
    
    def refresh_table(self):
        """刷新表格显示"""
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        search_text = self.search_var.get().lower()
        filter_type = self.filter_var.get()
        
        # 添加符合条件的行
        for fund in self.fund_data:
            # 搜索筛选
            if search_text:
                if (search_text not in fund['code'].lower() and 
                    search_text not in fund['name'].lower()):
                    continue
            
            # 状态筛选
            if filter_type != "all":
                status_filter_map = {
                    "溢价告警": "premium_alert",
                    "折价告警": "discount_alert",
                    "溢价": "premium",
                    "折价": "discount"
                }
                if fund['status'] != status_filter_map.get(filter_type):
                    continue
                
            self.add_table_row(fund)
    
    def apply_sort_data(self):
        """应用当前排序规则到数据"""
        if not self.fund_data or not self.sort_column:
            return

        # 定义排序键
        def sort_key(fund):
            value = fund.get(self.sort_column)
            if value is None:
                return float('-inf') if self.sort_reverse else float('inf')
            if isinstance(value, str):
                return value.lower()
            return value
        
        # 排序数据
        self.fund_data.sort(key=sort_key, reverse=self.sort_reverse)
        
        # 更新列标题显示排序方向
        direction = "▼" if self.sort_reverse else "▲"
        columns_text = {
            "code": "基金代码",
            "name": "基金名称",
            "market_price": "场内价格",
            "nav_price": "场外净值",
            "premium_rate": "溢价率 (%)",
            "discount_rate": "折价率 (%)",
            "status": "状态",
            "fund_state": "基金状态"
        }
        
        for col, text in columns_text.items():
            if col == self.sort_column:
                self.tree.heading(col, text=f"{text} {direction}")
            else:
                self.tree.heading(col, text=text)

    def sort_by_column(self, column):
        """按列排序"""
        if not self.fund_data:
            return
        
        # 如果点击同一列，切换排序方向
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = True  # 默认降序
        
        # 应用排序
        self.apply_sort_data()
        
        # 刷新表格
        self.refresh_table()
    
    def add_table_row(self, fund_info):
        """添加表格行"""
        # 只有在溢价或折价超过阈值时，才显示基金状态
        show_state = ""
        if fund_info['status'] in ['premium_alert', 'discount_alert']:
            show_state = fund_info.get('fund_state', '')
            
        values = (
            fund_info['code'],
            fund_info['name'],
            f"{fund_info['market_price']:.4f}" if fund_info['market_price'] else "N/A",
            f"{fund_info['nav_price']:.4f}" if fund_info['nav_price'] else "N/A",
            f"{fund_info['premium_rate']:.2f}" if fund_info['premium_rate'] is not None else "N/A",
            f"{fund_info['discount_rate']:.2f}" if fund_info['discount_rate'] is not None else "N/A",
            self.get_status_text(fund_info['status']),
            show_state
        )
        
        self.tree.insert("", tk.END, values=values, tags=(fund_info['status'],))
    
    def get_status_text(self, status):
        """获取状态文本"""
        status_map = {
            'premium_alert': '⚠️ 溢价告警',
            'discount_alert': '⚠️ 折价告警',
            'premium': '📈 溢价',
            'discount': '📉 折价',
            'normal': '➖ 正常',
            'unknown': '❓ 未知'
        }
        return status_map.get(status, '❓ 未知')
    
    def update_completion_status(self):
        """更新完成状态"""
        total = len(self.fund_data)
        premium_alert = sum(1 for f in self.fund_data if f['status'] == 'premium_alert')
        discount_alert = sum(1 for f in self.fund_data if f['status'] == 'discount_alert')
        
        now = datetime.now().strftime("%H:%M:%S")
        self.status_label.config(text=f"数据刷新完成 - 更新时间: {now}")
        self.count_label.config(text=f"关注: {total} | 溢价告警: {premium_alert} | 折价告警: {discount_alert}")
    
    def trigger_alert(self, fund_info, alert_type, rate):
        """触发告警"""
        code = fund_info['code']
        name = fund_info['name']
        threshold = (self.premium_threshold.get() if alert_type == 'premium' 
                    else self.discount_threshold.get())
        
        # 记录日志
        log_alert(code, name, alert_type, rate, threshold)
        
        # 发送钉钉通知（包含去重逻辑）
        if self.webhook_url.get():
            message = format_alert_message(
                code, name, alert_type, rate,
                fund_info['market_price'], fund_info['nav_price'],
                fund_info.get('fund_state', '')
            )
            send_dingtalk_alert(self.webhook_url.get(), self.webhook_secret.get(), message, fund_info['code'])
 
 
def run_app():
    """启动应用程序"""
    root = tk.Tk()
    app = LOFMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()
