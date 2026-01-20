"""
文件管理模块
"""

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
            "copy": "复制文件或目录",
            "move": "移动或重命名文件或目录",
            "del": "删除文件或目录",
            "mkdir": "创建目录",
            "cat": "显示文件内容",
            "edit": "编辑文件",
            "find": "查找文件",
            "sync": "同步文件或目录（基于rsync）",
            "info": "显示文件或目录信息"
        }

    def get_boolean_params(self, action: str = None) -> Dict[str, List[str]]:
        """
        获取布尔参数列表

        Returns:
            布尔参数字典，格式为 {action: [param1, param2, ...]}
        """
        boolean_params = {
            "copy": ["archive", "recursive", "verbose", "update", "softlink", "force"],
            "move": ["force"],
            "del": ["recursive", "force"],
            "mkdir": ["parents"],
            "cat": ["number", "show_nonprinting"],
            "sync": ["recursive", "delete", "progress", "compress", "dry_run", "checksum"],
            "info": ["human_readable", "dereference"],
            "edit": [],
            "find": []
        }
        return boolean_params

    def _handle_copy(self, source: str, params: Dict[str, str]) -> int:
        """
        复制文件或目录

        Args:
            source: 源路径
                   - 以/结尾：复制目录下的内容
                   - 不以/结尾：复制目录本身
            params: 参数字典，必须包含 dest

        Returns:
            执行结果状态码
        """
        # 检查必填参数
        if "dest" not in params:
            print("错误：缺少目标路径参数 'dest'")
            return 1

        dest = params["dest"]

        # 构建cp命令
        command = ["cp"]

        # 获取archive参数（默认true）
        archive = self._convert_bool(
            self._get_param_value("archive", "copy", params, "true")
        )

        # 如果archive为true，添加归档模式的参数
        # 注意：这些参数的顺序很重要，会影响后续参数的效果
        if archive:
            # 归档模式：--no-dereference --preserve=mode,ownership,timestamps,xattr,context --recursive
            command.append("--no-dereference")
            command.append("--preserve=mode,ownership,timestamps,xattr,context")
            command.append("--recursive")

        # 获取recursive参数（默认true）
        # 注意：如果archive已经添加了--recursive，这里会根据值决定是否覆盖
        recursive = self._convert_bool(
            self._get_param_value("recursive", "copy", params, "true")
        )

        if archive:
            # archive模式已经添加了--recursive
            # 如果recursive为false，需要移除--recursive
            if not recursive:
                # 移除最后添加的--recursive
                if command[-1] == "--recursive":
                    command.pop()
        else:
            # 非archive模式，根据recursive参数决定
            if recursive:
                command.append("--recursive")
            # 如果recursive为false且不是目录复制，不需要特殊处理

        # 获取verbose参数（默认true）
        if self._convert_bool(
            self._get_param_value("verbose", "copy", params, "true")
        ):
            command.append("--verbose")

        # 获取update参数（默认false）
        if self._convert_bool(
            self._get_param_value("update", "copy", params, "false")
        ):
            command.append("--update")

        # 获取preserve参数（可选值：links, mode, owner, time, exmode, context）
        # 如果指定了preserve参数，添加--preserve
        if "preserve" in params:
            preserve_value = params["preserve"]
            if preserve_value:
                preserve_items = []
                for item in preserve_value.split(","):
                    item = item.strip()
                    if item:
                        # 映射用户友好的参数名到cp的实际参数名
                        if item == "exmode":
                            # 扩展权限对应xattr
                            preserve_items.append("xattr")
                        elif item == "time":
                            # 时间戳对应timestamps
                            preserve_items.append("timestamps")
                        elif item == "owner":
                            # 所有者对应ownership
                            preserve_items.append("ownership")
                        else:
                            # mode, context等直接使用
                            preserve_items.append(item)

                if preserve_items:
                    command.append(f"--preserve={','.join(preserve_items)}")

        # 获取softlink参数（默认true，保持软链接）
        softlink = self._convert_bool(
            self._get_param_value("softlink", "copy", params, "true")
        )

        # 如果archive模式已经添加了--no-dereference，这里需要处理
        if archive:
            # archive模式默认是--no-dereference（保持软链接）
            # 如果softlink为false，需要改为--dereference
            if not softlink:
                # 移除--no-dereference（在位置1）
                if "--no-dereference" in command:
                    command.remove("--no-dereference")
                command.append("--dereference")
        else:
            # 非archive模式
            if softlink:
                command.append("--no-dereference")
            else:
                command.append("--dereference")

        # 获取force参数（默认false）
        force = self._convert_bool(
            self._get_param_value("force", "copy", params, "false")
        )

        if force:
            # 强制覆盖，不提示
            command.append("--force")
        else:
            # 不强制，覆盖前提示
            # 注意：cp命令在交互模式下使用-i参数
            command.append("--interactive")

        # 处理源路径和目标路径
        # 目标地址无论有无/，都视为目录
        # 源地址：
        #   - 以/结尾：复制目录下的内容
        #   - 不以/结尾：复制目录本身

        # 确保目标路径以/结尾（视为目录）
        if not dest.endswith("/"):
            dest = dest + "/"

        command.extend([source, dest])
        return self._run_command(command)

    def _handle_sync(self, source: str, params: Dict[str, str]) -> int:
        """
        同步文件或目录（基于rsync）

        Args:
            source: 源路径
            params: 参数字典，必须包含 dest，可能包含 recursive, delete, progress 等

        Returns:
            执行结果状态码
        """
        if "dest" not in params:
            print("错误：缺少目标路径参数 'dest'")
            return 1

        dest = params["dest"]

        # 检查rsync是否可用
        check_cmd = ["which", "rsync"]
        check_result = self._run_command_capture(check_cmd, check=False)
        if check_result.returncode != 0:
            print("错误：rsync命令未安装")
            print("提示：使用 'sudo apt install rsync' 或 'sudo yum install rsync' 安装")
            return 1

        # 构建rsync命令
        command = ["rsync", "-av"]

        # 如果指定了recursive参数且为假，添加-d选项（只复制目录本身，不递归）
        if not self._convert_bool(
            self._get_param_value("recursive", "sync", params, "true")
        ):
            command.append("-d")

        # 如果指定了delete参数且为真，添加--delete选项（删除目标中有而源中没有的文件）
        if self._convert_bool(
            self._get_param_value("delete", "sync", params, "false")
        ):
            command.append("--delete")

        # 如果指定了progress参数且为真，添加--progress选项（显示进度）
        if self._convert_bool(
            self._get_param_value("progress", "sync", params, "false")
        ):
            command.append("--progress")

        # 如果指定了compress参数且为真，添加-z选项（压缩传输）
        if self._convert_bool(
            self._get_param_value("compress", "sync", params, "false")
        ):
            command.append("-z")

        # 如果指定了dry_run参数且为真，添加--dry-run选项（试运行）
        if self._convert_bool(
            self._get_param_value("dry_run", "sync", params, "false")
        ):
            command.append("--dry-run")

        # 如果指定了checksum参数且为真，添加-c选项（使用校验和而非时间戳）
        if self._convert_bool(
            self._get_param_value("checksum", "sync", params, "false")
        ):
            command.append("-c")

        # 如果指定了exclude参数，添加--exclude选项
        if "exclude" in params:
            for pattern in params["exclude"].split(","):
                pattern = pattern.strip()
                if pattern:
                    command.extend(["--exclude", pattern])

        # 添加源和目标
        # 注意：rsync的路径处理
        # 如果source以/结尾，表示同步目录内容
        # 如果source不以/结尾，表示同步目录本身
        command.extend([source, dest])

        return self._run_command(command)

    def _handle_move(self, source: str, params: Dict[str, str]) -> int:
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

        # 如果指定了force参数且为真，添加-f选项（使用配置系统）
        if self._convert_bool(
            self._get_param_value("force", "move", params, "false")
        ):
            command.append("-f")

        command.extend([source, dest])
        return self._run_command(command)

    def _handle_del(self, path: str, params: Dict[str, str]) -> int:
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

        # 如果指定了recursive参数且为真，添加-r选项（使用配置系统）
        if self._convert_bool(
            self._get_param_value("recursive", "del", params, "false")
        ):
            command.append("-r")

        # 如果指定了force参数且为真，添加-f选项（使用配置系统）
        if self._convert_bool(
            self._get_param_value("force", "del", params, "false")
        ):
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

        # 如果指定了parents参数且为真，添加-p选项（使用配置系统）
        if self._convert_bool(
            self._get_param_value("parents", "mkdir", params, "false")
        ):
            command.append("-p")

        # 如果指定了mode参数，添加-m选项（使用配置系统）
        mode = self._get_param_value("mode", "mkdir", params, "755")
        if mode:
            command.extend(["-m", mode])

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

        # 如果指定了number参数且为真，添加-n选项（使用配置系统）
        if self._convert_bool(
            self._get_param_value("number", "cat", params, "false")
        ):
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
        # 获取编辑器（使用配置系统，默认使用vi）
        editor = self._get_param_value("editor", "edit", params, "vi")

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
