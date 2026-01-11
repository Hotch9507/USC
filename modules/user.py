"""
用户管理模块
"""

from typing import Dict

from .base import BaseModule


class UserModule(BaseModule):
    """用户管理模块"""

    def get_description(self) -> str:
        """获取模块描述"""
        return "管理系统用户"

    def get_actions(self) -> Dict[str, str]:
        """获取模块支持的操作及其描述"""
        return {
            "add": "添加新用户",
            "del": "删除用户",
            "mod": "修改用户属性",
            "list": "列出用户",
            "info": "显示用户详细信息"
        }

    def _handle_add(self, username: str, params: Dict[str, str]) -> int:
        """
        添加新用户

        Args:
            username: 用户名
            params: 参数字典，可能包含 home, shell, group, groups, uid, comment, chroot, system, password, lock 等

        Returns:
            执行结果状态码
        """
        # 检查是否为系统用户
        is_system = params.get("system", "").lower() in ("true", "yes", "1")
        
        # 构建useradd命令
        command = ["sudo", "useradd"]
        
        # 系统用户设置
        if is_system:
            command.append("-r")  # 系统用户
            # 系统用户不创建家目录
            # 系统用户shell为nologin（强制覆盖）
            params["shell"] = "/sbin/nologin"
        else:
            command.append("-m")  # 创建家目录
        
        # 设置主目录
        if "home" in params:
            command.extend(["-d", params["home"]])
        
        # 设置chroot目录
        if "chroot" in params:
            command.extend(["-b", params["chroot"]])
        
        # 设置shell（获取系统默认shell）
        if "shell" in params:
            command.extend(["-s", params["shell"]])
        else:
            # 获取系统默认shell
            import os
            default_shell = os.environ.get("SHELL", "/bin/bash")
            command.extend(["-s", default_shell])
        
        # 设置用户组
        if "group" in params:
            # 解析组列表，第一个组为主组，其余为附加组
            groups_str = params["group"]
            groups = groups_str.split(",")
            
            # 设置主组
            command.extend(["-g", groups[0]])
            
            # 如果有多个组，设置附加组
            if len(groups) > 1:
                command.extend(["-G", ",".join(groups[1:])])
        else:
            # 默认创建与用户同名的用户组
            command.extend(["-U"])  # 创建与用户同名的用户组
        
        # 设置用户ID
        if "uid" in params:
            command.extend(["-u", params["uid"]])
        
        # 设置用户注释
        if "comment" in params:
            command.extend(["-c", params["comment"]])
        
        # 添加用户名
        command.append(username)
        
        # 执行useradd命令
        result = self._run_command(command)
        
        # 设置密码
        password = params.get("password", "123456")  # 默认密码为123456
        password_cmd = ["echo", f"{username}:{password}", "|", "sudo", "chpasswd"]
        result = result or self._run_command(password_cmd, check=False)
        
        # 设置首次登录强制修改密码
        if params.get("force_change", "").lower() in ("true", "yes", "1") or "password" not in params:
            # 使用chage命令设置密码过期
            expire_cmd = ["sudo", "chage", "-d", "0", username]
            result = result or self._run_command(expire_cmd)
        
        # 锁定用户
        if params.get("lock", "").lower() in ("true", "yes", "1"):
            lock_cmd = ["sudo", "usermod", "-L", username]
            result = result or self._run_command(lock_cmd)
        
        return result

    def _handle_del(self, username: str, params: Dict[str, str]) -> int:
        """
        删除用户

        Args:
            username: 用户名
            params: 参数字典，可能包含 home, group 等

        Returns:
            执行结果状态码
        """
        # 构建userdel命令
        command = ["sudo", "userdel"]

        # 检查是否删除家目录
        if params.get("home", "").lower() in ("true", "yes", "1"):
            command.append("-r")  # 删除用户主目录和邮件池

        command.append(username)
        result = self._run_command(command)

        # 如果用户删除成功且需要删除同名用户组
        if result == 0 and params.get("group", "").lower() in ("true", "yes", "1"):
            # 检查是否存在同名用户组
            group_cmd = ["getent", "group", username]
            group_result = self._run_command(group_cmd, check=False, output_format="raw")

            if group_result == 0 and group_result.stdout:
                # 删除同名用户组
                delgroup_cmd = ["sudo", "groupdel", username]
                result = self._run_command(delgroup_cmd)

        return result

    def _handle_mod(self, username: str, params: Dict[str, str]) -> int:
        """
        修改用户属性

        Args:
            username: 用户名或UID
            params: 参数字典，可能包含 home, shell, group 等

        Returns:
            执行结果状态码
        """
        # 如果username是数字，则视为UID，需要先获取用户名
        if username.isdigit():
            # 使用UID获取用户名
            uid_cmd = ["getent", "passwd", username]
            uid_result = self._run_command(uid_cmd, check=False, output_format="raw")

            if uid_result != 0 or not uid_result.stdout:
                print(f"错误：找不到UID为 {username} 的用户")
                return 1

            # 解析用户名
            username = uid_result.stdout.strip().split(":")[0]

        # 构建usermod命令
        command = ["sudo", "usermod"]

        # 添加家目录参数
        if "home" in params:
            command.extend(["-d", params["home"], "-m"])

        # 添加用户组参数
        if "group" in params:
            groups = params["group"].split(",")
            if len(groups) >= 1:
                # 如果第一个组为空，则只设置附加组，不修改主组
                if groups[0] == "":
                    # 如果有附加组，设置附加组
                    if len(groups) > 1:
                        command.extend(["-G", ",".join(groups[1:])])
                else:
                    # 设置主组
                    command.extend(["-g", groups[0]])
                    # 如果有附加组，设置附加组
                    if len(groups) > 1:
                        command.extend(["-G", ",".join(groups[1:])])

        # 添加shell参数
        if "shell" in params:
            command.extend(["-s", params["shell"]])

        # 添加UID参数
        if "uid" in params:
            command.extend(["-u", params["uid"]])

        # 添加用户名参数
        if "uname" in params:
            command.extend(["-l", params["uname"]])

        # 添加注释参数
        if "comment" in params:
            command.extend(["-c", params["comment"]])

        # 添加chroot参数
        if "chroot" in params:
            command.extend(["-d", params["chroot"]])

        # 添加锁定/解锁参数
        if "lock" in params:
            if params["lock"].lower() in ("true", "yes", "1"):
                command.append("-L")
            elif params["lock"].lower() in ("false", "no", "0"):
                command.append("-U")

        # 添加密码参数
        if "password" in params:
            # 使用chpasswd设置密码
            password_cmd = f"echo '{username}:{params["password"]}' | sudo chpasswd"
            password_result = self._run_command(["bash", "-c", password_cmd])
            if password_result != 0:
                print(f"警告：密码设置失败")

        # 添加用户名到命令末尾
        command.append(username)

        # 执行usermod命令
        return self._run_command(command)

    def _handle_list(self, value: str, params: Dict[str, str]) -> int:
        """
        列出用户

        Args:
            value: 用户类型，可以是login（可登录用户）、nologin（不可登录用户）、all（全部用户），默认为login
            params: 参数字典

        Returns:
            执行结果状态码
        """
        # 获取用户类型，默认为login（可登录用户）
        user_type = value.lower() if value else "login"

        # 使用getent命令列出用户
        command = ["getent", "passwd"]
        result = self._run_command(command, check=False, output_format="raw")

        if result != 0:
            return result

        # 解析用户信息
        users = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split(':')
            if len(parts) < 7:
                continue

            username = parts[0]
            uid = parts[2]
            gid = parts[3]
            comment = parts[4]
            home = parts[5]
            shell = parts[6]

            # 判断用户是否可以登录
            can_login = not (shell.endswith('/nologin') or shell.endswith('/false') or shell.endswith('/sync'))

            # 判断是否为系统用户 (UID < 1000 通常认为是系统用户)
            is_system = "否"
            try:
                if int(uid) < 1000:
                    is_system = "是"
            except ValueError:
                pass

            # 根据用户类型过滤
            if user_type == "login" and can_login:
                users.append({
                    "username": username,
                    "uid": uid,
                    "gid": gid,
                    "comment": comment,
                    "home": home,
                    "shell": shell,
                    "can_login": "是",
                    "is_system": is_system
                })
            elif user_type == "nologin" and not can_login:
                users.append({
                    "username": username,
                    "uid": uid,
                    "gid": gid,
                    "comment": comment,
                    "home": home,
                    "shell": shell,
                    "can_login": "否",
                    "is_system": is_system
                })
            elif user_type == "all":
                users.append({
                    "username": username,
                    "uid": uid,
                    "gid": gid,
                    "comment": comment,
                    "home": home,
                    "shell": shell,
                    "can_login": "是" if can_login else "否",
                    "is_system": is_system
                })

        # 美化输出用户列表
        if users:
            # 按用户名排序
            users.sort(key=lambda x: x["username"])

            # 计算各列最大宽度
            max_username = max(len(user["username"]) for user in users)
            max_uid = max(len(user["uid"]) for user in users)
            max_gid = max(len(user["gid"]) for user in users)
            max_comment = max(len(user["comment"]) for user in users)
            max_home = max(len(user["home"]) for user in users)

            # 输出表头
            header = f"{'用户名':<{max_username}} {'UID':<{max_uid}} {'GID':<{max_gid}} {'注释':<{max_comment}} {'主目录':<{max_home}} {'Shell':<15} {'可登录':<6} {'系统用户':<6}"
            print(header)
            print("-" * len(header))

            # 输出用户信息
            for user in users:
                print(f"{user['username']:<{max_username}} {user['uid']:<{max_uid}} {user['gid']:<{max_gid}} {user['comment']:<{max_comment}} {user['home']:<{max_home}} {user['shell']:<15} {user['can_login']:<6} {user['is_system']:<6}")

            # 输出统计信息
            type_desc = {
                "login": "可登录",
                "nologin": "不可登录",
                "all": "全部"
            }
            print(f"\n共找到 {len(users)} 个{type_desc.get(user_type, '')}用户")
        else:
            type_desc = {
                "login": "可登录",
                "nologin": "不可登录",
                "all": ""
            }
            print(f"没有找到{type_desc.get(user_type, '')}用户")

        return 0

    def _handle_info(self, username: str, params: Dict[str, str]) -> int:
        """
        显示用户详细信息

        Args:
            username: 用户名
            params: 参数字典，可能包含 list 等

        Returns:
            执行结果状态码
        """
        # 获取list参数，默认为base
        list_param = params.get("list", "base").lower()

        # 获取用户基本信息
        passwd_cmd = ["getent", "passwd", username]
        passwd_result = self._run_command(passwd_cmd, check=False, output_format="raw")

        if passwd_result != 0:
            print(f"错误：找不到用户 '{username}'")
            return 1

        # 解析passwd信息
        passwd_info = passwd_result.stdout.strip().split(":")
        if len(passwd_info) < 7:
            print(f"错误：无法解析用户 '{username}' 的信息")
            return 1

        # 提取基本信息
        user_name = passwd_info[0]
        uid = passwd_info[2]
        gid = passwd_info[3]
        comment = passwd_info[4]
        home = passwd_info[5]
        shell = passwd_info[6]

        # 获取组信息
        group_cmd = ["getent", "group", gid]
        group_result = self._run_command(group_cmd, check=False, output_format="raw")
        group_name = ""
        if group_result == 0:
            group_info = group_result.stdout.strip().split(":")
            if len(group_info) >= 1:
                group_name = group_info[0]

        # 获取用户所属的所有组
        groups_cmd = ["id", "-Gn", username]
        groups_result = self._run_command(groups_cmd, check=False, output_format="raw")
        all_groups = ""
        if groups_result == 0:
            all_groups = groups_result.stdout.strip()

        # 检查是否为系统用户 (UID < 1000 通常认为是系统用户)
        is_system = "false"
        try:
            if int(uid) < 1000:
                is_system = "true"
        except ValueError:
            pass

        # 检查用户是否被锁定
        lock_status = "false"
        passwd_status_cmd = ["sudo", "passwd", "-S", username]
        lock_result = self._run_command(passwd_status_cmd, check=False, output_format="raw")
        if lock_result == 0 and lock_result.stdout:
            # 输出格式通常是: username status date...
            status_parts = lock_result.stdout.strip().split()
            if len(status_parts) >= 2 and status_parts[1] in ["L", "LK"]:
                lock_status = "true"

        # 检查chroot状态
        chroot_status = "false"
        # 这里可能需要更复杂的逻辑来检查chroot状态，暂时设为false

        # 根据list参数决定显示哪些信息
        if list_param == "all":
            # 显示所有信息
            print(f"用户名: {user_name}")
            print(f"UID: {uid}")
            print(f"Shell: {shell}")
            print(f"锁定状态: {lock_status}")
            print(f"注释: {comment}")
            print(f"系统用户: {is_system}")
            print(f"Chroot: {chroot_status}")
            print(f"主组: {group_name}({gid})")
            print(f"所有组: {all_groups}")
        elif list_param == "base":
            # 显示基本信息
            print(f"用户名: {user_name}")
            print(f"UID: {uid}")
            print(f"主组: {group_name}({gid})")
        else:
            # 显示指定字段
            fields = list_param.split(",")
            for field in fields:
                field = field.strip().lower()
                if field == "username":
                    print(f"用户名: {user_name}")
                elif field == "uid":
                    print(f"UID: {uid}")
                elif field == "shell":
                    print(f"Shell: {shell}")
                elif field == "lock":
                    print(f"锁定状态: {lock_status}")
                elif field == "comment":
                    print(f"注释: {comment}")
                elif field == "system":
                    print(f"系统用户: {is_system}")
                elif field == "chroot":
                    print(f"Chroot: {chroot_status}")
                elif field == "group":
                    print(f"主组: {group_name}({gid})")
                elif field == "groups":
                    print(f"所有组: {all_groups}")
                else:
                    print(f"警告：未知字段 '{field}'")

        return 0

    def _help_add(self) -> Dict:
        """添加用户操作的帮助信息"""
        return {
            "module": "user",
            "action": "add",
            "description": "添加新用户",
            "parameters": {
                "home": "用户主目录路径（默认：创建与用户同名的家目录）",
                "shell": "用户Shell路径（默认：系统默认shell）",
                "group": "用户组，第一个组为主组，其余为附加组，多个组用逗号分隔",
                "uid": "用户ID（默认：系统自动分配）",
                "comment": "用户注释信息",
                "chroot": "chroot目录（默认：用户家目录）",
                "system": "是否创建系统用户，值为true/false（默认：false）",
                "password": "用户密码（默认：123456，首次登录强制修改）",
                "lock": "是否锁定用户，值为true/false（默认：false）"
            },
            "usage": "usc user add:<username> home:<path> shell:<path> group:<groups> uid:<uid> comment:<comment> chroot:<path> system:<true/false> password:<password> lock:<true/false>",
            "notes": [
                "system:true时优先级最高，将强制设置uid为系统保留区间，不创建家目录，设置shell为nologin",
                "未指定password时，默认设置为123456且用户首次登录需要修改密码",
                "group参数中，第一个组为用户主组，后面的组为附加组"
            ]
        }

    def _help_del(self) -> Dict:
        """删除用户操作的帮助信息"""
        return {
            "module": "user",
            "action": "del",
            "description": "删除用户",
            "parameters": {
                "home": "是否同时删除用户主目录，值为true/false（默认：false）",
                "group": "是否同时删除同名用户组，值为true/false（默认：false）"
            },
            "usage": "usc user del:<username> home:<true/false> group:<true/false>",
            "notes": [
                "删除用户是危险操作，请谨慎使用",
                "home:true 时会同时删除用户主目录和邮件池",
                "group:true 时会在删除用户后尝试删除与用户同名的用户组"
            ]
        }

    def _help_mod(self) -> Dict:
        """修改用户操作的帮助信息"""
        return {
            "module": "user",
            "action": "mod",
            "description": "修改用户属性",
            "parameters": {
                "home": "用户家目录路径",
                "group": "用户所属组，第一个参数为用户的所属组，后面的所有组均为附加组，多个组用逗号分隔。如果第一个参数为空，则只修改附加组，不修改主组",
                "shell": "用户Shell路径",
                "uid": "用户ID",
                "uname": "修改用户名",
                "comment": "用户注释信息",
                "chroot": "chroot目录",
                "lock": "修改锁定用户状态，值为true/false",
                "password": "密码修改/设置"
            },
            "usage": "usc user mod:<username|uid> home:<path> group:<primary,additional1,additional2,...> shell:<path> uid:<uid> uname:<new_name> comment:<comment> chroot:<path> lock:<true/false> password:<password>",
            "notes": [
                "可以使用用户名或UID作为第一个参数",
                "group参数中，第一个组为用户主组，后面的组为附加组",
                "lock:true表示锁定用户，lock:false表示解锁用户",
                "password参数会直接设置用户密码，请注意安全性"
            ]
        }

    def _help_info(self) -> Dict:
        """显示用户信息操作的帮助信息"""
        return {
            "module": "user",
            "action": "info",
            "description": "显示用户详细信息",
            "parameters": {
                "list": "显示信息类型，可以是all（全部信息）、base（基本信息，默认）或指定字段组合（如：uid,group,lock）"
            },
            "usage": "usc user info:<username> list:<all|base|field1,field2,...>",
            "notes": [
                "all: 显示所有信息（用户名、UID、Shell、锁定状态、注释、系统用户标识、Chroot状态、主组、所有组）",
                "base: 显示基本信息（用户名、UID、主组）",
                "自定义字段: 可以指定一个或多个字段，用逗号分隔，如：uid,group,lock",
                "可用字段包括：username、uid、shell、lock、comment、system、chroot、group、groups"
            ]
        }

    def _help_list(self) -> Dict:
        """列出用户操作的帮助信息"""
        return {
            "module": "user",
            "action": "list",
            "description": "列出用户",
            "parameters": {
                "value": "用户类型，可以是login（可登录用户，默认）、nologin（不可登录用户）或all（全部用户）",
                "out": "输出文件路径，可以是目录路径或完整文件路径（默认输出到控制台）"
            },
            "usage": "usc user list:<login|nologin|all> out:<path>",
            "notes": [
                "login: 列出可以登录系统的用户（Shell不是nologin、false或sync）",
                "nologin: 列出不能登录系统的用户（Shell是nologin、false或sync）",
                "all: 列出所有用户，包括可登录和不可登录用户",
                "如果不指定参数，默认列出可登录用户",
                "输出以表格形式显示，包含用户名、UID、GID、注释、主目录、Shell、可登录状态和系统用户标识",
                "使用out参数可将输出保存到TOML格式的文件中",
                "out:/path/to/dir - 输出到指定目录，文件名自动生成为usc-时间戳.toml",
                "out:/path/to/file.toml - 输出到指定文件"
            ]
        }
