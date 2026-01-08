#!/usr/bin/env python3
"""
USC - Unified Shell Command
统一命令翻译兼容层
"""

import sys
import argparse
from typing import Dict, List, Optional, Any

# 导入所有模块
from modules import user, file, network, system, process, service, disk, package, group

# 模块映射表
MODULE_MAP = {
    'user': user.UserModule,
    'file': file.FileModule,
    'network': network.NetworkModule,
    'system': system.SystemModule,
    'process': process.ProcessModule,
    'service': service.ServiceModule,
    'disk': disk.DiskModule,
    'package': package.PackageModule,
    'group': group.GroupModule,
}

class USC:
    def __init__(self):
        self.modules = {}
        self._load_modules()
        self.help_module = None

    def _load_modules(self):
        """加载所有模块"""
        for name, module_class in MODULE_MAP.items():
            self.modules[name] = module_class()

        # 初始化帮助模块
        from .modules import help
        self.help_module = help.HelpModule(self.modules)

    def execute(self, args: List[str]) -> int:
        """
        执行USC命令

        Args:
            args: 命令行参数列表

        Returns:
            执行结果状态码，0表示成功，非0表示失败
        """
        if not args:
            self._show_help()
            return 1

        # 解析全局参数
        output_format = "toml"  # 默认输出格式
        filtered_args = []
        i = 0

        while i < len(args):
            if args[i] == "--output" and i + 1 < len(args):
                output_format = args[i + 1]
                i += 2
            else:
                filtered_args.append(args[i])
                i += 1

        args = filtered_args

        if not args:
            self._show_help()
            return 1

        # 检查是否是帮助命令
        if args[0] == "help" or args[0].endswith(":help"):
            return self._handle_help(args[0], args[1:])

        # 解析命令
        module_name = args[0]

        if module_name not in self.modules:
            print(f"错误：未知模块 '{module_name}'")
            self._show_modules()
            return 1

        module = self.modules[module_name]

        # 设置模块输出格式
        module.output_format = output_format

        if len(args) < 2:
            print(f"错误：模块 '{module_name}' 缺少操作参数")
            module.show_help()
            return 1

        # 解析操作和参数
        try:
            action, value = self._parse_action(args[1])
            params = self._parse_params(args[2:])
            return module.execute(action, value, params)
        except Exception as e:
            print(f"错误：{e}")
            return 1

    def _parse_action(self, action_str: str) -> tuple:
        """
        解析操作字符串

        Args:
            action_str: 操作字符串，格式为 "action:value"

        Returns:
            (action, value) 元组
        """
        if ':' not in action_str:
            raise ValueError("操作参数格式错误，应为 'action:value'")

        action, value = action_str.split(':', 1)
        if not action or not value:
            raise ValueError("操作和值不能为空")

        return action, value

    def _parse_params(self, param_list: List[str]) -> Dict[str, str]:
        """
        解析参数列表

        Args:
            param_list: 参数列表，每个元素格式为 "param:value"

        Returns:
            参数字典
        """
        params = {}
        for param in param_list:
            if ':' not in param:
                raise ValueError(f"参数格式错误: '{param}'，应为 'param:value'")

            key, value = param.split(':', 1)
            if not key:
                raise ValueError(f"参数名不能为空: '{param}'")

            params[key] = value

        return params

    def _show_help(self):
        """显示帮助信息"""
        print("USC - Unified Shell Command")
        print("用法: usc [--output FORMAT] <module> <action>:<value> [parameter:value] [...]")
        print("")
        print("选项:")
        print("  --output FORMAT  输出格式，可以是 toml（默认）或 raw")
        print("")
        print("可用模块:")
        self._show_modules()

    def _show_modules(self):
        """显示所有可用模块"""
        for name in self.modules:
            print(f"  {name} - {self.modules[name].get_description()}")

    def _handle_help(self, help_cmd: str, args: List[str]) -> int:
        """
        处理帮助命令

        Args:
            help_cmd: 帮助命令，可以是 "help" 或 "module:help"
            args: 其他参数

        Returns:
            执行结果状态码
        """
        # 设置帮助模块的输出格式
        self.help_module.output_format = "toml"

        if help_cmd == "help":
            # 如果是 "help" 命令
            if not args:
                # 没有参数，显示所有模块
                return self.help_module.execute("modules", "", {})
            else:
                # 有参数，显示特定模块的帮助
                return self.help_module.execute("module", args[0], {})
        else:
            # 如果是 "module:help" 命令
            module_name = help_cmd.replace(":help", "")
            return self.help_module.execute("module", module_name, {})

def main():
    """主函数"""
    usc = USC()
    return usc.execute(sys.argv[1:])

if __name__ == "__main__":
    sys.exit(main())
