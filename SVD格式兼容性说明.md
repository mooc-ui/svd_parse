# SVD 位域格式兼容性说明

## 问题背景

不同厂商的SVD文件使用不同的格式来定义寄存器位域（field），导致某些SVD文件无法正确显示位域信息。

## 常见的SVD位域格式

### 格式1: lsb/msb 标签
**使用厂商**: Infineon (TLE987x.svd)

```xml
<field>
    <name>FIELD_NAME</name>
    <lsb>0</lsb>
    <msb>7</msb>
    <access>read-write</access>
</field>
```

### 格式2: bitRange 标签
**使用厂商**: Nuvoton (NSUC1602.svd)

```xml
<field>
    <name>FIELD_NAME</name>
    <bitRange>[7:0]</bitRange>
    <access>read-write</access>
</field>
```

### 格式3: bitOffset + bitWidth
**使用厂商**: STMicroelectronics, ARM

```xml
<field>
    <name>FIELD_NAME</name>
    <bitOffset>0</bitOffset>
    <bitWidth>8</bitWidth>
    <access>read-write</access>
</field>
```

### 格式4: 单个 bitOffset
**使用场景**: 单位字段

```xml
<field>
    <name>FLAG</name>
    <bitOffset>5</bitOffset>
    <access>read-write</access>
</field>
```

## 解决方案

SVD GUI Viewer 现已更新，支持所有4种格式：

### 解析优先级

1. **优先检查 lsb/msb** - 如果存在，直接使用
2. **检查 bitRange** - 解析 `[msb:lsb]` 或 `[bit]` 格式
3. **检查 bitOffset + bitWidth** - 计算 lsb 和 msb
4. **仅 bitOffset** - 假设为单位字段

### 代码实现

```python
# 格式1: lsb/msb
if field_lsb is not None and field_msb is not None:
    lsb = int(field_lsb.text)
    msb = int(field_msb.text)

# 格式2: bitRange
elif field.find('bitRange') is not None:
    bit_range = field.find('bitRange').text.strip('[]')
    msb, lsb = map(int, bit_range.split(':'))

# 格式3: bitOffset + bitWidth
elif bitOffset and bitWidth:
    lsb = int(bitOffset.text)
    msb = lsb + int(bitWidth.text) - 1

# 格式4: 仅 bitOffset
elif bitOffset:
    lsb = msb = int(bitOffset.text)
```

## 兼容性测试

已测试兼容以下SVD文件：
- ✅ TLE987x.svd (Infineon) - lsb/msb 格式
- ✅ NSUC1602.svd (Nuvoton) - bitRange 格式
- ✅ STM32F103xx.svd (STM) - bitOffset/bitWidth 格式
- ✅ STM32F407IG.svd (STM) - bitOffset/bitWidth 格式

## 使用建议

1. 如果您的SVD文件仍然无法显示位域，请检查：
   - 文件是否包含 `<fields>` 标签
   - 位域定义是否使用了非标准格式

2. 可以手动检查SVD文件的位域格式：
   ```bash
   # 查看第一个位域的结构
   python -c "import xml.etree.ElementTree as ET; tree = ET.parse('your_file.svd'); field = tree.find('.//field'); print([e.tag for e in field])"
   ```

3. 如遇到新的格式，请提供SVD文件示例以便添加支持

## 技术细节

- **向后兼容**: 所有旧格式仍然完全支持
- **容错处理**: 如果某个字段无法解析，会跳过该字段但不影响其他字段
- **日志输出**: 解析错误会在控制台输出，便于调试
