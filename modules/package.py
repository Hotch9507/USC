
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


    # 这些方法需要添加到package.py文件末尾

    def _help_install(self) -> Dict:
        """安装软件包操作的帮助信息"""
        return {
            "module": "package",
            "action": "install",
            "description": "安装软件包",
            "parameters": {
                "repo": "指定软件仓库",
                "arch": "指定架构",
                "version": "指定版本"
            },
            "usage": "usc package install:<package_name> repo:<repository> arch:<architecture> version:<version>"
        }

    def _help_remove(self) -> Dict:
        """删除软件包操作的帮助信息"""
        return {
            "module": "package",
            "action": "remove",
            "description": "删除软件包",
            "parameters": {
                "autoremove": "是否自动删除不需要的依赖，值为true/false",
                "purge": "是否完全删除包括配置文件，值为true/false"
            },
            "usage": "usc package remove:<package_name> autoremove:<true/false> purge:<true/false>"
        }

    def _help_update(self) -> Dict:
        """更新软件包操作的帮助信息"""
        return {
            "module": "package",
            "action": "update",
            "description": "更新软件包",
            "parameters": {
                "repo": "指定软件仓库",
                "security": "是否只更新安全补丁，值为true/false"
            },
            "usage": "usc package update:<package_name|all> repo:<repository> security:<true/false>"
        }

    def _help_search(self) -> Dict:
        """搜索软件包操作的帮助信息"""
        return {
            "module": "package",
            "action": "search",
            "description": "搜索软件包",
            "parameters": {
                "repo": "指定软件仓库",
                "arch": "指定架构",
                "exact": "是否精确匹配，值为true/false"
            },
            "usage": "usc package search:<keyword> repo:<repository> arch:<architecture> exact:<true/false>"
        }

    def _help_list(self) -> Dict:
        """列出软件包操作的帮助信息"""
        return {
            "module": "package",
            "action": "list",
            "description": "列出已安装的软件包",
            "parameters": {
                "repo": "指定软件仓库",
                "arch": "指定架构",
                "out": "输出文件路径，可以是目录路径或完整文件路径（默认输出到控制台）"
            },
            "usage": "usc package list:<all|installed|updates> repo:<repository> arch:<architecture> out:<path>",
            "notes": [
                "使用out参数可将输出保存到TOML格式的文件中",
                "out:/path/to/dir - 输出到指定目录，文件名自动生成为usc-时间戳.toml",
                "out:/path/to/file.toml - 输出到指定文件"
            ]
        }

    def _help_info(self) -> Dict:
        """显示软件包信息操作的帮助信息"""
        return {
            "module": "package",
            "action": "info",
            "description": "显示软件包详细信息",
            "parameters": {
                "repo": "指定软件仓库",
                "version": "指定版本"
            },
            "usage": "usc package info:<package_name> repo:<repository> version:<version>"
        }
