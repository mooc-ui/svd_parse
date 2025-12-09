#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVD文件图形化查看器
使用Tkinter创建GUI界面，以树形结构显示SVD文件内容
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import xml.etree.ElementTree as ET
import os
import re
from difflib import SequenceMatcher


class SVDViewerGUI:
    """SVD文件图形化查看器主类"""
    
    def __init__(self, root):
        """初始化GUI界面"""
        self.root = root
        self.root.title("SVD 文件查看器")
        self.root.geometry("1200x700")
        
        # 当前加载的设备信息
        self.device_info = None
        self.current_file = None
        self.current_register_data = None  # 保存当前显示的寄存器数据
        
        # 搜索选项（复选框）
        self.match_case = tk.BooleanVar(value=False)
        self.match_whole_word = tk.BooleanVar(value=False)
        self.use_regex = tk.BooleanVar(value=False)
        self.filter_mode = tk.BooleanVar(value=False)  # 过滤模式
        
        # 跟踪搜索高亮标签
        self.search_tags = []
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        """创建所有GUI组件"""
        
        # ====== 顶部工具栏 ======
        toolbar = tk.Frame(self.root, relief=tk.RAISED, borderwidth=2)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # 打开文件按钮
        btn_open = tk.Button(toolbar, text="📂 打开SVD文件", command=self.open_file, 
                            font=("Arial", 10), bg="#4CAF50", fg="white", padx=10, pady=5)
        btn_open.pack(side=tk.LEFT, padx=5)
        
        # 展开所有按钮
        btn_expand = tk.Button(toolbar, text="➕ 展开所有", command=self.expand_all,
                              font=("Arial", 10), padx=10, pady=5)
        btn_expand.pack(side=tk.LEFT, padx=5)
        
        # 折叠所有按钮
        btn_collapse = tk.Button(toolbar, text="➖ 折叠所有", command=self.collapse_all,
                                font=("Arial", 10), padx=10, pady=5)
        btn_collapse.pack(side=tk.LEFT, padx=5)
        
        # 导出按钮
        btn_export = tk.Button(toolbar, text="💾 导出文本", command=self.export_to_text,
                              font=("Arial", 10), padx=10, pady=5)
        btn_export.pack(side=tk.LEFT, padx=5)
        
        # 文件名标签
        self.file_label = tk.Label(toolbar, text="未加载文件", font=("Arial", 10), fg="gray")
        self.file_label.pack(side=tk.RIGHT, padx=10)
        
        # ====== 搜索栏 ======
        search_frame = tk.Frame(self.root)
        search_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="🔍 搜索:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                               font=("Arial", 10), width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        btn_clear_search = tk.Button(search_frame, text="✖ 清除", 
                                     command=self.clear_search, font=("Arial", 9))
        btn_clear_search.pack(side=tk.LEFT, padx=5)
        
        # 搜索选项（复选框）
        options_frame = tk.Frame(search_frame)
        options_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        cb_case = tk.Checkbutton(options_frame, text="Aa", variable=self.match_case,
                                font=("Arial", 9), command=self.on_search_option_change)
        cb_case.pack(side=tk.LEFT, padx=2)
        
        cb_word = tk.Checkbutton(options_frame, text="|w|", variable=self.match_whole_word,
                                font=("Arial", 9), command=self.on_search_option_change)
        cb_word.pack(side=tk.LEFT, padx=2)
        
        cb_regex = tk.Checkbutton(options_frame, text=".*", variable=self.use_regex,
                                 font=("Arial", 9), command=self.on_search_option_change)
        cb_regex.pack(side=tk.LEFT, padx=2)
        
        # 分隔线
        tk.Label(search_frame, text="|", font=("Arial", 9), fg="gray").pack(side=tk.LEFT, padx=5)
        
        # 过滤模式复选框
        cb_filter = tk.Checkbutton(search_frame, text="📍 过滤", variable=self.filter_mode,
                                  font=("Arial", 9), command=self.on_search_option_change)
        cb_filter.pack(side=tk.LEFT, padx=2)
        
        # 统计信息标签
        self.stats_label = tk.Label(search_frame, text="", font=("Arial", 9), fg="blue")
        self.stats_label.pack(side=tk.RIGHT, padx=10)
        
        # ====== 主内容区域 ======
        main_frame = tk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧：树形视图
        tree_frame = tk.Frame(main_frame)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(tree_frame, text="外设与寄存器树形结构", 
                font=("Arial", 11, "bold")).pack(side=tk.TOP, pady=5)
        
        # 创建树形控件
        tree_scroll_y = tk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        tree_scroll_x = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        self.tree = ttk.Treeview(tree_frame, 
                                yscrollcommand=tree_scroll_y.set,
                                xscrollcommand=tree_scroll_x.set,
                                selectmode='browse')
        
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 配置列
        self.tree['columns'] = ('value', 'address', 'description')
        self.tree.column('#0', width=250, minwidth=200)
        self.tree.column('value', width=150, minwidth=100)
        self.tree.column('address', width=120, minwidth=100)
        self.tree.column('description', width=350, minwidth=200)
        
        self.tree.heading('#0', text='名称', anchor=tk.W)
        self.tree.heading('value', text='数值/数量', anchor=tk.W)
        self.tree.heading('address', text='地址', anchor=tk.W)
        self.tree.heading('description', text='描述', anchor=tk.W)
        
        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        # 右侧：详细信息面板
        detail_frame = tk.Frame(main_frame, width=350, relief=tk.RIDGE, borderwidth=2)
        detail_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        detail_frame.pack_propagate(False)
        
        tk.Label(detail_frame, text="详细信息", 
                font=("Arial", 11, "bold")).pack(side=tk.TOP, pady=5)
        
        self.detail_text = scrolledtext.ScrolledText(detail_frame, 
                                                     wrap=tk.WORD, 
                                                     font=("Courier New", 9),
                                                     bg="#f5f5f5")
        self.detail_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ====== 底部状态栏 ======
        status_bar = tk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(status_bar, text="就绪", 
                                     font=("Arial", 9), anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        # ====== 寄存器位图区域（底部） ======
        bit_diagram_frame = tk.Frame(self.root, relief=tk.RIDGE, borderwidth=2)
        bit_diagram_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=10, pady=(0, 5), before=status_bar)
        bit_diagram_frame.pack_forget()  # Hide frame initially
        
        self.bit_diagram_canvas = tk.Canvas(bit_diagram_frame, height=150, bg='white')
        self.bit_diagram_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
    def open_file(self):
        """打开SVD文件"""
        file_path = filedialog.askopenfilename(
            title="选择SVD文件",
            filetypes=[("SVD文件", "*.svd"), ("XML文件", "*.xml"), ("所有文件", "*.*")]
        )
        
        if file_path:
            self.load_svd_file(file_path)
    
    def load_svd_file(self, file_path):
        """加载并解析SVD文件"""
        try:
            self.status_label.config(text=f"正在加载 {os.path.basename(file_path)}...")
            self.root.update()
            
            # 解析SVD文件
            self.device_info = self.parse_svd(file_path)
            
            if self.device_info:
                self.current_file = file_path
                self.file_label.config(text=f"📄 {os.path.basename(file_path)}", fg="green")
                
                # 显示到树形控件
                self.populate_tree()
                
                # 更新统计信息
                total_regs = sum(len(p['registers']) for p in self.device_info['peripherals'])
                self.stats_label.config(
                    text=f"外设: {len(self.device_info['peripherals'])} | 寄存器: {total_regs}"
                )
                
                self.status_label.config(text=f"成功加载 {os.path.basename(file_path)}")
                messagebox.showinfo("成功", f"成功加载SVD文件！\n\n外设数量: {len(self.device_info['peripherals'])}\n寄存器总数: {total_regs}")
            else:
                self.status_label.config(text="加载失败")
                messagebox.showerror("错误", "无法解析SVD文件")
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.status_label.config(text="加载出错")
            messagebox.showerror("错误", f"加载文件时出错:\n{str(e)}\n\n详细信息:\n{error_details}")
    
    def parse_svd(self, svd_file):
        """解析SVD文件（与命令行版本相同）"""
        try:
            tree = ET.parse(svd_file)
            root = tree.getroot()
            
            device_info = {
                'name': root.find('name').text if root.find('name') is not None else 'Unknown',
                'vendor': root.find('vendor').text if root.find('vendor') is not None else '',
                'version': root.find('version').text if root.find('version') is not None else '',
                'description': root.find('description').text if root.find('description') is not None else '',
                'peripherals': []
            }
            
            peripherals_elem = root.find('peripherals')
            if peripherals_elem is None:
                return device_info
            
            for peripheral in peripherals_elem.findall('peripheral'):
                peripheral_name = peripheral.find('name')
                peripheral_desc = peripheral.find('description')
                peripheral_base = peripheral.find('baseAddress')
                
                if peripheral_name is None:
                    continue
                
                peripheral_data = {
                    'name': peripheral_name.text,
                    'description': peripheral_desc.text if peripheral_desc is not None else '',
                    'base_address': peripheral_base.text if peripheral_base is not None else '0x0',
                    'registers': []
                }
                
                # 解析寄存器
                registers_elem = peripheral.find('registers')
                if registers_elem is not None:
                    for register in registers_elem.findall('register'):
                        reg_name = register.find('name')
                        reg_desc = register.find('description')
                        reg_offset = register.find('addressOffset')
                        reg_size = register.find('size')
                        reg_reset = register.find('resetValue')
                        
                        if reg_name is None:
                            continue
                        
                        # 计算绝对地址
                        base_addr = int(peripheral_data['base_address'], 16)
                        offset = int(reg_offset.text, 16) if reg_offset is not None else 0
                        absolute_addr = base_addr + offset
                        
                        # 解析size字段（支持十六进制和十进制）
                        size_str = reg_size.text if reg_size is not None else '32'
                        try:
                            size_value = int(size_str, 0)  # base 0 自动检测进制
                        except (ValueError, TypeError):
                            size_value = 32
                        
                        register_data = {
                            'name': reg_name.text,
                            'description': reg_desc.text if reg_desc is not None else '',
                            'offset': reg_offset.text if reg_offset is not None else '0x0',
                            'address': f'0x{absolute_addr:08X}',
                            'size': str(size_value),  # 转换为字符串存储
                            'reset_value': reg_reset.text if reg_reset is not None else '',
                            'fields': []
                        }
                        
                        # 解析字段信息（支持多种格式）
                        fields_elem = register.find('fields')
                        if fields_elem is not None:
                            for field in fields_elem.findall('field'):
                                field_name = field.find('name')
                                field_desc = field.find('description')
                                field_access = field.find('access')
                                
                                if field_name is None:
                                    continue
                                
                                # 尝试多种位域定义格式
                                lsb = None
                                msb = None
                                
                                # 格式1: 使用 lsb 和 msb 标签（如 TLE987x.svd）
                                field_lsb = field.find('lsb')
                                field_msb = field.find('msb')
                                if field_lsb is not None and field_msb is not None:
                                    lsb = int(field_lsb.text)
                                    msb = int(field_msb.text)
                                
                                # 格式2: 使用 bitRange 标签（如 NSUC1602.svd）
                                # bitRange 格式: "[msb:lsb]" 例如 "[7:0]"
                                elif field.find('bitRange') is not None:
                                    bit_range = field.find('bitRange').text
                                    # 解析 [msb:lsb] 格式
                                    bit_range = bit_range.strip('[]')
                                    if ':' in bit_range:
                                        msb_str, lsb_str = bit_range.split(':')
                                        msb = int(msb_str.strip())
                                        lsb = int(lsb_str.strip())
                                    else:
                                        # 单个位，如 "[5]"
                                        lsb = msb = int(bit_range.strip())
                                
                                # 格式3: 使用 bitOffset 和 bitWidth 标签
                                elif field.find('bitOffset') is not None:
                                    bit_offset_elem = field.find('bitOffset')
                                    bit_width_elem = field.find('bitWidth')
                                    
                                    if bit_offset_elem is not None and bit_offset_elem.text:
                                        bit_offset = int(bit_offset_elem.text)
                                        lsb = bit_offset
                                        
                                        if bit_width_elem is not None and bit_width_elem.text:
                                            bit_width = int(bit_width_elem.text)
                                            msb = bit_offset + bit_width - 1
                                        else:
                                            # 如果只有 bitOffset，假设为单位
                                            msb = lsb
                                
                                # 如果成功解析出位范围，添加字段
                                if lsb is not None and msb is not None:
                                    field_data = {
                                        'name': field_name.text,
                                        'description': field_desc.text if field_desc is not None else '',
                                        'lsb': lsb,
                                        'msb': msb,
                                        'access': field_access.text if field_access is not None else 'read-write'
                                    }
                                    register_data['fields'].append(field_data)

                        
                        peripheral_data['registers'].append(register_data)
                
                device_info['peripherals'].append(peripheral_data)
            
            return device_info
            
        except Exception as e:
            print(f"解析错误: {e}")
            return None
    
    def populate_tree(self):
        """填充树形控件"""
        # 清空现有内容
        self.tree.delete(*self.tree.get_children())
        
        if not self.device_info:
            return
        
        # 添加根节点（设备）
        device_name = self.device_info['name']
        device_desc = self.device_info.get('description', '')
        vendor = self.device_info.get('vendor', '')
        
        root_text = f"📱 {device_name}"
        if vendor:
            root_text += f" ({vendor})"
        
        device_node = self.tree.insert('', 'end', text=root_text,
                                      values=('', '', device_desc),
                                      tags=('device',))
        
        # 添加外设和寄存器
        for peripheral in self.device_info['peripherals']:
            # 外设节点
            periph_text = f"📦 {peripheral.get('name', 'Unknown')}"
            periph_desc = peripheral.get('description', '')
            periph_node = self.tree.insert(device_node, 'end', text=periph_text,
                                          values=(f"{len(peripheral.get('registers', []))} 个寄存器", 
                                                 peripheral.get('base_address', ''),
                                                 periph_desc if periph_desc else ''),
                                          tags=('peripheral',))
            
            # 寄存器节点
            for register in peripheral.get('registers', []):
                reg_text = f"📋 {register.get('name', 'Unknown')}"
                reg_desc = register.get('description', '')
                # 安全地截取描述文本
                desc_preview = reg_desc[:50] if reg_desc else ''
                self.tree.insert(periph_node, 'end', text=reg_text,
                               values=(f"{register.get('size', '32')} bits",
                                      register.get('address', ''),
                                      desc_preview),
                               tags=('register',))
        
        # 配置标签颜色
        self.tree.tag_configure('device', font=('Arial', 10, 'bold'))
        self.tree.tag_configure('peripheral', font=('Arial', 9, 'bold'), foreground='blue')
        self.tree.tag_configure('register', font=('Arial', 9))
    
    def on_tree_select(self, event):
        """树形控件选择事件"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        item_text = self.tree.item(item, 'text')
        item_values = self.tree.item(item, 'values')
        item_tags = self.tree.item(item, 'tags')
        
        # 清空详细信息
        self.detail_text.delete('1.0', tk.END)
        
        # 显示详细信息
        self.detail_text.insert('1.0', f"{'='*40}\n")
        self.detail_text.insert(tk.END, f"{item_text.replace('📱 ', '').replace('📦 ', '').replace('📋 ', '')}\n")
        self.detail_text.insert(tk.END, f"{'='*40}\n\n")
        
        if item_values:
            if len(item_values) > 0 and item_values[0]:
                self.detail_text.insert(tk.END, f"数值: {item_values[0]}\n")
            if len(item_values) > 1 and item_values[1]:
                self.detail_text.insert(tk.END, f"地址: {item_values[1]}\n")
            if len(item_values) > 2 and item_values[2]:
                self.detail_text.insert(tk.END, f"\n描述:\n{item_values[2]}\n")
        
        # 根据类型显示不同信息
        if 'register' in item_tags:
            self.detail_text.insert(tk.END, f"\n类型: 寄存器\n")
            # 尝试获取并绘制寄存器位图
            self.draw_register_bit_diagram(item)
        elif 'peripheral' in item_tags:
            self.detail_text.insert(tk.END, f"\n类型: 外设模块\n")
            self.bit_diagram_canvas.master.pack_forget()  # Hide canvas frame
        elif 'device' in item_tags:
            self.detail_text.insert(tk.END, f"\n类型: 设备\n")
            self.bit_diagram_canvas.master.pack_forget()  # Hide canvas frame
            if self.device_info:
                vendor = self.device_info.get('vendor', '')
                version = self.device_info.get('version', '')
                if vendor:
                    self.detail_text.insert(tk.END, f"厂商: {vendor}\n")
                if version:
                    self.detail_text.insert(tk.END, f"版本: {version}\n")
    
    def draw_register_bit_diagram(self, tree_item):
        """绘制寄存器位图"""
        # 查找对应的寄存器数据
        register_data = None
        item_text = self.tree.item(tree_item, 'text')
        reg_name = item_text.replace('📋 ', '')
        
        # 查找寄存器数据
        if self.device_info:
            for peripheral in self.device_info['peripherals']:
                for register in peripheral['registers']:
                    if register['name'] == reg_name:
                        register_data = register
                        break
                if register_data:
                    break
        
        # 如果没有字段信息,隐藏Canvas frame
        if not register_data or not register_data.get('fields'):
            self.bit_diagram_canvas.master.pack_forget()
            self.current_register_data = None
            return
        
        # 保存当前寄存器数据供点击事件使用
        self.current_register_data = register_data
        
        
        # 获取寄存器大小（支持十六进制和十进制）
        reg_size_str = register_data.get('size', '32')
        try:
            # 自动检测十六进制（0x前缀）或十进制
            reg_size = int(reg_size_str, 0)  # base 0 自动检测进制
        except (ValueError, TypeError):
            reg_size = 32  # 默认32位
        fields = register_data['fields']
        
        # 清空canvas并显示frame
        self.bit_diagram_canvas.delete('all')
        if not self.bit_diagram_canvas.master.winfo_ismapped():
            self.bit_diagram_canvas.master.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=10, pady=(0, 5), before=self.status_label.master)
        
        # Canvas尺寸
        canvas_width = self.bit_diagram_canvas.winfo_width()
        if canvas_width <= 1:  # Canvas未初始化
            canvas_width = 1180  # 默认宽度（更大）
        canvas_height = 150
        
        # 边距和布局参数
        margin_left = 20
        margin_right = 20
        margin_top = 20
        bit_height = 50
        
        # 计算可用宽度和每位的宽度
        available_width = canvas_width - margin_left - margin_right
        bit_width = available_width / reg_size
        
        # 绘制位号 (顶部)
        y_bit_number = margin_top
        for bit in range(reg_size):
            x = margin_left + (reg_size - 1 - bit) * bit_width
            # 每隔8位显示位号
            if bit % 8 == 0 or bit == reg_size - 1:
                self.bit_diagram_canvas.create_text(x + bit_width/2, y_bit_number, 
                                                    text=str(bit), 
                                                    font=('Arial', 9, 'bold'), 
                                                    fill='#333')
        
        # 绘制字段框
        y_field = margin_top + 15
        
        # 准备颜色列表
        field_colors = ['#E3F2FD', '#FFF3E0', '#F3E5F5', '#E8F5E9', '#FFF9C4', '#FCE4EC']
        
        # 创建位数组,标记哪些位已被使用
        bit_used = [False] * reg_size
        
        # 按字段绘制
        for idx, field in enumerate(fields):
            lsb = field['lsb']
            msb = field['msb']
            field_name = field['name']
            access_type = field.get('access', 'rw')
            
            # 标记使用的位
            for bit in range(lsb, msb + 1):
                if bit < reg_size:
                    bit_used[bit] = True
            
            # 计算字段框的位置和宽度
            x1 = margin_left + (reg_size - 1 - msb) * bit_width
            x2 = margin_left + (reg_size - lsb) * bit_width
            
            # 选择颜色
            color = field_colors[idx % len(field_colors)]
            
            # 绘制字段框（添加标签以便点击识别）
            field_rect = self.bit_diagram_canvas.create_rectangle(
                x1, y_field, x2, y_field + bit_height,
                fill=color, outline='#333', width=1,
                tags=f'field_{idx}'
            )
            
            # 绑定点击事件
            self.bit_diagram_canvas.tag_bind(f'field_{idx}', '<Button-1>', 
                                            lambda e, f=field: self.on_field_click(f))
            # 绑定鼠标悬停效果
            self.bit_diagram_canvas.tag_bind(f'field_{idx}', '<Enter>', 
                                            lambda e, tag=f'field_{idx}': self.on_field_enter(tag))
            self.bit_diagram_canvas.tag_bind(f'field_{idx}', '<Leave>', 
                                            lambda e, tag=f'field_{idx}': self.on_field_leave(tag))
            # 绘制字段名称 (如果宽度足够)
            field_width = x2 - x1
            if field_width > 15:  # 降低最小宽度要求
                # 显示完整字段名称,不截断
                self.bit_diagram_canvas.create_text((x1 + x2) / 2, y_field + bit_height/2 - 8,
                                                   text=field_name, 
                                                   font=('Arial', 8), 
                                                   fill='#000')
            
            # 绘制访问类型
            if field_width > 20:  # 提高访问类型显示的最小宽度
                access_short = access_type.replace('read-write', 'rw').replace('read-only', 'r').replace('write-only', 'w')
                self.bit_diagram_canvas.create_text((x1 + x2) / 2, y_field + bit_height/2 + 10,
                                                   text=access_short, 
                                                   font=('Arial', 7), 
                                                   fill='#666')
        
        # 绘制预留位(Reserved)
        current_reserved_start = None
        for bit in range(reg_size):
            if not bit_used[bit]:
                if current_reserved_start is None:
                    current_reserved_start = bit
            else:
                if current_reserved_start is not None:
                    # 绘制预留区域
                    x1 = margin_left + (reg_size - 1 - (bit - 1)) * bit_width
                    x2 = margin_left + (reg_size - current_reserved_start) * bit_width
                    
                    self.bit_diagram_canvas.create_rectangle(x1, y_field, x2, y_field + bit_height,
                                                            fill='#F5F5F5', outline='#999', 
                                                            width=1, dash=(2, 2))
                    
                    # 如果宽度足够,显示"RES"
                    if (x2 - x1) > 20:
                        self.bit_diagram_canvas.create_text((x1 + x2) / 2, y_field + bit_height/2,
                                                           text='RES', 
                                                           font=('Arial', 8), 
                                                           fill='#999')
                    
                    current_reserved_start = None
        
        # 处理最后的预留位
        if current_reserved_start is not None:
            x1 = margin_left
            x2 = margin_left + (reg_size - current_reserved_start) * bit_width
            
            self.bit_diagram_canvas.create_rectangle(x1, y_field, x2, y_field + bit_height,
                                                    fill='#F5F5F5', outline='#999', 
                                                    width=1, dash=(2, 2))
            
            if (x2 - x1) > 20:
                self.bit_diagram_canvas.create_text((x1 + x2) / 2, y_field + bit_height/2,
                                                   text='RES', 
                                                   font=('Arial', 8), 
                                                   fill='#999')
        
        # 在底部绘制位范围标签
        y_bit_range = y_field + bit_height + 10
        for field in fields:
            lsb = field['lsb']
            msb = field['msb']
            x1 = margin_left + (reg_size - 1 - msb) * bit_width
            x2 = margin_left + (reg_size - lsb) * bit_width
            
            if msb == lsb:
                bit_range = str(lsb)
            else:
                bit_range = f"{msb}:{lsb}"
            
            if (x2 - x1) > 15:
                self.bit_diagram_canvas.create_text((x1 + x2) / 2, y_bit_range,
                                                   text=bit_range, 
                                                   font=('Arial', 8, 'bold'), 
                                                   fill='#333')
    
    def on_field_click(self, field_data):
        """位域点击事件处理"""
        # 清空详细信息
        self.detail_text.delete('1.0', tk.END)
        
        # 显示位域详细信息
        self.detail_text.insert('1.0', f"{'='*40}\n")
        self.detail_text.insert(tk.END, f"位域: {field_data['name']}\n")
        self.detail_text.insert(tk.END, f"{'='*40}\n\n")
        
        # 位范围
        lsb = field_data['lsb']
        msb = field_data['msb']
        if msb == lsb:
            bit_range = f"Bit {lsb}"
        else:
            bit_range = f"Bits {msb}:{lsb}"
        self.detail_text.insert(tk.END, f"位范围: {bit_range}\n")
        
        # 位宽
        bit_width = msb - lsb + 1
        self.detail_text.insert(tk.END, f"位宽: {bit_width} bit(s)\n")
        
        # 访问类型
        access_type = field_data.get('access', 'read-write')
        access_map = {
            'read-write': '读写',
            'read-only': '只读',
            'write-only': '只写',
            'rw': '读写',
            'r': '只读',
            'w': '只写'
        }
        access_cn = access_map.get(access_type, access_type)
        self.detail_text.insert(tk.END, f"访问权限: {access_cn} ({access_type})\n")
        
        # 描述信息
        description = field_data.get('description', '')
        if description:
            self.detail_text.insert(tk.END, f"\n描述:\n{description}\n")
        
        # 如果有寄存器信息，也显示
        if self.current_register_data:
            self.detail_text.insert(tk.END, f"\n所属寄存器: {self.current_register_data['name']}\n")
            self.detail_text.insert(tk.END, f"寄存器地址: {self.current_register_data['address']}\n")
        
        self.detail_text.insert(tk.END, f"\n{'='*40}\n")
        self.detail_text.insert(tk.END, "提示: 点击位域可查看详细信息\n")
        
        # 更新状态栏
        self.status_label.config(text=f"已选择位域: {field_data['name']} [{bit_range}]")
    
    def on_field_enter(self, tag):
        """鼠标进入位域时的效果"""
        # 改变鼠标光标为手型
        self.bit_diagram_canvas.config(cursor='hand2')
        # 加粗边框
        items = self.bit_diagram_canvas.find_withtag(tag)
        for item in items:
            self.bit_diagram_canvas.itemconfig(item, width=2, outline='#000')
    
    def on_field_leave(self, tag):
        """鼠标离开位域时恢复"""
        # 恢复默认光标
        self.bit_diagram_canvas.config(cursor='')
        # 恢复边框
        items = self.bit_diagram_canvas.find_withtag(tag)
        for item in items:
            self.bit_diagram_canvas.itemconfig(item, width=1, outline='#333')


    def expand_all(self):
        """展开所有节点"""
        def expand_recursive(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                expand_recursive(child)
        
        for item in self.tree.get_children():
            expand_recursive(item)
        
        self.status_label.config(text="已展开所有节点")
    
    def collapse_all(self):
        """折叠所有节点"""
        def collapse_recursive(item):
            self.tree.item(item, open=False)
            for child in self.tree.get_children(item):
                collapse_recursive(child)
        
        for item in self.tree.get_children():
            collapse_recursive(item)
        
        self.status_label.config(text="已折叠所有节点")
    
    def on_search(self, *args):
        """搜索功能"""
        search_text = self.search_var.get()
        
        if not search_text:
            # 恢复所有项目
            self.populate_tree()
            return
        
        # 高亮匹配项
        self.highlight_search_results(search_text)
    
    def on_search_option_change(self):
        """搜索选项改变时重新搜索"""
        if self.search_var.get():
            self.on_search()
    
    def highlight_search_results(self, search_text):
        """搜索结果（支持过滤模式和高亮模式）"""
        # 清除之前的高亮
        for tag in self.search_tags:
            self.tree.tag_configure(tag, background='')
        self.search_tags = []
        
        # 搜索并高亮
        matches = []
        match_case = self.match_case.get()
        match_whole = self.match_whole_word.get()
        use_regex = self.use_regex.get()
        filter_enabled = self.filter_mode.get()  # 是否启用过滤模式
        
        # 编译正则表达式（如果启用正则）
        regex_pattern = None
        if use_regex:
            try:
                flags = 0 if match_case else re.IGNORECASE
                regex_pattern = re.compile(search_text, flags)
            except re.error as e:
                self.status_label.config(text=f"正则表达式错误: {str(e)}")
                return
        
        def is_match_text(text_to_search, pattern):
            """根据搜索选项判断是否匹配"""
            if use_regex:
                # 使用正则表达式
                return regex_pattern and regex_pattern.search(text_to_search) is not None
            else:
                # 普通文本搜索
                search_str = pattern if match_case else pattern.lower()
                target_str = text_to_search if match_case else text_to_search.lower()
                
                if match_whole:
                    # 整词匹配：使用单词边界
                    word_pattern = r'\b' + re.escape(search_str) + r'\b'
                    flags = 0 if match_case else re.IGNORECASE
                    return re.search(word_pattern, target_str, flags) is not None
                else:
                    # 包含匹配
                    return search_str in target_str
            return False
        
        # 收集所有节点和它们的匹配状态
        all_nodes = {}
        
        def collect_nodes(item):
            """递归收集所有节点"""
            item_text = self.tree.item(item, 'text')
            clean_text = item_text.replace('📱 ', '').replace('📦 ', '').replace('📋 ', '')
            is_match = is_match_text(clean_text, search_text)
            
            all_nodes[item] = {
                'match': is_match,
                'children': list(self.tree.get_children(item)),
                'parent': self.tree.parent(item)
            }
            
            for child in self.tree.get_children(item):
                collect_nodes(child)
        
        # 收集所有节点
        for root_item in self.tree.get_children():
            collect_nodes(root_item)
        
        # 确定哪些节点应该显示（匹配的节点 + 它们的所有父节点）
        visible_nodes = set()
        
        for item, info in all_nodes.items():
            if info['match']:
                matches.append(item)
                # 添加此节点及其所有父节点到可见集合
                current = item
                while current:
                    visible_nodes.add(current)
                    current = all_nodes[current]['parent'] if current in all_nodes else None
        
        # 如果启用过滤模式，隐藏不匹配的节点
        if filter_enabled:
            for item in all_nodes.keys():
                try:
                    if item not in visible_nodes:
                        self.tree.detach(item)
                except:
                    pass
        
        # 高亮匹配的节点
        for idx, item in enumerate(matches, 1):
            try:
                search_tag = f'search_{idx}'
                current_tags = list(self.tree.item(item, 'tags'))
                current_tags.append(search_tag)
                self.tree.item(item, tags=current_tags)
                self.tree.tag_configure(search_tag, background='yellow')
                self.search_tags.append(search_tag)
                
                # 展开所有父节点
                parent = self.tree.parent(item)
                while parent:
                    self.tree.item(parent, open=True)
                    parent = self.tree.parent(parent)
                # 展开匹配的外设节点
                if self.tree.get_children(item):
                    self.tree.item(item, open=True)
            except:
                pass
        
        # 更新状态显示
        options = []
        if match_case:
            options.append('Aa')
        if match_whole:
            options.append('|w|')
        if use_regex:
            options.append('.*')
        option_text = ' '.join(options) if options else '默认'
        self.status_label.config(text=f"[{option_text}] 找到 {len(matches)} 个匹配项")
    
    def clear_search(self):
        """清除搜索"""
        self.search_var.set('')
        self.populate_tree()
        self.status_label.config(text="搜索已清除")
    
    def export_to_text(self):
        """导出到文本文件"""
        if not self.device_info:
            messagebox.showwarning("警告", "请先加载SVD文件")
            return
        
        output_file = filedialog.asksaveasfilename(
            title="保存文本文件",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=f"{self.device_info['name']}_registers.txt"
        )
        
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"Device: {self.device_info['name']}\n")
                    f.write("=" * 100 + "\n\n")
                    
                    for peripheral in self.device_info['peripherals']:
                        f.write(f"\n外设: {peripheral['name']}\n")
                        f.write(f"基地址: {peripheral['base_address']}\n")
                        f.write(f"描述: {peripheral['description']}\n")
                        f.write(f"寄存器数量: {len(peripheral['registers'])}\n")
                        f.write("-" * 100 + "\n")
                        
                        if peripheral['registers']:
                            f.write(f"{'寄存器名称':<30} {'地址':<15} {'偏移':<15} {'描述'}\n")
                            f.write("-" * 100 + "\n")
                            
                            for register in peripheral['registers']:
                                f.write(f"{register['name']:<30} {register['address']:<15} "
                                       f"{register['offset']:<15} {register['description']}\n")
                        
                        f.write("\n")
                
                messagebox.showinfo("成功", f"已导出到:\n{output_file}")
                self.status_label.config(text=f"已导出到 {os.path.basename(output_file)}")
                
            except Exception as e:
                messagebox.showerror("错误", f"导出失败:\n{str(e)}")


def main():
    """主函数"""
    root = tk.Tk()
    app = SVDViewerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
