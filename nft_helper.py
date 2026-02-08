#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
nft命令执行辅助脚本
用于简化nft命令的执行流程，提供交互式界面生成并执行nft规则命令

功能：
- 创建和管理nftables防火墙规则
- 完整协议模式快速配置常用服务
- 查询当前防火墙规则
- 导出/备份防火墙规则
- 支持系统安装
"""

import subprocess
import sys
import os
import shutil
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

SCRIPT_NAME = "nft_helper"
INSTALL_MARKER = ".nft_helper_installed"
LOG_FILE = "nft_helper.log"

MAX_PORT = 65535
MIN_PORT = 1
COMMAND_TIMEOUT = 30

def log_operation(message: str) -> None:
    """记录操作日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    try:
        log_path = os.path.join(os.path.dirname(__file__), LOG_FILE)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except (IOError, OSError):
        pass

def sanitize_input(input_str: str) -> str:
    """清理用户输入，防止注入攻击"""
    if not input_str:
        return ""
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_str)
    sanitized = sanitized.strip()
    return sanitized

def is_valid_port(port: Union[str, int]) -> bool:
    """验证端口号是否有效"""
    try:
        port_int = int(port)
        return MIN_PORT <= port_int <= MAX_PORT
    except (ValueError, TypeError):
        return False

def is_valid_port_range(port_input: str) -> Tuple[bool, Optional[Tuple[int, int]], str]:
    """验证端口范围输入是否有效"""
    port_input = sanitize_input(port_input)
    
    if not port_input:
        return False, None, "输入不能为空"
    
    if ',' in port_input:
        ports = [p.strip() for p in port_input.split(',')]
        valid_ports = []
        for port in ports:
            if not is_valid_port(port):
                return False, None, f"端口 '{port}' 无效，必须在{MIN_PORT}-{MAX_PORT}之间"
            valid_ports.append(int(port))
        return True, tuple(valid_ports), "多端口"
    
    elif '-' in port_input:
        parts = port_input.split('-')
        if len(parts) != 2:
            return False, None, "端口范围格式错误"
        
        start_str, end_str = parts[0].strip(), parts[1].strip()
        if not (start_str.isdigit() and end_str.isdigit()):
            return False, None, "端口号必须为数字"
        
        start_port, end_port = int(start_str), int(end_str)
        if not (MIN_PORT <= start_port <= end_port <= MAX_PORT):
            return False, None, f"端口号必须在{MIN_PORT}-{MAX_PORT}之间，且起始端口小于等于结束端口"
        
        return True, (start_port, end_port), f"{start_port}-{end_port}"
    
    elif port_input.isdigit():
        if not is_valid_port(port_input):
            return False, None, f"端口号必须在{MIN_PORT}-{MAX_PORT}之间"
        return True, (int(port_input),), port_input
    
    else:
        return False, None, "无效输入格式"

def clear_screen():
    """清空屏幕（Linux系统）"""
    subprocess.run(['clear'])

def get_install_dir():
    """获取安装目录（Linux系统）"""
    return '/usr/local/bin'

def check_admin_permissions() -> bool:
    """检查是否具有root权限（Linux系统）"""
    try:
        return os.geteuid() == 0
    except (OSError, AttributeError):
        return False

def request_admin_permissions() -> bool:
    """请求root权限"""
    print("\n需要root权限来安装系统级工具。")
    print("请使用以下命令重新运行：")
    abs_path = os.path.abspath(__file__)
    print(f"  sudo python3 {abs_path}")
    return False

def detect_linux_distro() -> str:
    """检测Linux发行版类型"""
    try:
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('ID='):
                        distro = line.strip().split('=')[1].lower()
                        distro = distro.strip('"')
                        if 'ubuntu' in distro or 'debian' in distro:
                            return 'debian'
                        elif 'centos' in distro or 'rhel' in distro or 'fedora' in distro or 'rocky' in distro or 'alma' in distro:
                            return 'rhel'
                        elif 'arch' in distro:
                            return 'arch'
                        elif 'opensuse' in distro or 'suse' in distro:
                            return 'suse'
                        elif 'alpine' in distro:
                            return 'alpine'
                        return distro
    except Exception:
        pass
    
    result = subprocess.run(['which', 'apt-get'], capture_output=True, text=True)
    if result.returncode == 0:
        return 'debian'
    result = subprocess.run(['which', 'yum'], capture_output=True, text=True)
    if result.returncode == 0:
        return 'rhel'
    result = subprocess.run(['which', 'dnf'], capture_output=True, text=True)
    if result.returncode == 0:
        return 'rhel'
    result = subprocess.run(['which', 'pacman'], capture_output=True, text=True)
    if result.returncode == 0:
        return 'arch'
    
    return 'unknown'

def check_nftables_installed() -> tuple:
    """检查nftables是否已安装，返回(是否安装, 命令路径或None)"""
    try:
        result = subprocess.run(['which', 'nft'], capture_output=True, text=True)
        if result.returncode == 0:
            nft_path = result.stdout.strip()
            return True, nft_path
        return False, None
    except Exception:
        return False, None

def install_nftables() -> bool:
    """自动安装nftables工具"""
    print("\n" + "=" * 60)
    print("正在检查nftables安装状态...")
    print("=" * 60)
    
    installed, nft_path = check_nftables_installed()
    if installed:
        print(f"✓ nftables 已安装于：{nft_path}")
        return True
    
    print("⚠ 未检测到 nftables 工具")
    print("\n正在检测系统类型...")
    
    distro = detect_linux_distro()
    
    print(f"检测到系统类型：{distro}")
    
    if not check_admin_permissions():
        print("\n⚠ 需要root权限来安装nftables")
        if not request_admin_permissions():
            print("✗ 无法获取root权限，安装取消")
            return False
    
    print(f"\n正在安装 nftables...")
    
    install_commands = {
        'debian': [
            ['apt-get', 'update'],
            ['apt-get', 'install', '-y', 'nftables']
        ],
        'rhel': [
            ['yum', 'install', '-y', 'nftables'],
            ['dnf', 'install', '-y', 'nftables']
        ],
        'arch': [
            ['pacman', '-Sy', '--noconfirm', 'nftables']
        ],
        'suse': [
            ['zypper', 'install', '-y', 'nftables']
        ],
        'alpine': [
            ['apk', 'add', 'nftables']
        ]
    }
    
    if distro not in install_commands:
        print(f"✗ 不支持的系统类型：{distro}")
        print("请手动安装nftables后重试")
        return False
    
    success = False
    for cmd in install_commands[distro]:
        cmd_name = cmd[0]
        print(f"\n执行：{' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ {cmd_name} 执行成功")
            success = True
        else:
            print(f"✗ {cmd_name} 执行失败")
            if result.stderr:
                print(f"错误信息：{result.stderr}")
            if cmd_name in ['apt-get', 'yum']:
                print("尝试备用安装命令...")
                continue
            success = False
            break
    
    if success:
        installed, nft_path = check_nftables_installed()
        if installed:
            print(f"\n✓ nftables 安装成功！")
            print(f"  安装路径：{nft_path}")
            log_operation(f"nftables 安装成功")
            return True
    
    print("\n✗ nftables 安装失败")
    print("请手动安装：")
    print("  Ubuntu/Debian: sudo apt-get install nftables")
    print("  CentOS/RHEL:   sudo yum install nftables")
    print("  Fedora:        sudo dnf install nftables")
    print("  Arch:          sudo pacman -S nftables")
    print("  OpenSUSE:      sudo zypper install nftables")
    print("  Alpine:        sudo apk add nftables")
    
    log_operation("nftables 安装失败")
    return False

def is_installed() -> Dict[str, Union[str, bool]]:
    """检查程序是否已安装"""
    current_dir = os.path.dirname(__file__)
    if not current_dir:
        current_dir = '.'
    
    install_marker = os.path.join(current_dir, INSTALL_MARKER)
    if os.path.exists(install_marker):
        try:
            with open(install_marker, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    lines = content.split('\n', 1)
                    if len(lines) >= 1 and lines[0]:
                        return {'installed': True, 'install_path': lines[0]}
        except (IOError, OSError, ValueError):
            pass
    return {'installed': False}

def install_program() -> bool:
    """安装程序到系统bin目录（Linux系统）"""
    print("\n" + "=" * 60)
    print("安装 nft_helper 到系统")
    print("=" * 60)
    
    log_operation("开始安装程序")
    
    current_path = os.path.abspath(__file__)
    install_path = os.path.join(get_install_dir(), SCRIPT_NAME)
    
    print(f"\n安装目录：{install_path}")
    
    install_info = is_installed()
    if install_info['installed']:
        print(f"\n⚠ 检测到程序已安装于：{install_info['install_path']}")
        confirm = input("是否重新安装？(直接回车确认): ").strip().lower()
        if confirm != '' and confirm != 'y':
            print("取消安装。")
            return False
    
    if not check_admin_permissions():
        print("\n⚠ 需要root权限来完成安装。")
        if not request_admin_permissions():
            print("✗ 无法获取root权限，安装失败。")
            return False
    
    try:
        if os.path.exists(install_path):
            os.remove(install_path)
        
        shutil.copy2(current_path, install_path)
        os.chmod(install_path, 0o755)
        
        current_dir = os.path.dirname(__file__)
        if not current_dir:
            current_dir = '.'
        install_marker_path = os.path.join(current_dir, INSTALL_MARKER)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(install_marker_path, 'w', encoding='utf-8') as f:
            f.write(f"{install_path}\n{timestamp}")
        
        subprocess.run(['chmod', '+x', install_path], capture_output=True, check=False)
        
        print("\n" + "=" * 60)
        print("✓ 安装成功！")
        print("=" * 60)
        print(f"\n安装路径：{install_path}")
        print(f"\n使用方法：")
        print(f"  直接在终端输入以下命令即可运行：")
        print(f"  {SCRIPT_NAME}")
        print(f"\n示例：")
        print(f"  $ {SCRIPT_NAME}")
        print(f"  $ {SCRIPT_NAME} --help")
        print("\n注意：如果命令不可用，请重新打开终端会话。")
        
        log_operation(f"安装成功：{install_path}")
        return True
        
    except PermissionError:
        print("\n✗ 权限不足，无法写入安装目录。")
        print(f"  请使用 sudo 权限重新运行。")
        log_operation("安装失败：权限不足")
        return False
    except (IOError, OSError) as e:
        print(f"\n✗ 安装失败：文件操作错误 - {e}")
        log_operation(f"安装失败：{e}")
        return False
    except Exception as e:
        print(f"\n✗ 安装失败：{e}")
        log_operation(f"安装失败：{e}")
        return False

def uninstall_program() -> bool:
    """卸载程序（Linux系统）"""
    print("\n" + "=" * 60)
    print("卸载 nft_helper")
    print("=" * 60)
    
    log_operation("开始卸载程序")
    
    install_info = is_installed()
    
    if not install_info['installed']:
        print("\n⚠ 未检测到已安装的版本。")
        print("尝试查找系统中的安装文件...")
        
        search_paths = [
            '/usr/local/bin/' + SCRIPT_NAME,
            '/usr/bin/' + SCRIPT_NAME
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                install_info = {'installed': True, 'install_path': path}
                break
    
    if not install_info['installed']:
        print("\n✗ 未找到已安装的程序。")
        print("可能从未安装过，或安装位置不在标准目录中。")
        log_operation("卸载失败：未找到安装信息")
        return False
    
    install_path = install_info['install_path']
    print(f"\n找到安装路径：{install_path}")
    
    confirm = input("\n确认卸载？(直接回车确认): ").strip().lower()
    if confirm != '' and confirm != 'y':
        print("取消卸载。")
        return False
    
    if not check_admin_permissions():
        print("\n⚠ 需要root权限来卸载。")
        if not request_admin_permissions():
            print("✗ 无法获取root权限，卸载失败。")
            return False
    
    try:
        if os.path.exists(install_path):
            os.remove(install_path)
            print(f"\n✓ 已删除安装文件：{install_path}")
            log_operation(f"已删除安装文件：{install_path}")
        else:
            print(f"\n⚠ 安装文件不存在：{install_path}")
        
        current_dir = os.path.dirname(__file__)
        if not current_dir:
            current_dir = '.'
        install_marker = os.path.join(current_dir, INSTALL_MARKER)
        
        if os.path.exists(install_marker):
            os.remove(install_marker)
            print("✓ 已清除安装标记文件")
            log_operation("已清除安装标记文件")
        
        print("\n" + "=" * 60)
        print("✓ 卸载完成！")
        print("=" * 60)
        print("\n卸载成功！")
        print("程序已从系统中完全移除。")
        print("如果命令仍然可用，请重新打开终端会话。")
        
        log_operation("卸载完成")
        return True
        
    except PermissionError:
        print("\n✗ 权限不足，无法删除文件。")
        log_operation("卸载失败：权限不足")
        return False
    except (IOError, OSError) as e:
        print(f"\n✗ 卸载失败：文件操作错误 - {e}")
        log_operation(f"卸载失败：{e}")
        return False
    except Exception as e:
        print(f"\n✗ 卸载失败：{e}")
        log_operation(f"卸载失败：{e}")
        return False

def show_install_help():
    """显示安装帮助信息（Linux系统）"""
    print("\n" + "=" * 60)
    print("安装指南")
    print("=" * 60)
    print("""
将 nft_helper 安装到系统后，可以直接在终端中调用，无需指定完整路径。

安装选项：
  直接运行此脚本时选择 '5. 安装到系统' 或 '6. 卸载'

安装位置：
  - /usr/local/bin/nft_helper

使用方法：
  安装后，在终端中直接输入：
    nft_helper
  
  即可启动程序。

卸载方法：
  选择 '6. 卸载' 选项即可从系统中完全移除。

注意事项：
  - 安装/卸载需要root权限
  - 安装后可能需要重新打开终端会话
  - 日志文件 nft_helper.log 保留在原目录
    """)
    print("=" * 60)
    input("\n按回车键返回主菜单...")

def print_header():
    """打印程序头部"""
    print("=" * 50)
    print("        nft命令执行辅助工具 v2.0")
    print("=" * 50)

def get_action():
    """获取用户选择的操作类型（开放/拒绝）"""
    while True:
        print("\n请选择操作类型：")
        print("1. 开放 (accept) - 允许流量通过")
        print("2. 拒绝 (drop)   - 丢弃流量")
        print("3. 返回主菜单")
        
        choice = input("请输入选项编号: ").strip()
        
        if choice == '1':
            log_operation("选择了操作类型：开放 (accept)")
            return 'accept'
        elif choice == '2':
            log_operation("选择了操作类型：拒绝 (drop)")
            return 'drop'
        elif choice == '3':
            return None
        else:
            print("✗ 无效输入，请重新选择。")

def get_full_protocol_mode():
    """获取完整协议模式选项"""
    while True:
        print("\n完整协议模式 - 选择您要配置的服务：")
        print("1. Web服务 (HTTP/HTTPS)")
        print("2. SSH服务 (TCP 22)")
        print("3. 邮件服务 (SMTP/POP3/IMAP)")
        print("4. 数据库服务 (MySQL/PostgreSQL/MongoDB)")
        print("5. 文件传输服务 (FTP/SFTP)")
        print("6. DNS服务 (TCP/UDP 53)")
        print("7. 返回主菜单")
        
        choice = input("请输入选项编号: ").strip()
        
        if choice == '1':
            return {'mode': 'web', 'protocol': 'tcp', 'ports': ['80', '443']}
        elif choice == '2':
            return {'mode': 'ssh', 'protocol': 'tcp', 'ports': ['22']}
        elif choice == '3':
            return {'mode': 'mail', 'protocol': 'tcp', 'ports': ['25', '110', '143', '993', '995']}
        elif choice == '4':
            return {'mode': 'database', 'protocol': 'tcp', 'ports': ['3306', '5432', '27017']}
        elif choice == '5':
            return {'mode': 'ftp', 'protocol': 'tcp', 'ports': ['21']}
        elif choice == '6':
            return {'mode': 'dns', 'protocol': 'both', 'ports': ['53']}
        elif choice == '7':
            return None
        else:
            print("✗ 无效输入，请重新选择。")

def get_protocol():
    """获取用户选择的网络协议"""
    common_protocols = ['tcp', 'udp', 'icmp', 'sctp', 'dccp']
    protocol_descriptions = {
        'tcp': 'TCP - 传输控制协议（面向连接）',
        'udp': 'UDP - 用户数据报协议（无连接）',
        'icmp': 'ICMP - Internet控制消息协议',
        'sctp': 'SCTP - 流控制传输协议',
        'dccp': 'DCCP - 数据报拥塞控制协议'
    }
    
    while True:
        print("\n请选择网络协议：")
        print("-" * 40)
        for i, proto in enumerate(common_protocols, 1):
            desc = protocol_descriptions.get(proto, '')
            print(f"{i}. {proto:<6} {desc}")
        print("-" * 40)
        print(f"{len(common_protocols) + 1}. 其他（手动输入）")
        print(f"{len(common_protocols) + 2}. 完整协议模式（预设服务配置）")
        print(f"{len(common_protocols) + 3}. 返回主菜单")
        
        choice = input("\n请输入选项编号: ").strip()
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(common_protocols):
                selected_proto = common_protocols[choice_num - 1]
                log_operation(f"选择了协议：{selected_proto}")
                return selected_proto
            elif choice_num == len(common_protocols) + 1:
                custom_proto = input("请输入协议名称（如：tcp, udp, icmp等）: ").strip().lower()
                if custom_proto:
                    log_operation(f"手动输入了协议：{custom_proto}")
                    return custom_proto
                else:
                    print("✗ 协议名称不能为空，请重新输入。")
            elif choice_num == len(common_protocols) + 2:
                log_operation("选择了完整协议模式")
                return 'full_mode'
            elif choice_num == len(common_protocols) + 3:
                return None
            else:
                print("✗ 无效输入，请重新选择。")
        except ValueError:
            print("✗ 无效输入，请输入数字。")

def get_port():
    """获取用户输入的端口号（支持单个端口或端口范围）"""
    while True:
        print("\n请输入端口号：")
        print("- 单个端口：如 22, 80, 443")
        print("- 端口范围：如 8080-8090")
        print("- 多个端口：用逗号分隔，如：80,443,8080")
        print("- 输入 'menu' 返回主菜单")
        
        port_input = input("\n请输入: ").strip()
        
        if port_input.lower() == 'menu':
            return None
        
        if not port_input:
            print("✗ 输入不能为空，请重新输入。")
            continue
        
        try:
            if ',' in port_input:
                ports = [p.strip() for p in port_input.split(',')]
                valid_ports = []
                for port in ports:
                    if port.isdigit() and 1 <= int(port) <= 65535:
                        valid_ports.append(port)
                    else:
                        print(f"✗ 端口 '{port}' 无效，必须在1-65535之间。")
                        break
                else:
                    if valid_ports:
                        log_operation(f"选择了多个端口：{valid_ports}")
                        return ports
            elif '-' in port_input:
                parts = port_input.split('-')
                if len(parts) == 2 and all(part.strip().isdigit() for part in parts):
                    start_port = int(parts[0].strip())
                    end_port = int(parts[1].strip())
                    if 1 <= start_port <= end_port <= 65535:
                        log_operation(f"选择了端口范围：{start_port}-{end_port}")
                        return port_input
                    else:
                        print("✗ 端口号必须在1-65535之间，且起始端口小于等于结束端口。")
                else:
                    print("✗ 端口范围格式错误，请使用格式：起始端口-结束端口")
            elif port_input.isdigit():
                port = int(port_input)
                if 1 <= port <= 65535:
                    log_operation(f"选择了单个端口：{port}")
                    return port_input
                else:
                    print("✗ 端口号必须在1-65535之间。")
            else:
                print("✗ 无效输入，请检查格式。")
        except Exception as e:
            print(f"✗ 处理输入时出错：{e}")

def get_ip_address():
    """获取用户输入的IP地址（支持单个IP、IP范围、CIDR格式）"""
    print("\n请输入IP地址：")
    print("- 单个IP：如 192.168.1.100")
    print("- IP范围：如 192.168.1.0-192.168.1.255")
    print("- CIDR格式：如 192.168.1.0/24")
    print("- 直接回车：所有IP (0.0.0.0/0)")
    print("- 输入 'menu' 返回主菜单")
    
    ip_input = input("\n请输入: ").strip()
    
    if ip_input.lower() == 'menu':
        return None
    
    if not ip_input:
        log_operation("选择了所有IP：0.0.0.0/0")
        return "0.0.0.0/0"
    
    import ipaddress
    
    try:
        if '-' in ip_input:
            parts = ip_input.split('-')
            if len(parts) != 2:
                print("✗ IP范围格式错误，请使用格式：起始IP-结束IP")
                return get_ip_address()
            
            ip_start = ipaddress.ip_address(parts[0].strip())
            ip_end = ipaddress.ip_address(parts[1].strip())
            
            if ip_start > ip_end:
                print("✗ IP范围起始地址必须小于等于结束地址")
                return get_ip_address()
            
            log_operation(f"选择了IP范围：{ip_start}-{ip_end}")
            return ip_input
        
        if '/' in ip_input:
            try:
                network = ipaddress.ip_network(ip_input, strict=False)
                if network.num_addresses == 0:
                    print("✗ 无效的网络地址")
                    return get_ip_address()
                log_operation(f"选择了CIDR网络：{ip_input}")
                return ip_input
            except ValueError as e:
                print(f"✗ CIDR格式无效：{e}")
                return get_ip_address()
        
        ipaddress.ip_address(ip_input)
        log_operation(f"选择了单个IP：{ip_input}")
        return ip_input
    
    except ValueError as e:
        print(f"✗ IP地址格式无效：{e}")
        return get_ip_address()

def validate_protocol_port(protocol, port):
    """验证协议和端口的兼容性"""
    protocols_without_port = ['icmp', 'igmp', 'esp', 'ah', 'ip', 'ipv6-icmp']
    
    if protocol.lower() in protocols_without_port:
        return False, f"协议 '{protocol}' 不需要端口参数"
    
    if port is None or (isinstance(port, list) and len(port) > 1):
        return False, f"协议 '{protocol}' 需要指定单个端口"
    
    return True, "验证通过"

def generate_nft_command(action, protocol, port, is_full_mode=False, ip_address=None):
    """生成nft命令"""
    if is_full_mode:
        commands = []
        if port == '53' and protocol == 'both':
            commands.append(f"nft add rule ip filter input tcp dport 53 {action}")
            commands.append(f"nft add rule ip filter input udp dport 53 {action}")
        else:
            for p in port:
                port_part = f"tcp dport {p}" if protocol == 'tcp' else f"udp dport {p}"
                commands.append(f"nft add rule ip filter input {port_part} {action}")
        log_operation(f"生成了完整协议模式的命令：{commands}")
        return commands
    
    if protocol.lower() == 'icmp' or protocol.lower() == 'ipv6-icmp':
        command = f"nft add rule ip filter input {protocol} {action}"
        log_operation(f"生成了ICMP协议命令：{command}")
        return [command]
    
    if '-' in str(port):
        start, end = str(port).split('-')
        start_port = int(start.strip())
        end_port = int(end.strip())
        if start_port > end_port:
            return None
        port_part = f"tcp dport {start_port}:{end_port}" if protocol == 'tcp' else f"udp dport {start_port}:{end_port}"
    else:
        port_part = f"{protocol} dport {port}"
    
    if ip_address:
        command = f"nft add rule ip filter input ip daddr {ip_address} {port_part} {action}"
    else:
        command = f"nft add rule ip filter input {port_part} {action}"
    
    log_operation(f"生成了命令：{command}")
    return [command]

def check_nftables_table_exists(family='ip', table='filter'):
    """检查nftables表是否存在"""
    try:
        result = subprocess.run(
            ['nft', 'list', 'tables'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True
        return False
    except Exception:
        return False

def init_nftables_filter_table():
    """初始化nftables filter表和input链"""
    print("\n检测到filter表不存在，正在初始化...")
    log_operation("初始化nftables filter表")
    
    rules_content = """table ip filter {
    chain input {
        type filter hook input priority 0; policy accept;
    }
    chain output {
        type filter hook output priority 0; policy accept;
    }
    chain forward {
        type filter hook forward priority 0; policy accept;
    }
}
"""
    
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nft', delete=False) as f:
            f.write(rules_content)
            temp_file = f.name
        
        result = subprocess.run(['nft', '-f', temp_file], capture_output=True, text=True)
        os.unlink(temp_file)
        
        if result.returncode == 0:
            print("✓ filter表和链初始化成功！")
            log_operation("filter表初始化成功")
        else:
            print(f"✗ 初始化失败：{result.stderr}")
            log_operation(f"filter表初始化失败：{result.stderr}")
            return False
        
        print("初始化完成。")
        return True
        
    except Exception as e:
        print(f"✗ 初始化过程中发生错误：{e}")
        log_operation(f"初始化错误：{e}")
        return False

def execute_command(commands):
    """执行命令并返回结果"""
    installed, nft_path = check_nftables_installed()
    if not installed:
        print("\n⚠ 未检测到 nftables 工具")
        print("\n是否尝试自动安装nftables？(直接回车确认)")
        
        confirm = input("选择: ").strip().lower()
        if confirm == '' or confirm == 'y':
            if not install_nftables():
                return False
    
    print("\n" + "=" * 50)
    print("准备执行的命令：")
    print("=" * 50)
    
    if isinstance(commands, list):
        for i, cmd in enumerate(commands, 1):
            print(f"{i}. {cmd}")
    else:
        print(commands)
    
    print("=" * 50)
    
    confirm = input("\n确认执行以上命令？(直接回车确认，输入 c 自定义命令): ").strip().lower()
    
    if confirm == '' or confirm == 'y':
        if isinstance(commands, list):
            success_count = 0
            failed_commands = []
            
            for cmd in commands:
                print(f"\n执行命令: {cmd}")
                try:
                    cmd_parts = cmd.split()
                    result = subprocess.run(cmd_parts, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print("✓ 命令执行成功！")
                        if result.stdout:
                            print(f"输出: {result.stdout}")
                        success_count += 1
                    else:
                        error_msg = result.stderr.strip() if result.stderr else "未知错误"
                        print("✗ 命令执行失败！")
                        print(f"错误信息: {error_msg}")
                        
                        if "No such file or directory" in error_msg or "Could not process rule" in error_msg:
                            print("\n⚠ 检测到表或链不存在，正在尝试初始化...")
                            init_nftables_filter_table()
                            
                            print("\n重新执行原命令...")
                            cmd_parts = cmd.split()
                            result2 = subprocess.run(cmd_parts, capture_output=True, text=True)
                            if result2.returncode == 0:
                                print("✓ 初始化后命令执行成功！")
                                success_count += 1
                            else:
                                print(f"✗ 仍然失败: {result2.stderr}")
                                failed_commands.append(cmd)
                        else:
                            failed_commands.append(cmd)
                            
                except Exception as e:
                    print(f"✗ 执行命令时发生错误：{e}")
                    failed_commands.append(cmd)
            
            log_operation(f"执行了 {success_count}/{len(commands)} 个命令")
            return success_count == len(commands)
        else:
            try:
                cmd_parts = commands.split()
                result = subprocess.run(cmd_parts, capture_output=True, text=True)
                if result.returncode == 0:
                    print("✓ 命令执行成功！")
                    if result.stdout:
                        print(f"输出: {result.stdout}")
                    return True
                else:
                    error_msg = result.stderr.strip() if result.stderr else "未知错误"
                    print("✗ 命令执行失败！")
                    print(f"错误信息: {error_msg}")
                    
                    if "No such file or directory" in error_msg or "Could not process rule" in error_msg:
                        print("\n⚠ 检测到表或链不存在，正在尝试初始化...")
                        init_nftables_filter_table()
                        
                        print("\n重新执行原命令...")
                        cmd_parts = commands.split()
                        result2 = subprocess.run(cmd_parts, capture_output=True, text=True)
                        if result2.returncode == 0:
                            print("✓ 初始化后命令执行成功！")
                            return True
                        else:
                            print(f"✗ 仍然失败: {result2.stderr}")
                    return False
            except Exception as e:
                print(f"✗ 执行命令时发生错误：{e}")
                return False
    
    elif confirm == 'c':
        custom_cmd = input("请输入自定义命令: ").strip()
        if custom_cmd:
            return execute_command(custom_cmd)
        else:
            print("✗ 未输入命令，操作取消。")
            return False
    
    else:
        print("操作已取消。")
        return False

def delete_rule(family, table, chain, handle):
    """删除特定规则的nft命令"""
    return f"nft delete rule {family} {table} {chain} handle {handle}"

def delete_nft_rule(family, table, chain, handle):
    """删除nftables规则"""
    cmd_parts = ['nft', 'delete', 'rule', family, table, chain, 'handle', str(handle)]
    cmd_str = ' '.join(cmd_parts)
    
    print(f"\n执行删除命令: {cmd_str}")
    
    try:
        result = subprocess.run(cmd_parts, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 规则删除成功！")
            if result.stdout:
                print(f"输出: {result.stdout}")
            log_operation(f"删除规则成功: {cmd_str}")
            return True
        else:
            error_msg = result.stderr.strip() if result.stderr else "未知错误"
            print("✗ 规则删除失败！")
            print(f"错误信息: {error_msg}")
            log_operation(f"删除规则失败: {error_msg}")
            return False
            
    except Exception as e:
        print(f"✗ 执行删除命令时发生错误：{e}")
        log_operation(f"删除规则错误: {e}")
        return False

def search_rules_by_port(port, protocol='tcp'):
    """搜索特定端口的规则"""
    try:
        result = subprocess.run(
            ['nft', '-j', '-a', 'list', 'ruleset'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return None
        
        ruleset_data = json.loads(result.stdout)
        
        matches = []
        port_int = int(port)
        
        for item in ruleset_data.get('nftables', []):
            if 'rule' in item:
                rule = item['rule']
                expr = rule.get('expr', [])
                
                rule_family = rule.get('family', '')
                rule_table = rule.get('table', '')
                rule_chain = rule.get('chain', '')
                
                has_port_match = False
                port_info = ""
                
                for e in expr:
                    if 'match' in e:
                        match = e['match']
                        left = match.get('left', {})
                        right = match.get('right', '')
                        payload = left.get('payload', {})
                        proto = payload.get('protocol', '')
                        field = payload.get('field', '')
                        
                        if proto == protocol and field == 'dport':
                            right_val = right if isinstance(right, int) else int(right)
                            if right_val == port_int:
                                has_port_match = True
                                port_info = f"{proto} dport {right_val}"
                                break
                
                if has_port_match:
                    matches.append({
                        'family': rule_family,
                        'table': rule_table,
                        'chain': rule_chain,
                        'rule': format_rule_expression(expr),
                        'port_info': port_info,
                        'handle': rule.get('handle', '')
                    })
        
        return matches
        
    except Exception as e:
        print(f"搜索错误: {e}")
        return None

def advanced_rule_search(search_term):
    """高级规则搜索，支持复杂查询"""
    try:
        result = subprocess.run(
            ['nft', '-j', 'list', 'ruleset'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return None
        
        ruleset_data = json.loads(result.stdout)
        
        matches = []
        search_lower = search_term.lower()
        
        for item in ruleset_data.get('nftables', []):
            if 'rule' in item:
                rule = item['rule']
                expr = rule.get('expr', [])
                
                rule_text = format_rule_expression(expr).lower()
                table_info = item.get('table', {})
                chain_info = item.get('chain', {})
                
                # 在规则文本中搜索
                if search_lower in rule_text:
                    matches.append({
                        'family': table_info.get('family', 'unknown'),
                        'table': table_info.get('name', 'unknown'),
                        'chain': chain_info.get('name', 'unknown'),
                        'rule': format_rule_expression(expr),
                        'match_reason': f"规则文本包含: {search_term}"
                    })
        
        return matches
        
    except Exception:
        return None

def query_nft_rules():
    """查询当前nftables规则"""
    print("\n" + "=" * 60)
    print("查询当前防火墙规则")
    print("=" * 60)
    
    log_operation("用户查询当前nft规则")
    
    try:
        result = subprocess.run(
            ['nft', '-j', 'list', 'ruleset'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "未知错误"
            print(f"\n✗ 查询失败：{error_msg}")
            if "Operation not permitted" in error_msg or "Permission denied" in error_msg:
                print("提示：可能需要root权限来查看防火墙规则。")
                print("请使用 sudo 权限重新运行。")
            log_operation(f"查询失败：{error_msg}")
            return False
        
        try:
            ruleset_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"\n⚠ JSON解析失败，尝试使用原始格式...")
            log_operation(f"JSON解析失败：{e}，尝试备用方案")
            try:
                result_backup = subprocess.run(
                    ['nft', '-nn', 'list', 'ruleset'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result_backup.returncode == 0:
                    print("\n原始规则输出：")
                    print("-" * 60)
                    print(result_backup.stdout)
                    print("-" * 60)
                    print("提示：JSON格式不可用，但以上是原始规则列表")
                    log_operation("使用原始格式输出成功")
                    return True
                else:
                    print(f"\n✗ JSON解析失败且无法获取原始格式：{e}")
                    log_operation(f"JSON和原始格式都失败：{e}")
                    return False
            except Exception as backup_error:
                print(f"\n✗ JSON解析失败，备用方案也出错：{backup_error}")
                log_operation(f"备用方案失败：{backup_error}")
                return False
        
        if not ruleset_data.get('nftables'):
            print("\n当前没有配置任何防火墙规则。")
            print("系统使用默认防火墙策略。")
            return True
        
        all_rules = display_rules(ruleset_data['nftables'])
        
        if not all_rules:
            print("\n当前没有INPUT链规则。")
            print("\n" + "=" * 60)
            print("查看JSON格式？(直接回车确认): ", end="")
            show_raw = input().strip().lower()
            if show_raw == '' or show_raw == 'y':
                print("\n" + "=" * 60)
                print("JSON格式规则列表")
                print("=" * 60)
                result2 = subprocess.run(
                    ['nft', '-j', 'list', 'ruleset'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result2.returncode == 0:
                    try:
                        data = json.loads(result2.stdout)
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                    except:
                        print(result2.stdout)
                else:
                    print("无法获取JSON格式规则列表。")
                print("=" * 60)
            
            log_operation("成功查询并显示规则")
            return True
        
        print("\n" + "=" * 60)
        print("操作选项")
        print("=" * 60)
        print("1. 删除规则")
        print("2. 查看JSON格式")
        print("3. 返回主菜单")
        
        op_choice = input("选择操作: ").strip()
        
        if op_choice == '1':
            while True:
                print("\n" + "=" * 60)
                print("删除INPUT链规则")
                print("=" * 60)
                print("\n输入要删除的规则编号，多个用逗号分隔（1-{0}），或输入 'menu' 返回主菜单".format(len(all_rules)))
                print("格式: 编号或 1,3,4")
                print("例如: 1")
                print("或: 1,3")
                
                delete_input = input("\n输入: ").strip().lower()
                
                if delete_input == 'menu':
                    print("返回主菜单。")
                    break
                
                try:
                    if ',' in delete_input:
                        rule_nums = [int(x.strip()) for x in delete_input.split(',')]
                    else:
                        rule_nums = [int(delete_input)]
                    
                    valid_rules = []
                    invalid_rules = []
                    for rule_num in rule_nums:
                        if 1 <= rule_num <= len(all_rules):
                            valid_rules.append(rule_num)
                        else:
                            invalid_rules.append(rule_num)
                    
                    if invalid_rules:
                        print("✗ 以下编号无效：{0}".format(', '.join(map(str, invalid_rules))))
                        print("有效范围: 1-{0}".format(len(all_rules)))
                        continue
                    
                    if valid_rules:
                        print("\n将删除以下规则：")
                        for rule_num in valid_rules:
                            rule_to_delete = all_rules[rule_num - 1]
                            family = rule_to_delete['family']
                            table = rule_to_delete['table']
                            chain = rule_to_delete['chain']
                            handle = rule_to_delete.get('handle', '')
                            print("  {0}. nft delete rule {1} {2} {3} handle {4}".format(
                                rule_num, family, table, chain, handle))
                        
                        confirm = input("\n确认执行以上命令？(直接回车确认): ").strip().lower()
                        if confirm == '' or confirm == 'y':
                            for rule_num in valid_rules:
                                rule_to_delete = all_rules[rule_num - 1]
                                family = rule_to_delete['family']
                                table = rule_to_delete['table']
                                chain = rule_to_delete['chain']
                                handle = rule_to_delete.get('handle', '')
                                if handle:
                                    delete_nft_rule(family, table, chain, handle)
                            break
                        else:
                            print("取消删除。")
                            break
                    else:
                        print("✗ 没有有效的规则编号！")
                        print("有效范围: 1-{0}".format(len(all_rules)))
                        
                except ValueError:
                    print("✗ 输入无效，请输入数字或 'menu'")
        
        elif op_choice == '2':
            print("\n" + "=" * 60)
            print("JSON格式规则列表")
            print("=" * 60)
            result2 = subprocess.run(
                ['nft', '-j', 'list', 'ruleset'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result2.returncode == 0:
                try:
                    data = json.loads(result2.stdout)
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                except:
                    print(result2.stdout)
            else:
                print("无法获取JSON格式规则列表。")
            print("=" * 60)
        
        log_operation("成功查询并显示规则")
        return True
        
    except subprocess.TimeoutExpired:
        print("\n✗ 查询超时，请稍后重试。")
        log_operation("查询超时")
        return False
    except FileNotFoundError:
        print("\n✗ 未找到nftables工具。")
        print("\n是否尝试自动安装nftables？(直接回车确认)")
        
        confirm = input("选择: ").strip().lower()
        if confirm == '' or confirm == 'y':
            if install_nftables():
                print("\n✓ nftables 已安装，请重新运行查询")
                return True
        print("请确保系统已安装nftables。")
        print("手动安装命令：")
        print("  Ubuntu/Debian: sudo apt-get install nftables")
        print("  CentOS/RHEL:   sudo yum install nftables")
        log_operation("未找到nftables工具")
        return False
    except Exception as e:
        print(f"\n✗ 查询过程中发生错误：{e}")
        log_operation(f"查询错误：{e}")
        return False

def display_rules(ruleset_data):
    """格式化显示nftables规则（简化版 - 只显示input链端口规则）"""
    print("\n" + "=" * 60)
    print("当前防火墙规则 - INPUT链")
    print("=" * 60)
    
    port_rules = []
    
    for item in ruleset_data:
        if item.get('metainfo'):
            continue
        
        if 'rule' in item:
            rule = item['rule']
            rule_family = rule.get('family', '')
            rule_table = rule.get('table', '')
            rule_chain = rule.get('chain', '')
            rule_handle = rule.get('handle', '')
            
            if rule_chain == 'input' and rule_family == 'ip' and rule_table == 'filter':
                expr = rule.get('expr', [])
                rule_desc = format_rule_expression(expr)
                
                if '端口' in rule_desc:
                    port_rules.append({
                        'handle': rule_handle,
                        'description': rule_desc,
                        'expr': expr
                    })
    
    if port_rules:
        print("\n端口规则列表：")
        print("-" * 40)
        for i, rule in enumerate(port_rules, 1):
            print(f"[ {i}] {rule['description']}")
        print("-" * 40)
        print(f"共 {len(port_rules)} 条端口规则")
    else:
        print("\n未找到端口规则")
        print("系统使用默认防火墙策略（input链默认accept）")
    
    print("\n" + "=" * 60)
    
    all_rules = []
    rule_id = 0
    
    for item in ruleset_data:
        if 'rule' in item:
            rule = item['rule']
            if rule.get('chain') == 'input' and rule.get('family') == 'ip' and rule.get('table') == 'filter':
                rule_id += 1
                all_rules.append({
                    'id': rule_id,
                    'family': rule.get('family'),
                    'table': rule.get('table'),
                    'chain': rule.get('chain'),
                    'handle': rule.get('handle'),
                    'rule': rule
                })
    
    return all_rules

def format_rule_expression(expr_list):
    """格式化规则表达式为可读字符串"""
    if not expr_list:
        return "(空规则)"
    
    parts = []
    port_info = ""
    action = ""
    
    for expr in expr_list:
        if not expr:
            continue
        
        expr_type = list(expr.keys())[0] if expr else None
        
        if expr_type == 'match':
            match = expr.get('match', {})
            op = match.get('op', '')
            left = match.get('left', {})
            right = match.get('right', '')
            negate = match.get('negate', False)
            
            neg_str = '!' if negate else ''
            
            payload = left.get('payload', {})
            protocol = payload.get('protocol', '')
            field = payload.get('field', '')
            
            if field in ['dport', 'sport']:
                port_info = f"{neg_str}端口 {right}"
            elif protocol and field:
                parts.append(f"{neg_str}{protocol} {field} {right}")
            elif right:
                parts.append(f"{neg_str}{op} {right}")
        
        elif expr_type == 'relational':
            rel_expr = expr.get('relational', {})
            op = rel_expr.get('op', '')
            left = rel_expr.get('left', {})
            right = rel_expr.get('right', '')
            negate = rel_expr.get('negate', False)
            
            neg_str = '!' if negate else ''
            
            payload = left.get('payload', {})
            protocol = payload.get('protocol', '')
            field = payload.get('field', '')
            
            if isinstance(right, str):
                right_val = right
            elif isinstance(right, dict):
                if 'val' in right:
                    right_val = right['val']
                elif 'prefix' in right:
                    prefix = right['prefix']
                    addr = prefix.get('addr', '')
                    length = prefix.get('len', 0)
                    right_val = f"{addr}/{length}"
                else:
                    right_val = str(right)
            else:
                right_val = str(right)
            
            if field in ['dport', 'sport']:
                port_info = f"{neg_str}端口 {right_val}"
            elif protocol == 'ip' and field == 'daddr':
                parts.append(f"{neg_str}ip daddr {right_val}")
            elif protocol and field:
                parts.append(f"{neg_str}{protocol} {field} {right_val}")
            elif field:
                parts.append(f"{neg_str}{field} {right_val}")
            elif right_val:
                parts.append(f"{neg_str}{op} {right_val}")
        
        elif expr_type == 'cmp':
            cmp_expr = expr.get('cmp', {})
            op = cmp_expr.get('op', '')
            left = cmp_expr.get('left', {})
            right = cmp_expr.get('right', {})
            negate = cmp_expr.get('negate', False)
            
            neg_str = '!' if negate else ''
            
            payload = left.get('payload', {})
            protocol = payload.get('protocol', '')
            field = payload.get('field', '')
            
            if isinstance(right, str):
                right_val = right
            elif isinstance(right, dict):
                if 'val' in right:
                    right_val = right['val']
                elif 'prefix' in right:
                    prefix = right['prefix']
                    right_val = f"{prefix.get('addr', '')}/{prefix.get('len', '')}"
                else:
                    right_val = str(right)
            else:
                right_val = str(right)
            
            if field in ['dport', 'sport']:
                port_info = f"{neg_str}端口 {right_val}"
            elif protocol and field:
                parts.append(f"{neg_str}{protocol} {field} {right_val}")
            elif field and right_val:
                parts.append(f"{neg_str}{field} {right_val}")
            elif right_val:
                parts.append(f"{neg_str}{op} {right_val}")
        
        elif expr_type == 'payload':
            payload = expr.get('payload', {})
            protocol = payload.get('protocol', '')
            field = payload.get('field', '')
            value = payload.get('value', '')
            
            if field in ['dport', 'sport']:
                port_info = f"端口 {value}"
            elif protocol and field:
                parts.append(f"{protocol} {field} {value}")
        
        elif expr_type == 'meta':
            meta = expr.get('meta', {})
            key = meta.get('key', '')
            if key:
                parts.append(f"meta {key}")
            
            negate = meta.get('negate', False)
            neg_str = '!' if negate else ''
            
            left = meta.get('left', {})
            right = meta.get('right', '')
            
            if left:
                left_type = list(left.keys())[0] if left else None
                if left_type == 'meta':
                    left_key = left['meta'].get('key', '')
                    if left_key:
                        parts[-1] = f"{neg_str}{left_key}"
            
            if isinstance(right, str):
                parts.append(f"{neg_str}{right}")
            elif isinstance(right, dict):
                if 'val' in right:
                    parts.append(f"{neg_str}{right['val']}")
                elif 'prefix' in right:
                    prefix = right['prefix']
                    right_val = f"{prefix.get('addr', '')}/{prefix.get('len', '')}"
                    parts.append(f"{neg_str}{right_val}")
        
        elif expr_type == 'ct':
            ct = expr.get('ct', {})
            direction = ct.get('direction', '')
            key = ct.get('key', '')
            value = ct.get('value', '')
            if direction and key:
                parts.append(f"ct {direction} {key}")
            elif key:
                parts.append(f"ct {key}")
        
        elif expr_type == 'accept':
            action = "放行"
        
        elif expr_type == 'drop':
            action = "拒绝"
        
        elif expr_type == 'reject':
            action = "拒绝"
        
        elif expr_type == 'log':
            parts.append("LOG")
        
        elif expr_type == 'counter':
            counter = expr.get('counter', {})
            packets = counter.get('packets', 0)
            bytes_count = counter.get('bytes', 0)
            parts.append(f"计数器: {packets}包 {bytes_count}字节")
        
        elif expr_type == 'jump':
            jump = expr.get('jump', {})
            target = jump.get('target', '')
            if target:
                parts.append(f"跳转到 {target}")
        
        elif expr_type == 'return':
            parts.append("返回")
        
        elif expr_type == 'xt':
            xt = expr.get('xt', {})
            target = xt.get('target', '')
            if target:
                parts.append(f"[{target}]")
        
        elif expr_type == 'snat':
            action = "源NAT"
        
        elif expr_type == 'dnat':
            action = "目标NAT"
        
        elif expr_type == 'masquerade':
            action = "伪装"
        
        elif expr_type == 'redir':
            action = "重定向"
    
    # 构建最终显示字符串
    result_parts = []
    
    # 添加端口信息（如果有）
    if port_info:
        result_parts.append(port_info)
    
    # 添加其他信息
    if parts:
        result_parts.append(" ".join(parts))
    
    # 添加动作
    if action:
        result_parts.append(action)
    
    if result_parts:
        return " ".join(result_parts)
    else:
        return " ".join(parts) if parts else "(复杂规则)"

def get_rule_summary(ruleset_data=None):
    """获取规则摘要统计（INPUT链）"""
    try:
        if ruleset_data is None:
            result = subprocess.run(
                ['nft', '-j', 'list', 'ruleset'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            ruleset_data = json.loads(result.stdout)
        
        if not ruleset_data.get('nftables'):
            return {'input_rules': 0, 'input_port_rules': 0}
        
        input_rules = 0
        input_port_rules = 0
        
        for item in ruleset_data['nftables']:
            if 'rule' in item:
                rule = item['rule']
                if rule.get('chain') == 'input' and rule.get('family') == 'ip' and rule.get('table') == 'filter':
                    input_rules += 1
                    expr = rule.get('expr', [])
                    rule_desc = format_rule_expression(expr)
                    if '端口' in rule_desc:
                        input_port_rules += 1
        
        return {
            'input_rules': input_rules,
            'input_port_rules': input_port_rules,
        }
        
    except Exception:
        return None

def export_rules():
    """导出当前规则到文件"""
    print("\n" + "=" * 60)
    print("导出防火墙规则")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ['nft', '-j', 'list', 'ruleset'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "未知错误"
            print(f"\n✗ 导出失败：{error_msg}")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nft_rules_backup_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        print(f"\n✓ 规则已导出到：{filename}")
        log_operation(f"导出规则到 {filename}")
        return True
        
    except Exception as e:
        print(f"\n✗ 导出失败：{e}")
        log_operation(f"导出失败：{e}")
        return False

def show_help():
    """显示帮助信息"""
    print("\n" + "=" * 60)
    print("帮助信息")
    print("=" * 60)
    print("""
本工具用于简化nftables防火墙规则的管理。

主要功能：
1. 创建防火墙规则 - 添加允许或拒绝的流量规则
2. 完整协议模式 - 快速配置常见服务的防火墙规则
3. 查询当前规则 - 查看现有防火墙配置
4. 导出规则 - 备份当前防火墙规则
5. 支持多种网络协议 - TCP、UDP、ICMP等
6. 灵活的端口配置 - 支持单个端口、端口范围、多个端口
7. 操作日志记录 - 记录所有操作的详细日志
8. 系统安装 - 可安装到系统目录全局使用

使用提示：
- 始终仔细检查生成的命令后再执行
- 使用完整协议模式可以快速配置常见服务
- 输入过程中可随时输入 'menu' 返回上级菜单
- 在确认执行时可输入 'c' 自定义命令
- 定期导出备份防火墙规则

常见端口参考：
- SSH: 22
- HTTP: 80
- HTTPS: 443
- FTP: 21
- MySQL: 3306
- PostgreSQL: 5432
- DNS: 53
- SMTP: 25
- POP3: 110
- IMAP: 143
    """)
    print("=" * 60)
    input("\n按回车键返回主菜单...")

def main():
    """主函数"""
    log_operation("程序启动")
    print_header()
    print("\n欢迎使用nft命令执行辅助工具！")
    print("输入帮助信息查看详细使用指南。")
    
    while True:
        print("\n" + "=" * 50)
        print("主菜单")
        print("=" * 50)
        print("1. 创建新的nft规则")
        print("2. 完整协议模式（预设服务配置）")
        print("3. 查询当前防火墙规则")
        print("4. 导出规则到文件")
        print("5. 初始化防火墙表")
        print("6. 查看帮助信息")
        print("7. 安装指南")
        print("8. 安装到系统")
        print("9. 卸载")
        print("10. 退出")
        
        choice = input("\n请输入选项编号: ").strip()
        
        if choice == '1':
            log_operation("用户选择了创建新的nft规则")
            
            action = get_action()
            if action is None:
                continue
            
            protocol = get_protocol()
            if protocol is None:
                continue
            
            if protocol == 'full_mode':
                protocol_info = get_full_protocol_mode()
                if protocol_info is None:
                    continue
                
                commands = generate_nft_command(
                    action, 
                    protocol_info['protocol'], 
                    protocol_info['ports'],
                    is_full_mode=True
                )
            else:
                port = get_port()
                if port is None:
                    continue
                
                is_valid, message = validate_protocol_port(protocol, port)
                if not is_valid:
                    print(f"✗ {message}")
                    continue
                
                ip_address = get_ip_address()
                if ip_address is None:
                    continue
                
                commands = generate_nft_command(action, protocol, port, ip_address=ip_address)
                if commands is None:
                    print("✗ 端口范围无效，起始端口必须小于等于结束端口")
                    continue
            
            execute_command(commands)
            
        elif choice == '2':
            log_operation("用户选择了完整协议模式")
            print("\n完整协议模式 - 快速配置常用服务")
            
            protocol_info = get_full_protocol_mode()
            if protocol_info is None:
                continue
            
            action = get_action()
            if action is None:
                continue
            
            commands = generate_nft_command(
                action,
                protocol_info['protocol'],
                protocol_info['ports'],
                is_full_mode=True
            )
            
            execute_command(commands)
            
        elif choice == '3':
            query_nft_rules()
            input("\n按回车键返回主菜单...")
            
        elif choice == '4':
            export_rules()
            input("\n按回车键返回主菜单...")
            
        elif choice == '5':
            init_nftables_filter_table()
            input("\n按回车键返回主菜单...")
            
        elif choice == '6':
            show_help()
            
        elif choice == '7':
            show_install_help()
            
        elif choice == '8':
            install_program()
            
        elif choice == '9':
            uninstall_program()
            
        elif choice == '10':
            print("\n感谢使用nft命令执行辅助工具，再见！")
            log_operation("程序退出")
            break
        
        else:
            print("✗ 无效输入，请重新选择。")

def delete_rule_menu():
    """删除规则菜单"""
    print("\n" + "=" * 60)
    print("删除防火墙规则")
    print("=" * 60)
    
    print("\n删除规则需要知道规则的位置和handle号")
    print("-" * 60)
    print("使用说明：")
    print("1. 先使用 '3. 查询当前防火墙规则' 查看规则信息")
    print("2. 查看原始规则列表获取handle号")
    print("3. 记录下要删除规则的位置信息")
    print("-" * 60)
    
    print("\n选项：")
    print("1. 查看所有规则的handle号")
    print("2. 按端口搜索规则")
    print("3. 删除规则")
    print("4. 返回主菜单")
    
    sub_choice = input("\n请选择操作: ").strip()
    
    if sub_choice == '1':
        print("\n显示所有规则的handle号：")
        print("-" * 60)
        result = subprocess.run(
            ['nft', '-a', 'list', 'ruleset'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("无法获取规则列表。")
        print("-" * 60)
        
    elif sub_choice == '2':
        port = input("\n输入要搜索的端口号: ").strip()
        if port:
            matches = search_rules_by_port(port, 'tcp')
            if matches:
                print(f"\n找到 {len(matches)} 条相关规则：")
                for i, match in enumerate(matches, 1):
                    print(f"[{i}] {match['family']}::{match['table']} -> {match['chain']}")
                    print(f"    完整规则: {match['rule']}")
            else:
                print(f"未找到端口 {port} 的规则")
        else:
            print("端口号不能为空")
    
    elif sub_choice == '3':
        print("\n删除规则")
        print("格式: family table chain handle")
        print("例如: ip filter input 10")
        print("\n先查看handle号列表，选择要删除的规则")
        
        delete_input = input("\n输入规则信息: ").strip()
        
        parts = delete_input.split()
        if len(parts) == 4:
            family, table, chain = parts[0], parts[1], parts[2]
            try:
                handle = int(parts[3])
                confirm = input(f"\n确认删除规则？\n{family} {table} {chain} handle {handle}\n(直接回车确认): ").strip().lower()
                if confirm == '' or confirm == 'y':
                    delete_nft_rule(family, table, chain, handle)
                else:
                    print("取消删除。")
            except ValueError:
                print("✗ handle必须是数字！")
        else:
            print("✗ 格式错误！")
            print("正确格式: family table chain handle")
            print("例如: ip filter input 10")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n检测到用户中断，程序退出。")
        log_operation("用户中断程序")
    except Exception as e:
        print(f"\n程序发生错误：{e}")
        log_operation(f"程序错误：{e}")
