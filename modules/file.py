"""
文件管理模块
"""

import os
import shutil
from typing import Dict
from .base import BaseModule

class FileModule(BaseModule):
    """文件管理模块"""

    def get_description(self) -> str:
        """获取模块描述"""
        return "管理系统文件和目录"

    def get_actions(self) -> Dict[str, str]:
        """获取模块支持的操作及其描述"""
        return {
            "cp": "复制文件或目录",
            "mv": "移动或重命名文件或目录",
            "rm": "删除文件或目录",
            "mkdir": "创建目录",
            "cat": "显示文件内容",
            "edit": "编辑文件",
            "find": "查找文件",
            "info": "显示文件或目录信息"
        }

    def _handle_cp(self, source: str, params: Dict[str, str]) -> int:
        """
        复制文件或目录

        Args:
            source: 源路径
            params: 参数字典，必须包含 dest，可能包含 recursive, force 等

        Returns:
            执行结果状态码
        """
        if "dest" not in params:
            print("错误：缺少目标路径参数 'dest'")
            return 1

        dest = params["dest"]

        # 构建cp命令
        command = ["cp"]

        # 如果指定了recursive参数且为真，添加-r选项
        if params.get("recursive", "").lower() in ("true", "yes", "1"):
            command.append("-r")

        # 如果指定了force参数且为真，添加-f选项
        if params.get("force", "").lower() in ("true", "yes", "1"):
            command.append("-f")

        # 如果指定了preserve参数且为真，添加-p选项
        if params.get("preserve", "").lower() in ("true", "yes", "1"):
            command.append("-p")

        command.extend([source, dest])
        return self._run_command(command)

    def _handle_mv(self, source: str, params: Dict[str, str]) -> int:
        """
        移动或重命名文件或目录

        Args:
            source: 源路径
            params: 参数字典，必须包含 dest，可能包含 force 等

        Returns:
            执行结果状态码
        """
        if "dest" not in params:
            print("错误：缺少目标路径参数 'dest'")
            return 1

        dest = params["dest"]

        # 构建mv命令
        command = ["mv"]

        # 如果指定了force参数且为真，添加-f选项
        if params.get("force", "").lower() in ("true", "yes", "1"):
            command.append("-f")

        command.extend([source, dest])
        return self._run_command(command)

    def _handle_rm(self, path: str, params: Dict[str, str]) -> int:
        """
        删除文件或目录

        Args:
            path: 要删除的路径
            params: 参数字典，可能包含 recursive, force 等

        Returns:
            执行结果状态码
        """
        # 构建rm命令
        command = ["rm"]

        # 如果指定了recursive参数且为真，添加-r选项
        if params.get("recursive", "").lower() in ("true", "yes", "1"):
            command.append("-r")

        # 如果指定了force参数且为真，添加-f选项
        if params.get("force", "").lower() in ("true", "yes", "1"):
            command.append("-f")

        command.append(path)
        return self._run_command(command)

    def _handle_mkdir(self, path: str, params: Dict[str, str]) -> int:
        """
        创建目录

        Args:
            path: 要创建的目录路径
            params: 参数字典，可能包含 parents, mode 等

        Returns:
            执行结果状态码
        """
        # 构建mkdir命令
        command = ["mkdir"]

        # 如果指定了parents参数且为真，添加-p选项
        if params.get("parents", "").lower() in ("true", "yes", "1"):
            command.append("-p")

        # 如果指定了mode参数，添加-m选项
        if "mode" in params:
            command.extend(["-m", params["mode"]])

        command.append(path)
        return self._run_command(command)

    def _handle_cat(self, path: str, params: Dict[str, str]) -> int:
        """
        显示文件内容

        Args:
            path: 文件路径
            params: 参数字典，可能包含 number, show_nonprinting 等

        Returns:
            执行结果状态码
        """
        # 构建cat命令
        command = ["cat"]

        # 如果指定了number参数且为真，添加-n选项
        if params.get("number", "").lower() in ("true", "yes", "1"):
            command.append("-n")

        # 如果指定了show_nonprinting参数且为真，添加-A选项
        if params.get("show_nonprinting", "").lower() in ("true", "yes", "1"):
            command.append("-A")

        command.append(path)
        return self._run_command(command)

    def _handle_edit(self, path: str, params: Dict[str, str]) -> int:
        """
        编辑文件

        Args:
            path: 文件路径
            params: 参数字典，可能包含 editor 等

        Returns:
            执行结果状态码
        """
        # 获取编辑器，默认使用vi
        editor = params.get("editor", "vi")

        # 构建编辑命令
        command = [editor, path]
        return self._run_command(command)

    def _handle_find(self, path: str, params: Dict[str, str]) -> int:
        """
        查找文件

        Args:
            path: 搜索路径
            params: 参数字典，可能包含 name, type, exec 等

        Returns:
            执行结果状态码
        """
        # 构建find命令
        command = ["find", path]

        # 添加名称参数
        if "name" in params:
            command.extend(["-name", params["name"]])

        # 添加类型参数
        if "type" in params:
            command.extend(["-type", params["type"]])

        # 添加执行参数
        if "exec" in params:
            exec_cmd = params["exec"]
            # 将exec参数分割为列表
            exec_parts = exec_cmd.split()
            command.extend(["-exec"] + exec_parts + [";"])

        return self._run_command(command)

    def _handle_info(self, path: str, params: Dict[str, str]) -> int:
        """
        显示文件或目录信息

        Args:
            path: 文件或目录路径
            params: 参数字典，可能包含 human_readable, dereference 等

        Returns:
            执行结果状态码
        """
        # 构建stat命令
        command = ["stat"]

        # 如果指定了human_readable参数且为真，添加-h选项
        if params.get("human_readable", "").lower() in ("true", "yes", "1"):
            command.append("-h")

        # 如果指定了dereference参数且为真，添加-L选项
        if params.get("dereference", "").lower() in ("true", "yes", "1"):
            command.append("-L")

        command.append(path)
        return self._run_command(command)
