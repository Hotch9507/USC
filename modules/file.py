"""
文件管理模块
"""

import os
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
            "copy": ["archive", "recursive", "verbose", "update", "force"],
            "move": ["recursive", "force", "update", "verbose"],
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

        参数说明：
            source: 源路径
                    - 以/*结尾：复制目录下的文件
                    - 不加/或者加了/但没有*：复制目录本身
            params: 参数字典
                - dest: 目标路径（可选，无论有无/都视为目录）
                       如果为空，默认复制到原始目录并添加_数字序列
                - recursive: 是否递归复制（默认true）
                - archive: 归档模式（默认true，这是参数预设集合）
                         添加 --no-dereference --preserve=mode,ownership,timestamps,links,xattr,context,all --recursive
                - verbose: 显示复制进度（默认true）
                - force: 是否强制覆盖（默认false，有同名文件时提示）
                - update: 只复制更新的文件（默认false）
                - preserve: 保持信息参数，逗号分割，可选值：
                           hardlink(硬链接), softlink(软链接), mode(文件权限),
                           owner(所有者), time(时间戳), exmode(扩展权限), context(SELinux上下文)

        Returns:
            执行结果状态码
        """
        # 获取dest参数（可以为空）
        dest = params.get("dest", "")

        # 如果dest为空，默认复制到原始目录并添加_数字序列
        if not dest:
            # 提取源路径的父目录
            if source.endswith("/*"):
                # 源以/*结尾，表示目录下的文件
                source_dir = source[:-2]  # 移除 /*
                parent_dir = os.path.dirname(source_dir)
                base_name = os.path.basename(source_dir)
            else:
                # 源不以/*结尾（不加/或者加了/但没有*），表示目录或文件本身
                # 统一移除末尾的/（如果有）
                source_clean = source.rstrip("/")
                parent_dir = os.path.dirname(source_clean)
                base_name = os.path.basename(source_clean)

            # 确定目标路径为父目录
            dest_dir = parent_dir if parent_dir else "."

            # 查找可用的序列号
            seq = 1
            while True:
                dest_path = os.path.join(dest_dir, f"{base_name}_{seq}")
                if not os.path.exists(dest_path):
                    break
                seq += 1

            dest = dest_path

        # 确保目标路径以/结尾（视为目录）
        if not dest.endswith("/"):
            dest = dest + "/"

        # 获取archive参数（默认true）
        # 注意：这是"参数预设集合"，会添加多个参数
        archive = self._convert_bool(
            self._get_param_value("archive", "copy", params, "true")
        )

        # 构建cp命令
        command = ["cp"]

        # 如果archive为true，添加归档模式的参数
        # 注意：这些参数的顺序很重要，会影响后续参数的效果
        if archive:
            # 归档模式：添加完整参数而非简单的 -a
            # --no-dereference --preserve=mode,ownership,timestamps,links,xattr,context,all --recursive
            command.append("--no-dereference")
            command.append("--preserve=mode,ownership,timestamps,links,xattr,context,all")
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

        # 获取preserve参数（可选值：hardlink, softlink, mode, owner, time, exmode, context）
        # 如果指定了preserve参数，需要处理
        if "preserve" in params:
            preserve_value = params["preserve"]
            if preserve_value:
                preserve_items = []
                for item in preserve_value.split(","):
                    item = item.strip()
                    if item:
                        # 映射用户友好的参数名到cp的实际参数名
                        if item == "hardlink":
                            # 硬链接对应-d参数（--dereference-prevents-hardlink）
                            preserve_items.append("links")
                        elif item == "softlink":
                            # 软链接对应--no-dereference
                            preserve_items.append("links")
                        elif item == "exmode":
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
                    # 移除archive添加的preserve参数（如果有）
                    if archive and "--preserve" in " ".join(command):
                        # 找到并移除archive添加的preserve参数
                        new_command = []
                        for cmd in command:
                            if not cmd.startswith("--preserve="):
                                new_command.append(cmd)
                        command = new_command

                    command.append(f"--preserve={','.join(preserve_items)}")

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

        # 添加源和目标
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

        参数说明：
            source: 源路径
                    - 以/*结尾：移动目录下的文件
                    - 不加/或者加了/但没有*：移动目录本身
            params: 参数字典
                - dest: 目标路径（必需，无论有无/都视为目录）
                       如果为同目录，则为重命名行为
                - recursive: 是否递归移动目录下的所有文件（默认true）
                - force: 是否强制覆盖（默认false，有同名文件时提示）
                - update: 只移动更新的文件到目标（默认false）
                - verbose: 显示移动进度（默认true）

        Returns:
            执行结果状态码
        """
        # 检查必填参数
        if "dest" not in params:
            print("错误：缺少目标路径参数 'dest'")
            return 1

        dest = params["dest"]

        # 处理源路径：如果以/*结尾，需要移动目录下的文件
        if source.endswith("/*"):
            # 移动目录下的所有文件到目标目录
            source_dir = source[:-2]  # 移除 /*
            if not os.path.isdir(source_dir):
                print(f"错误：源目录不存在: {source_dir}")
                return 1

            # 确保目标路径以/结尾（视为目录）
            if not dest.endswith("/"):
                dest = dest + "/"

            # 遍历源目录下的所有项并逐个移动
            try:
                entries = os.listdir(source_dir)
                for entry in entries:
                    src_path = os.path.join(source_dir, entry)
                    # 跳过隐藏文件和子目录（如果recursive为false）
                    if entry.startswith("."):
                        continue

                    # 检查recursive参数
                    recursive = self._convert_bool(
                        self._get_bool_param_value("recursive", "move", params, "true")
                    )

                    if os.path.isdir(src_path) and not recursive:
                        # 是目录但不需要递归，跳过
                        continue

                    # 构建单个文件的移动命令
                    result = self._move_single_item(src_path, dest, params)
                    if result != 0:
                        return result

                return 0
            except Exception as e:
                print(f"错误：无法读取源目录: {e}")
                return 1
        else:
            # 移动目录或文件本身（统一移除末尾的/）
            source_clean = source.rstrip("/")
            return self._move_single_item(source_clean, dest, params)

    def _move_single_item(self, source: str, dest: str, params: Dict[str, str]) -> int:
        """
        移动单个文件或目录

        Args:
            source: 源路径
            dest: 目标路径
            params: 参数字典

        Returns:
            执行结果状态码
        """
        # 构建mv命令
        command = ["mv"]

        # 获取force参数（使用新的布尔参数处理方法，空值默认为true）
        force = self._convert_bool(
            self._get_bool_param_value("force", "move", params, "false")
        )

        if force:
            # 强制覆盖，不提示
            command.append("-f")
        else:
            # 不强制，覆盖前提示
            command.append("-i")

        # 获取update参数（默认false）
        update = self._convert_bool(
            self._get_bool_param_value("update", "move", params, "false")
        )

        if update:
            # 只移动更新的文件
            command.append("-u")

        # 获取verbose参数（默认true）
        verbose = self._convert_bool(
            self._get_bool_param_value("verbose", "move", params, "true")
        )

        if verbose:
            # 显示详细信息
            command.append("-v")

        # 处理目标路径
        # 如果目标以/结尾，或者目标是已存在的目录，则移动到目录内
        # 否则视为重命名
        target = dest
        if dest.endswith("/"):
            target = dest.rstrip("/")
        elif os.path.isdir(dest):
            target = dest.rstrip("/")

        # 添加源和目标
        command.extend([source, target])
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

    def _help_copy(self) -> Dict:
        """
        返回copy操作的详细帮助信息

        Returns:
            帮助信息字典
        """
        return {
            "module": "file",
            "action": "copy",
            "description": "复制文件或目录",
            "usage": "usc file copy:<source> [dest:<destination>] [parameter:value] [...]",
            "parameters": {
                "source": {
                    "description": "源文件或目录路径",
                    "required": True,
                    "notes": "以/*结尾表示复制目录下的文件，不加/或者加了/但没有*表示复制目录本身"
                },
                "dest": {
                    "description": "目标路径（无论有无/都视为目录）",
                    "required": False,
                    "default": "复制到原始目录并添加_数字序列",
                    "notes": "如果为空，则自动在源目录同级创建_数字序列的副本"
                },
                "recursive": {
                    "description": "是否递归复制目录下的所有文件",
                    "type": "boolean",
                    "default": "true"
                },
                "archive": {
                    "description": "归档模式（参数预设集合）",
                    "type": "boolean",
                    "default": "true",
                    "notes": "添加 --no-dereference --preserve=mode,ownership,timestamps,links,xattr,context,all --recursive"
                },
                "verbose": {
                    "description": "显示复制进度",
                    "type": "boolean",
                    "default": "true"
                },
                "force": {
                    "description": "是否强制覆盖（默认false，有同名文件时提示）",
                    "type": "boolean",
                    "default": "false"
                },
                "update": {
                    "description": "只复制更新的文件到目标",
                    "type": "boolean",
                    "default": "false"
                },
                "preserve": {
                    "description": "保持信息参数，逗号分割",
                    "type": "string",
                    "options": ["hardlink", "softlink", "mode", "owner", "time", "exmode", "context"],
                    "notes": "hardlink=硬链接, softlink=软链接, mode=文件权限, owner=所有者, time=时间戳, exmode=扩展权限, context=SELinux上下文"
                }
            },
            "examples": [
                {
                    "command": "usc file copy:/home/user/data dest:/backup",
                    "description": "复制目录本身到目标位置（保持所有属性）"
                },
                {
                    "command": "usc file copy:/home/user/data/* dest:/backup",
                    "description": "复制目录下的所有文件到目标位置"
                },
                {
                    "command": "usc file copy:/home/user/file.txt",
                    "description": "复制文件到原始目录（自动添加_1后缀）"
                },
                {
                    "command": "usc file copy:/data dest:/backup force:true",
                    "description": "强制复制目录，覆盖时不提示"
                },
                {
                    "command": "usc file copy:/data dest:/backup preserve:mode,owner,time",
                    "description": "复制目录，只保持权限、所有者和时间戳"
                },
                {
                    "command": "usc file copy:/data dest:/backup archive:false recursive:false",
                    "description": "复制目录（不使用归档模式，不递归）"
                }
            ],
            "notes": [
                "archive参数是'参数预设集合'，会添加多个cp参数，而非简单的-a选项",
                "archive和recursive的参数顺序很重要：archive先添加--recursive，recursive:false可以覆盖它",
                "dest为空时会自动生成_数字序列的副本名称"
            ]
        }

    def _help_move(self) -> Dict:
        """
        返回move操作的详细帮助信息

        Returns:
            帮助信息字典
        """
        return {
            "module": "file",
            "action": "move",
            "description": "移动或重命名文件或目录",
            "usage": "usc file move:<source> dest:<target> [parameter:value] [...]",
            "parameters": {
                "source": {
                    "description": "源文件或目录路径",
                    "required": True,
                    "notes": "以/*结尾表示移动目录下的文件，不加/或者加了/但没有*表示移动目录本身"
                },
                "dest": {
                    "description": "目标路径（必需）",
                    "required": True,
                    "notes": "无论有无/都视为目录；如果为同目录，则为重命名行为"
                },
                "recursive": {
                    "description": "是否递归移动目录下的所有文件",
                    "type": "boolean",
                    "default": "true"
                },
                "force": {
                    "description": "是否强制覆盖（默认false，有同名文件时提示）",
                    "type": "boolean",
                    "default": "false",
                    "notes": "只指定参数名不加值（如force:）默认为true"
                },
                "update": {
                    "description": "只移动更新的文件到目标",
                    "type": "boolean",
                    "default": "false",
                    "notes": "只指定参数名不加值（如update:）默认为true"
                },
                "verbose": {
                    "description": "显示移动进度",
                    "type": "boolean",
                    "default": "true",
                    "notes": "只指定参数名不加值（如verbose:）默认为true"
                }
            },
            "examples": [
                {
                    "command": "usc file move:/home/user/file.txt dest:/backup",
                    "description": "移动文件到目标目录"
                },
                {
                    "command": "usc file move:/home/user/file.txt dest:/home/user/newname.txt",
                    "description": "重命名文件（同目录下移动）"
                },
                {
                    "command": "usc file move:/home/user/data dest:/backup",
                    "description": "移动目录到目标位置"
                },
                {
                    "command": "usc file move:/home/user/data/* dest:/backup",
                    "description": "移动目录下的所有文件到目标位置"
                },
                {
                    "command": "usc file move:/data dest:/backup force:",
                    "description": "强制移动，覆盖时不提示（force: 等同于 force:true）"
                },
                {
                    "command": "usc file move:/data dest:/backup update:",
                    "description": "只移动更新的文件（update: 等同于 update:true）"
                },
                {
                    "command": "usc file move:/src dest:/backup recursive:false",
                    "description": "移动目录但不递归移动子目录"
                }
            ],
            "notes": [
                "移动和重命名本质上是相同的操作，mv命令统一处理这两种情况",
                "布尔参数如果只指定参数名不加值（如force:），默认为true",
                "源路径以/*结尾时，会遍历目录下所有项逐个移动",
                "重命名就是同目录下的移动操作"
            ]
        }
