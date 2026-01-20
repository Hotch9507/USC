"""
服务管理模块
"""

from typing import Dict

from .base import BaseModule
from .distro_adapter import DistroAdapter


class ServiceModule(BaseModule):
    """服务管理模块"""

    def __init__(self):
        super().__init__()
        self.distro_adapter = DistroAdapter()

    def get_description(self) -> str:
        """获取模块描述"""
        return "管理系统服务"

    def get_actions(self) -> Dict[str, str]:
        """获取模块支持的操作及其描述"""
        return {
            "list": "列出服务",
            "start": "启动服务",
            "stop": "停止服务",
            "restart": "重启服务",
            "status": "查看服务状态",
            "enable": "启用服务自启动",
            "disable": "禁用服务自启动",
            "mask": "屏蔽服务",
            "unmask": "取消屏蔽服务"
        }

    def get_boolean_params(self, action: str = None) -> Dict[str, List[str]]:
        """
        获取布尔参数列表

        Returns:
            布尔参数字典，格式为 {action: [param1, param2, ...]}
        """
        boolean_params = {
            "list": ["detail"],
            "start": [],
            "stop": [],
            "restart": [],
            "status": [],
            "enable": ["now"],
            "disable": ["now"],
            "mask": [],
            "unmask": []
        }
        return boolean_params

    def _handle_list(self, value: str, params: Dict[str, str]) -> int:
        """
        列出服务

        Args:
            value: 未使用
            params: 参数字典，可能包含 state, type 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取服务管理命令
            cmd, need_sudo = self.distro_adapter.get_service_command("list", None, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_start(self, service_name: str, params: Dict[str, str]) -> int:
        """
        启动服务

        Args:
            service_name: 服务名称
            params: 参数字典，可能包含 timeout 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取服务管理命令
            cmd, need_sudo = self.distro_adapter.get_service_command("start", service_name, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_stop(self, service_name: str, params: Dict[str, str]) -> int:
        """
        停止服务

        Args:
            service_name: 服务名称
            params: 参数字典，可能包含 timeout 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取服务管理命令
            cmd, need_sudo = self.distro_adapter.get_service_command("stop", service_name, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_restart(self, service_name: str, params: Dict[str, str]) -> int:
        """
        重启服务

        Args:
            service_name: 服务名称
            params: 参数字典，可能包含 timeout 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取服务管理命令
            cmd, need_sudo = self.distro_adapter.get_service_command("restart", service_name, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_status(self, service_name: str, params: Dict[str, str]) -> int:
        """
        查看服务状态

        Args:
            service_name: 服务名称
            params: 参数字典，可能包含 detail 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取服务管理命令
            cmd, need_sudo = self.distro_adapter.get_service_command("status", service_name, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_enable(self, service_name: str, params: Dict[str, str]) -> int:
        """
        启用服务自启动

        Args:
            service_name: 服务名称
            params: 参数字典，可能包含 now 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取服务管理命令
            cmd, need_sudo = self.distro_adapter.get_service_command("enable", service_name, **params)

            # 执行命令
            result = self._run_command(cmd)

            # 如果指定了now参数且为真，同时启动服务
            if result == 0 and params.get("now", "").lower() in ("true", "yes", "1"):
                cmd, _ = self.distro_adapter.get_service_command("start", service_name, **params)
                result = self._run_command(cmd)

            return result
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_disable(self, service_name: str, params: Dict[str, str]) -> int:
        """
        禁用服务自启动

        Args:
            service_name: 服务名称
            params: 参数字典，可能包含 now 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取服务管理命令
            cmd, need_sudo = self.distro_adapter.get_service_command("disable", service_name, **params)

            # 执行命令
            result = self._run_command(cmd)

            # 如果指定了now参数且为真，同时停止服务
            if result == 0 and params.get("now", "").lower() in ("true", "yes", "1"):
                cmd, _ = self.distro_adapter.get_service_command("stop", service_name, **params)
                result = self._run_command(cmd)

            return result
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_mask(self, service_name: str, params: Dict[str, str]) -> int:
        """
        屏蔽服务

        Args:
            service_name: 服务名称
            params: 参数字典，可能包含 runtime 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取服务管理命令
            cmd, need_sudo = self.distro_adapter.get_service_command("mask", service_name, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_unmask(self, service_name: str, params: Dict[str, str]) -> int:
        """
        取消屏蔽服务

        Args:
            service_name: 服务名称
            params: 参数字典，可能包含 runtime 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取服务管理命令
            cmd, need_sudo = self.distro_adapter.get_service_command("unmask", service_name, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)
