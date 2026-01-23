"""
USC基础模块类
所有具体模块都应继承此类
"""

import datetime
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from typing import Any, Dict, List

import toml

from .toml_output import TomlOutputMixin

logger = logging.getLogger(__name__)

class BaseModule(ABC, TomlOutputMixin):
    """USC模块基类"""

    def __init__(self):
        self.name = self.__class__.__name__.lower().replace('module', '')
        self.description = ""
        self.actions = {}
        self.output_format = "toml"  # 默认输出格式为TOML
        self.output_file = None  # 输出文件路径
        self.config = {}  # 模块配置
        self._load_config()  # 加载配置文件

    @abstractmethod
    def get_description(self) -> str:
        """获取模块描述"""
        pass

    @abstractmethod
    def get_actions(self) -> Dict[str, str]:
        """获取模块支持的操作及其描述"""
        pass

    def get_boolean_params(self, action: str = None) -> Dict[str, List[str]]:
        """
        获取布尔参数列表

        Args:
            action: 操作名称，如果提供则返回该操作的布尔参数，否则返回所有操作的布尔参数

        Returns:
            布尔参数字典，格式为 {action: [param1, param2, ...]}
        """
        return {}

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
        # 检查out参数
        output_file = None
        if "out" in params:
            out_param = params["out"]
            if not out_param:
                print("错误：out参数不能为空")
                return 1

            # 处理out参数
            if out_param.startswith("/") or out_param.startswith("./"):
                # 绝对路径或相对路径
                if out_param.endswith(".toml"):
                    output_file = out_param
                else:
                    output_file = f"{out_param}/usc-{self._get_timestamp()}.toml"
            else:
                # 相对路径或文件名
                if out_param.endswith(".toml"):
                    output_file = out_param
                else:
                    output_file = f"{out_param}/usc-{self._get_timestamp()}.toml"

            # 设置输出文件
            self._set_output_file(output_file)

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

    def _run_command_capture(self, command: List[str], check: bool = True):
        """
        执行系统命令并捕获输出

        Args:
            command: 要执行的命令列表
            check: 是否检查返回码

        Returns:
            包含 returncode, stdout, stderr 的对象
        """
        try:
            logger.debug(f"执行命令: {' '.join(command)}")
            result = subprocess.run(
                command,
                check=check,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            # 返回异常结果，但仍然包含输出信息
            return e
        except FileNotFoundError:
            # 返回一个模拟的结果对象
            class NotFoundResult:
                def __init__(self):
                    self.returncode = 1
                    self.stdout = ""
                    self.stderr = f"找不到命令 '{command[0]}'"
            return NotFoundResult()
        except Exception as e:
            class ErrorResult:
                def __init__(self, msg):
                    self.returncode = 1
                    self.stdout = ""
                    self.stderr = str(msg)
            return ErrorResult(e)

    def _get_timestamp(self) -> str:
        """
        获取当前时间戳

        Returns:
            格式化的时间字符串
        """
        return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    def _load_config(self):
        """
        加载模块配置文件
        从 /etc/usc/{模块名}.toml 加载配置
        """
        config_path = f"/etc/usc/{self.name}.toml"
        self.config = {}

        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = toml.load(f)
                logger.debug(f"已加载配置文件: {config_path}")
            else:
                logger.warning(f"配置文件不存在: {config_path}，使用代码默认值")
        except PermissionError:
            logger.error(f"无法读取配置文件 {config_path} (权限拒绝)")
            print(f"警告：无法读取配置文件 {config_path} (权限拒绝)")
        except toml.TomlDecodeError as e:
            logger.error(f"配置文件格式错误 {config_path}: {e}")
            print(f"警告：配置文件格式错误: {e}，使用代码默认值")
        except Exception as e:
            logger.error(f"加载配置文件失败 {config_path}: {e}")
            print(f"警告：加载配置文件失败: {e}，使用代码默认值")

    def _get_param_value(self, key: str, action: str = None,
                         params: Dict[str, str] = None, fallback: Any = None) -> Any:
        """
        获取参数值，实现三层优先级
        优先级: 命令行参数 > 操作级配置 > 全局配置 > 代码默认值

        Args:
            key: 参数名
            action: 操作名
            params: 命令行参数字典
            fallback: 代码默认值

        Returns:
            参数值
        """
        # 第一优先级：命令行参数
        if params and key in params:
            return params[key]

        # 第二优先级：操作级配置
        if action:
            action_config = self.config.get('default', {}).get(action, {})
            if key in action_config:
                return action_config[key]

        # 第三优先级：全局配置
        global_config = self.config.get('default', {})
        if key in global_config and not isinstance(global_config[key], dict):
            return global_config[key]

        # 第四优先级：代码默认值
        return fallback

    def _get_action_config(self, action: str) -> Dict[str, Any]:
        """
        获取特定操作的配置
        合并全局配置和操作级配置

        Args:
            action: 操作名

        Returns:
            合并后的配置字典
        """
        global_config = self.config.get('default', {})
        action_config = global_config.get(action, {}).copy()

        # 移除嵌套的配置节，只保留参数
        result = {}
        for key, value in action_config.items():
            if not isinstance(value, dict):
                result[key] = value

        return result

    def _convert_bool(self, value: Any, default: bool = False) -> bool:
        """
        转换布尔值

        Args:
            value: 要转换的值
            default: 默认值

        Returns:
            布尔值
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "on")
        if isinstance(value, (int, float)):
            return bool(value)
        return default

    def _get_bool_param_value(self, key: str, action: str = None,
                              params: Dict[str, str] = None, fallback: Any = None) -> Any:
        """
        获取布尔参数值，支持空值默认为 true

        如果参数存在于 params 中但值为空字符串，则返回 "true"
        否则按照原有的优先级规则返回值

        Args:
            key: 参数名
            action: 操作名
            params: 命令行参数字典
            fallback: 代码默认值

        Returns:
            参数值
        """
        # 第一优先级：命令行参数
        if params and key in params:
            value = params[key]
            # 如果参数值为空字符串，默认为 true
            if value == "":
                return "true"
            return value

        # 第二优先级：操作级配置
        if action:
            action_config = self.config.get('default', {}).get(action, {})
            if key in action_config:
                return action_config[key]

        # 第三优先级：全局配置
        global_config = self.config.get('default', {})
        if key in global_config and not isinstance(global_config[key], dict):
            return global_config[key]

        # 第四优先级：代码默认值
        return fallback

    def _convert_list(self, value: Any, separator: str = ",") -> List[str]:
        """
        转换列表值

        Args:
            value: 要转换的值
            separator: 分隔符

        Returns:
            列表
        """
        if isinstance(value, list):
            return [str(v).strip() for v in value]
        if isinstance(value, str):
            return [item.strip() for item in value.split(separator) if item.strip()]
        return []
