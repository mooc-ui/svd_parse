import xml.etree.ElementTree as ET

tree = ET.parse('svd/NSUC1602.svd')
root = tree.getroot()
peripherals_elem = root.find('peripherals')

print("=== Analyzing APMU Peripheral ===\n")

for peripheral in peripherals_elem.findall('peripheral'):
    periph_name_elem = peripheral.find('name')
    if periph_name_elem is not None and periph_name_elem.text == 'APMU':
        print(f"Peripheral name: {periph_name_elem.text}")
        print(f"derivedFrom attribute: {peripheral.get('derivedFrom')}")
        
        # Print all direct children
        print(f"\nDirect children of <peripheral>:")
        for child in peripheral:
            print(f"  - {child.tag}: {child.text[:50] if child.text and child.text.strip() else '(no text)'}")
        
        # Check registers element
        registers_elem = peripheral.find('registers')
        if registers_elem is not None:
            print(f"\n<registers> element found")
            print(f"Number of children: {len(list(registers_elem))}")
            print(f"Children tags: {[c.tag for c in registers_elem]}")
            
            # Check text content
            if registers_elem.text and registers_elem.text.strip():
                print(f"Text content: {registers_elem.text[:100]}")
            
            # Debug: show raw XML
            xml_str = ET.tostring(registers_elem, encoding='unicode')
            print(f"\nRaw XML (first 300 chars):\n{xml_str[:300]}")
        else:
            print("\nNo <registers> element")
        
        break

print("\n=== Checking other 0-register peripherals ===")
count = 0
for peripheral in peripherals_elem.findall('peripheral'):
    registers_elem = peripheral.find('registers')
    if registers_elem is not None:
        reg_count = len(registers_elem.findall('register'))
        if reg_count == 0:
            name_elem = peripheral.find('name')
            periph_name = name_elem.text if name_elem is not None else 'Unknown'
            print(f"{periph_name}: 0 registers")
            count += 1
            if count >= 5:
                break
