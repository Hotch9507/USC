"""
发行版适配器模块
处理不同Linux发行版之间的命令差异
"""

import logging
import platform
import re
import subprocess
from typing import List, Tuple

logger = logging.getLogger(__name__)

class DistroAdapter:
    """发行版适配器，处理不同Linux发行版之间的命令差异"""

    def __init__(self):
        self.distro_id = self._detect_distro()
        self.distro_version = self._detect_distro_version()
        self.package_manager = self._detect_package_manager()

        logger.info(f"检测到发行版: {self.distro_id} {self.distro_version}")
        logger.info(f"包管理器: {self.package_manager}")

    def _detect_distro(self) -> str:
        """检测Linux发行版"""
        # 尝试从/etc/os-release读取
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('ID='):
                        return line.strip().split('=')[1].strip('"')
        except (FileNotFoundError, PermissionError):
            pass

        # 尝试从/etc/redhat-release读取
        try:
            with open('/etc/redhat-release', 'r') as f:
                content = f.read().lower()
                if 'centos' in content:
                    return 'centos'
                elif 'rhel' in content or 'red hat' in content:
                    return 'rhel'
                elif 'fedora' in content:
                    return 'fedora'
        except (FileNotFoundError, PermissionError):
            pass

        # 尝试使用platform模块
        try:
            distro = platform.linux_distribution()[0].lower()
            if 'ubuntu' in distro:
                return 'ubuntu'
            elif 'debian' in distro:
                return 'debian'
            elif 'centos' in distro:
                return 'centos'
            elif 'rhel' in distro or 'red hat' in distro:
                return 'rhel'
            elif 'fedora' in distro:
                return 'fedora'
        except:
            pass

        # 默认返回unknown
        return 'unknown'

    def _detect_distro_version(self) -> str:
        """检测Linux发行版版本"""
        # 尝试从/etc/os-release读取
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('VERSION_ID='):
                        return line.strip().split('=')[1].strip('"')
        except (FileNotFoundError, PermissionError):
            pass

        # 尝试从/etc/redhat-release读取
        try:
            with open('/etc/redhat-release', 'r') as f:
                content = f.read()
                # 提取版本号
                match = re.search(r'(\d+\.?\d*)', content)
                if match:
                    return match.group(1)
        except (FileNotFoundError, PermissionError):
            pass

        # 默认返回unknown
        return 'unknown'

    def _detect_package_manager(self) -> str:
        """检测包管理器"""
        # 检测是否有yum/dnf
        if self._command_exists('dnf'):
            return 'dnf'
        elif self._command_exists('yum'):
            return 'yum'

        # 检测是否有apt
        elif self._command_exists('apt'):
            return 'apt'

        # 检测是否有apt-get
        elif self._command_exists('apt-get'):
            return 'apt-get'

        # 检测是否有zypper
        elif self._command_exists('zypper'):
            return 'zypper'

        # 检测是否有pacman
        elif self._command_exists('pacman'):
            return 'pacman'

        # 默认返回unknown
        return 'unknown'

    def _command_exists(self, command: str) -> bool:
        """检查命令是否存在"""
        try:
            subprocess.run(['which', command], check=True, 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False

    def get_package_command(self, action: str, package_name: str = None, **kwargs) -> Tuple[List[str], bool]:
        """
        获取包管理命令

        Args:
            action: 操作类型，可以是 install, remove, update, search, info, list
            package_name: 包名
            **kwargs: 其他参数

        Returns:
            (命令列表, 是否需要sudo) 元组
        """
        # 根据包管理器返回相应的命令
        if self.package_manager == 'dnf':
            return self._get_dnf_command(action, package_name, **kwargs)
        elif self.package_manager == 'yum':
            return self._get_yum_command(action, package_name, **kwargs)
        elif self.package_manager == 'apt':
            return self._get_apt_command(action, package_name, **kwargs)
        elif self.package_manager == 'apt-get':
            return self._get_apt_get_command(action, package_name, **kwargs)
        elif self.package_manager == 'zypper':
            return self._get_zypper_command(action, package_name, **kwargs)
        elif self.package_manager == 'pacman':
            return self._get_pacman_command(action, package_name, **kwargs)
        else:
            raise ValueError(f"不支持的包管理器: {self.package_manager}")

    def get_service_command(self, action: str, service_name: str = None, **kwargs) -> Tuple[List[str], bool]:
        """
        获取服务管理命令

        Args:
            action: 操作类型，可以是 start, stop, restart, status, enable, disable, list
            service_name: 服务名
            **kwargs: 其他参数

        Returns:
            (命令列表, 是否需要sudo) 元组
        """
        # 检测系统服务管理器
        if self._command_exists('systemctl'):
            return self._get_systemctl_command(action, service_name, **kwargs)
        elif self._command_exists('service'):
            return self._get_service_command(action, service_name, **kwargs)
        else:
            raise ValueError("不支持的系统服务管理器")

    def _get_systemctl_command(self, action: str, service_name: str = None, **kwargs) -> Tuple[List[str], bool]:
        """获取systemctl命令"""
        need_sudo = True

        if action == "list":
            cmd = ["systemctl", "list-units", "--type=service", "--all"]

            # 如果指定了state参数，过滤服务状态
            if "state" in kwargs:
                cmd.extend(["--state", kwargs["state"]])

            need_sudo = False

        elif action in ("start", "stop", "restart", "status", "enable", "disable"):
            if not service_name:
                raise ValueError(f"{action} 操作需要指定服务名称")

            cmd = ["systemctl", action, service_name]

            # status操作不需要sudo
            if action == "status":
                need_sudo = False

        else:
            raise ValueError(f"不支持的systemctl操作: {action}")

        return cmd, need_sudo

    def _get_service_command(self, action: str, service_name: str = None, **kwargs) -> Tuple[List[str], bool]:
        """获取service命令"""
        need_sudo = True

        if action == "list":
            cmd = ["service", "--status-all"]
            need_sudo = False

        elif action in ("start", "stop", "restart", "status"):
            if not service_name:
                raise ValueError(f"{action} 操作需要指定服务名称")

            cmd = ["service", service_name, action]

            # status操作不需要sudo
            if action == "status":
                need_sudo = False

        elif action == "enable":
            if not service_name:
                raise ValueError("enable 操作需要指定服务名称")

            # 使用chkconfig启用服务
            cmd = ["chkconfig", service_name, "on"]

        elif action == "disable":
            if not service_name:
                raise ValueError("disable 操作需要指定服务名称")

            # 使用chkconfig禁用服务
            cmd = ["chkconfig", service_name, "off"]

        else:
            raise ValueError(f"不支持的service操作: {action}")

        return cmd, need_sudo

    def _get_dnf_command(self, action: str, package_name: str = None, **kwargs) -> Tuple[List[str], bool]:
        """获取DNF命令"""
        need_sudo = True

        if action == "install":
            cmd = ["sudo", "dnf", "install", "-y"]
            if package_name:
                cmd.append(package_name)
        elif action == "remove":
            cmd = ["sudo", "dnf", "remove", "-y"]
            if package_name:
                cmd.append(package_name)
        elif action == "update":
            cmd = ["sudo", "dnf", "update", "-y"]
            if package_name:
                cmd.append(package_name)
        elif action == "search":
            cmd = ["dnf", "search"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        elif action == "info":
            cmd = ["dnf", "info"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        elif action == "list":
            cmd = ["dnf", "list", "installed"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        else:
            raise ValueError(f"不支持的DNF操作: {action}")

        return cmd, need_sudo

    def _get_yum_command(self, action: str, package_name: str = None, **kwargs) -> Tuple[List[str], bool]:
        """获取YUM命令"""
        need_sudo = True

        if action == "install":
            cmd = ["sudo", "yum", "install", "-y"]
            if package_name:
                cmd.append(package_name)
        elif action == "remove":
            cmd = ["sudo", "yum", "remove", "-y"]
            if package_name:
                cmd.append(package_name)
        elif action == "update":
            cmd = ["sudo", "yum", "update", "-y"]
            if package_name:
                cmd.append(package_name)
        elif action == "search":
            cmd = ["yum", "search"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        elif action == "info":
            cmd = ["yum", "info"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        elif action == "list":
            cmd = ["yum", "list", "installed"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        else:
            raise ValueError(f"不支持的YUM操作: {action}")

        return cmd, need_sudo

    def _get_apt_command(self, action: str, package_name: str = None, **kwargs) -> Tuple[List[str], bool]:
        """获取APT命令"""
        need_sudo = True

        if action == "install":
            cmd = ["sudo", "apt", "install", "-y"]
            if package_name:
                cmd.append(package_name)
        elif action == "remove":
            cmd = ["sudo", "apt", "remove", "-y"]
            if package_name:
                cmd.append(package_name)
        elif action == "update":
            cmd = ["sudo", "apt", "update"]
            if kwargs.get("upgrade", False):
                cmd = ["sudo", "apt", "upgrade", "-y"]
        elif action == "search":
            cmd = ["apt", "search"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        elif action == "info":
            cmd = ["apt", "show"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        elif action == "list":
            cmd = ["apt", "list", "--installed"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        else:
            raise ValueError(f"不支持的APT操作: {action}")

        return cmd, need_sudo

    def _get_apt_get_command(self, action: str, package_name: str = None, **kwargs) -> Tuple[List[str], bool]:
        """获取APT-GET命令"""
        need_sudo = True

        if action == "install":
            cmd = ["sudo", "apt-get", "install", "-y"]
            if package_name:
                cmd.append(package_name)
        elif action == "remove":
            cmd = ["sudo", "apt-get", "remove", "-y"]
            if package_name:
                cmd.append(package_name)
        elif action == "update":
            cmd = ["sudo", "apt-get", "update"]
            if kwargs.get("upgrade", False):
                cmd = ["sudo", "apt-get", "upgrade", "-y"]
        elif action == "search":
            cmd = ["apt-cache", "search"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        elif action == "info":
            cmd = ["apt-cache", "show"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        elif action == "list":
            cmd = ["dpkg", "-l"]
            if package_name:
                cmd.extend(["|", "grep", package_name])
            need_sudo = False
        else:
            raise ValueError(f"不支持的APT-GET操作: {action}")

        return cmd, need_sudo

    def _get_zypper_command(self, action: str, package_name: str = None, **kwargs) -> Tuple[List[str], bool]:
        """获取Zypper命令"""
        need_sudo = True

        if action == "install":
            cmd = ["sudo", "zypper", "install", "-y"]
            if package_name:
                cmd.append(package_name)
        elif action == "remove":
            cmd = ["sudo", "zypper", "remove", "-y"]
            if package_name:
                cmd.append(package_name)
        elif action == "update":
            cmd = ["sudo", "zypper", "refresh"]
            if kwargs.get("upgrade", False):
                cmd = ["sudo", "zypper", "update", "-y"]
        elif action == "search":
            cmd = ["zypper", "search"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        elif action == "info":
            cmd = ["zypper", "info"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        elif action == "list":
            cmd = ["zypper", "search", "-i"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        else:
            raise ValueError(f"不支持的Zypper操作: {action}")

        return cmd, need_sudo

    def _get_pacman_command(self, action: str, package_name: str = None, **kwargs) -> Tuple[List[str], bool]:
        """获取Pacman命令"""
        need_sudo = True

        if action == "install":
            cmd = ["sudo", "pacman", "-S", "--noconfirm"]
            if package_name:
                cmd.append(package_name)
        elif action == "remove":
            cmd = ["sudo", "pacman", "-R", "--noconfirm"]
            if package_name:
                cmd.append(package_name)
        elif action == "update":
            cmd = ["sudo", "pacman", "-Syu", "--noconfirm"]
        elif action == "search":
            cmd = ["pacman", "-Ss"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        elif action == "info":
            cmd = ["pacman", "-Si"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        elif action == "list":
            cmd = ["pacman", "-Q"]
            if package_name:
                cmd.append(package_name)
            need_sudo = False
        else:
            raise ValueError(f"不支持的Pacman操作: {action}")

        return cmd, need_sudo

    def get_service_command(self, action: str, service_name: str = None) -> Tuple[List[str], bool]:
        """
        获取服务管理命令

        Args:
            action: 操作类型，可以是 start, stop, restart, status, enable, disable, list
            service_name: 服务名

        Returns:
            (命令列表, 是否需要sudo) 元组
        """
        # 检测是否有systemctl
        if self._command_exists('systemctl'):
            return self._get_systemctl_command(action, service_name)
        # 检测是否有service
        elif self._command_exists('service'):
            return self._get_service_command(action, service_name)
        else:
            raise ValueError("系统中找不到systemctl或service命令")

    def _get_systemctl_command(self, action: str, service_name: str = None) -> Tuple[List[str], bool]:
        """获取systemctl命令"""
        need_sudo = True

        if action == "start":
            cmd = ["sudo", "systemctl", "start"]
            if service_name:
                cmd.append(service_name)
        elif action == "stop":
            cmd = ["sudo", "systemctl", "stop"]
            if service_name:
                cmd.append(service_name)
        elif action == "restart":
            cmd = ["sudo", "systemctl", "restart"]
            if service_name:
                cmd.append(service_name)
        elif action == "status":
            cmd = ["systemctl", "status"]
            if service_name:
                cmd.append(service_name)
            need_sudo = False
        elif action == "enable":
            cmd = ["sudo", "systemctl", "enable"]
            if service_name:
                cmd.append(service_name)
        elif action == "disable":
            cmd = ["sudo", "systemctl", "disable"]
            if service_name:
                cmd.append(service_name)
        elif action == "list":
            cmd = ["systemctl", "list-units", "--type=service", "--all"]
            need_sudo = False
        else:
            raise ValueError(f"不支持的systemctl操作: {action}")

        return cmd, need_sudo

    def _get_service_command(self, action: str, service_name: str = None) -> Tuple[List[str], bool]:
        """获取service命令"""
        need_sudo = True

        if action == "start":
            cmd = ["sudo", "service", service_name, "start"] if service_name else ["sudo", "service"]
        elif action == "stop":
            cmd = ["sudo", "service", service_name, "stop"] if service_name else ["sudo", "service"]
        elif action == "restart":
            cmd = ["sudo", "service", service_name, "restart"] if service_name else ["sudo", "service"]
        elif action == "status":
            cmd = ["service", service_name, "status"] if service_name else ["service"]
            need_sudo = False
        elif action in ("enable", "disable"):
            # service命令不支持enable/disable，使用chkconfig
            cmd = ["sudo", "chkconfig", service_name, action]
        elif action == "list":
            cmd = ["service", "--status-all"]
            need_sudo = False
        else:
            raise ValueError(f"不支持的service操作: {action}")

        return cmd, need_sudo

    def get_firewall_command(self, action: str, rule: str = None, table: str = "filter", chain: str = "INPUT") -> Tuple[List[str], bool]:
        """
        获取防火墙命令

        Args:
            action: 操作类型，可以是 list, add, del
            rule: 防火墙规则
            table: 表名，默认为filter
            chain: 链名，默认为INPUT

        Returns:
            (命令列表, 是否需要sudo) 元组
        """
        # 检测是否有firewalld
        if self._command_exists('firewall-cmd'):
            return self._get_firewalld_command(action, rule)
        # 检测是否有ufw
        elif self._command_exists('ufw'):
            return self._get_ufw_command(action, rule)
        # 默认使用iptables
        else:
            return self._get_iptables_command(action, rule, table, chain)

    def _get_firewalld_command(self, action: str, rule: str = None) -> Tuple[List[str], bool]:
        """获取firewalld命令"""
        need_sudo = True

        if action == "list":
            cmd = ["sudo", "firewall-cmd", "--list-all"]
            need_sudo = False
        elif action == "add":
            # 规则格式: "port=80/tcp"
            if "=" in rule:
                key, value = rule.split("=", 1)
                if key == "port":
                    cmd = ["sudo", "firewall-cmd", "--permanent", "--add-port", value]
                elif key == "service":
                    cmd = ["sudo", "firewall-cmd", "--permanent", "--add-service", value]
                else:
                    raise ValueError(f"不支持的firewalld规则类型: {key}")
            else:
                raise ValueError("firewalld规则格式应为: key=value")
        elif action == "del":
            # 规则格式: "port=80/tcp"
            if "=" in rule:
                key, value = rule.split("=", 1)
                if key == "port":
                    cmd = ["sudo", "firewall-cmd", "--permanent", "--remove-port", value]
                elif key == "service":
                    cmd = ["sudo", "firewall-cmd", "--permanent", "--remove-service", value]
                else:
                    raise ValueError(f"不支持的firewalld规则类型: {key}")
            else:
                raise ValueError("firewalld规则格式应为: key=value")
        else:
            raise ValueError(f"不支持的firewalld操作: {action}")

        return cmd, need_sudo

    def _get_ufw_command(self, action: str, rule: str = None) -> Tuple[List[str], bool]:
        """获取UFW命令"""
        need_sudo = True

        if action == "list":
            cmd = ["sudo", "ufw", "status", "verbose"]
        elif action == "add":
            # 规则格式: "allow 80/tcp" 或 "deny 22"
            cmd = ["sudo", "ufw", rule]
        elif action == "del":
            # 规则格式: "allow 80/tcp" 或 "deny 22"
            cmd = ["sudo", "ufw", "delete", rule]
        else:
            raise ValueError(f"不支持的UFW操作: {action}")

        return cmd, need_sudo

    def _get_iptables_command(self, action: str, rule: str = None, table: str = "filter", chain: str = "INPUT") -> Tuple[List[str], bool]:
        """获取iptables命令"""
        need_sudo = True

        if action == "list":
            cmd = ["sudo", "iptables", "-t", table, "-L", chain, "-n", "-v"]
        elif action == "add":
            # 规则格式: "-p tcp --dport 80 -j ACCEPT"
            cmd = ["sudo", "iptables", "-t", table, "-A", chain]
            if rule:
                cmd.extend(rule.split())
        elif action == "del":
            # 规则格式: "-p tcp --dport 80 -j ACCEPT"
            cmd = ["sudo", "iptables", "-t", table, "-D", chain]
            if rule:
                cmd.extend(rule.split())
        else:
            raise ValueError(f"不支持的iptables操作: {action}")

        return cmd, need_sudo


# 全局发行版适配器实例
_distro_adapter = None

def get_distro_adapter() -> DistroAdapter:
    """获取全局发行版适配器实例"""
    global _distro_adapter
    if _distro_adapter is None:
        _distro_adapter = DistroAdapter()
    return _distro_adapter
