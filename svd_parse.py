#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVD文件解析脚本
解析ARM CMSIS-SVD格式文件，提取外设和寄存器信息
"""

import xml.etree.ElementTree as ET
import sys


def parse_svd(svd_file):
    """
    解析SVD文件
    
    Args:
        svd_file: SVD文件路径
        
    Returns:
        dict: 包含设备信息的字典
    """
    try:
        tree = ET.parse(svd_file)
        root = tree.getroot()
        
        device_info = {
            'name': root.find('name').text if root.find('name') is not None else 'Unknown',
            'peripherals': []
        }
        
        peripherals_elem = root.find('peripherals')
        if peripherals_elem is None:
            print("未找到peripherals节点")
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
                    
                    if reg_name is None:
                        continue
                    
                    # 计算绝对地址
                    base_addr = int(peripheral_data['base_address'], 16)
                    offset = int(reg_offset.text, 16) if reg_offset is not None else 0
                    absolute_addr = base_addr + offset
                    
                    register_data = {
                        'name': reg_name.text,
                        'description': reg_desc.text if reg_desc is not None else '',
                        'offset': reg_offset.text if reg_offset is not None else '0x0',
                        'address': f'0x{absolute_addr:08X}'
                    }
                    
                    peripheral_data['registers'].append(register_data)
                
            device_info['peripherals'].append(peripheral_data)
        
        return device_info
        
    except ET.ParseError as e:
        print(f"XML解析错误: {e}")
        return None
    except Exception as e:
        print(f"解析错误: {e}")
        return None


def print_device_tree(device_info):
    """
    以树形结构打印设备信息
    
    Args:
        device_info: 设备信息字典
    """
    if not device_info:
        print("没有可显示的设备信息")
        return
    
    print(f"╔═══════════════════════════════════════════════════════════════════")
    print(f"║ Device: {device_info['name']}")
    print(f"╠═══════════════════════════════════════════════════════════════════")
    print(f"║ {'名称':<25} {'寄存器数量':<15} {'描述'}")
    print(f"╠═══════════════════════════════════════════════════════════════════")
    
    for peripheral in device_info['peripherals']:
        reg_count = len(peripheral['registers'])
        print(f"║ ├─ {peripheral['name']:<22} {reg_count:<15} {peripheral['description'][:50]}")
        
        for idx, register in enumerate(peripheral['registers']):
            is_last = (idx == len(peripheral['registers']) - 1)
            prefix = "   └──" if is_last else "   ├──"
            reg_info = f"{register['name']:<20} @ {register['address']}"
            print(f"║ {prefix} {reg_info:<45} {register['description'][:30]}")
    
    print(f"╚═══════════════════════════════════════════════════════════════════")


def export_to_file(device_info, output_file):
    """
    将解析结果导出到文件
    
    Args:
        device_info: 设备信息字典
        output_file: 输出文件路径
    """
    if not device_info:
        print("没有可导出的设备信息")
        return
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Device: {device_info['name']}\n")
        f.write("=" * 100 + "\n\n")
        
        for peripheral in device_info['peripherals']:
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
    
    print(f"结果已导出到: {output_file}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python svd_parse.py <svd文件路径> [输出文件路径]")
        print("示例: python svd_parse.py TLE987x.svd output.txt")
        return
    
    svd_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"正在解析SVD文件: {svd_file}")
    device_info = parse_svd(svd_file)
    
    if device_info:
        print(f"\n解析成功！")
        print(f"设备名称: {device_info['name']}")
        print(f"外设数量: {len(device_info['peripherals'])}")
        total_regs = sum(len(p['registers']) for p in device_info['peripherals'])
        print(f"寄存器总数: {total_regs}\n")
        
        # 打印树形结构
        print_device_tree(device_info)
        
        # 如果指定了输出文件，则导出
        if output_file:
            export_to_file(device_info, output_file)
    else:
        print("解析失败！")


if __name__ == "__main__":
    main()
