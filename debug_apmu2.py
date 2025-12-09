import xml.etree.ElementTree as ET

tree = ET.parse('svd/NSUC1602.svd')
root = tree.getroot()
peripherals_elem = root.find('peripherals')

print("Checking APMU peripheral structure...")
for peripheral in peripherals_elem.findall('peripheral'):
    periph_name = peripheral.find('name')
    if periph_name is not None and periph_name.text == 'APMU':
        print(f"Found APMU")
        
        registers_elem = peripheral.find('registers')
        if registers_elem is not None:
            print(f"\n<registers> element exists")
            print(f"Children in <registers>:")
            for child in registers_elem:
                print(f"  - Tag: {child.tag}")
                if child.tag == 'register':
                    name_elem = child.find('name')
                    print(f"    Name: {name_elem.text if name_elem is not None else 'N/A'}")
                elif child.tag == 'cluster':
                    name_elem = child.find('name')
                    print(f"    Cluster name: {name_elem.text if name_elem is not None else 'N/A'}")
                    # Count registers in cluster
                    clust_regs = len(child.findall('register'))
                    print(f"    Registers in cluster: {clust_regs}")
        
        break
