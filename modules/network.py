"""
网络管理模块
"""

from typing import Dict
from .base import BaseModule

class NetworkModule(BaseModule):
    """网络管理模块"""

    def get_description(self) -> str:
        """获取模块描述"""
        return "管理系统网络配置和连接"

    def get_actions(self) -> Dict[str, str]:
        """获取模块支持的操作及其描述"""
        return {
            "iface": "管理网络接口",
            "conn": "管理网络连接",
            "ping": "测试网络连通性",
            "port": "管理端口",
            "firewall": "管理防火墙规则",
            "dns": "管理DNS配置",
            "route": "管理路由表",
            "scan": "扫描网络"
        }

    def _handle_iface(self, action: str, params: Dict[str, str]) -> int:
        """
        管理网络接口

        Args:
            action: 操作类型，可以是 up, down, show, config
            params: 参数字典，可能包含 name, ip, mask, gateway 等

        Returns:
            执行结果状态码
        """
        if action == "up":
            if "name" not in params:
                print("错误：缺少接口名称参数 'name'")
                return 1

            # 启用网络接口
            command = ["sudo", "ip", "link", "set", params["name"], "up"]
            return self._run_command(command)

        elif action == "down":
            if "name" not in params:
                print("错误：缺少接口名称参数 'name'")
                return 1

            # 禁用网络接口
            command = ["sudo", "ip", "link", "set", params["name"], "down"]
            return self._run_command(command)

        elif action == "show":
            # 显示网络接口信息
            command = ["ip", "addr", "show"]

            # 如果指定了name参数，只显示特定接口
            if "name" in params:
                command.append(params["name"])

            return self._run_command(command)

        elif action == "config":
            if "name" not in params:
                print("错误：缺少接口名称参数 'name'")
                return 1

            name = params["name"]

            # 配置IP地址
            if "ip" in params:
                ip = params["ip"]
                mask = params.get("mask", "24")
                command = ["sudo", "ip", "addr", "add", f"{ip}/{mask}", "dev", name]
                result = self._run_command(command)

                # 如果配置失败，直接返回
                if result != 0:
                    return result

            # 配置网关
            if "gateway" in params:
                gateway = params["gateway"]
                command = ["sudo", "ip", "route", "add", "default", "via", gateway]
                result = self._run_command(command)

                # 如果配置失败，直接返回
                if result != 0:
                    return result

            return 0

        else:
            print(f"错误：未知操作 '{action}'")
            return 1

    def _handle_conn(self, action: str, params: Dict[str, str]) -> int:
        """
        管理网络连接

        Args:
            action: 操作类型，可以是 list, close
            params: 参数字典，可能包含 proto, state, port 等

        Returns:
            执行结果状态码
        """
        if action == "list":
            # 构建ss命令
            command = ["ss"]

            # 添加协议参数
            if "proto" in params:
                command.extend(["-t" if params["proto"] == "tcp" else "-u"])

            # 添加状态参数
            if "state" in params:
                command.extend(["state", params["state"]])

            # 添加端口参数
            if "port" in params:
                command.extend(["sport", f":{params['port']}"])

            return self._run_command(command)

        elif action == "close":
            if "pid" not in params and "fd" not in params:
                print("错误：缺少进程ID 'pid' 或文件描述符 'fd' 参数")
                return 1

            # 使用ss命令关闭连接
            command = ["ss"]

            if "pid" in params:
                command.extend(["-K", "-p"])

            if "fd" in params:
                command.extend(["-K"])

            return self._run_command(command)

        else:
            print(f"错误：未知操作 '{action}'")
            return 1

    def _handle_ping(self, host: str, params: Dict[str, str]) -> int:
        """
        测试网络连通性

        Args:
            host: 目标主机
            params: 参数字典，可能包含 count, interval, size 等

        Returns:
            执行结果状态码
        """
        # 构建ping命令
        command = ["ping"]

        # 添加计数参数
        if "count" in params:
            command.extend(["-c", params["count"]])

        # 添加间隔参数
        if "interval" in params:
            command.extend(["-i", params["interval"]])

        # 添加数据包大小参数
        if "size" in params:
            command.extend(["-s", params["size"]])

        command.append(host)
        return self._run_command(command)

    def _handle_port(self, action: str, params: Dict[str, str]) -> int:
        """
        管理端口

        Args:
            action: 操作类型，可以是 list, listen, connect
            params: 参数字典，可能包含 port, proto, host 等

        Returns:
            执行结果状态码
        """
        if action == "list":
            # 构建netstat命令
            command = ["netstat", "-tuln"]

            # 如果指定了port参数，使用grep过滤
            if "port" in params:
                port = params["port"]
                command.extend(["|", "grep", f":{port}"])

            return self._run_command(command, check=False)

        elif action == "listen":
            if "port" not in params:
                print("错误：缺少端口号参数 'port'")
                return 1

            port = params["port"]
            proto = params.get("proto", "tcp")

            # 使用nc命令监听端口
            command = ["nc", "-l"]

            if proto == "udp":
                command.append("-u")

            command.append(port)
            return self._run_command(command)

        elif action == "connect":
            if "port" not in params or "host" not in params:
                print("错误：缺少端口号参数 'port' 或主机参数 'host'")
                return 1

            port = params["port"]
            host = params["host"]
            proto = params.get("proto", "tcp")

            # 使用nc命令连接端口
            command = ["nc"]

            if proto == "udp":
                command.append("-u")

            command.extend([host, port])
            return self._run_command(command)

        else:
            print(f"错误：未知操作 '{action}'")
            return 1

    def _handle_firewall(self, action: str, params: Dict[str, str]) -> int:
        """
        管理防火墙规则

        Args:
            action: 操作类型，可以是 list, add, del
            params: 参数字典，可能包含 chain, rule, table 等

        Returns:
            执行结果状态码
        """
        if action == "list":
            # 构建iptables命令
            command = ["sudo", "iptables", "-L"]

            # 如果指定了table参数，添加-t选项
            if "table" in params:
                command.extend(["-t", params["table"]])

            # 如果指定了chain参数，只显示特定链
            if "chain" in params:
                command.append(params["chain"])

            return self._run_command(command)

        elif action == "add":
            if "rule" not in params:
                print("错误：缺少规则参数 'rule'")
                return 1

            rule = params["rule"]
            chain = params.get("chain", "INPUT")
            table = params.get("table", "filter")

            # 构建iptables命令
            command = ["sudo", "iptables", "-t", table, "-A", chain]

            # 解析规则参数
            rule_parts = rule.split()
            command.extend(rule_parts)

            return self._run_command(command)

        elif action == "del":
            if "rule" not in params:
                print("错误：缺少规则参数 'rule'")
                return 1

            rule = params["rule"]
            chain = params.get("chain", "INPUT")
            table = params.get("table", "filter")

            # 构建iptables命令
            command = ["sudo", "iptables", "-t", table, "-D", chain]

            # 解析规则参数
            rule_parts = rule.split()
            command.extend(rule_parts)

            return self._run_command(command)

        else:
            print(f"错误：未知操作 '{action}'")
            return 1

    def _handle_dns(self, action: str, params: Dict[str, str]) -> int:
        """
        管理DNS配置

        Args:
            action: 操作类型，可以是 query, set, add, del
            params: 参数字典，可能包含 domain, server, record 等

        Returns:
            执行结果状态码
        """
        if action == "query":
            if "domain" not in params:
                print("错误：缺少域名参数 'domain'")
                return 1

            domain = params["domain"]
            server = params.get("server", "")

            # 构建dig命令
            command = ["dig"]

            if server:
                command.extend(["@", server])

            command.append(domain)
            return self._run_command(command)

        elif action == "set":
            if "servers" not in params:
                print("错误：缺少DNS服务器参数 'servers'")
                return 1

            servers = params["servers"]

            # 构建resolvconf命令
            command = ["sudo", "resolvconf", "-a"]

            # 解析服务器列表
            server_list = servers.split(",")
            for server in server_list:
                command.extend(["-a", f"nameserver {server.strip()}"])

            return self._run_command(command)

        elif action == "add":
            if "record" not in params or "zone" not in params:
                print("错误：缺少记录参数 'record' 或区域参数 'zone'")
                return 1

            record = params["record"]
            zone = params["zone"]

            # 构建nsupdate命令
            command = ["nsupdate"]

            # 添加记录
            command.extend(["-l", f"update add {record}"])

            return self._run_command(command)

        elif action == "del":
            if "record" not in params or "zone" not in params:
                print("错误：缺少记录参数 'record' 或区域参数 'zone'")
                return 1

            record = params["record"]
            zone = params["zone"]

            # 构建nsupdate命令
            command = ["nsupdate"]

            # 删除记录
            command.extend(["-l", f"update delete {record}"])

            return self._run_command(command)

        else:
            print(f"错误：未知操作 '{action}'")
            return 1

    def _handle_route(self, action: str, params: Dict[str, str]) -> int:
        """
        管理路由表

        Args:
            action: 操作类型，可以是 list, add, del
            params: 参数字典，可能包含 destination, gateway, device 等

        Returns:
            执行结果状态码
        """
        if action == "list":
            # 构建ip route命令
            command = ["ip", "route", "show"]

            return self._run_command(command)

        elif action == "add":
            if "destination" not in params:
                print("错误：缺少目标地址参数 'destination'")
                return 1

            destination = params["destination"]
            gateway = params.get("gateway", "")
            device = params.get("device", "")

            # 构建ip route命令
            command = ["sudo", "ip", "route", "add", destination]

            if gateway:
                command.extend(["via", gateway])

            if device:
                command.extend(["dev", device])

            return self._run_command(command)

        elif action == "del":
            if "destination" not in params:
                print("错误：缺少目标地址参数 'destination'")
                return 1

            destination = params["destination"]

            # 构建ip route命令
            command = ["sudo", "ip", "route", "del", destination]

            return self._run_command(command)

        else:
            print(f"错误：未知操作 '{action}'")
            return 1

    def _handle_scan(self, target: str, params: Dict[str, str]) -> int:
        """
        扫描网络

        Args:
            target: 目标地址或网络
            params: 参数字典，可能包含 ports, type, speed 等

        Returns:
            执行结果状态码
        """
        # 构建nmap命令
        command = ["nmap"]

        # 添加端口参数
        if "ports" in params:
            command.extend(["-p", params["ports"]])

        # 添加扫描类型参数
        if "type" in params:
            scan_type = params["type"]
            if scan_type == "syn":
                command.append("-sS")
            elif scan_type == "udp":
                command.append("-sU")
            elif scan_type == "ping":
                command.append("-sn")

        # 添加速度参数
        if "speed" in params:
            speed = params["speed"]
            if speed.isdigit():
                command.extend(["-T", speed])

        command.append(target)
        return self._run_command(command)
