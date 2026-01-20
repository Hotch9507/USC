"""
磁盘管理模块
"""

from typing import Dict

from .base import BaseModule


class DiskModule(BaseModule):
    """磁盘管理模块"""

    def get_description(self) -> str:
        """获取模块描述"""
        return "管理磁盘、分区和文件系统"

    def get_actions(self) -> Dict[str, str]:
        """获取模块支持的操作及其描述"""
        return {
            "list": "列出磁盘和分区",
            "info": "显示磁盘详细信息",
            "format": "格式化磁盘或分区",
            "mount": "挂载文件系统",
            "unmount": "卸载文件系统",
            "partition": "管理磁盘分区",
            "fsck": "检查和修复文件系统",
            "usage": "显示磁盘使用情况",
            "uuid": "管理文件系统UUID"
        }

    def get_boolean_params(self, action: str = None) -> Dict[str, List[str]]:
        """
        获取布尔参数列表

        Returns:
            布尔参数字典，格式为 {action: [param1, param2, ...]}
        """
        boolean_params = {
            "list": ["detail"],
            "info": [],
            "format": ["force"],
            "mount": [],
            "unmount": ["force", "lazy"],
            "partition": [],
            "fsck": ["force", "auto_repair", "no_repair"],
            "usage": ["human_readable", "inode"],
            "uuid": []
        }
        return boolean_params

    def _handle_list(self, item: str, params: Dict[str, str]) -> int:
        """
        列出磁盘和分区

        Args:
            item: 列表类型，可以是 disk, partition, all
            params: 参数字典，可能包含 format, detail 等

        Returns:
            执行结果状态码
        """
        if item == "disk" or item == "all":
            # 使用lsblk命令列出磁盘
            command = ["lsblk"]

            # 如果指定了format参数，添加输出格式
            if "format" in params:
                command.extend(["-o", params["format"]])
            else:
                command.extend(["-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT"])

            # 如果指定了detail参数且为真，添加更多详细信息
            if params.get("detail", "").lower() in ("true", "yes", "1"):
                command.append("-f")

            result = self._run_command(command)

            # 如果不是all类型，直接返回
            if item != "all":
                return result

        if item == "partition" or item == "all":
            # 使用fdisk命令列出分区表
            command = ["sudo", "fdisk", "-l"]

            # 如果指定了device参数，只列出特定设备的分区
            if "device" in params:
                command.append(params["device"])

            result = result or self._run_command(command)

        return result

    def _handle_info(self, device: str, params: Dict[str, str]) -> int:
        """
        显示磁盘详细信息

        Args:
            device: 设备路径
            params: 参数字典，可能包含 format 等

        Returns:
            执行结果状态码
        """
        # 构建lsblk命令
        command = ["lsblk", "-f", device]

        # 如果指定了format参数，使用自定义输出格式
        if "format" in params:
            command = ["lsblk", "-o", params["format"], device]

        return self._run_command(command)

    def _handle_format(self, device: str, params: Dict[str, str]) -> int:
        """
        格式化磁盘或分区

        Args:
            device: 设备路径
            params: 参数字典，必须包含 type，可能包含 label, force 等

        Returns:
            执行结果状态码
        """
        if "type" not in params:
            print("错误：format 操作需要指定文件系统类型 'type'")
            return 1

        fs_type = params["type"]

        # 如果指定了force参数且为真，添加-f选项
        force = params.get("force", "").lower() in ("true", "yes", "1")

        # 根据文件系统类型选择格式化命令
        if fs_type.lower() == "ext4":
            command = ["sudo", "mkfs.ext4"]
            if force:
                command.append("-F")
        elif fs_type.lower() == "ext3":
            command = ["sudo", "mkfs.ext3"]
            if force:
                command.append("-F")
        elif fs_type.lower() == "ext2":
            command = ["sudo", "mkfs.ext2"]
            if force:
                command.append("-F")
        elif fs_type.lower() == "xfs":
            command = ["sudo", "mkfs.xfs"]
            if force:
                command.append("-f")
        elif fs_type.lower() == "btrfs":
            command = ["sudo", "mkfs.btrfs"]
            if force:
                command.append("-f")
        elif fs_type.lower() == "ntfs":
            command = ["sudo", "mkfs.ntfs"]
            if force:
                command.append("-f")
        elif fs_type.lower() == "fat32":
            command = ["sudo", "mkfs.vfat", "-F", "32"]
        elif fs_type.lower() == "fat16":
            command = ["sudo", "mkfs.vfat", "-F", "16"]
        elif fs_type.lower() == "swap":
            command = ["sudo", "mkswap"]
            if force:
                command.append("-f")
        else:
            print(f"错误：不支持的文件系统类型 '{fs_type}'")
            return 1

        # 如果指定了label参数，添加标签
        if "label" in params:
            label = params["label"]
            if fs_type.lower() in ["ext4", "ext3", "ext2"]:
                command.extend(["-L", label])
            elif fs_type.lower() == "xfs":
                command.extend(["-L", label])
            elif fs_type.lower() == "btrfs":
                command.extend(["-L", label])
            elif fs_type.lower() == "ntfs":
                command.extend(["-L", label])
            elif fs_type.lower() in ["fat32", "fat16"]:
                command.extend(["-n", label])

        command.append(device)
        return self._run_command(command)

    def _handle_mount(self, device: str, params: Dict[str, str]) -> int:
        """
        挂载文件系统

        Args:
            device: 设备路径
            params: 参数字典，必须包含 path，可能包含 type, options 等

        Returns:
            执行结果状态码
        """
        if "path" not in params:
            print("错误：mount 操作需要指定挂载点 'path'")
            return 1

        path = params["path"]

        # 构建mount命令
        command = ["sudo", "mount"]

        # 添加类型参数
        if "type" in params:
            command.extend(["-t", params["type"]])

        # 添加选项参数
        if "options" in params:
            command.extend(["-o", params["options"]])

        command.extend([device, path])
        return self._run_command(command)

    def _handle_unmount(self, path: str, params: Dict[str, str]) -> int:
        """
        卸载文件系统

        Args:
            path: 挂载点或设备路径
            params: 参数字典，可能包含 force, lazy 等

        Returns:
            执行结果状态码
        """
        # 构建umount命令
        command = ["sudo", "umount"]

        # 如果指定了force参数且为真，添加-f选项
        if params.get("force", "").lower() in ("true", "yes", "1"):
            command.append("-f")

        # 如果指定了lazy参数且为真，添加-l选项
        if params.get("lazy", "").lower() in ("true", "yes", "1"):
            command.append("-l")

        command.append(path)
        return self._run_command(command)

    def _handle_partition(self, action: str, params: Dict[str, str]) -> int:
        """
        管理磁盘分区

        Args:
            action: 操作类型，可以是 create, delete, list, resize
            params: 参数字典，可能包含 device, size, type 等

        Returns:
            执行结果状态码
        """
        if action == "list":
            # 使用fdisk命令列出分区表
            command = ["sudo", "fdisk", "-l"]

            # 如果指定了device参数，只列出特定设备的分区
            if "device" in params:
                command.append(params["device"])

            return self._run_command(command)

        elif action == "create":
            if "device" not in params:
                print("错误：create 操作需要指定设备 'device'")
                return 1

            device = params["device"]

            # 使用parted命令创建分区
            command = ["sudo", "parted", device, "--script"]

            # 如果指定了size参数，创建指定大小的分区
            if "size" in params:
                size = params["size"]
                command.extend(["mkpart", "primary", size])
            else:
                # 创建使用全部空间的分区
                command.extend(["mkpart", "primary", "100%"])

            return self._run_command(command)

        elif action == "delete":
            if "device" not in params or "number" not in params:
                print("错误：delete 操作需要指定设备 'device' 和分区号 'number'")
                return 1

            device = params["device"]
            number = params["number"]

            # 使用parted命令删除分区
            command = ["sudo", "parted", device, "--script", "rm", number]
            return self._run_command(command)

        elif action == "resize":
            if "device" not in params or "number" not in params or "size" not in params:
                print("错误：resize 操作需要指定设备 'device'、分区号 'number' 和大小 'size'")
                return 1

            device = params["device"]
            number = params["number"]
            size = params["size"]

            # 使用parted命令调整分区大小
            command = ["sudo", "parted", device, "--script", "resizepart", number, size]
            return self._run_command(command)

        else:
            print(f"错误：未知操作 '{action}'")
            return 1

    def _handle_fsck(self, device: str, params: Dict[str, str]) -> int:
        """
        检查和修复文件系统

        Args:
            device: 设备路径
            params: 参数字典，可能包含 type, force, auto 等

        Returns:
            执行结果状态码
        """
        # 构建fsck命令
        command = ["sudo", "fsck"]

        # 添加类型参数
        if "type" in params:
            command.extend(["-t", params["type"]])

        # 如果指定了force参数且为真，添加-f选项
        if params.get("force", "").lower() in ("true", "yes", "1"):
            command.append("-f")

        # 如果指定了auto参数且为真，添加-a选项
        if params.get("auto", "").lower() in ("true", "yes", "1"):
            command.append("-a")

        # 如果指定了no_repair参数且为真，添加-n选项
        if params.get("no_repair", "").lower() in ("true", "yes", "1"):
            command.append("-n")

        command.append(device)
        return self._run_command(command)

    def _handle_usage(self, path: str, params: Dict[str, str]) -> int:
        """
        显示磁盘使用情况

        Args:
            path: 路径，可以是目录或设备
            params: 参数字典，可能包含 human_readable, inode 等

        Returns:
            执行结果状态码
        """
        # 构建df命令
        command = ["df"]

        # 如果指定了human_readable参数且为真，添加-h选项
        if params.get("human_readable", "").lower() in ("true", "yes", "1"):
            command.append("-h")

        # 如果指定了inode参数且为真，添加-i选项
        if params.get("inode", "").lower() in ("true", "yes", "1"):
            command.append("-i")

        # 如果指定了path参数，只显示特定路径的使用情况
        if path:
            command.append(path)

        return self._run_command(command)

    def _handle_uuid(self, action: str, params: Dict[str, str]) -> int:
        """
        管理文件系统UUID

        Args:
            action: 操作类型，可以是 list, set, get
            params: 参数字典，可能包含 device, uuid 等

        Returns:
            执行结果状态码
        """
        if action == "list":
            # 使用blkid命令列出所有文件系统的UUID
            command = ["sudo", "blkid"]

            # 如果指定了device参数，只显示特定设备的UUID
            if "device" in params:
                command.append(params["device"])

            return self._run_command(command)

        elif action == "get":
            if "device" not in params:
                print("错误：get 操作需要指定设备 'device'")
                return 1

            device = params["device"]

            # 使用blkid命令获取特定设备的UUID
            command = ["sudo", "blkid", "-o", "value", "-s", "UUID", device]
            return self._run_command(command)

        elif action == "set":
            if "device" not in params or "uuid" not in params:
                print("错误：set 操作需要指定设备 'device' 和UUID 'uuid'")
                return 1

            device = params["device"]
            uuid = params["uuid"]

            # 使用tune2fs命令设置ext文件系统的UUID
            command = ["sudo", "tune2fs", "-U", uuid, device]
            return self._run_command(command)

        else:
            print(f"错误：未知操作 '{action}'")
            return 1
