# 第一部分：導入庫和數據類
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
from typing import Optional
from dataclasses import dataclass
import threading
from pathlib import Path
import subprocess
import math
import re
import requests
import json
import time
from urllib.parse import quote
import hashlib
import random
import string
from lanzou.api import LanZouCloud

@dataclass
class CompressionConfig:
    initial_size: float
    step_reduction: float
    size_unit: str
    custom_suffix: str

@dataclass
class SplitConfig:
    initial_size: float
    step_reduction: float
    size_unit: str
    file_type: str

# 第二部分：MainApplication 類
class MainApplication:
    def __init__(self):
        self.window = tk.Tk()
        self.setup_window()
        self.initialize_variables()
        self.create_styles()
        self.create_widgets()
        self.current_tool = None
        
        # 初始化蓝奏云API
        self.lanzou = LanZouCloud()
        self.lanzou.ignore_limits()  # 解除官方限制
        self.lanzou.set_max_size(100)  # 设置最大文件大小
        self.lanzou.set_upload_delay((0, 0))  # 设置上传延时
        self.lanzou.is_logged_in = False  # 初始化登录状态
    
    def initialize_variables(self):
        self.progress_var = tk.DoubleVar(value=0)
    
    def setup_window(self):
        self.window.title("蓝奏云工具集 v3.6")
        self.window.geometry("1100x700")
        self.window.minsize(1100, 700)
        self.window.configure(bg='#f5f5f5')  # 恢复浅色背景
    
    def create_styles(self):
        style = ttk.Style()
        
        # 設置全局樣式
        style.configure('.',
                       background='#f5f5f5',
                       foreground='#333333')
        
        # 一般按鈕樣式
        style.configure('Custom.TButton', 
                       font=('Microsoft YaHei UI', 9),
                       padding=6)
        
        # 主要操作按鈕樣式
        style.configure('Action.TButton',
                       font=('Microsoft YaHei UI', 9, 'bold'),
                       padding=8)
        
        # 工具選擇按鈕樣式
        style.configure('Tool.TButton',
                       font=('Microsoft YaHei UI', 10),
                       padding=(20, 10),
                       width=12)
        
        # 標籤樣式
        style.configure('Custom.TLabel',
                       font=('Microsoft YaHei UI', 9),
                       background='#f5f5f5')
        
        # 狀態標籤樣式
        style.configure('Status.TLabel',
                       font=('Microsoft YaHei UI', 9),
                       background='#f5f5f5',
                       foreground='#666666')
        
        # 版本標籤樣式
        style.configure('Version.TLabel',
                       font=('Microsoft YaHei UI', 9),
                       background='#f5f5f5',
                       foreground='#999999')
        
        # 框架樣式
        style.configure('Custom.TFrame',
                       background='#f5f5f5')
        
        # 框架標題樣式
        style.configure('Custom.TLabelframe',
                       background='#f5f5f5')
        style.configure('Custom.TLabelframe.Label',
                       font=('Microsoft YaHei UI', 10, 'bold'),
                       background='#f5f5f5',
                       foreground='#1976D2')
        
        # 進度條樣式
        style.configure('Custom.Horizontal.TProgressbar',
                       troughcolor='#E0E0E0',
                       background='#2196F3',
                       thickness=10)
        
        # 修改设置按钮样式，使其更加紧凑
        style.configure('Settings.TButton',
                       font=('Microsoft YaHei UI', 9),
                       padding=0,
                       width=1)
        
        # 添加菜单按钮样式
        style.configure('Menu.TButton',
                       font=('Microsoft YaHei UI', 11),
                       padding=(15, 10),
                       width=15)
        
        # 添加云盘按钮样式
        style.configure('Cloud.TButton',
                       font=('Microsoft YaHei UI', 10),
                       padding=(10, 8))
    
    def create_widgets(self):
        # 創建主框架
        self.main_frame = ttk.Frame(self.window, style='Custom.TFrame')
        self.main_frame.pack(fill='both', expand=True, padx=25, pady=20)
        
        # 創建頂層容器
        top_container = ttk.Frame(self.main_frame, style='Custom.TFrame')
        top_container.pack(fill='both', expand=True)
        
        # 創建左側工具選擇欄
        tool_frame = ttk.LabelFrame(top_container,
                                  text=" 🛠️ 工具选择 ",
                                  style='Custom.TLabelframe')
        tool_frame.pack(side='left', fill='y', padx=(0, 20))
        
        # 創建內部按鈕容器
        button_container = ttk.Frame(tool_frame, style='Custom.TFrame')
        button_container.pack(padx=15, pady=15)
        
        # 添加工具選擇按鈕
        tools = [
            ("📦 分卷工具", "分卷工具"),
            ("🔄 合并工具", "合并工具"),
            ("🎬 音视频工具", "音视频工具")
        ]
        
        for text, command in tools:
            btn = ttk.Button(button_container,
                           text=text,
                           style='Tool.TButton',
                           command=lambda cmd=command: self.switch_tool(cmd))
            btn.pack(pady=6)
        
        # 添加分隔线
        ttk.Separator(button_container, orient='horizontal').pack(fill='x', pady=10)
        
        # 添加蓝奏云功能按钮
        cloud_tools = [
            ("📂 全部文件", self.show_all_files),
            ("⬆️ 上传文件", self.show_upload_dialog),
            ("⬇️ 下载文件", self.show_download_dialog)
        ]
        
        for text, command in cloud_tools:
            btn = ttk.Button(button_container,
                           text=text,
                           style='Tool.TButton',
                           command=command)
            btn.pack(pady=6)
    
        # 創建右側內容區域
        self.content_frame = ttk.Frame(top_container, style='Custom.TFrame')
        self.content_frame.pack(side='left', fill='both', expand=True)
        
        # 添加狀態欄
        status_frame = ttk.Frame(self.main_frame, style='Custom.TFrame')
        status_frame.pack(fill='x', pady=(10, 0))

        self.status_label = ttk.Label(status_frame,
                                    text="✅ 就绪",
                                    style='Status.TLabel')
        self.status_label.pack(side='left', padx=5)

        version_label = ttk.Label(status_frame,
                                text="v3.6",
                                style='Version.TLabel')
        version_label.pack(side='right', padx=5)
    
    def switch_tool(self, tool_name):
        # 清除當前內容
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # 停止當前工具的處理（如果有）
        if hasattr(self, 'current_tool') and self.current_tool:
            if hasattr(self.current_tool, 'stop_processing'):
                self.current_tool.stop_processing()
        
        # 創建新工具實例
        if tool_name == "分卷工具":
            self.current_tool = LanzouCompressor(self.content_frame)
        elif tool_name == "合并工具":
            self.current_tool = LanzouDecompressor(self.content_frame)
        elif tool_name == "音视频工具":
            self.current_tool = MediaSplitter(self.content_frame)
        
        # 更新狀態欄
        if self.current_tool:
            self.status_label.config(text=f"✅ {tool_name}已就绪")
    
    def run(self):
        try:
            self.window.mainloop()
        except Exception as e:
            messagebox.showerror("錯誤", f"程序運行時出錯: {str(e)}")
        finally:
            if hasattr(self, 'current_tool') and self.current_tool:
                if hasattr(self.current_tool, 'stop_processing'):
                    self.current_tool.stop_processing()

    def show_settings(self):
        SettingsDialog(self.window)

    def show_login_dialog(self, callback=None):
        """显示登录对话框"""
        dialog = tk.Toplevel(self.window)
        dialog.title("登录蓝奏云")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()  # 设置为模态窗口
        
        # 创建选项卡
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 账号密码登录页
        account_frame = ttk.Frame(notebook)
        notebook.add(account_frame, text="账号密码登录")
        
        ttk.Label(account_frame,
                 text="用户名:",
                 style='Custom.TLabel').pack(pady=(20, 5))
                 
        username_entry = ttk.Entry(account_frame, width=30)
        username_entry.pack(pady=5)
        
        ttk.Label(account_frame,
                 text="密码:",
                 style='Custom.TLabel').pack(pady=5)
                 
        password_entry = ttk.Entry(account_frame, width=30, show="*")
        password_entry.pack(pady=5)
        
        # Cookie登录页
        cookie_frame = ttk.Frame(notebook)
        notebook.add(cookie_frame, text="Cookie登录")
        
        ttk.Label(cookie_frame,
                 text="请输入Cookie:",
                 style='Custom.TLabel').pack(pady=(20, 5))
                 
        cookie_text = tk.Text(cookie_frame, width=35, height=5)
        cookie_text.pack(pady=5)
        
        # 状态标签
        status_label = ttk.Label(dialog,
                               text="",
                               style='Custom.TLabel')
        status_label.pack(pady=10)
        
        def do_login():
            try:
                if notebook.index(notebook.select()) == 0:  # 账号密码登录
                    username = username_entry.get().strip()
                    password = password_entry.get().strip()
                    
                    if not username or not password:
                        status_label.config(text="请输入用户名和密码", foreground='red')
                        return
                    
                    status_label.config(text="正在登录...", foreground='#666666')
                    dialog.update()
                    
                    # 使用账号密码登录
                    if self.lanzou.login(username, password) == LanZouCloud.SUCCESS:
                        self.lanzou.is_logged_in = True  # 设置登录状态
                        status_label.config(text="登录成功！", foreground='green')
                        dialog.update()
                        time.sleep(1)
                        dialog.destroy()
                        if callback:
                            callback()
                    else:
                        status_label.config(text="登录失败，请检查账号密码", foreground='red')
                else:  # Cookie登录
                    cookie = cookie_text.get('1.0', tk.END).strip()
                    if not cookie:
                        status_label.config(text="请输入Cookie", foreground='red')
                        return
                    
                    status_label.config(text="正在验证Cookie...", foreground='#666666')
                    dialog.update()
                    
                    # 解析cookie字符串
                    cookie_dict = {}
                    for item in cookie.split(';'):
                        if '=' in item:
                            key, value = item.strip().split('=', 1)
                            cookie_dict[key] = value
                    
                    # 使用Cookie登录
                    if self.lanzou.login_by_cookie(cookie_dict) == LanZouCloud.SUCCESS:
                        self.lanzou.is_logged_in = True  # 设置登录状态
                        status_label.config(text="登录成功！", foreground='green')
                        dialog.update()
                        time.sleep(1)
                        dialog.destroy()
                        if callback:
                            callback()
                    else:
                        status_label.config(text="Cookie无效或已过期", foreground='red')
            except Exception as e:
                status_label.config(text=f"登录出错: {str(e)}", foreground='red')
        
        # 按钮框架
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame,
                  text="登录",
                  style='Custom.TButton',
                  command=do_login).pack(side='left', padx=5)
                  
        ttk.Button(button_frame,
                  text="取消",
                  style='Custom.TButton',
                  command=dialog.destroy).pack(side='left', padx=5)
        
        # 绑定回车键
        dialog.bind('<Return>', lambda e: do_login())
        
        # 设置初始焦点
        username_entry.focus()

    def show_upload_dialog(self):
        if not hasattr(self, 'lanzou') or not self.lanzou.is_logged_in:
            if messagebox.askyesno("提示", "您尚未登录，是否现在登录？"):
                self.show_login_dialog(callback=self.show_upload_dialog)
            return
        
        file_path = filedialog.askopenfilename(
            title="选择要上传的文件",
            filetypes=[("所有文件", "*.*")]
        )
        
        if file_path:
            result = self.lanzou.upload_file(file_path)
            if result['code'] == 1:
                messagebox.showinfo("成功", "文件上传成功！")
            else:
                messagebox.showerror("错误", f"上传失败: {result['message']}")

    def show_download_dialog(self):
        if not hasattr(self, 'lanzou') or not self.lanzou.is_logged_in:
            if messagebox.askyesno("提示", "您尚未登录，是否现在登录？"):
                self.show_login_dialog(callback=self.show_download_dialog)
            return
        
        dialog = tk.Toplevel(self.window)
        dialog.title("下载文件")
        dialog.geometry("600x400")
        dialog.resizable(True, True)
        
        # 创建文件列表框架
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 创建树形视图
        columns = ('文件名', '大小', '上传时间', '下载次数')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 设置列标题
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # 设置第一列（文件名）宽度更大
        tree.column('文件名', width=200)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side='right', fill='y')
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='left', fill='both', expand=True)
        
        # 获取并显示文件列表
        files = self.lanzou.get_file_list()
        for file in files:
            tree.insert('', 'end', values=(
                file['name'],
                file['size'],
                file['time'],
                file['downs']
            ), tags=('file',))
        
        def download_selected():
            selection = tree.selection()
            if not selection:
                messagebox.showerror("错误", "请选择要下载的文件")
                return
            
            item = tree.item(selection[0])
            file_name = item['values'][0]
            
            # 找到对应的文件信息
            file_info = next((f for f in files if f['name'] == file_name), None)
            if not file_info:
                messagebox.showerror("错误", "未找到文件信息")
                return
            
            # 选择保存位置
            save_path = filedialog.asksaveasfilename(
                title="保存文件",
                initialfile=file_info['name'],
                defaultextension=os.path.splitext(file_info['name'])[1]
            )
            
            if save_path:
                try:
                    if self.lanzou.download_file(file_info['id'], save_path):
                        messagebox.showinfo("成功", "文件下载成功！")
                        dialog.destroy()
                    else:
                        messagebox.showerror("错误", "下载失败")
                except Exception as e:
                    messagebox.showerror("错误", f"下载出错: {str(e)}")
        
        # 按钮框架
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame,
                  text="下载选中文件",
                  style='Custom.TButton',
                  command=download_selected).pack(side='left', padx=5)
                  
        ttk.Button(button_frame,
                  text="刷新列表",
                  style='Custom.TButton',
                  command=lambda: refresh_list()).pack(side='left', padx=5)
                  
        ttk.Button(button_frame,
                  text="关闭",
                  style='Custom.TButton',
                  command=dialog.destroy).pack(side='right', padx=5)
        
        def refresh_list():
            # 清空现有列表
            for item in tree.get_children():
                tree.delete(item)
            
            # 重新获取文件列表
            nonlocal files
            files = self.lanzou.get_file_list()
            for file in files:
                tree.insert('', 'end', values=(
                    file['name'],
                    file['size'],
                    file['time'],
                    file['downs']
                ), tags=('file',))

    def create_file_manager(self):
        """创建文件管理器界面"""
        # 清空当前内容区域
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 创建工具栏
        toolbar = ttk.Frame(self.content_frame)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(toolbar,
                   text="上传文件",
                   style='Custom.TButton',
                   command=self.show_upload_dialog).pack(side='left', padx=2)
                   
        ttk.Button(toolbar,
                   text="新建文件夹",
                   style='Custom.TButton',
                   command=self.create_folder).pack(side='left', padx=2)
                   
        ttk.Button(toolbar,
                   text="刷新",
                   style='Custom.TButton',
                   command=self.refresh_file_list).pack(side='left', padx=2)
        
        # 创建文件列表框架
        list_frame = ttk.Frame(self.content_frame)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建树形视图
        columns = ('文件名', '大小', '上传时间', '下载次数')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 设置列标题
        for col in columns:
            self.file_tree.heading(col, text=col)
            self.file_tree.column(col, width=100)
        
        # 设置第一列（文件名）宽度更大
        self.file_tree.column('文件名', width=200)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        # 打包组件
        self.file_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 绑定双击和右键事件
        self.file_tree.bind('<Double-1>', self.on_double_click)
        self.file_tree.bind('<Button-3>', self.show_context_menu)
        
        # 加载文件列表
        self.refresh_file_list()

    def refresh_file_list(self):
        """刷新文件列表"""
        if not hasattr(self, 'lanzou') or not self.lanzou.is_logged_in:
            print("未登录或 lanzou 实例未初始化")  # 调试信息
            return
        
        # 清空现有列表
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        try:
            print("正在获取文件夹列表...")  # 调试信息
            # 获取文件夹列表
            folders = self.lanzou.get_dir_list()
            for folder in folders:
                self.file_tree.insert('', 'end', values=(
                    f"📁 {folder['name']}",
                    "文件夹",
                    "-",
                    "-"
                ), tags=('folder',))
            
            print("正在获取文件列表...")  # 调试信息
            # 获取文件列表
            files = self.lanzou.get_file_list()
            for file in files:
                self.file_tree.insert('', 'end', values=(
                    f"📄 {file['name']}",
                    file['size'],
                    file['time'],
                    file['downs']
                ), tags=('file',))
                
            if not folders and not files:
                print("没有找到文件和文件夹")  # 调试信息
                # 如果没有文件和文件夹，显示空提示
                self.file_tree.insert('', 'end', values=(
                    "暂无文件",
                    "-",
                    "-",
                    "-"
                ), tags=('empty',))
                
        except Exception as e:
            error_msg = str(e)
            print(f"刷新文件列表时出错: {error_msg}")  # 调试信息
            messagebox.showerror("错误", f"获取文件列表失败: {error_msg}")
            
            # 显示错误提示
            self.file_tree.insert('', 'end', values=(
                "获取文件列表失败",
                "-",
                "-",
                "-"
            ), tags=('error',))

    def on_double_click(self, event):
        """双击处理"""
        item = self.file_tree.selection()[0]
        values = self.file_tree.item(item)['values']
        tags = self.file_tree.item(item)['tags']
        
        if 'folder' in tags:
            # 如果是文件夹，进入文件夹
            folder_name = values[0].replace("📁 ", "")
            folder = next((f for f in self.lanzou.get_dir_list() if f.name == folder_name), None)
            if folder:
                self.current_folder_id = folder.id
                self.refresh_file_list()
        else:
            # 如果是文件，下载文件
            self.download_selected(item)

    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.file_tree.identify_row(event.y)
        if not item:
            return
        
        # 选中被右键的项
        self.file_tree.selection_set(item)
        
        # 创建右键菜单
        menu = tk.Menu(self.window, tearoff=0)
        
        # 获取项目类型（文件夹或文件）
        tags = self.file_tree.item(item)['tags']
        
        if 'folder' in tags:
            menu.add_command(label="打开", command=lambda: self.on_double_click(None))
            menu.add_command(label="删除", command=lambda: self.delete_selected(item))
        else:
            menu.add_command(label="下载", command=lambda: self.download_selected(item))
            menu.add_command(label="删除", command=lambda: self.delete_selected(item))
            menu.add_command(label="复制链接", command=lambda: self.copy_link(item))
        
        # 显示菜单
        menu.post(event.x_root, event.y_root)

    def create_folder_dialog(self):
        """创建新文件夹对话框"""
        dialog = tk.Toplevel(self.window)
        dialog.title("新建文件夹")
        dialog.geometry("300x120")
        dialog.resizable(False, False)
        
        dialog.transient(self.window)
        dialog.grab_set()
        
        ttk.Label(dialog,
                 text="文件夹名称:",
                 style='Custom.TLabel').pack(padx=20, pady=(20,5))
                 
        folder_name = ttk.Entry(dialog, width=30)
        folder_name.pack(padx=20)
        
        def do_create():
            name = folder_name.get().strip()
            if name:
                if self.lanzou.create_folder(name):
                    messagebox.showinfo("成功", "文件夹创建成功！")
                    dialog.destroy()
                    self.refresh_file_list()
                else:
                    messagebox.showerror("错误", "创建文件夹失败")
            else:
                messagebox.showerror("错误", "请输入文件夹名称")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame,
                  text="创建",
                  style='Custom.TButton',
                  command=do_create).pack(side='left', padx=5)
                  
        ttk.Button(button_frame,
                  text="取消",
                  style='Custom.TButton',
                  command=dialog.destroy).pack(side='left', padx=5)
        
        folder_name.focus()
        dialog.bind('<Return>', lambda e: do_create())

    def download_selected(self, item):
        file_name = self.file_tree.item(item)['values'][0]
        files = self.lanzou.get_file_list()
        file_info = next((f for f in files if f['name'] == file_name), None)
        
        if file_info:
            save_path = filedialog.asksaveasfilename(
                title="保存文件",
                initialfile=file_info['name']
            )
            if save_path:
                if self.lanzou.download_file(file_info['id'], save_path):
                    messagebox.showinfo("成功", "文件下载成功！")
                else:
                    messagebox.showerror("错误", "下载失败")

    def delete_selected(self, item):
        if messagebox.askyesno("确认", "确定要删除选中的文件吗？"):
            file_name = self.file_tree.item(item)['values'][0]
            files = self.lanzou.get_file_list()
            file_info = next((f for f in files if f['name'] == file_name), None)
            
            if file_info and self.lanzou.delete_file(file_info['id']):
                self.file_tree.delete(item)
                messagebox.showinfo("成功", "文件已删除！")
            else:
                messagebox.showerror("错误", "删除失败")

    def copy_link(self, item):
        file_name = self.file_tree.item(item)['values'][0]
        files = self.lanzou.get_file_list()
        file_info = next((f for f in files if f['name'] == file_name), None)
        
        if file_info:
            link = self.lanzou.get_share_url(file_info['id'])
            if link:
                self.window.clipboard_clear()
                self.window.clipboard_append(link)
                messagebox.showinfo("成功", "链接已复制到剪贴板！")
            else:
                messagebox.showerror("错误", "获取链接失败")

    def create_folder(self):
        folder_name = simpledialog.askstring("新建文件夹", "请输入文件夹名称：")
        if folder_name:
            if self.lanzou.create_folder(folder_name):
                self.refresh_file_list()
                messagebox.showinfo("成功", "文件夹创建成功！")
            else:
                messagebox.showerror("错误", "创建文件夹失败")

    def show_all_files(self):
        """显示全部文件"""
        # 清空当前内容区域
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 检查是否已登录
        if not hasattr(self, 'lanzou') or not self.lanzou.is_logged_in:
            # 如果未登录，显示登录提示和按钮
            login_frame = ttk.Frame(self.content_frame)
            login_frame.pack(expand=True)
            
            # 添加一个大的登录提示图标
            ttk.Label(login_frame, 
                     text="🔒",
                     font=('Microsoft YaHei UI', 48),
                     style='Custom.TLabel').pack(pady=(0, 20))
            
            ttk.Label(login_frame, 
                     text="请先登录蓝奏云账号",
                     font=('Microsoft YaHei UI', 12),
                     style='Custom.TLabel').pack(pady=(0, 10))
            
            ttk.Button(login_frame,
                      text="立即登录",
                      style='Custom.TButton',
                      command=lambda: self.show_login_dialog(callback=self.show_all_files)).pack()
        else:
            # 已登录，显示文件管理器
            self.create_file_manager()

    def show_recycle_bin(self):
        """显示回收站"""
        if not hasattr(self, 'lanzou') or not self.lanzou.get_cookie():
            if messagebox.askyesno("提示", "您尚未登录，是否现在登录？"):
                self.show_login_dialog()
            return
        
        self.create_recycle_bin()

    def create_recycle_bin(self):
        """创建回收站界面"""
        # 清除当前内容区域
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 创建回收站框架
        recycle_frame = ttk.Frame(self.content_frame)
        recycle_frame.pack(fill='both', expand=True)
        
        # 创建工具栏
        toolbar = ttk.Frame(recycle_frame)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(toolbar,
                  text="🔄 刷新",
                  style='Custom.TButton',
                  command=self.refresh_recycle_bin).pack(side='left', padx=2)
              
        ttk.Button(toolbar,
                  text="🗑️ 清空回收站",
                  style='Custom.TButton',
                  command=self.clear_recycle_bin).pack(side='left', padx=2)
        
        # 创建文件列表
        list_frame = ttk.Frame(recycle_frame)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        columns = ('文件名', '大小', '删除时间', '操作')
        self.recycle_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 设置列标题和宽度
        self.recycle_tree.heading('文件名', text='文件名')
        self.recycle_tree.heading('大小', text='大小')
        self.recycle_tree.heading('删除时间', text='删除时间')
        self.recycle_tree.heading('操作', text='操作')
        
        self.recycle_tree.column('文件名', width=400)
        self.recycle_tree.column('大小', width=100)
        self.recycle_tree.column('删除时间', width=150)
        self.recycle_tree.column('操作', width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.recycle_tree.yview)
        self.recycle_tree.configure(yscrollcommand=scrollbar.set)
        
        self.recycle_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 绑定右键菜单
        self.recycle_tree.bind('<Button-3>', self.show_recycle_context_menu)
        
        # 加载回收站文件列表
        self.refresh_recycle_bin()

class SettingsDialog:
    def __init__(self, parent):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("设置")
        self.dialog.geometry("500x500")  # 增加高度以容纳新设置
        self.dialog.resizable(False, False)
        
        # 使设置窗口居中显示
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()/2 - 250,
            parent.winfo_rooty() + parent.winfo_height()/2 - 250
        ))
        
        # 设置模态窗口
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 初始化变量
        self.init_variables()
        self.create_widgets()
        
    def init_variables(self):
        # 默认路径
        self.path_var = tk.StringVar(value=str(Path.home() / "Desktop"))
        
        # 分卷工具默认值
        self.split_initial_size = tk.StringVar(value="99")
        self.split_step_reduction = tk.StringVar(value="10.24")
        self.split_size_unit = tk.StringVar(value="MB")
        self.split_custom_suffix = tk.StringVar(value=".zip")
        
        # 音视频工具默认值
        self.media_initial_size = tk.StringVar(value="99")
        self.media_step_reduction = tk.StringVar(value="10.24")
        self.media_size_unit = tk.StringVar(value="MB")
        
        # 缓冲区大小
        self.buffer_size = tk.StringVar(value="4MB")
        
    def create_widgets(self):
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 常规设置选项卡
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="常规设置")
        
        # 默认保存路径设置
        path_frame = ttk.LabelFrame(general_frame, text="默认保存路径", style='Custom.TLabelframe')
        path_frame.pack(fill='x', padx=10, pady=5)
        
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        path_entry.pack(side='left', fill='x', expand=True, padx=5, pady=5)
        
        ttk.Button(path_frame,
                  text="浏览",
                  style='Custom.TButton',
                  command=self.select_default_path).pack(side='left', padx=5, pady=5)
        
        # 分卷工具设置
        split_frame = ttk.LabelFrame(general_frame, text="分卷工具默认值", style='Custom.TLabelframe')
        split_frame.pack(fill='x', padx=10, pady=5)
        
        # 初始大小设置
        size_frame = ttk.Frame(split_frame)
        size_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(size_frame,
                 text="初始大小:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(size_frame,
                 textvariable=self.split_initial_size,
                 width=8).pack(side='left', padx=(0, 5))
        
        ttk.Combobox(size_frame,
                    textvariable=self.split_size_unit,
                    values=["GB", "MB", "KB"],
                    state="readonly",
                    width=5).pack(side='left')
        
        # 递减步长设置
        step_frame = ttk.Frame(split_frame)
        step_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(step_frame,
                 text="递减步长:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(step_frame,
                 textvariable=self.split_step_reduction,
                 width=8).pack(side='left', padx=(0, 5))
        
        ttk.Label(step_frame,
                 text="KB",
                 style='Custom.TLabel').pack(side='left')
        
        # 自定义后缀设置
        suffix_frame = ttk.Frame(split_frame)
        suffix_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(suffix_frame,
                 text="默认后缀:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(suffix_frame,
                 textvariable=self.split_custom_suffix,
                 width=8).pack(side='left')
        
        # 音视频工具设置
        media_frame = ttk.LabelFrame(general_frame, text="音视频工具默认值", style='Custom.TLabelframe')
        media_frame.pack(fill='x', padx=10, pady=5)
        
        # 初始大小设置
        media_size_frame = ttk.Frame(media_frame)
        media_size_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(media_size_frame,
                 text="初始大小:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(media_size_frame,
                 textvariable=self.media_initial_size,
                 width=8).pack(side='left', padx=(0, 5))
        
        ttk.Combobox(media_size_frame,
                    textvariable=self.media_size_unit,
                    values=["GB", "MB", "KB"],
                    state="readonly",
                    width=5).pack(side='left')
        
        # 递减步长设置
        media_step_frame = ttk.Frame(media_frame)
        media_step_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(media_step_frame,
                 text="递减步长:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(media_step_frame,
                 textvariable=self.media_step_reduction,
                 width=8).pack(side='left', padx=(0, 5))
        
        ttk.Label(media_step_frame,
                 text="KB",
                 style='Custom.TLabel').pack(side='left')
        
        # 高级设置选项卡
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="高级设置")
        
        # 性能设置
        performance_frame = ttk.LabelFrame(advanced_frame, text="性能设置", style='Custom.TLabelframe')
        performance_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(performance_frame,
                 text="缓冲区大小:",
                 style='Custom.TLabel').pack(side='left', padx=5, pady=5)
        
        ttk.Combobox(performance_frame,
                    textvariable=self.buffer_size,
                    values=["1MB", "2MB", "4MB", "8MB"],
                    state="readonly",
                    width=10).pack(side='left', padx=5, pady=5)
        
        # 添加关于信息框架
        about_frame = ttk.LabelFrame(advanced_frame, text="关于", style='Custom.TLabelframe')
        about_frame.pack(fill='x', padx=10, pady=5)
        
        # 创建一个内部框架来组织信息
        info_frame = ttk.Frame(about_frame)
        info_frame.pack(padx=10, pady=5)
        
        # 作者信息
        author_frame = ttk.Frame(info_frame)
        author_frame.pack(fill='x', pady=2)
        
        ttk.Label(author_frame,
                 text="作者:",
                 width=10,
                 style='Custom.TLabel').pack(side='left')
        
        ttk.Label(author_frame,
                 text="云山海",  # 更新作者名字
                 style='Custom.TLabel').pack(side='left')
        
        # 版本信息
        version_frame = ttk.Frame(info_frame)
        version_frame.pack(fill='x', pady=2)
        
        ttk.Label(version_frame,
                 text="版本:",
                 width=10,
                 style='Custom.TLabel').pack(side='left')
        
        ttk.Label(version_frame,
                 text="v3.6",
                 style='Custom.TLabel').pack(side='left')
        
        # 修改时间
        update_frame = ttk.Frame(info_frame)
        update_frame.pack(fill='x', pady=2)
        
        ttk.Label(update_frame,
                 text="更新时间:",
                 width=10,
                 style='Custom.TLabel').pack(side='left')
        
        ttk.Label(update_frame,
                 text="2025-04-01 17:28",  # 更新时间
                 style='Custom.TLabel').pack(side='left')
        
        # 版权信息
        copyright_frame = ttk.Frame(info_frame)
        copyright_frame.pack(fill='x', pady=2)
        
        ttk.Label(copyright_frame,
                 text="版权:",
                 width=10,
                 style='Custom.TLabel').pack(side='left')
        
        ttk.Label(copyright_frame,
                 text="© 2025 All Rights Reserved",  # 更新年份
                 style='Custom.TLabel').pack(side='left')

        # 底部按钮
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame,
                  text="确定",
                  style='Custom.TButton',
                  command=self.save_settings).pack(side='right', padx=5)
        
        ttk.Button(button_frame,
                  text="取消",
                  style='Custom.TButton',
                  command=self.dialog.destroy).pack(side='right', padx=5)
    
    def select_default_path(self):
        dirname = filedialog.askdirectory(
            title="选择默认保存位置",
            initialdir=self.path_var.get()
        )
        if dirname:
            self.path_var.set(dirname)
    
    def save_settings(self):
        # 这里可以添加保存设置到配置文件的代码
        # 例如可以使用 json 或 ini 格式保存设置
        self.dialog.destroy()

# 在这里放入 MainApplication 类的代码
class LanzouCompressor:
    def __init__(self, parent) -> None:
        self.parent = parent
        self.initialize_variables()
        self.create_widgets()
        
    def initialize_variables(self) -> None:
        self.input_file: str = ""
        self.output_dir: str = str(Path.home() / "Desktop")
        self.is_processing: bool = False
        self.stop_flag: bool = False
        
        # UI Variables
        self.custom_suffix = tk.StringVar(value=".zip")
        self.initial_size_var = tk.StringVar(value="99")
        self.step_reduction_var = tk.StringVar(value="10.24")
        self.size_unit = tk.StringVar(value="MB")
        self.progress_var = tk.DoubleVar(value=0)
        self.output_path_var = tk.StringVar(value=self.output_dir)
        
    def create_widgets(self) -> None:
        # Progress Section
        progress_frame = ttk.LabelFrame(self.parent,
                                      text="处理进度",
                                      style='Custom.TLabelframe')
        progress_frame.pack(fill='both', expand=True, pady=10)
        
        self.progress = ttk.Progressbar(progress_frame,
                                      variable=self.progress_var,
                                      mode='determinate')
        self.progress.pack(fill='x', padx=10, pady=10)
        
        self.progress_label = ttk.Label(progress_frame,
                                      text="0%",
                                      style='Custom.TLabel')
        self.progress_label.pack()
        
        log_frame = ttk.Frame(progress_frame)
        log_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.log_text = tk.Text(log_frame,
                               height=10,
                               wrap=tk.WORD,
                               font=('Consolas', 9))
        self.log_text.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame,
                                orient="vertical",
                                command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # File Selection Frame
        file_frame = ttk.LabelFrame(self.parent,
                                  text="文件选择",
                                  style='Custom.TLabelframe')
        file_frame.pack(fill='x', pady=5)
        
        input_frame = ttk.Frame(file_frame)
        input_frame.pack(fill='x', pady=5, padx=5)
        
        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side='left')
        
        ttk.Button(button_frame,
                  text="选择文件",
                  style='Custom.TButton',
                  command=self.select_input_file).pack(side='left', padx=2)
        
        ttk.Button(button_frame,
                  text="选择目录",
                  style='Custom.TButton',
                  command=self.select_input_dir).pack(side='left', padx=2)
        
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill='x', pady=5, padx=5)
        
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var)
        self.output_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        ttk.Button(output_frame,
                  text="选择保存位置",
                  style='Custom.TButton',
                  command=self.select_output_dir).pack(side='left')
        
        # Settings Frame
        settings_frame = ttk.LabelFrame(self.parent,
                                      text="设置",
                                      style='Custom.TLabelframe')
        settings_frame.pack(fill='x', pady=10)
        
        # Main container for left and right sections
        main_container = ttk.Frame(settings_frame)
        main_container.pack(fill='x', pady=5, padx=5)
        
        # Left Section - Settings Controls
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side='left', fill='x', expand=True)
        
        # Initial Size
        size_frame = ttk.Frame(left_frame)
        size_frame.pack(side='left', padx=(0, 15))
        
        ttk.Label(size_frame,
                 text="初始大小:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(size_frame,
                 textvariable=self.initial_size_var,
                 width=8).pack(side='left', padx=(0, 5))
        
        ttk.Combobox(size_frame,
                    textvariable=self.size_unit,
                    values=["GB", "MB", "KB"],
                    state="readonly",
                    width=5).pack(side='left')
        
        # Step Reduction
        step_frame = ttk.Frame(left_frame)
        step_frame.pack(side='left', padx=(0, 15))
        
        ttk.Label(step_frame,
                 text="递减步长:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(step_frame,
                 textvariable=self.step_reduction_var,
                 width=8).pack(side='left', padx=(0, 5))
        
        ttk.Label(step_frame,
                 text="KB",
                 style='Custom.TLabel').pack(side='left')
        
        # Custom Suffix
        suffix_frame = ttk.Frame(left_frame)
        suffix_frame.pack(side='left')
        
        ttk.Label(suffix_frame,
                 text="自定义后缀:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(suffix_frame,
                 textvariable=self.custom_suffix,
                 width=8).pack(side='left')
        
        # Right Section - Operation Buttons
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side='right')
        
        start_button = ttk.Button(right_frame,
                                text="开始处理",
                                style='Custom.TButton',
                                command=self.start_processing)
        start_button.pack(side='left', padx=(0, 5))
        
        stop_button = ttk.Button(right_frame,
                               text="停止处理",
                               style='Custom.TButton',
                               command=self.stop_processing)
        stop_button.pack(side='left')
        
    def log(self, message: str, error: bool = False) -> None:
        self.log_text.insert(tk.END, f"{message}\n")
        if error:
            self.log_text.tag_configure("error", foreground="red")
            self.log_text.tag_add("error",
                                "end-2c linestart",
                                "end-1c")
        self.log_text.see(tk.END)
        
    def validate_inputs(self) -> Optional[CompressionConfig]:
        if not self.input_file:
            messagebox.showerror("错误", "请选择要处理的文件")
            return None
            
        try:
            initial_size = float(self.initial_size_var.get())
            step_reduction = float(self.step_reduction_var.get())
            
            if initial_size <= 0:
                raise ValueError("初始大小必须大于0")
            if step_reduction <= 0:
                raise ValueError("递减步长必须大于0")
                
            return CompressionConfig(
                initial_size=initial_size,
                step_reduction=step_reduction,
                size_unit=self.size_unit.get(),
                custom_suffix=self.custom_suffix.get()
            )
        except ValueError as e:
            messagebox.showerror("错误", f"无效的输入值: {str(e)}")
            return None
            
    def process_file(self, config: CompressionConfig) -> None:
        try:
            if config.size_unit == "GB":
                unit_factor = 1024 * 1024 * 1024
            elif config.size_unit == "MB":
                unit_factor = 1024 * 1024
            else:  # KB
                unit_factor = 1024
                
            initial_bytes = int(config.initial_size * unit_factor)
            step_bytes = int(config.step_reduction * 1024)
            
            total_size = os.path.getsize(self.input_file)
            chunk_num = 1
            offset = 0
            
            with open(self.input_file, 'rb') as f:
                while offset < total_size and not self.stop_flag:
                    current_size = max(
                        initial_bytes - (chunk_num - 1) * step_bytes,
                        1024 * 1024  # Minimum 1MB
                    )
                    current_size = min(current_size, total_size - offset)
                    
                    self.write_chunk(f, offset, current_size, chunk_num, config)
                    
                    offset += current_size
                    chunk_num += 1
                    
                    # Update progress
                    progress = (offset / total_size) * 100
                    self.progress_var.set(progress)
                    self.progress_label.config(text=f"{progress:.1f}%")
                    
            if not self.stop_flag:
                self.log("✅ 处理完成!")
                messagebox.showinfo("完成", "文件处理已完成!")
            else:
                self.log("⚠️ 处理已停止", error=True)
                
        except Exception as e:
            self.log(f"❌ 错误: {str(e)}", error=True)
            messagebox.showerror("错误", f"处理文件时出错: {str(e)}")
        finally:
            self.is_processing = False
            self.progress_label.config(text="0%")
            
    def write_chunk(self, f: object, offset: int, size: int,
                   chunk_num: int, config: CompressionConfig) -> None:
        try:
            f.seek(offset)
            data = f.read(size)
            
            filename = Path(self.input_file).name
            chunk_name = f"{filename}.part({chunk_num}){config.custom_suffix}"
            output_path = Path(self.output_dir) / chunk_name
            
            with open(output_path, 'wb') as chunk_file:
                chunk_file.write(data)
                
            size_mb = size / (1024 * 1024)
            self.log(f"📦 已生成: {chunk_name} ({size_mb:.2f}MB)")
        except Exception as e:
            self.log(f"❌ 写入分卷 {chunk_num} 时出错: {str(e)}", error=True)
            raise
        
    def start_processing(self) -> None:
        if self.is_processing:
            messagebox.showwarning("警告", "已有处理任务正在进行中")
            return
            
        config = self.validate_inputs()
        if not config:
            return
            
        self.is_processing = True
        self.stop_flag = False
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.log_text.delete(1.0, tk.END)
        
        self.log("🚀 开始处理文件...")
        thread = threading.Thread(target=self.process_file, args=(config,))
        thread.daemon = True
        thread.start()
        
    def stop_processing(self) -> None:
        if self.is_processing:
            self.stop_flag = True
            self.log("⏹️ 正在停止处理...", error=True)

    def select_input_file(self) -> None:
        filename = filedialog.askopenfilename(
            title="选择要分卷的文件",
            filetypes=[("所有文件", "*.*")]
        )
        if filename:
            self.input_file = filename
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filename)

    def select_input_dir(self) -> None:
        dirname = filedialog.askdirectory(
            title="选择要分卷的目录"
        )
        if dirname:
            self.input_file = dirname
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, dirname)

    def select_output_dir(self) -> None:
        dirname = filedialog.askdirectory(
            title="选择保存位置",
            initialdir=self.output_dir
        )
        if dirname:
            self.output_dir = dirname
            self.output_path_var.set(dirname)

    def _create_settings_controls(self, parent):
        # Initial Size
        size_frame = ttk.Frame(parent)
        size_frame.pack(side='left', padx=(0, 15))
        
        ttk.Label(size_frame,
                 text="初始大小:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(size_frame,
                 textvariable=self.initial_size_var,
                 width=8).pack(side='left', padx=(0, 5))
        
        ttk.Combobox(size_frame,
                    textvariable=self.size_unit,
                    values=["GB", "MB", "KB"],
                    state="readonly",
                    width=5).pack(side='left')
        
        # Step Reduction
        step_frame = ttk.Frame(parent)
        step_frame.pack(side='left', padx=(0, 15))
        
        ttk.Label(step_frame,
                 text="递减步长:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(step_frame,
                 textvariable=self.step_reduction_var,
                 width=8).pack(side='left', padx=(0, 5))
        
        ttk.Label(step_frame,
                 text="KB",
                 style='Custom.TLabel').pack(side='left')
        
        # Custom Suffix
        suffix_frame = ttk.Frame(parent)
        suffix_frame.pack(side='left')
        
        ttk.Label(suffix_frame,
                 text="自定义后缀:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(suffix_frame,
                 textvariable=self.custom_suffix,
                 width=8).pack(side='left')

class LanzouDecompressor:
    def __init__(self, parent) -> None:
        self.parent = parent
        self.initialize_variables()
        self.create_widgets()
        
    def initialize_variables(self) -> None:
        self.input_dir: str = ""
        self.input_files: list = []
        self.file_groups: dict = {}
        self.output_dir: str = str(Path.home() / "Desktop")
        self.is_processing: bool = False
        self.stop_flag: bool = False
        self.progress_var = tk.DoubleVar(value=0)
        self.output_path_var = tk.StringVar(value=self.output_dir)
        
    def create_widgets(self) -> None:
        # Progress Section
        progress_frame = ttk.LabelFrame(self.parent,
                                      text="处理进度",
                                      style='Custom.TLabelframe')
        progress_frame.pack(fill='both', expand=True, pady=10)
        
        self.progress = ttk.Progressbar(progress_frame,
                                      variable=self.progress_var,
                                      mode='determinate')
        self.progress.pack(fill='x', padx=10, pady=10)
        
        self.progress_label = ttk.Label(progress_frame,
                                      text="0%",
                                      style='Custom.TLabel')
        self.progress_label.pack()
        
        log_frame = ttk.Frame(progress_frame)
        log_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.log_text = tk.Text(log_frame,
                               height=10,
                               wrap=tk.WORD,
                               font=('Consolas', 9))
        self.log_text.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame,
                                orient="vertical",
                                command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # File Selection Frame
        file_frame = ttk.LabelFrame(self.parent,
                                  text="文件选择",
                                  style='Custom.TLabelframe')
        file_frame.pack(fill='x', pady=5)
        
        input_frame = ttk.Frame(file_frame)
        input_frame.pack(fill='x', pady=5, padx=5)
        
        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side='left')
        
        ttk.Button(button_frame,
                  text="选择文件",
                  style='Custom.TButton',
                  command=self.select_input_file).pack(side='left', padx=2)
        
        ttk.Button(button_frame,
                  text="选择目录",
                  style='Custom.TButton',
                  command=self.select_input_dir).pack(side='left', padx=2)
        
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill='x', pady=5, padx=5)
        
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var)
        self.output_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        ttk.Button(output_frame,
                  text="选择保存位置",
                  style='Custom.TButton',
                  command=self.select_output_dir).pack(side='left')
        
        # Control Frame
        control_frame = ttk.LabelFrame(self.parent,
                                     text="操作控制",
                                     style='Custom.TLabelframe')
        control_frame.pack(fill='x', pady=10)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill='x', pady=5, padx=5)
        
        ttk.Label(button_frame, style='Custom.TLabel').pack(side='left', fill='x', expand=True)
        
        start_button = ttk.Button(button_frame,
                                text="开始合并",
                                style='Custom.TButton',
                                command=self.start_processing)
        start_button.pack(side='left', padx=(0, 5))
        
        stop_button = ttk.Button(button_frame,
                               text="停止合并",
                               style='Custom.TButton',
                               command=self.stop_processing)
        stop_button.pack(side='left')

    def show_completion_dialog(self, message: str, folder_path: str) -> None:
        dialog = tk.Toplevel(self.parent)
        dialog.title("完成")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        
        dialog.transient(self.parent)
        dialog.grab_set()
        
        dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + self.parent.winfo_width()/2 - 150,
            self.parent.winfo_rooty() + self.parent.winfo_height()/2 - 75
        ))
        
        ttk.Label(dialog, 
                 text=message,
                 style='Custom.TLabel',
                 wraplength=280).pack(pady=20)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def open_folder():
            os.startfile(folder_path)
            dialog.destroy()
        
        ttk.Button(button_frame,
                  text="打开文件夹",
                  style='Custom.TButton',
                  command=open_folder).pack(side='left', padx=5)
        
        ttk.Button(button_frame,
                  text="确定",
                  style='Custom.TButton',
                  command=dialog.destroy).pack(side='left', padx=5)
        
        dialog.focus_set()
        dialog.bind('<Return>', lambda e: dialog.destroy())
        dialog.wait_window()

    def find_related_parts(self, first_file: str) -> list:
        try:
            base_name = re.split(r'\.part\(\d+\)', Path(first_file).name)[0]
            dir_path = Path(first_file).parent
            
            related_files = []
            pattern = re.compile(rf'{re.escape(base_name)}\.part\((\d+)\).*')
            
            for file in dir_path.glob(f"{base_name}.part*"):
                match = pattern.match(file.name)
                if match:
                    related_files.append((int(match.group(1)), str(file)))
            
            related_files.sort(key=lambda x: x[0])
            return [f for _, f in related_files]
            
        except Exception as e:
            messagebox.showerror("错误", f"查找分卷文件时出错: {str(e)}")
            return []

    def select_input_file(self) -> None:
        filename = filedialog.askopenfilename(
            title="选择第一个分卷文件",
            filetypes=[("分卷文件", "*.part*"), ("所有文件", "*.*")]
        )
        if filename:
            self.input_files = self.find_related_parts(filename)
            if self.input_files:
                self.input_dir = str(Path(filename).parent)
                self.input_entry.delete(0, tk.END)
                self.input_entry.insert(0, filename)
                self.log(f"✅ 已找到 {len(self.input_files)} 个分卷文件")
                for f in self.input_files:
                    self.log(f"📄 {Path(f).name}")
            else:
                messagebox.showerror("错误", "未找到相关分卷文件")
            
    def select_input_dir(self) -> None:
        dirname = filedialog.askdirectory(
            title="选择分卷文件所在目录"
        )
        if dirname:
            self.input_dir = dirname
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, dirname)
            
            self.file_groups = {}
            for file in Path(dirname).glob("*.part*"):
                base_name = re.split(r'\.part\(\d+\)', file.name)[0]
                if base_name not in self.file_groups:
                    self.file_groups[base_name] = []
                self.file_groups[base_name].append(str(file))
            
            if self.file_groups:
                for base_name in self.file_groups:
                    self.file_groups[base_name].sort(key=lambda x: 
                        int(re.search(r'\.part\((\d+)\)', Path(x).name).group(1)))
                    
                total_files = sum(len(files) for files in self.file_groups.values())
                self.log(f"✅ 已找到 {len(self.file_groups)} 组分卷文件，共 {total_files} 个文件")
                for base_name, files in self.file_groups.items():
                    self.log(f"\n📁 {base_name}:")
                    for f in files:
                        self.log(f"  └─ {Path(f).name}")
            else:
                messagebox.showerror("错误", "所选目录中未找到分卷文件")
            
    def select_output_dir(self) -> None:
        dirname = filedialog.askdirectory(
            title="选择保存位置",
            initialdir=self.output_dir
        )
        if dirname:
            self.output_dir = dirname
            self.output_path_var.set(dirname)
            
    def log(self, message: str, error: bool = False) -> None:
        self.log_text.insert(tk.END, f"{message}\n")
        if error:
            self.log_text.tag_configure("error", foreground="red")
            self.log_text.tag_add("error",
                                "end-2c linestart",
                                "end-1c")
        self.log_text.see(tk.END)
        
    def validate_inputs(self) -> bool:
        if hasattr(self, 'input_files') and self.input_files:
            return True
        if hasattr(self, 'file_groups') and self.file_groups:
            return True
        
        messagebox.showerror("错误", "请选择分卷文件或包含分卷文件的目录")
        return False
            
    def process_files(self) -> None:
        try:
            if hasattr(self, 'input_files') and self.input_files:
                file_groups = {'single': self.input_files}
            elif hasattr(self, 'file_groups') and self.file_groups:
                file_groups = self.file_groups
            else:
                self.log("❌ 未找到分卷文件", error=True)
                messagebox.showerror("错误", "未找到分卷文件")
                return
            
            total_groups = len(file_groups)
            processed_groups = 0
            
            for base_name, files in file_groups.items():
                if self.stop_flag:
                    break
                    
                self.log(f"\n🔄 正在处理: {base_name}")
                
                output_path = Path(self.output_dir) / base_name
                
                total_files = len(files)
                processed_files = 0
                
                with open(output_path, 'wb') as outfile:
                    for file in files:
                        if self.stop_flag:
                            break
                            
                        with open(file, 'rb') as infile:
                            outfile.write(infile.read())
                            
                        processed_files += 1
                        group_progress = (processed_files / total_files)
                        total_progress = ((processed_groups + group_progress) / total_groups) * 100
                        
                        self.progress_var.set(total_progress)
                        self.progress_label.config(text=f"{total_progress:.1f}%")
                        self.log(f"📦 已合并: {Path(file).name}")
                        
                if not self.stop_flag:
                    self.log(f"✅ {base_name} 合并完成!")
                    processed_groups += 1
                else:
                    self.log(f"⚠️ {base_name} 处理已停止", error=True)
                    if output_path.exists():
                        output_path.unlink()
                    break
                        
            if not self.stop_flag:
                self.log("\n✅ 所有文件合并完成!")
                self.show_completion_dialog(
                    "所有文件合并已完成!",
                    self.output_dir
                )
            else:
                self.log("\n⚠️ 处理已停止", error=True)
                        
        except Exception as e:
            self.log(f"❌ 错误: {str(e)}", error=True)
            messagebox.showerror("错误", f"处理文件时出错: {str(e)}")
        finally:
            self.is_processing = False
            self.progress_label.config(text="0%")
            
    def start_processing(self) -> None:
        if self.is_processing:
            messagebox.showwarning("警告", "已有处理任务正在进行中")
            return
            
        if not self.validate_inputs():
            return
            
        self.is_processing = True
        self.stop_flag = False
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.log_text.delete(1.0, tk.END)
        
        self.log("🚀 开始合并文件...")
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()
        
    def stop_processing(self) -> None:
        if self.is_processing:
            self.stop_flag = True
            self.log("⏹️ 正在停止处理...", error=True)

class MediaSplitter:
    def __init__(self, parent) -> None:
        self.parent = parent
        self.initialize_variables()
        self.create_widgets()
        self.check_ffmpeg()
        
    def check_ffmpeg(self) -> None:
        """检查是否安装了ffmpeg"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)
        except FileNotFoundError:
            messagebox.showerror("错误", 
                               "未检测到ffmpeg，请先安装ffmpeg并确保其在系统PATH中。\n"
                               "您可以从 https://ffmpeg.org/download.html 下载安装。")
            
    def initialize_variables(self) -> None:
        self.input_file: str = ""
        self.output_dir: str = str(Path.home() / "Desktop")
        self.is_processing: bool = False
        self.stop_flag: bool = False
        
        # UI Variables
        self.initial_size_var = tk.StringVar(value="99")
        self.step_reduction_var = tk.StringVar(value="10.24")
        self.size_unit = tk.StringVar(value="MB")
        self.file_type = tk.StringVar(value="mp4")
        self.progress_var = tk.DoubleVar(value=0)
        self.output_path_var = tk.StringVar(value=self.output_dir)
        
    def create_widgets(self) -> None:
        # Progress Section
        progress_frame = ttk.LabelFrame(self.parent,
                                      text="处理进度",
                                      style='Custom.TLabelframe')
        progress_frame.pack(fill='both', expand=True, pady=10)
        
        self.progress = ttk.Progressbar(progress_frame,
                                      variable=self.progress_var,
                                      mode='determinate')
        self.progress.pack(fill='x', padx=10, pady=10)
        
        self.progress_label = ttk.Label(progress_frame,
                                      text="0%",
                                      style='Custom.TLabel')
        self.progress_label.pack()
        
        log_frame = ttk.Frame(progress_frame)
        log_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.log_text = tk.Text(log_frame,
                               height=10,
                               wrap=tk.WORD,
                               font=('Consolas', 9))
        self.log_text.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame,
                                orient="vertical",
                                command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # File Selection Frame
        file_frame = ttk.LabelFrame(self.parent,
                                  text="文件选择",
                                  style='Custom.TLabelframe')
        file_frame.pack(fill='x', pady=5)
        
        input_frame = ttk.Frame(file_frame)
        input_frame.pack(fill='x', pady=5, padx=5)
        
        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side='left')
        
        ttk.Button(button_frame,
                  text="选择文件",
                  style='Custom.TButton',
                  command=self.select_input_file).pack(side='left', padx=2)
        
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill='x', pady=5, padx=5)
        
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var)
        self.output_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        ttk.Button(output_frame,
                  text="选择保存位置",
                  style='Custom.TButton',
                  command=self.select_output_dir).pack(side='left')
        
        # Settings Frame
        settings_frame = ttk.LabelFrame(self.parent,
                                      text="设置",
                                      style='Custom.TLabelframe')
        settings_frame.pack(fill='x', pady=10)
        
        controls_frame = ttk.Frame(settings_frame)
        controls_frame.pack(fill='x', pady=5, padx=5)
        
        # Left side - Settings
        left_frame = ttk.Frame(controls_frame)
        left_frame.pack(side='left', fill='x', expand=True)
        
        # File Type Selection
        ttk.Label(left_frame,
                 text="文件类型:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Combobox(left_frame,
                    textvariable=self.file_type,
                    values=["mp4", "mp3"],
                    state="readonly",
                    width=5).pack(side='left', padx=(0, 10))
        
        # Initial Size
        ttk.Label(left_frame,
                 text="初始大小:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(left_frame,
                 textvariable=self.initial_size_var,
                 width=8).pack(side='left', padx=(0, 5))
        
        ttk.Combobox(left_frame,
                    textvariable=self.size_unit,
                    values=["GB", "MB", "KB"],
                    state="readonly",
                    width=5).pack(side='left', padx=(0, 10))
        
        # Step Reduction
        ttk.Label(left_frame,
                 text="递减步长:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(left_frame,
                 textvariable=self.step_reduction_var,
                 width=8).pack(side='left', padx=(0, 5))
        
        ttk.Label(left_frame,
                 text="KB",
                 style='Custom.TLabel').pack(side='left')
        
        # Right side - Control Buttons
        right_frame = ttk.Frame(controls_frame)
        right_frame.pack(side='right')
        
        start_button = ttk.Button(right_frame,
                                text="开始分卷",
                                style='Custom.TButton',
                                command=self.start_processing)
        start_button.pack(side='left', padx=(0, 5))
        
        stop_button = ttk.Button(right_frame,
                               text="停止分卷",
                               style='Custom.TButton',
                               command=self.stop_processing)
        stop_button.pack(side='left')
            
    def select_input_file(self) -> None:
        filetypes = [("媒体文件", "*.mp4;*.mp3"), ("所有文件", "*.*")]
        filename = filedialog.askopenfilename(
            title="选择要分卷的文件",
            filetypes=filetypes
        )
        if filename:
            # 自动设置文件类型
            ext = Path(filename).suffix.lower()
            if ext in ['.mp4', '.mp3']:
                self.file_type.set(ext[1:])
            
            self.input_file = filename
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filename)
            
    def select_output_dir(self) -> None:
        dirname = filedialog.askdirectory(
            title="选择保存位置",
            initialdir=self.output_dir
        )
        if dirname:
            self.output_dir = dirname
            self.output_path_var.set(dirname)
            
    def log(self, message: str, error: bool = False) -> None:
        self.log_text.insert(tk.END, f"{message}\n")
        if error:
            self.log_text.tag_configure("error", foreground="red")
            self.log_text.tag_add("error",
                                "end-2c linestart",
                                "end-1c")
        self.log_text.see(tk.END)
        
    def validate_inputs(self) -> Optional[SplitConfig]:
        if not self.input_file:
            messagebox.showerror("错误", "请选择要处理的文件")
            return None
            
        file_ext = Path(self.input_file).suffix.lower()
        if file_ext != f".{self.file_type.get()}":
            messagebox.showerror("错误", f"选择的文件类型与设置不符")
            return None
            
        try:
            initial_size = float(self.initial_size_var.get())
            step_reduction = float(self.step_reduction_var.get())
            
            if initial_size <= 0:
                raise ValueError("初始大小必须大于0")
            if step_reduction <= 0:
                raise ValueError("递减步长必须大于0")
                
            return SplitConfig(
                initial_size=initial_size,
                step_reduction=step_reduction,
                size_unit=self.size_unit.get(),
                file_type=self.file_type.get()
            )
        except ValueError as e:
            messagebox.showerror("错误", f"无效的输入值: {str(e)}")
            return None

    def get_video_duration(self, file_path: str) -> float:
        """获取视频时长（秒）"""
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
               '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return float(result.stdout)

    def split_video(self, input_file: str, output_pattern: str, 
                   start_time: float, duration: float) -> None:
        """使用ffmpeg分割视频"""
        cmd = [
            'ffmpeg', '-i', input_file,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c', 'copy',
            '-avoid_negative_ts', '1',
            output_pattern
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def process_file(self, config: SplitConfig) -> None:
        try:
            if config.file_type == "mp4":
                # 获取视频总时长
                total_duration = self.get_video_duration(self.input_file)
                
                # 计算每个分段的时长（秒）
                if config.size_unit == "GB":
                    target_size = config.initial_size * 1024
                elif config.size_unit == "MB":
                    target_size = config.initial_size
                else:  # KB
                    target_size = config.initial_size / 1024
                
                # 估算比特率（bits/second）
                filesize = os.path.getsize(self.input_file)
                bitrate = (filesize * 8) / total_duration
                
                # 计算每个分段的时长
                segment_duration = (target_size * 1024 * 1024 * 8) / bitrate
                
                # 计算需要分割的段数
                num_segments = math.ceil(total_duration / segment_duration)
                
                current_time = 0
                for i in range(num_segments):
                    if self.stop_flag:
                        break
                        
                    # 计算当前段的时长
                    current_duration = min(segment_duration, total_duration - current_time)
                    
                    # 生成输出文件名
                    filename = Path(self.input_file).name
                    output_file = Path(self.output_dir) / f"{filename}.part({i+1}).{config.file_type}"
                    
                    # 分割视频
                    self.split_video(self.input_file, str(output_file), 
                                   current_time, current_duration)
                    
                    # 更新进度
                    progress = ((i + 1) / num_segments) * 100
                    self.progress_var.set(progress)
                    self.progress_label.config(text=f"{progress:.1f}%")
                    
                    # 记录日志
                    size_mb = os.path.getsize(output_file) / (1024 * 1024)
                    self.log(f"📦 已生成: {output_file.name} ({size_mb:.2f}MB)")
                    
                    current_time += current_duration
                    
            else:  # mp3文件使用原来的二进制分割方法
                if config.size_unit == "GB":
                    unit_factor = 1024 * 1024 * 1024
                elif config.size_unit == "MB":
                    unit_factor = 1024 * 1024
                else:  # KB
                    unit_factor = 1024
                    
                initial_bytes = int(config.initial_size * unit_factor)
                step_bytes = int(config.step_reduction * 1024)
                
                total_size = os.path.getsize(self.input_file)
                chunk_num = 1
                offset = 0
                
                with open(self.input_file, 'rb') as f:
                    while offset < total_size and not self.stop_flag:
                        current_size = max(
                            initial_bytes - (chunk_num - 1) * step_bytes,
                            1024 * 1024  # Minimum 1MB
                        )
                        current_size = min(current_size, total_size - offset)
                        
                        f.seek(offset)
                        data = f.read(current_size)
                        
                        filename = Path(self.input_file).name
                        output_file = Path(self.output_dir) / f"{filename}.part({chunk_num}).{config.file_type}"
                        
                        with open(output_file, 'wb') as chunk_file:
                            chunk_file.write(data)
                        
                        offset += current_size
                        chunk_num += 1
                        
                        # Update progress
                        progress = (offset / total_size) * 100
                        self.progress_var.set(progress)
                        self.progress_label.config(text=f"{progress:.1f}%")
                        
                        size_mb = current_size / (1024 * 1024)
                        self.log(f"📦 已生成: {output_file.name} ({size_mb:.2f}MB)")

            if not self.stop_flag:
                self.log("✅ 处理完成!")
                messagebox.showinfo("完成", "文件处理已完成!")
            else:
                self.log("⚠️ 处理已停止", error=True)
                
        except Exception as e:
            self.log(f"❌ 错误: {str(e)}", error=True)
            messagebox.showerror("错误", f"处理文件时出错: {str(e)}")
        finally:
            self.is_processing = False
            self.progress_label.config(text="0%")
            
    def start_processing(self) -> None:
        if self.is_processing:
            messagebox.showwarning("警告", "已有处理任务正在进行中")
            return
            
        config = self.validate_inputs()
        if not config:
            return
            
        self.is_processing = True
        self.stop_flag = False
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.log_text.delete(1.0, tk.END)
        
        self.log("🚀 开始处理文件...")
        thread = threading.Thread(target=self.process_file, args=(config,))
        thread.daemon = True
        thread.start()
        
    def stop_processing(self) -> None:
        if self.is_processing:
            self.stop_flag = True
            self.log("⏹️ 正在停止处理...", error=True)

    def _create_settings_controls(self, parent):
        # File Type Selection
        ttk.Label(parent,
                 text="文件类型:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Combobox(parent,
                    textvariable=self.file_type,
                    values=["mp4", "mp3"],
                    state="readonly",
                    width=5).pack(side='left', padx=(0, 10))
        
        # Initial Size
        ttk.Label(parent,
                 text="初始大小:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(parent,
                 textvariable=self.initial_size_var,
                 width=8).pack(side='left', padx=(0, 5))
        
        ttk.Combobox(parent,
                    textvariable=self.size_unit,
                    values=["GB", "MB", "KB"],
                    state="readonly",
                    width=5).pack(side='left', padx=(0, 10))
        
        # Step Reduction
        ttk.Label(parent,
                 text="递减步长:",
                 style='Custom.TLabel').pack(side='left', padx=(0, 5))
        
        ttk.Entry(parent,
                 textvariable=self.step_reduction_var,
                 width=8).pack(side='left', padx=(0, 5))
        
        ttk.Label(parent,
                 text="KB",
                 style='Custom.TLabel').pack(side='left')

class LanzouAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Content-Type': 'application/json'
        }
        self.cookies = {}
        self.is_logged_in = False
        self.folder_id = -1
        self.api_base_url = 'http://localhost:3000/api'
        self.check_server_connection()
        
    def check_server_connection(self):
        """检查 Node.js 服务器是否正常运行"""
        try:
            response = self.session.get(f'{self.api_base_url}/health')
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'ok':
                    print("Node.js 服务器连接正常")
                    return True
                else:
                    print(f"Node.js 服务器状态异常: {result}")
                    return False
            else:
                print(f"Node.js 服务器连接异常: HTTP {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("无法连接到 Node.js 服务器，请确保服务器已启动")
            print("请在命令行中运行: node lanzou_server.js")
            raise Exception("Node.js 服务器未运行")
            
    def login(self, username: str, password: str) -> bool:
        """登录蓝奏云账号"""
        try:
            print("正在尝试登录...")
            response = self.session.post(
                f'{self.api_base_url}/login',
                json={'username': username, 'password': password}
            )
            
            if response.status_code != 200:
                print(f"登录请求失败: HTTP {response.status_code}")
                return False
                
            result = response.json()
            
            if result.get('success'):
                self.is_logged_in = True
                folders = []
                for folder in result.get('data', []):
                    if isinstance(folder, dict):
                        folders.append({
                            'name': folder.get('name', ''),
                            'id': folder.get('fol_id', ''),
                            'parent_id': folder.get('pid', '')
                        })
                print(f"成功获取到 {len(folders)} 个文件夹")
                return folders
            else:
                print(f"获取文件夹列表失败: {result.get('message')}")
                return []
                
        except Exception as e:
            print(f"获取文件夹列表失败: {str(e)}")
            return []

    def get_file_list(self, folder_id: str = '') -> list:
        """获取文件列表"""
        if not self.is_logged_in:
            return []

        try:
            print(f"正在获取文件夹 {folder_id} 的文件列表...")
            response = self.session.get(
                f'{self.api_base_url}/files',
                params={'folder_id': folder_id}
            )
            result = response.json()
            
            if result.get('success'):
                files = []
                for item in result.get('data', []):
                    if isinstance(item, dict):
                        file_info = {
                            'name': item.get('name', ''),
                            'id': item.get('id', ''),
                            'size': item.get('size', ''),
                            'time': item.get('time', ''),
                            'downs': item.get('downs', '0'),
                            'is_folder': item.get('folder_id', '-1') != '-1'
                        }
                        files.append(file_info)
                print(f"成功获取到 {len(files)} 个文件")
                return files
            else:
                print(f"获取文件列表失败: {result.get('message')}")
                return []
                
        except Exception as e:
            print(f"获取文件列表失败: {str(e)}")
            return []

    def get_download_url(self, file_id: str) -> str:
        """获取文件下载链接"""
        if not self.is_logged_in:
            return ""

        try:
            # 第一步：获取下载页面
            url = f'https://pc.woozooo.com/mydisk.php?item=files&action=down&id={file_id}'
            response = self.session.get(url)
            
            # 第二步：解析页面获取sign参数
            sign_match = re.search(r"sign\s*=\s*'([^']+)'", response.text)
            if not sign_match:
                return ""
            
            sign = sign_match.group(1)
            
            # 第三步：获取实际下载链接
            ajax_url = 'https://pc.woozooo.com/ajaxm.php'
            params = {
                "action": "downprocess",
                "sign": sign,
                "ves": 1
            }
            
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Referer': url,
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            response = self.session.post(ajax_url, data=params, headers=headers)
            result = response.json()
            
            if result.get('zt') == 1:
                return result.get('dom', '') + '/file/' + result.get('url', '')
            return ""
            
        except Exception as e:
            print(f"获取下载链接失败: {str(e)}")
            return ""

    def download_file(self, file_id: str, save_path: str) -> bool:
        """下载文件"""
        download_url = self.get_download_url(file_id)
        if not download_url:
            return False

        try:
            response = self.session.get(download_url, stream=True)
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            print(f"下载文件失败: {str(e)}")
            return False

    def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        if not self.is_logged_in:
            return False
        
        try:
            url = 'https://pc.woozooo.com/doupload.php'
            params = {
                "task": "6",
                "file_id": file_id
            }
            
            response = self.session.get(url, params=params)
            result = response.json()
            
            return result.get('zt') == 1
        
        except Exception as e:
            print(f"删除文件失败: {str(e)}")
            return False

    def create_folder(self, folder_name: str) -> bool:
        """创建文件夹"""
        if not self.is_logged_in:
            return False
        
        try:
            url = 'https://pc.woozooo.com/doupload.php'
            params = {
                "task": "2",
                "folder_name": folder_name,
                "parent_id": "0"
            }
            
            response = self.session.get(url, params=params)
            result = response.json()
            
            return result.get('zt') == 1
        
        except Exception as e:
            print(f"创建文件夹失败: {str(e)}")
            return False

    def get_share_url(self, file_id: str) -> str:
        """获取分享链接"""
        if not self.is_logged_in:
            return ""
        
        try:
            url = 'https://pc.woozooo.com/doupload.php'
            params = {
                "task": "22",
                "file_id": file_id
            }
            
            response = self.session.get(url, params=params)
            result = response.json()
            
            if result.get('zt') == 1:
                return f"https://wwp.lanzouw.com/{file_id}"
            return ""
        
        except Exception as e:
            print(f"获取分享链接失败: {str(e)}")
            return ""

    def get_recycle_bin(self) -> list:
        """获取回收站文件列表"""
        if not self.is_logged_in:
            return []
        
        try:
            url = 'https://pc.woozooo.com/doupload.php'
            params = {
                "task": "recycle_bin",
                "t": str(int(time.time() * 1000))
            }
            
            response = self.session.get(url, params=params)
            result = response.json()
            
            if result.get('zt') == 1:
                files = []
                for item in result.get('text', []):
                    if isinstance(item, dict):
                        files.append({
                            'name': item.get('name_all', ''),
                            'id': item.get('id', ''),
                            'size': item.get('size', ''),
                            'time': item.get('time', ''),
                            'is_folder': item.get('folder_id', '-1') != '-1'
                        })
                return files
            return []
        except Exception as e:
            print(f"获取回收站列表失败: {str(e)}")
            return []

    def restore_file(self, file_id: str) -> bool:
        """从回收站恢复文件"""
        if not self.is_logged_in:
            return False
        
        try:
            url = 'https://pc.woozooo.com/doupload.php'
            params = {
                "task": "restore",
                "file_id": file_id
            }
            
            response = self.session.get(url, params=params)
            result = response.json()
            
            return result.get('zt') == 1
        except Exception as e:
            print(f"恢复文件失败: {str(e)}")
            return False

    def clear_recycle_bin(self) -> bool:
        """清空回收站"""
        if not self.is_logged_in:
            return False
        
        try:
            url = 'https://pc.woozooo.com/doupload.php'
            params = {
                "task": "clean_recycle"
            }
            
            response = self.session.get(url, params=params)
            result = response.json()
            
            return result.get('zt') == 1
        except Exception as e:
            print(f"清空回收站失败: {str(e)}")
            return False

if __name__ == "__main__":
    app = MainApplication()
    app.run()
    app.run()