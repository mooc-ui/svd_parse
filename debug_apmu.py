import xml.etree.ElementTree as ET

tree = ET.parse('svd/NSUC1602.svd')
root = tree.getroot()
peripherals_elem = root.find('peripherals')

print("Checking APMU peripheral...")
for peripheral in peripherals_elem.findall('peripheral'):
    periph_name = peripheral.find('name')
    if periph_name is not None and periph_name.text == 'APMU':
        print(f"Found APMU peripheral")
        
        # Check for derivedFrom
        derived_from = peripheral.get('derivedFrom')
        print(f"derivedFrom: {derived_from}")
        
        # Check for registers
        registers_elem = peripheral.find('registers')
        if registers_elem is not None:
            direct_regs = registers_elem.findall('register')
            print(f"Direct <register> elements: {len(direct_regs)}")
            
            # Show first register if exists
            if len(direct_regs) > 0:
                first_reg = direct_regs[0]
                reg_name = first_reg.find('name')
                print(f"First register: {reg_name.text if reg_name is not None else 'Unknown'}")
        else:
            print("No <registers> element found")
        
        break
