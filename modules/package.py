
"""
包管理模块
"""

from typing import Dict
from .base import BaseModule
from .distro_adapter import DistroAdapter

class PackageModule(BaseModule):
    """包管理模块"""

    def __init__(self):
        super().__init__()
        self.distro_adapter = DistroAdapter()

    def get_description(self) -> str:
        """获取模块描述"""
        return "管理系统软件包"

    def get_actions(self) -> Dict[str, str]:
        """获取模块支持的操作及其描述"""
        return {
            "install": "安装软件包",
            "remove": "删除软件包",
            "update": "更新软件包",
            "search": "搜索软件包",
            "list": "列出已安装的软件包",
            "info": "显示软件包详细信息"
        }

    def _handle_install(self, package_name: str, params: Dict[str, str]) -> int:
        """
        安装软件包

        Args:
            package_name: 软件包名称
            params: 参数字典，可能包含 repo, arch, version 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取包管理命令
            cmd, need_sudo = self.distro_adapter.get_package_command("install", package_name, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_remove(self, package_name: str, params: Dict[str, str]) -> int:
        """
        删除软件包

        Args:
            package_name: 软件包名称
            params: 参数字典，可能包含 autoremove, purge 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取包管理命令
            cmd, need_sudo = self.distro_adapter.get_package_command("remove", package_name, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_update(self, package_name: str, params: Dict[str, str]) -> int:
        """
        更新软件包

        Args:
            package_name: 软件包名称，"all"表示更新所有软件包
            params: 参数字典，可能包含 repo, security 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取包管理命令
            cmd, need_sudo = self.distro_adapter.get_package_command("update", package_name, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_search(self, keyword: str, params: Dict[str, str]) -> int:
        """
        搜索软件包

        Args:
            keyword: 搜索关键词
            params: 参数字典，可能包含 repo, arch, exact 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取包管理命令
            cmd, need_sudo = self.distro_adapter.get_package_command("search", keyword, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_list(self, filter_type: str, params: Dict[str, str]) -> int:
        """
        列出已安装的软件包

        Args:
            filter_type: 过滤类型，可以是 all, installed, updates 等
            params: 参数字典，可能包含 repo, arch 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取包管理命令
            cmd, need_sudo = self.distro_adapter.get_package_command("list", filter_type, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)

    def _handle_info(self, package_name: str, params: Dict[str, str]) -> int:
        """
        显示软件包详细信息

        Args:
            package_name: 软件包名称
            params: 参数字典，可能包含 repo, version 等

        Returns:
            执行结果状态码
        """
        try:
            # 使用发行版适配器获取包管理命令
            cmd, need_sudo = self.distro_adapter.get_package_command("info", package_name, **params)

            # 执行命令
            return self._run_command(cmd)
        except ValueError as e:
            return self._output_error(str(e), 1)
