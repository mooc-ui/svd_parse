# SVD加载问题修复说明

## 修复的问题

### 问题1: NSUC1602.svd 加载错误
**错误信息**: `'NoneType' object is not subscriptable`

**原因**: 
- 代码直接访问字典键而不检查None值
- `register['description'][:50]` 当description为None时会报错

**解决方案**:
使用`.get()`方法并提供默认值：
```python
# 修改前
periph_text = f"📦 {peripheral['name']}"
desc = register['description'][:50]

# 修改后
periph_text = f"📦 {peripheral.get('name', 'Unknown')}"
reg_desc = register.get('description', '')
desc_preview = reg_desc[:50] if reg_desc else ''
```

### 问题2: STM32 SVD文件位域不显示
**原因**: 
- bitOffset/bitWidth解析逻辑不够健壮
- 没有检查元素是否存在就访问`.text`属性

**解决方案**:
改进解析逻辑：
```python
# 修改前
elif field.find('bitOffset') is not None and field.find('bitWidth') is not None:
    bit_offset = int(field.find('bitOffset').text)
    bit_width = int(field.find('bitWidth').text)

# 修改后  
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
            # 单位字段
            msb = lsb
```

## 改进的错误处理

### 详细的错误信息
现在错误对话框会显示：
- 错误消息
- 完整的堆栈跟踪
- 便于定位问题的源头

```python
except Exception as e:
    import traceback
    error_details = traceback.format_exc()
    messagebox.showerror("错误", f"加载文件时出错:\n{str(e)}\n\n详细信息:\n{error_details}")
```

## 已测试的SVD文件

| 文件 | 厂商 | 位域格式 | 状态 |
|------|------|---------|------|
| TLE987x.svd | Infineon | lsb/msb | ✅ 正常 |
| NSUC1602.svd | Nuvoton | bitRange | ✅ 已修复 |
| STM32F103xx.svd | STM | bitOffset/bitWidth | ✅ 已修复 |
| STM32F407IG.svd | STM | bitOffset/bitWidth | ✅ 已修复 |

## 使用建议

1. **重新测试**: 重新加载之前无法显示的SVD文件
2. **报告问题**: 如果仍有问题，错误对话框会显示详细信息
3. **检查SVD**: 确保SVD文件格式正确，包含必要的字段

## 技术细节

### None值检查模式
所有可能为None的字段都使用`.get()`方法：
- `peripheral.get('name', 'Unknown')` - 提供默认值
- `peripheral.get('registers', [])` - 空列表默认值
- `register.get('description', '')` - 空字符串默认值

### 位域解析优先级
1. **lsb/msb** - 直接使用
2. **bitRange** - 解析`[msb:lsb]`格式
3. **bitOffset + bitWidth** - 计算msb
4. **仅bitOffset** - 单位字段

### 容错设计
- 如果某个字段无法解析，跳过该字段
- 不影响其他字段和寄存器的显示
- 保证程序稳定性

## 新增修复 (2025-12-09)

### 问题3: 十六进制size字段解析错误
**错误信息**: `ValueError: invalid literal for int() with base 10: '0x20'`

**原因**: 
- 某些SVD文件使用十六进制格式定义寄存器大小（如`0x20`）
- 代码直接使用`int()`转换时没有指定基数

**解决方案**:
使用`int(value, 0)`自动检测进制：
```python
# 修改前
reg_size = int(register_data.get('size', '32'))

# 修改后
reg_size_str = register_data.get('size', '32')
try:
    # base 0 自动检测十六进制（0x前缀）或十进制
    reg_size = int(reg_size_str, 0)
except (ValueError, TypeError):
    reg_size = 32  # 默认32位
```

**影响范围**:
- SVD解析阶段（`parse_svd`方法）
- 位域图绘制阶段（`draw_register_bit_diagram`方法）
- 支持`32`、`0x20`、`0x40`等各种格式

