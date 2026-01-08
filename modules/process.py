"""
进程管理模块
"""

from typing import Dict
from .base import BaseModule

class ProcessModule(BaseModule):
    """进程管理模块"""

    def get_description(self) -> str:
        """获取模块描述"""
        return "管理系统进程"

    def get_actions(self) -> Dict[str, str]:
        """获取模块支持的操作及其描述"""
        return {
            "list": "列出进程",
            "kill": "终止进程",
            "tree": "显示进程树",
            "search": "搜索进程",
            "info": "显示进程详细信息",
            "nice": "调整进程优先级",
            "limit": "设置进程资源限制"
        }

    def _handle_list(self, value: str, params: Dict[str, str]) -> int:
        """
        列出进程

        Args:
            value: 未使用
            params: 参数字典，可能包含 user, sort, format 等

        Returns:
            执行结果状态码
        """
        # 构建ps命令
        command = ["ps", "aux"]

        # 如果指定了user参数，使用grep过滤
        if "user" in params:
            user = params["user"]
            command.extend(["|", "grep", user])

        # 如果指定了sort参数，使用sort排序
        if "sort" in params:
            sort_field = params["sort"]
            command.extend(["|", "sort", "-k", sort_field])

        # 如果指定了format参数，使用awk格式化输出
        if "format" in params:
            format_str = params["format"]
            command.extend(["|", "awk", f"'{format_str}'"])

        return self._run_command(command, check=False)

    def _handle_kill(self, pid: str, params: Dict[str, str]) -> int:
        """
        终止进程

        Args:
            pid: 进程ID
            params: 参数字典，可能包含 signal, force 等

        Returns:
            执行结果状态码
        """
        # 构建kill命令
        command = ["kill"]

        # 添加信号参数
        signal = params.get("signal", "15")  # 默认使用SIGTERM
        command.append(f"-{signal}")

        # 如果指定了force参数且为真，使用SIGKILL信号
        if params.get("force", "").lower() in ("true", "yes", "1"):
            command = ["kill", "-9"]

        command.append(pid)
        return self._run_command(command)

    def _handle_tree(self, value: str, params: Dict[str, str]) -> int:
        """
        显示进程树

        Args:
            value: 未使用
            params: 参数字典，可能包含 pid, format 等

        Returns:
            执行结果状态码
        """
        # 构建pstree命令
        command = ["pstree"]

        # 如果指定了pid参数，只显示特定进程树
        if "pid" in params:
            command.append(params["pid"])

        # 如果指定了format参数，添加相应选项
        if "format" in params:
            format_type = params["format"]
            if format_type == "pid":
                command.append("-p")
            elif format_type == "user":
                command.append("-u")
            elif format_type == "compact":
                command.append("-c")

        return self._run_command(command)

    def _handle_search(self, name: str, params: Dict[str, str]) -> int:
        """
        搜索进程

        Args:
            name: 进程名称
            params: 参数字典，可能包含 exact, user 等

        Returns:
            执行结果状态码
        """
        # 使用pgrep命令搜索进程
        command = ["pgrep"]

        # 如果指定了exact参数且为真，精确匹配进程名
        if params.get("exact", "").lower() in ("true", "yes", "1"):
            command.append("-x")

        # 如果指定了user参数，只搜索特定用户的进程
        if "user" in params:
            command.extend(["-u", params["user"]])

        # 添加-l选项显示进程名
        command.append("-l")

        command.append(name)
        return self._run_command(command)

    def _handle_info(self, pid: str, params: Dict[str, str]) -> int:
        """
        显示进程详细信息

        Args:
            pid: 进程ID
            params: 参数字典，可能包含 detail 等

        Returns:
            执行结果状态码
        """
        # 使用ps命令显示进程详细信息
        command = ["ps", "-p", pid]

        # 如果指定了detail参数且为真，显示更详细的信息
        if params.get("detail", "").lower() in ("true", "yes", "1"):
            command.extend(["-o", "pid,ppid,user,%cpu,%mem,vsz,rss,tty,stat,start,time,command"])

        return self._run_command(command)

    def _handle_nice(self, pid: str, params: Dict[str, str]) -> int:
        """
        调整进程优先级

        Args:
            pid: 进程ID
            params: 参数字典，可能包含 priority, increment 等

        Returns:
            执行结果状态码
        """
        # 如果指定了priority参数，使用renice命令设置绝对优先级
        if "priority" in params:
            priority = params["priority"]
            command = ["sudo", "renice", priority, pid]
            return self._run_command(command)

        # 如果指定了increment参数，使用renice命令调整相对优先级
        if "increment" in params:
            increment = params["increment"]
            # 获取当前优先级
            get_prio_cmd = ["ps", "-o", "nice", "-p", pid, "|", "tail", "-1"]
            result = self._run_command(get_prio_cmd, check=False)

            if result != 0:
                return result

            # 计算新优先级并设置
            # 这里简化处理，实际应用中可能需要更复杂的逻辑
            command = ["sudo", "renice", f"{increment}", pid]
            return self._run_command(command)

        # 默认使用nice命令启动新进程
        print("错误：nice操作需要指定priority或increment参数")
        return 1

    def _handle_limit(self, pid: str, params: Dict[str, str]) -> int:
        """
        设置进程资源限制

        Args:
            pid: 进程ID
            params: 参数字典，可能包含 resource, value 等

        Returns:
            执行结果状态码
        """
        if "resource" not in params or "value" not in params:
            print("错误：limit操作需要指定resource和value参数")
            return 1

        resource = params["resource"]
        value = params["value"]

        # 构建prlimit命令
        command = ["sudo", "prlimit"]

        # 添加资源限制参数
        if resource == "cpu":
            command.extend(["--cpu", value])
        elif resource == "memory":
            command.extend(["--as", value])
        elif resource == "nofile":
            command.extend(["--nofile", value])
        elif resource == "nproc":
            command.extend(["--nproc", value])
        else:
            print(f"错误：不支持的资源类型 '{resource}'")
            return 1

        # 添加进程ID
        command.append(pid)

        return self._run_command(command)
