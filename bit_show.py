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
        
        # 如果没有字段信息,隐藏Canvas
        if not register_data or not register_data.get('fields'):
            self.bit_diagram_canvas.pack_forget()
            return
        
        # 显示Canvas并清空
        self.bit_diagram_canvas.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5, before=self.detail_text)
        self.bit_diagram_canvas.delete('all')
        
        # 获取寄存器大小
        reg_size = int(register_data.get('size', '32'))
        fields = register_data['fields']
        
        # Canvas尺寸
        canvas_width = self.bit_diagram_canvas.winfo_width()
        if canvas_width <= 1:  # Canvas未初始化
            canvas_width = 340  # 默认宽度
        canvas_height = 120
        
        # 边距和布局参数
        margin_left = 10
        margin_right = 10
        margin_top = 10
        bit_height = 35
        
        # 计算可用宽度和每位的宽度
        available_width = canvas_width - margin_left - margin_right
        bit_width = available_width / reg_size
        
        # 绘制位号 (顶部)
        y_bit_number = margin_top
        for bit in range(reg_size):
            x = margin_left + (reg_size - 1 - bit) * bit_width
            # 每隔4位或8位显示位号
            if bit % 8 == 0 or bit == reg_size - 1:
                self.bit_diagram_canvas.create_text(x + bit_width/2, y_bit_number, 
                                                    text=str(bit), 
                                                    font=('Arial', 7), 
                                                    fill='#666')
        
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
            
            # 绘制字段框
            self.bit_diagram_canvas.create_rectangle(x1, y_field, x2, y_field + bit_height,
                                                     fill=color, outline='#333', width=1)
            
            # 绘制字段名称 (如果宽度足够)
            field_width = x2 - x1
            if field_width > 20:  # 只有宽度足够时才显示名称
                # 计算文本长度,如果太长则缩短
                display_name = field_name
                if len(display_name) > 8 and field_width < 60:
                    display_name = field_name[:6] + '..'
                
                self.bit_diagram_canvas.create_text((x1 + x2) / 2, y_field + bit_height/2 - 5,
                                                   text=display_name, 
                                                   font=('Arial', 7, 'bold'), 
                                                   fill='#000')
            
            # 绘制访问类型
            if field_width > 15:
                access_short = access_type.replace('read-write', 'rw').replace('read-only', 'r').replace('write-only', 'w')
                self.bit_diagram_canvas.create_text((x1 + x2) / 2, y_field + bit_height/2 + 8,
                                                   text=access_short, 
                                                   font=('Arial', 6), 
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
                                                           font=('Arial', 6), 
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
                                                   font=('Arial', 6), 
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
            
            if (x2 - x1) > 20:
                self.bit_diagram_canvas.create_text((x1 + x2) / 2, y_bit_range,
                                                   text=bit_range, 
                                                   font=('Arial', 6), 
                                                   fill='#333')
