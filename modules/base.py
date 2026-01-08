"""
USC基础模块类
所有具体模块都应继承此类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import subprocess
import logging
from .toml_output import TomlOutputMixin

logger = logging.getLogger(__name__)

class BaseModule(ABC, TomlOutputMixin):
    """USC模块基类"""

    def __init__(self):
        self.name = self.__class__.__name__.lower().replace('module', '')
        self.description = ""
        self.actions = {}
        self.output_format = "toml"  # 默认输出格式为TOML

    @abstractmethod
    def get_description(self) -> str:
        """获取模块描述"""
        pass

    @abstractmethod
    def get_actions(self) -> Dict[str, str]:
        """获取模块支持的操作及其描述"""
        pass

    def execute(self, action: str, value: str, params: Dict[str, str]) -> int:
        """
        执行模块操作

        Args:
            action: 操作名称
            value: 操作值
            params: 参数字典

        Returns:
            执行结果状态码，0表示成功，非0表示失败
        """
        if action not in self.get_actions():
            print(f"错误：未知操作 '{action}'")
            self.show_help()
            return 1

        # 调用具体的操作处理方法
        method_name = f"_handle_{action}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(value, params)
        else:
            print(f"错误：操作 '{action}' 尚未实现")
            return 1

    def show_help(self):
        """显示模块帮助信息"""
        print(f"{self.name} 模块 - {self.get_description()}")
        print("")
        print("支持的操作:")
        for action, desc in self.get_actions().items():
            print(f"  {action} - {desc}")

    def _run_command(self, command: List[str], check: bool = True, output_format: str = None) -> int:
        """
        执行系统命令

        Args:
            command: 要执行的命令列表
            check: 是否检查返回码
            output_format: 输出格式，可以是 toml, raw, auto

        Returns:
            命令执行状态码，0表示成功，非0表示失败
        """
        # 使用实例默认输出格式或指定的输出格式
        fmt = output_format or self.output_format

        try:
            logger.debug(f"执行命令: {' '.join(command)}")
            result = subprocess.run(
                command,
                check=check,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 根据输出格式处理结果
            if fmt == "toml":
                if result.returncode == 0:
                    # 解析命令输出
                    parsed_data = self._parse_command_output(result.stdout)
                    return self._output_toml(parsed_data)
                else:
                    return self._output_error(f"命令执行失败: {result.stderr}", result.returncode)
            else:  # raw 或其他格式
                if result.stdout:
                    print(result.stdout)

                if result.stderr and result.returncode != 0:
                    print(result.stderr)

                return result.returncode

        except subprocess.CalledProcessError as e:
            if fmt == "toml":
                return self._output_error(f"命令执行失败: {e}", e.returncode)
            else:
                print(f"命令执行失败: {e}")
                return e.returncode
        except FileNotFoundError:
            if fmt == "toml":
                return self._output_error(f"找不到命令 '{command[0]}'", 1)
            else:
                print(f"错误：找不到命令 '{command[0]}'")
                return 1
        except Exception as e:
            if fmt == "toml":
                return self._output_error(f"执行命令时发生错误: {e}", 1)
            else:
                print(f"执行命令时发生错误: {e}")
                return 1
