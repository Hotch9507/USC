"""
TOML格式输出模块
"""

import datetime
import json
import logging
import os
from typing import Any, Dict

import toml

logger = logging.getLogger(__name__)

class TomlOutputMixin:
    """TOML输出混入类，为模块添加TOML格式输出功能"""

    def _output_toml(self, data: Dict[str, Any], pretty: bool = True) -> int:
        """
        以TOML格式输出数据

        Args:
            data: 要输出的数据字典
            pretty: 是否格式化输出

        Returns:
            状态码，0表示成功
        """
        try:
            # 确保数据是字典类型
            if not isinstance(data, dict):
                logger.error("输出数据必须是字典类型")
                return 1

            # 添加元数据
            output_data = {
                "module": self.name,
                "status": "success",
                "data": data
            }

            # 输出TOML格式数据
            toml_str = toml.dumps(output_data)

            # 如果设置了输出文件，则写入文件
            if hasattr(self, 'output_file') and self.output_file:
                self._write_to_file(toml_str)
            else:
                # 否则输出到控制台
                print(toml_str)

            return 0
        except Exception as e:
            logger.error(f"TOML输出失败: {e}")
            return 1

    def _output_error(self, message: str, code: int = 1) -> int:
        """
        以TOML格式输出错误信息

        Args:
            message: 错误消息
            code: 错误码

        Returns:
            错误码
        """
        try:
            error_data = {
                "module": self.name,
                "status": "error",
                "error": {
                    "message": message,
                    "code": code
                }
            }

            # 输出TOML格式错误信息
            toml_str = toml.dumps(error_data)

            # 如果设置了输出文件，则写入文件
            if hasattr(self, 'output_file') and self.output_file:
                self._write_to_file(toml_str)
            else:
                # 否则输出到控制台
                print(toml_str)

            return code
        except Exception as e:
            logger.error(f"错误信息输出失败: {e}")
            return code

    def _parse_command_output(self, output: str, format_type: str = "auto") -> Dict[str, Any]:
        """
        解析命令输出为结构化数据

        Args:
            output: 命令输出文本
            format_type: 输出格式类型，可以是 auto, json, table, list, keyval

        Returns:
            结构化数据字典
        """
        if format_type == "auto":
            # 自动检测格式
            if output.strip().startswith('{') and output.strip().endswith('}'):
                format_type = "json"
            elif '\t' in output or '  ' in output:
                format_type = "table"
            elif '\n' in output and '=' in output:
                format_type = "keyval"
            else:
                format_type = "list"

        if format_type == "json":
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                logger.warning("无法解析JSON格式输出，回退到列表格式")
                format_type = "list"

        if format_type == "table":
            return self._parse_table_output(output)
        elif format_type == "keyval":
            return self._parse_keyval_output(output)
        else:  # list
            return {"items": output.splitlines()}

    def _parse_table_output(self, output: str) -> Dict[str, Any]:
        """
        解析表格格式输出

        Args:
            output: 表格格式文本

        Returns:
            结构化数据字典
        """
        lines = output.strip().splitlines()
        if not lines:
            return {"headers": [], "rows": []}

        # 尝试确定分隔符
        first_line = lines[0]
        if '\t' in first_line:
            delimiter = '\t'
        elif '  ' in first_line:
            delimiter = '  '
        else:
            delimiter = None

        # 分割行
        if delimiter:
            headers = first_line.split(delimiter)
            rows = [line.split(delimiter) for line in lines[1:]]
        else:
            # 如果没有明确的分隔符，尝试智能分割
            headers = first_line.split()
            rows = [line.split() for line in lines[1:]]

        return {
            "headers": headers,
            "rows": rows
        }

    def _parse_keyval_output(self, output: str) -> Dict[str, Any]:
        """
        解析键值对格式输出

        Args:
            output: 键值对格式文本

        Returns:
            结构化数据字典
        """
        data = {}
        for line in output.strip().splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                data[key.strip()] = value.strip()

        return data

    def _set_output_file(self, output_file: str):
        """
        设置输出文件路径

        Args:
            output_file: 输出文件路径
        """
        # 确保目录存在
        dir_path = os.path.dirname(output_file)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        self.output_file = output_file

    def _write_to_file(self, content: str):
        """
        将内容写入输出文件

        Args:
            content: 要写入的内容
        """
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"输出已保存到: {self.output_file}")
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            print(f"错误：无法写入文件 {self.output_file}: {e}")

    def _get_timestamp(self) -> str:
        """
        获取当前时间戳

        Returns:
            格式化的时间字符串
        """
        return datetime.datetime.now().strftime("%Y%m%d%H%M%S")
