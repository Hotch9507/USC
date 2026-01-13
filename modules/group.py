# -*- coding: utf-8 -*-
"""
用户组管理模块
"""

from typing import Dict

from .base import BaseModule


class GroupModule(BaseModule):
    """用户组管理模块"""

    def get_description(self) -> str:
        """获取模块描述"""
        return "管理系统用户组"

    def get_actions(self) -> Dict[str, str]:
        """获取模块支持的操作及其描述"""
        return {
            "add": "添加新用户组",
            "del": "删除用户组",
            "mod": "修改用户组属性",
            "list": "列出用户组",
            "info": "显示用户组详细信息"
        }

    def _handle_add(self, groupname: str, params: Dict[str, str]) -> int:
        """
        添加新用户组

        Args:
            groupname: 组名
            params: 参数字典，可能包含 gid, user, chroot, system 等

        Returns:
            执行结果状态码
        """
        # 检查是否为系统组
        is_system = params.get("system", "").lower() in ("true", "yes", "1")

        # 构建groupadd命令
        command = ["sudo", "groupadd"]

        # 系统组设置
        if is_system:
            command.append("-r")  # 系统组

        # 添加GID参数
        if "gid" in params:
            gid = params["gid"]
            command.extend(["-g", gid])

            # 检查GID是否已存在
            check_gid_cmd = ["getent", "group", gid]
            check_result = self._run_command_capture(check_gid_cmd, check=False)
            if check_result.returncode == 0 and check_result.stdout:
                print(f"警告：GID {gid} 已被其他组使用")

        command.append(groupname)
        result = self._run_command(command)

        # 如果组创建成功，添加成员
        if result == 0 and "user" in params:
            users = params["user"].split(",")
            for user in users:
                user = user.strip()
                if user:  # 跳过空字符串
                    # 使用usermod将用户添加到组
                    usermod_cmd = ["sudo", "usermod", "-aG", groupname, user]
                    user_result = self._run_command(usermod_cmd, check=False)
                    if user_result != 0:
                        print(f"警告：无法将用户 {user} 添加到组 {groupname}")

        # 处理chroot参数
        if result == 0 and "chroot" in params:
            chroot_dir = params["chroot"]
            # 在chroot环境中创建组
            chroot_cmd = ["sudo", "chroot", chroot_dir, "groupadd"]

            # 系统组设置
            if is_system:
                chroot_cmd.append("-r")

            # 添加GID参数
            if "gid" in params:
                chroot_cmd.extend(["-g", params["gid"]])

            chroot_cmd.append(groupname)
            chroot_result = self._run_command(chroot_cmd, check=False)
            if chroot_result != 0:
                print(f"警告：无法在chroot环境 {chroot_dir} 中创建组 {groupname}")

        return result

    def _handle_del(self, groupname: str, params: Dict[str, str]) -> int:
        """
        删除用户组

        Args:
            groupname: 组名或组ID
            params: 参数字典，可能包含 chroot, force 等

        Returns:
            执行结果状态码
        """
        # 检查是否为强制删除
        is_force = params.get("force", "").lower() in ("true", "yes", "1")

        # 如果groupname是数字，则视为GID，需要先获取组名
        if groupname.isdigit():
            # 使用GID获取组名
            gid_cmd = ["getent", "group", groupname]
            gid_result = self._run_command_capture(gid_cmd, check=False)

            if gid_result.returncode != 0 or not gid_result.stdout:
                print(f"错误：找不到GID为 {groupname} 的组")
                return 1

            # 解析组名
            groupname = gid_result.stdout.strip().split(":")[0]

        # 如果强制删除，需要处理组内用户
        if is_force:
            # 获取组信息
            group_info_cmd = ["getent", "group", groupname]
            group_info_result = self._run_command_capture(group_info_cmd, check=False)

            if group_info_result.returncode == 0 and group_info_result.stdout:
                # 解析组信息
                group_info = group_info_result.stdout.strip().split(":")
                if len(group_info) >= 4:
                    gid = group_info[2]
                    members = group_info[3].split(",") if group_info[3] else []

                    # 检查是否存在users组（GID为100）
                    users_group_exists = False
                    users_gid_check = ["getent", "group", "100"]
                    users_gid_result = self._run_command_capture(users_gid_check, check=False)

                    if users_gid_result.returncode == 0 and users_gid_result.stdout:
                        users_group_exists = True

                    # 如果不存在users组，则创建
                    if not users_group_exists:
                        create_users_cmd = ["sudo", "groupadd", "-g", "100", "users"]
                        create_result = self._run_command(create_users_cmd, check=False)
                        if create_result != 0:
                            print(f"警告：无法创建users组")

                    # 检查每个用户的主组是否为要删除的组
                    for user in members:
                        if not user:  # 跳过空字符串
                            continue

                        # 获取用户信息
                        user_info_cmd = ["getent", "passwd", user]
                        user_info_result = self._run_command_capture(user_info_cmd, check=False)

                        if user_info_result.returncode == 0 and user_info_result.stdout:
                            user_info = user_info_result.stdout.strip().split(":")
                            if len(user_info) >= 4:
                                user_gid = user_info[3]

                                # 如果用户的主组是要删除的组
                                if user_gid == gid:
                                    # 将用户的主组修改为users
                                    change_primary_cmd = ["sudo", "usermod", "-g", "users", user]
                                    change_result = self._run_command(change_primary_cmd, check=False)
                                    if change_result != 0:
                                        print(f"警告：无法将用户 {user} 的主组修改为users")

        # 处理chroot参数
        if "chroot" in params:
            chroot_dir = params["chroot"]
            # 在chroot环境中删除组
            chroot_cmd = ["sudo", "chroot", chroot_dir, "groupdel"]

            # 如果groupname是数字，则视为GID，需要先获取组名
            if groupname.isdigit():
                chroot_gid_cmd = ["sudo", "chroot", chroot_dir, "getent", "group", groupname]
                chroot_gid_result = self._run_command_capture(chroot_gid_cmd, check=False)

                if chroot_gid_result.returncode == 0 and chroot_gid_result.stdout:
                    groupname = chroot_gid_result.stdout.strip().split(":")[0]

            chroot_cmd.append(groupname)
            chroot_result = self._run_command(chroot_cmd, check=False)
            if chroot_result != 0:
                print(f"警告：无法在chroot环境 {chroot_dir} 中删除组 {groupname}")

        # 构建groupdel命令
        command = ["sudo", "groupdel", groupname]
        return self._run_command(command)

    def _handle_mod(self, groupname: str, params: Dict[str, str]) -> int:
        """
        修改用户组属性

        Args:
            groupname: 组名或组ID
            params: 参数字典，可能包含 name, gid, user 等

        Returns:
            执行结果状态码
        """
        # 如果groupname是数字，则视为GID，需要先获取组名
        if groupname.isdigit():
            # 使用GID获取组名
            gid_cmd = ["getent", "group", groupname]
            gid_result = self._run_command_capture(gid_cmd, check=False)

            if gid_result.returncode != 0 or not gid_result.stdout:
                print(f"错误：找不到GID为 {groupname} 的组")
                return 1

            # 解析组名
            groupname = gid_result.stdout.strip().split(":")[0]

        # 修改组名和GID
        result = 0  # 初始化返回值
        if "name" in params or "gid" in params:
            # 构建groupmod命令
            command = ["sudo", "groupmod"]

            # 添加新组名参数
            if "name" in params:
                command.extend(["-n", params["name"]])

            # 添加GID参数
            if "gid" in params:
                command.extend(["-g", params["gid"]])

            command.append(groupname)
            result = self._run_command(command)

            # 如果修改了组名，更新后续命令中使用的组名
            if "name" in params and result == 0:
                groupname = params["name"]

            # 如果修改组名或GID失败，不继续处理组成员
            if result != 0:
                return result

        # 处理组成员修改
        if "user" in params:
            user_param = params["user"]

            # 获取当前组成员
            get_members_cmd = ["getent", "group", groupname]
            get_members_result = self._run_command_capture(get_members_cmd, check=False)

            if get_members_result.returncode != 0 or not get_members_result.stdout:
                print(f"错误：无法获取组 '{groupname}' 的信息")
                return 1

            # 解析当前组成员
            group_info = get_members_result.stdout.strip().split(":")
            if len(group_info) < 4:
                print(f"错误：无法解析组 '{groupname}' 的信息")
                return 1

            current_members = group_info[3].split(",") if group_info[3] else []
            current_members = [m for m in current_members if m]  # 过滤掉空字符串

            # 检查是否是覆盖模式（不包含+或-符号）
            if not any(c in user_param for c in ["+", "-"]):
                # 覆盖模式：清空当前成员，设置新成员
                new_members = [u.strip() for u in user_param.split(",") if u.strip()]

                # 移除所有当前成员
                for member in current_members:
                    remove_cmd = ["sudo", "gpasswd", "-d", member, groupname]
                    remove_result = self._run_command(remove_cmd, check=False)
                    if remove_result != 0:
                        print(f"警告：无法从组 '{groupname}' 中移除用户 '{member}'")

                # 添加新成员
                add_result = result  # 跟踪最后一个命令的返回值
                for member in new_members:
                    add_cmd = ["sudo", "usermod", "-aG", groupname, member]
                    add_result = self._run_command(add_cmd, check=False)
                    if add_result != 0:
                        print(f"警告：无法将用户 '{member}' 添加到组 '{groupname}'")
                if "name" not in params and "gid" not in params:
                    result = add_result
            else:
                # 增删模式：解析要添加和删除的用户
                users_to_add = []
                users_to_remove = []

                for user_spec in user_param.split(","):
                    user_spec = user_spec.strip()
                    if not user_spec:
                        continue

                    if user_spec.startswith("+"):
                        users_to_add.append(user_spec[1:])
                    elif user_spec.startswith("-"):
                        users_to_remove.append(user_spec[1:])
                    else:
                        print(f"警告：忽略无效的用户规范 '{user_spec}'，请使用 +用户名 或 -用户名 格式")

                final_result = result

                # 移除指定用户
                for member in users_to_remove:
                    if member in current_members:
                        remove_cmd = ["sudo", "gpasswd", "-d", member, groupname]
                        remove_result = self._run_command(remove_cmd, check=False)
                        final_result = remove_result
                        if remove_result != 0:
                            print(f"警告：无法从组 '{groupname}' 中移除用户 '{member}'")
                    else:
                        print(f"警告：用户 '{member}' 不在组 '{groupname}' 中")

                # 添加指定用户
                for member in users_to_add:
                    if member not in current_members:
                        add_cmd = ["sudo", "usermod", "-aG", groupname, member]
                        add_result = self._run_command(add_cmd, check=False)
                        final_result = add_result
                        if add_result != 0:
                            print(f"警告：无法将用户 '{member}' 添加到组 '{groupname}'")
                    else:
                        print(f"注意：用户 '{member}' 已在组 '{groupname}' 中")

                if "name" not in params and "gid" not in params:
                    result = final_result

        return result

    def _handle_list(self, value: str, params: Dict[str, str]) -> int:
        """
        列出用户组

        Args:
            value: 列表类型，可以是all（所有组）或base（排除系统预置组，默认）
            params: 参数字典，可能包含sort（排序方式）

        Returns:
            执行结果状态码
        """
        # 获取列表类型，默认为base
        list_type = value.lower() if value else "base"
        if list_type not in ["all", "base"]:
            print(f"警告：不支持的列表类型 '{value}'，将使用默认的base类型")
            list_type = "base"

        # 获取排序方式，默认按gid排序
        sort_by = params.get("sort", "gid").lower()
        if sort_by not in ["gname", "gid"]:
            print(f"警告：不支持的排序方式 '{sort_by}'，将使用默认的gid排序")
            sort_by = "gid"

        # 使用getent命令列出用户组
        command = ["getent", "group"]
        result = self._run_command_capture(command, check=False)

        if result.returncode != 0:
            return result.returncode

        # 解析组信息
        groups = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split(':')
            if len(parts) >= 4:
                name = parts[0]
                gid = parts[2]
                members = parts[3].split(",") if parts[3] else []

                # 过滤掉空成员
                members = [m for m in members if m]

                # 判断是否为系统组 (GID < 1000 通常认为是系统组)
                is_system = False
                try:
                    if int(gid) < 1000:
                        is_system = True
                except ValueError:
                    pass

                groups.append({
                    "name": name,
                    "gid": gid,
                    "members": members,
                    "is_system": is_system
                })

        # 根据列表类型过滤
        if list_type == "base":
            # 过滤掉系统预置组
            filtered_groups = [g for g in groups if not g["is_system"]]
            print(f"注意：base模式已排除 {len(groups) - len(filtered_groups)} 个系统预置组")
            groups = filtered_groups

        # 根据排序方式排序
        if sort_by == "gname":
            groups.sort(key=lambda x: x["name"])
        else:  # 默认按gid排序
            try:
                groups.sort(key=lambda x: int(x["gid"]))
            except ValueError:
                # 如果gid不是数字，按字符串排序
                groups.sort(key=lambda x: x["gid"])

        # 计算各列最大宽度
        max_name = max(len(g["name"]) for g in groups) if groups else 0
        max_gid = max(len(g["gid"]) for g in groups) if groups else 0

        # 输出表头
        header = f"{'组名':<{max_name}} {'GID':<{max_gid}} 成员"
        print(header)
        print("-" * len(header))

        # 输出组信息
        for group in groups:
            members_str = ", ".join(group["members"]) if group["members"] else "(无)"
            print(f"{group['name']:<{max_name}} {group['gid']:<{max_gid}} {members_str}")

        # 输出统计信息
        print(f"共找到 {len(groups)} 个用户组")

        return 0

    def _handle_info(self, groupname: str, params: Dict[str, str]) -> int:
        """
        显示用户组详细信息

        Args:
            groupname: 组名
            params: 参数字典，可能包含 users 等

        Returns:
            执行结果状态码
        """
        # 获取组基本信息
        group_cmd = ["getent", "group", groupname]
        group_result = self._run_command_capture(group_cmd, check=False)

        if group_result.returncode != 0:
            print(f"错误：找不到组 '{groupname}'")
            return 1

        # 解析组信息
        group_info = group_result.stdout.strip().split(":")
        if len(group_info) < 4:
            print(f"错误：无法解析组 '{groupname}' 的信息")
            return 1

        # 提取基本信息
        name = group_info[0]
        gid = group_info[2]
        members = group_info[3].split(",") if group_info[3] else []

        # 检查是否为系统组 (GID < 1000 通常认为是系统组)
        is_system = "false"
        try:
            if int(gid) < 1000:
                is_system = "true"
        except ValueError:
            pass

        # 显示基本信息
        print(f"组名: {name}")
        print(f"GID: {gid}")
        print(f"系统组: {is_system}")

        # 如果指定了users参数或组成员不为空，显示成员列表
        if params.get("users", "").lower() in ("true", "yes", "1") or members:
            print("成员:")
            if members:
                for member in sorted(members):
                    if member:  # 跳过空字符串
                        print(f"  {member}")
            else:
                print("  (无)")

        return 0

    def _help_add(self) -> Dict:
        """添加组操作的帮助信息"""
        return {
            "module": "group",
            "action": "add",
            "description": "添加新用户组",
            "parameters": {
                "gid": "组ID（默认：系统自动分配）",
                "user": "创建组时指定组成员，多个用户用逗号分隔（默认：无）",
                "chroot": "chroot到指定目录创建组（默认：无）",
                "system": "是否创建为系统组，值为true/false（默认：false）"
            },
            "usage": "usc group add:<groupname> gid:<gid> user:<user1,user2,...> chroot:<path> system:<true/false>",
            "notes": [
                "system:true时优先级最高，将强制设置gid为系统保留区间",
                "未指定gid时，系统会自动分配一个可用的组ID",
                "如果指定的gid已被其他组使用，系统会显示警告但仍允许创建",
                "user参数可以指定多个用户，用逗号分隔，这些用户将被添加到新创建的组中",
                "chroot参数可以在指定的chroot环境中创建相同的组"
            ]
        }

    def _help_del(self) -> Dict:
        """删除组操作的帮助信息"""
        return {
            "module": "group",
            "action": "del",
            "description": "删除用户组",
            "parameters": {
                "chroot": "chroot到指定目录删除组（默认：无）",
                "force": "是否强制删除组，即使组里有用户，值为true/false（默认：false）"
            },
            "usage": "usc group del:<groupname|gid> chroot:<path> force:<true/false>",
            "notes": [
                "删除组是危险操作，请谨慎使用",
                "可以使用组名或GID作为删除对象",
                "force:true时，系统会自动处理组内用户：如果该组是用户的主组，则将用户的主组修改为users组",
                "如果系统中不存在users组（GID为100），系统会自动创建",
                "chroot参数可以在指定的chroot环境中删除相同的组"
            ]
        }

    def _help_mod(self) -> Dict:
        """修改组操作的帮助信息"""
        return {
            "module": "group",
            "action": "mod",
            "description": "修改用户组属性",
            "parameters": {
                "name": "新的组名",
                "gid": "新的组ID",
                "user": "修改组成员，支持增删模式和覆盖模式"
            },
            "usage": "usc group mod:<groupname|gid> name:<new_name> gid:<new_gid> user:<user_list>",
            "notes": [
                "可以使用组名或组ID作为修改对象",
                "修改组是重要操作，可能会影响系统安全",
                "修改组ID可能会影响文件权限",
                "user参数支持两种模式：",
                "  增删模式：使用+和-前缀，如 +chenxi,-yongyong,+hehed",
                "  覆盖模式：直接指定用户列表，如 chenxi,yongyng,hehed，会清空当前成员并设置新成员",
                "增删模式会保留当前不在删除列表中的成员",
                "覆盖模式会完全替换当前成员列表"
            ]
        }

    def _help_list(self) -> Dict[str, str]:
        """列出组操作的帮助信息"""
        return {
            "module": "group",
            "action": "list",
            "description": "列出用户组",
            "parameters": {
                "value": "列表类型，可以是all（所有组）或base（排除系统预置组，默认）",
                "sort": "排序方式，可以是gname（按组名排序）或gid（按组ID排序，默认）",
                "out": "输出文件路径，可以是目录路径或完整文件路径（默认输出到控制台）"
            },
            "usage": "usc group list:<all|base> sort:<gname|gid> out:<path>",
            "notes": [
                "列出系统中的用户组",
                "默认使用base模式，排除系统预置组（GID < 1000）",
                "使用all参数显示所有组，包括系统预置组",
                "默认按组ID(GID)排序输出",
                "使用sort:gname参数可以按组名字母顺序排序",
                "输出格式为表格，包含组名、GID和组成员",
                "使用out参数可将输出保存到TOML格式的文件中",
                "out:/path/to/dir - 输出到指定目录，文件名自动生成为usc-时间戳.toml",
                "out:/path/to/file.toml - 输出到指定文件"
            ]
        }

    def _help_info(self) -> Dict:
        """显示组信息操作的帮助信息"""
        return {
            "module": "group",
            "action": "info",
            "description": "显示用户组详细信息",
            "parameters": {
                "users": "是否显示组成员，值为true/false（默认：当组有成员时显示）"
            },
            "usage": "usc group info:<groupname> users:<true/false>",
            "notes": [
                "显示组的详细信息，包括组名、GID、是否为系统组等",
                "users:true 时强制显示组成员列表，即使组没有成员",
                "当组有成员时，即使不指定users参数也会显示成员列表"
            ]
        }
