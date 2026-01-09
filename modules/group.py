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
            check_result = self._run_command(check_gid_cmd, check=False, output_format="raw")
            if check_result == 0 and check_result.stdout:
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
            groupname: 组名
            params: 参数字典（当前未使用）

        Returns:
            执行结果状态码
        """
        # 构建groupdel命令
        command = ["sudo", "groupdel", groupname]
        return self._run_command(command)

    def _handle_mod(self, groupname: str, params: Dict[str, str]) -> int:
        """
        修改用户组属性

        Args:
            groupname: 组名
            params: 参数字典，可能包含 name, gid 等

        Returns:
            执行结果状态码
        """
        # 构建groupmod命令
        command = ["sudo", "groupmod"]

        # 添加新组名参数
        if "name" in params:
            command.extend(["-n", params["name"]])

        # 添加GID参数
        if "gid" in params:
            command.extend(["-g", params["gid"]])

        command.append(groupname)
        return self._run_command(command)

    def _handle_list(self, value: str, params: Dict[str, str]) -> int:
        """
        列出用户组

        Args:
            value: 未使用
            params: 参数字典（当前未使用）

        Returns:
            执行结果状态码
        """
        # 使用getent命令列出用户组
        command = ["getent", "group"]
        result = self._run_command(command, check=False, output_format="raw")

        if result != 0:
            return result

        # 解析并输出组名
        groups = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split(':')
            if len(parts) >= 1:
                groups.append(parts[0])

        # 按字母顺序排序并输出
        for group in sorted(groups):
            print(group)

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
        group_result = self._run_command(group_cmd, check=False, output_format="raw")

        if group_result != 0:
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
            "parameters": {},
            "usage": "usc group del:<groupname>",
            "notes": [
                "删除组是危险操作，请谨慎使用",
                "如果组是某些用户的主组，则不能删除"
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
                "gid": "新的组ID"
            },
            "usage": "usc group mod:<groupname> name:<new_name> gid:<new_gid>",
            "notes": [
                "修改组是重要操作，可能会影响系统安全",
                "修改组ID可能会影响文件权限"
            ]
        }

    def _help_list(self) -> Dict:
        """列出组操作的帮助信息"""
        return {
            "module": "group",
            "action": "list",
            "description": "列出用户组",
            "parameters": {},
            "usage": "usc group list",
            "notes": [
                "列出系统中的所有用户组",
                "输出按字母顺序排序"
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
