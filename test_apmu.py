import xml.etree.ElementTree as ET

tree = ET.parse('svd/NSUC1602.svd')
root = tree.getroot()
peripherals = root.find('peripherals')

apmu = None
for p in peripherals.findall('peripheral'):
    if p.find('name').text == 'APMU':
        apmu = p
        break

if apmu:
    regs = apmu.find('registers')
    if regs:
        reg_count = len(regs.findall('register'))
        cluster_count = len(regs.findall('cluster'))
        print(f'Direct registers: {reg_count}')
        print(f'Clusters: {cluster_count}')
        
        if cluster_count > 0:
            for cluster in regs.findall('cluster'):
                cluster_name = cluster.find('name')
                cluster_regs = len(cluster.findall('register'))
                print(f'Cluster: {cluster_name.text if cluster_name is not None else "Unknown"}')
                print(f'  Registers in cluster: {cluster_regs}')
