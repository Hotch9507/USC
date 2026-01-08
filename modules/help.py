"""
帮助模块
"""

from typing import Dict, List, Optional
from .base import BaseModule

class HelpModule(BaseModule):
    """帮助模块"""

    def __init__(self, module_map: Dict[str, BaseModule]):
        super().__init__()
        self.module_map = module_map

    def get_description(self) -> str:
        """获取模块描述"""
        return "显示帮助信息"

    def get_actions(self) -> Dict[str, str]:
        """获取模块支持的操作及其描述"""
        return {
            "modules": "列出所有可用模块",
            "module": "显示特定模块的帮助信息",
            "action": "显示特定操作的帮助信息",
            "examples": "显示使用示例"
        }

    def _handle_modules(self, value: str, params: Dict[str, str]) -> int:
        """
        列出所有可用模块

        Args:
            value: 未使用
            params: 参数字典

        Returns:
            执行结果状态码
        """
        modules_data = {
            "modules": []
        }

        for name, module in self.module_map.items():
            modules_data["modules"].append({
                "name": name,
                "description": module.get_description()
            })

        return self._output_toml(modules_data)

    def _handle_module(self, module_name: str, params: Dict[str, str]) -> int:
        """
        显示特定模块的帮助信息

        Args:
            module_name: 模块名称
            params: 参数字典

        Returns:
            执行结果状态码
        """
        if module_name not in self.module_map:
            return self._output_error(f"未知模块: {module_name}", 1)

        module = self.module_map[module_name]
        actions = module.get_actions()

        module_data = {
            "module": module_name,
            "description": module.get_description(),
            "actions": []
        }

        for action, desc in actions.items():
            module_data["actions"].append({
                "action": action,
                "description": desc
            })

        return self._output_toml(module_data)

    def _handle_action(self, action_path: str, params: Dict[str, str]) -> int:
        """
        显示特定操作的帮助信息

        Args:
            action_path: 操作路径，格式为 "module.action"
            params: 参数字典

        Returns:
            执行结果状态码
        """
        if "." not in action_path:
            return self._output_error("操作路径格式错误，应为 'module.action'", 1)

        module_name, action_name = action_path.split(".", 1)

        if module_name not in self.module_map:
            return self._output_error(f"未知模块: {module_name}", 1)

        module = self.module_map[module_name]
        actions = module.get_actions()

        if action_name not in actions:
            return self._output_error(f"未知操作: {action_name}", 1)

        # 获取操作的帮助信息
        help_method = getattr(module, f"_help_{action_name}", None)

        if help_method:
            help_data = help_method()
            return self._output_toml(help_data)
        else:
            # 如果没有特定的帮助方法，返回基本信息
            action_data = {
                "module": module_name,
                "action": action_name,
                "description": actions[action_name],
                "usage": f"usc {module_name} {action_name}:<value> [parameter:value] [...]"
            }

            return self._output_toml(action_data)

    def _handle_examples(self, value: str, params: Dict[str, str]) -> int:
        """
        显示使用示例

        Args:
            value: 未使用
            params: 参数字典

        Returns:
            执行结果状态码
        """
        examples_data = {
            "examples": [
                {
                    "command": "usc help modules",
                    "description": "列出所有可用模块"
                },
                {
                    "command": "usc help module:user",
                    "description": "显示用户模块的帮助信息"
                },
                {
                    "command": "usc help action:user.add",
                    "description": "显示添加用户操作的帮助信息"
                },
                {
                    "command": "usc user add:chenxi home:/home/chenxi",
                    "description": "添加用户chenxi，指定主目录"
                },
                {
                    "command": "usc file cp:/path/to/src dest:/path/to/dest",
                    "description": "复制文件或目录"
                },
                {
                    "command": "usc package install:vim",
                    "description": "安装vim软件包"
                },
                {
                    "command": "usc process list:all user:chenxi",
                    "description": "列出用户chenxi的所有进程"
                },
                {
                    "command": "usc service start:nginx",
                    "description": "启动nginx服务"
                },
                {
                    "command": "usc disk usage:/ human_readable:true",
                    "description": "显示根目录的磁盘使用情况，使用人类可读格式"
                }
            ]
        }

        return self._output_toml(examples_data)
