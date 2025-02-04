import psutil
import platform

def get_system_info():
    # 获取系统的基本信息
    system_info = {
        "操作系统": platform.system(),
        "主机名": platform.node(),
        "操作系统版本": platform.release(),
        "操作系统详细版本": platform.version(),
        "机器架构": platform.machine(),
        "处理器": platform.processor(),
        "CPU 核心数": psutil.cpu_count(logical=True),  # 获取逻辑CPU核心数
        "CPU 使用率": psutil.cpu_percent(interval=1),  # 获取CPU使用率
        "内存信息": {
            "总内存": psutil.virtual_memory().total,  # 获取总内存
            "可用内存": psutil.virtual_memory().available,  # 获取可用内存
            "内存使用率": psutil.virtual_memory().percent,  # 获取内存使用率
            "已用内存": psutil.virtual_memory().used,  # 获取已用内存
            "空闲内存": psutil.virtual_memory().free,  # 获取空闲内存
        },
        "磁盘信息": {
            "磁盘总容量": psutil.disk_usage('/').total,  # 获取磁盘总容量
            "磁盘已用容量": psutil.disk_usage('/').used,  # 获取磁盘已用容量
            "磁盘空闲容量": psutil.disk_usage('/').free,  # 获取磁盘空闲容量
            "磁盘使用率": psutil.disk_usage('/').percent,  # 获取磁盘使用率
        },
        "网络信息": psutil.net_if_addrs()  # 获取网络接口的地址信息
    }
    
    # 格式化并输出系统信息为中文可读格式
    formatted_info = f"""系统信息：
\t操作系统: {system_info["操作系统"]} {system_info["操作系统版本"]} ({system_info["操作系统详细版本"]})
\t主机名: {system_info["主机名"]}
\t机器架构: {system_info["机器架构"]}
\t处理器: {system_info["处理器"]}
\tCPU 核心数: {system_info["CPU 核心数"]}
\tCPU 使用率: {system_info["CPU 使用率"]}%

内存信息：
\t总内存: {format_bytes(system_info["内存信息"]["总内存"])}
\t可用内存: {format_bytes(system_info["内存信息"]["可用内存"])}
\t已用内存: {format_bytes(system_info["内存信息"]["已用内存"])}
\t空闲内存: {format_bytes(system_info["内存信息"]["空闲内存"])}
\t内存使用率: {system_info["内存信息"]["内存使用率"]}%

磁盘信息：
\t磁盘总容量: {format_bytes(system_info["磁盘信息"]["磁盘总容量"])}
\t磁盘已用容量: {format_bytes(system_info["磁盘信息"]["磁盘已用容量"])}
\t磁盘空闲容量: {format_bytes(system_info["磁盘信息"]["磁盘空闲容量"])}
\t磁盘使用率: {system_info["磁盘信息"]["磁盘使用率"]}%

网络信息：
"""
    
    for interface, addresses in system_info["网络信息"].items():
        formatted_info += f"\t{interface}:\n"
        for addr in addresses:
            # 由于psutil.net_if_addrs()返回的每个地址信息是一个元组，包含address、netmask、broadcast等
            # addr[0] 是 address, addr[1] 是 netmask, addr[2] 是 broadcast
            formatted_info += f"\t\t地址: {addr.address}  子网掩码: {addr.netmask}  广播地址: {addr.broadcast}\n"
    
    return formatted_info.replace("\t", ' ' * 4) 

def format_bytes(byte_size):
    """ 将字节数转换为人类可读的格式（KB, MB, GB等） """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if byte_size < 1024.0:
            return f"{byte_size:.2f} {unit}"
        byte_size /= 1024.0
    return f"{byte_size:.2f} PB"

if __name__ == '__main__':
    # 获取并打印系统信息
    system_info = get_system_info()
    print(system_info)