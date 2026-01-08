"""
系统管理模块
"""

from typing import Dict
from .base import BaseModule
from .distro_adapter import DistroAdapter

class SystemModule(BaseModule):
    """系统管理模块"""

    def __init__(self):
        super().__init__()
        self.distro_adapter = DistroAdapter()

    def get_description(self) -> str:
        """获取模块描述"""
        return "管理系统资源和配置"

    def get_actions(self) -> Dict[str, str]:
        """获取模块支持的操作及其描述"""
        return {
            "info": "显示系统信息",
            "service": "管理系统服务",
            "process": "管理进程",

            "log": "查看系统日志",
            "cron": "管理定时任务",
            "mount": "管理文件系统挂载",
            "shutdown": "系统关机和重启"
        }

    def _handle_info(self, item: str, params: Dict[str, str]) -> int:
        """
        显示系统信息

        Args:
            item: 信息类型，可以是 all, cpu, memory, disk, network 等
            params: 参数字典，可能包含 format, detail 等

        Returns:
            执行结果状态码
        """
        if item == "all":
            # 显示所有系统信息
            commands = [
                ["uname", "-a"],
                ["uptime"],
                ["free", "-h"],
                ["df", "-h"],
                ["ip", "addr", "show"]
            ]

            result = 0
            for cmd in commands:
                result = result or self._run_command(cmd)
                print("")  # 添加空行分隔

            return result

        elif item == "cpu":
            # 显示CPU信息
            if params.get("detail", "").lower() in ("true", "yes", "1"):
                command = ["lscpu"]
            else:
                command = ["cat", "/proc/cpuinfo", "|", "grep", "model name", "|", "uniq"]

            return self._run_command(command, check=False)

        elif item == "memory":
            # 显示内存信息
            command = ["free", "-h"]
            return self._run_command(command)

        elif item == "disk":
            # 显示磁盘信息
            command = ["df", "-h"]
            return self._run_command(command)

        elif item == "network":
            # 显示网络信息
            command = ["ip", "addr", "show"]
            return self._run_command(command)

        else:
            print(f"错误：未知信息类型 '{item}'")
            return 1

    def _handle_service(self, action: str, params: Dict[str, str]) -> int:
        """
        管理系统服务

        Args:
            action: 操作类型，可以是 start, stop, restart, status, enable, disable, list
            params: 参数字典，可能包含 name, state 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取服务管理命令
            service_name = params.get("name")
            cmd, need_sudo = self.distro_adapter.get_service_command(action, service_name, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_process(self, action: str, params: Dict[str, str]) -> int:
        """
        管理进程

        Args:
            action: 操作类型，可以是 list, kill, tree, search
            params: 参数字典，可能包含 pid, signal, name 等

        Returns:
            执行结果状态码
        """
        if action == "list":
            # 构建ps命令
            command = ["ps", "aux"]

            # 如果指定了name参数，使用grep过滤
            if "name" in params:
                name = params["name"]
                command.extend(["|", "grep", name])

            return self._run_command(command, check=False)

        elif action == "kill":
            if "pid" not in params:
                print("错误：kill 操作需要指定进程ID 'pid'")
                return 1

            pid = params["pid"]
            signal = params.get("signal", "15")  # 默认使用SIGTERM

            # 构建kill命令
            command = ["kill", f"-{signal}", pid]
            return self._run_command(command)

        elif action == "tree":
            # 构建pstree命令
            command = ["pstree"]

            # 如果指定了pid参数，只显示特定进程树
            if "pid" in params:
                command.append(params["pid"])

            return self._run_command(command)

        elif action == "search":
            if "name" not in params:
                print("错误：search 操作需要指定进程名称 'name'")
                return 1

            name = params["name"]

            # 使用pgrep命令搜索进程
            command = ["pgrep", "-l", name]
            return self._run_command(command)

        else:
            print(f"错误：未知操作 '{action}'")
            return 1

# 包管理功能已移至独立的package模块

    def _handle_service(self, action: str, params: Dict[str, str]) -> int:
        """
        管理系统服务

        Args:
            action: 操作类型，可以是 start, stop, restart, status, enable, disable, list
            params: 参数字典，可能包含 name, state 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取服务管理命令
            service_name = params.get("name")
            cmd, need_sudo = self.distro_adapter.get_service_command(action, service_name, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_log(self, source: str, params: Dict[str, str]) -> int:
        """
        查看系统日志

        Args:
            source: 日志源，可以是 system, kernel, service, auth 等
            params: 参数字典，可能包含 lines, since, until, follow 等

        Returns:
            执行结果状态码
        """
        # 构建journalctl命令
        command = ["journalctl"]

        if source == "system":
            # 系统日志
            pass  # 默认就是系统日志

        elif source == "kernel":
            # 内核日志
            command.append("-k")

        elif source == "service":
            # 服务日志
            if "name" not in params:
                print("错误：查看服务日志需要指定服务名称 'name'")
                return 1

            name = params["name"]
            command.extend(["-u", name])

        elif source == "auth":
            # 认证日志
            command.extend(["-f", "/var/log/auth.log"])

        else:
            print(f"错误：未知日志源 '{source}'")
            return 1

        # 添加行数参数
        if "lines" in params:
            command.extend(["-n", params["lines"]])

        # 添加起始时间参数
        if "since" in params:
            command.extend(["--since", params["since"]])

        # 添加结束时间参数
        if "until" in params:
            command.extend(["--until", params["until"]])

        # 添加跟踪参数
        if params.get("follow", "").lower() in ("true", "yes", "1"):
            command.append("-f")

        return self._run_command(command)

    def _handle_cron(self, action: str, params: Dict[str, str]) -> int:
        """
        管理定时任务

        Args:
            action: 操作类型，可以是 list, add, del, edit
            params: 参数字典，可能包含 expression, command, user 等

        Returns:
            执行结果状态码
        """
        if action == "list":
            # 构建crontab命令
            command = ["crontab", "-l"]

            # 如果指定了user参数，查看特定用户的定时任务
            if "user" in params:
                command.extend(["-u", params["user"]])

            return self._run_command(command)

        elif action == "edit":
            # 构建crontab命令
            command = ["crontab", "-e"]

            # 如果指定了user参数，编辑特定用户的定时任务
            if "user" in params:
                command.extend(["-u", params["user"]])

            return self._run_command(command)

        elif action == "add":
            if "expression" not in params or "command" not in params:
                print("错误：add 操作需要指定表达式 'expression' 和命令 'command'")
                return 1

            expression = params["expression"]
            command_str = params["command"]

            # 获取现有定时任务
            list_cmd = ["crontab", "-l"]
            result = self._run_command(list_cmd, check=False)

            # 添加新定时任务
            new_entry = f"{expression} {command_str}"
            add_cmd = ["echo", f"{new_entry}", "|", "crontab", "-"]
            return self._run_command(add_cmd, check=False)

        elif action == "del":
            # 删除所有定时任务
            if params.get("all", "").lower() in ("true", "yes", "1"):
                command = ["crontab", "-r"]
                return self._run_command(command)

            # 删除特定定时任务（需要先列出，然后过滤，再重新设置）
            else:
                print("错误：删除特定定时任务功能尚未实现")
                return 1

        else:
            print(f"错误：未知操作 '{action}'")
            return 1

    def _handle_mount(self, action: str, params: Dict[str, str]) -> int:
        """
        管理文件系统挂载

        Args:
            action: 操作类型，可以是 list, mount, unmount
            params: 参数字典，可能包含 device, path, type, options 等

        Returns:
            执行结果状态码
        """
        if action == "list":
            # 构建mount命令
            command = ["mount", "|", "column", "-t"]

            return self._run_command(command, check=False)

        elif action == "mount":
            if "device" not in params or "path" not in params:
                print("错误：mount 操作需要指定设备 'device' 和挂载点 'path'")
                return 1

            device = params["device"]
            path = params["path"]

            # 构建mount命令
            command = ["sudo", "mount"]

            # 添加类型参数
            if "type" in params:
                command.extend(["-t", params["type"]])

            # 添加选项参数
            if "options" in params:
                command.extend(["-o", params["options"]])

            command.extend([device, path])
            return self._run_command(command)

        elif action == "unmount":
            if "path" not in params:
                print("错误：unmount 操作需要指定挂载点 'path'")
                return 1

            path = params["path"]

            # 构建umount命令
            command = ["sudo", "umount", path]

            # 如果指定了force参数且为真，添加-f选项
            if params.get("force", "").lower() in ("true", "yes", "1"):
                command.append("-f")

            return self._run_command(command)

        else:
            print(f"错误：未知操作 '{action}'")
            return 1

    def _handle_shutdown(self, action: str, params: Dict[str, str]) -> int:
        """
        系统关机和重启

        Args:
            action: 操作类型，可以是 shutdown, reboot, halt, poweroff
            params: 参数字典，可能包含 time, message 等

        Returns:
            执行结果状态码
        """
        if action == "shutdown":
            # 构建shutdown命令
            command = ["sudo", "shutdown"]

            # 添加时间参数
            if "time" in params:
                command.append(params["time"])
            else:
                command.append("now")  # 默认立即关机

            # 添加消息参数
            if "message" in params:
                command.append(params["message"])

            return self._run_command(command)

        elif action == "reboot":
            # 构建reboot命令
            command = ["sudo", "reboot"]
            return self._run_command(command)

        elif action == "halt":
            # 构建halt命令
            command = ["sudo", "halt"]
            return self._run_command(command)

        elif action == "poweroff":
            # 构建poweroff命令
            command = ["sudo", "poweroff"]
            return self._run_command(command)

        else:
            print(f"错误：未知操作 '{action}'")
            return 1
