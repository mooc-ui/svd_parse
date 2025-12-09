#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF寄存器信息提取工具
从Infineon TLE987x User Manual PDF中提取寄存器的详细信息
"""

import json
import re
import os
from collections import defaultdict

try:
    import pdfplumber
except ImportError:
    print("错误：缺少pdfplumber库")
    print("请运行: pip install pdfplumber")
    exit(1)


class PDFRegisterExtractor:
    """PDF寄存器信息提取器"""
    
    def __init__(self, pdf_path):
        """
        初始化提取器
        
        Args:
            pdf_path: PDF文件路径
        """
        self.pdf_path = pdf_path
        self.registers = {}
        
    def extract_all(self):
        """提取所有寄存器信息"""
        print(f"正在打开PDF文件: {self.pdf_path}")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"PDF总页数: {total_pages}")
            
            current_register = None
            register_section = False
            description_buffer = []
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"处理第 {page_num}/{total_pages} 页...")
                
                # 提取文本
                text = page.extract_text()
                if not text:
                    continue
                
                # 提取表格
                tables = page.extract_tables()
                
                # 处理文本内容
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    # 检测寄存器章节标题（通常包含寄存器名称和地址）
                    # 例如: "10.4.1 SCU_SYSSTAT - System Status Register (0x50005040)"
                    reg_match = re.search(
                        r'(\d+\.\d+\.?\d*)\s+([A-Z_][A-Z0-9_]*)\s*[-–]\s*([^(]+?)\s*\(?0x([0-9A-Fa-f]+)\)?',
                        line
                    )
                    
                    if reg_match:
                        # 保存之前的寄存器信息
                        if current_register and description_buffer:
                            if current_register not in self.registers:
                                self.registers[current_register] = {}
                            self.registers[current_register]['description'] = ' '.join(description_buffer).strip()
                            description_buffer = []
                        
                        # 开始新的寄存器
                        section_num = reg_match.group(1)
                        reg_name = reg_match.group(2)
                        reg_desc_title = reg_match.group(3).strip()
                        reg_addr = reg_match.group(4)
                        
                        current_register = reg_name
                        register_section = True
                        
                        print(f"  发现寄存器: {reg_name} @ 0x{reg_addr}")
                        
                        self.registers[reg_name] = {
                            'name': reg_name,
                            'address': f'0x{reg_addr.upper()}',
                            'title': reg_desc_title,
                            'section': section_num,
                            'description': '',
                            'reset_value': '',
                            'notes': [],
                            'fields': {}
                        }
                        continue
                    
                    # 收集描述信息
                    if register_section and current_register:
                        # 检测复位值
                        reset_match = re.search(r'Reset\s+[Vv]alue[:\s]+0x([0-9A-Fa-f]+)', line, re.IGNORECASE)
                        if reset_match:
                            self.registers[current_register]['reset_value'] = f"0x{reset_match.group(1).upper()}"
                            continue
                        
                        # 检测注意事项
                        if re.match(r'Note[:\s]', line, re.IGNORECASE):
                            self.registers[current_register]['notes'].append(line)
                            continue
                        
                        # 收集普通描述文本
                        if line and not line.startswith('Table') and not re.match(r'^\d+\.', line):
                            # 避免收集页眉页脚
                            if len(line) > 20 and not line.lower().startswith('user manual'):
                                description_buffer.append(line)
                
                # 处理表格（位字段信息）
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # 检查是否是寄存器位字段表格
                    # 通常表头包含: Bit, Field, Access, Description等
                    header = [str(cell).lower() if cell else '' for cell in table[0]]
                    
                    # 查找列索引
                    bit_col = -1
                    field_col = -1
                    access_col = -1
                    desc_col = -1
                    reset_col = -1
                    
                    for idx, h in enumerate(header):
                        if 'bit' in h:
                            bit_col = idx
                        elif 'field' in h or 'name' in h:
                            field_col = idx
                        elif 'access' in h or 'type' in h:
                            access_col = idx
                        elif 'description' in h or 'function' in h:
                            desc_col = idx
                        elif 'reset' in h or 'value' in h:
                            reset_col = idx
                    
                    # 如果找到了关键列，则处理位字段
                    if bit_col >= 0 and field_col >= 0 and current_register:
                        for row in table[1:]:  # 跳过表头
                            if not row or len(row) <= max(bit_col, field_col):
                                continue
                            
                            bit_range = str(row[bit_col] if bit_col < len(row) else '')
                            field_name = str(row[field_col] if field_col < len(row) else '')
                            access = str(row[access_col] if access_col >= 0 and access_col < len(row) else '')
                            description = str(row[desc_col] if desc_col >= 0 and desc_col < len(row) else '')
                            reset_val = str(row[reset_col] if reset_col >= 0 and reset_col < len(row) else '')
                            
                            # 清理数据
                            bit_range = bit_range.strip()
                            field_name = field_name.strip()
                            access = access.strip()
                            description = description.strip()
                            reset_val = reset_val.strip()
                            
                            # 验证数据有效性
                            if field_name and field_name not in ['None', '-', ''] and bit_range:
                                # 解析位范围
                                bit_match = re.search(r'(\d+)(?::(\d+))?', bit_range)
                                if bit_match:
                                    self.registers[current_register]['fields'][field_name] = {
                                        'bit_range': bit_range,
                                        'access': access if access else 'R/W',
                                        'description': description,
                                        'reset_value': reset_val
                                    }
                                    print(f"    - 位字段: {field_name} [{bit_range}]")
            
            # 保存最后一个寄存器的描述
            if current_register and description_buffer:
                if current_register in self.registers:
                    self.registers[current_register]['description'] = ' '.join(description_buffer).strip()
        
        print(f"\n提取完成！共找到 {len(self.registers)} 个寄存器")
        return self.registers
    
    def save_to_json(self, output_file='register_descriptions.json'):
        """
        保存到JSON文件
        
        Args:
            output_file: 输出文件路径
        """
        print(f"\n正在保存到: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'source': os.path.basename(self.pdf_path),
                'registers': self.registers
            }, f, indent=2, ensure_ascii=False)
        
        print(f"保存成功！")
    
    def print_summary(self):
        """打印提取摘要"""
        print("\n=== 提取摘要 ===")
        print(f"总寄存器数: {len(self.registers)}")
        
        total_fields = sum(len(reg.get('fields', {})) for reg in self.registers.values())
        print(f"总位字段数: {total_fields}")
        
        regs_with_desc = sum(1 for reg in self.registers.values() if reg.get('description'))
        print(f"有描述的寄存器: {regs_with_desc}")
        
        regs_with_reset = sum(1 for reg in self.registers.values() if reg.get('reset_value'))
        print(f"有复位值的寄存器: {regs_with_reset}")
        
        print("\n前5个寄存器:")
        for i, (name, info) in enumerate(list(self.registers.items())[:5], 1):
            print(f"{i}. {name} @ {info.get('address', 'N/A')}")
            print(f"   标题: {info.get('title', 'N/A')}")
            print(f"   位字段数: {len(info.get('fields', {}))}")


def main():
    """主函数"""
    # PDF文件路径
    pdf_file = 'Infineon-TLE987x-UserManual-v01_91-EN.pdf'
    
    # 检查文件是否存在
    if not os.path.exists(pdf_file):
        print(f"错误: 文件不存在 - {pdf_file}")
        print("请确保PDF文件在当前目录下")
        return
    
    # 创建提取器
    extractor = PDFRegisterExtractor(pdf_file)
    
    # 提取信息
    try:
        extractor.extract_all()
        
        # 打印摘要
        extractor.print_summary()
        
        # 保存到JSON
        extractor.save_to_json()
        
        print("\n提取完成！请查看 register_descriptions.json 文件")
        
    except Exception as e:
        print(f"\n错误: 提取过程中发生异常")
        print(f"详细信息: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
