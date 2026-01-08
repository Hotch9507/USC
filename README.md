# USC - Unified Shell Command

一个为Linux命令设计的统一命令翻译兼容层，提供统一的参数和命令格式。

## 设计哲学

参考PowerShell和Kubernetes的命令设计哲学，提供一致、直观的命令结构。

## 命令格式

```
usc <module> <action>:<value> [parameter:value] [parameter:value] ...
```

- **主入口**: `usc`
- **二级模块**: 如 `user`, `file`, `network` 等
- **操作**: 如 `add`, `del`, `move`, `copy` 等
- **参数**: 格式为 `参数名:参数值`

### 命令示例

```bash
# 添加用户
usc user add:chenxi home:/home/chenxi

# 删除用户
usc user del:chenxi

# 移动文件
usc file mv:/path/to/src dest:/path/to/dest

# 复制文件
usc file cp:/path/to/src dest:/path/to/dest
```

## 设计原则

1. 所有二级模块的第一参数都是必填项
2. 第二及以后的参数有默认值，非必填
3. 长单词使用缩写(3-5个字符)
4. 短单词(少于5个字符)使用全称

## 帮助系统

USC提供了完善的帮助系统，方便用户查询模块和操作的使用方法：

1. **查看所有模块**：
   ```bash
   usc help
   ```

2. **查看特定模块帮助**：
   ```bash
   usc help user
   # 或
   usc user:help
   ```

3. **查看特定操作帮助**：
   ```bash
   usc help action:user.add
   ```

4. **查看使用示例**：
   ```bash
   usc help examples
   ```

帮助信息以TOML格式输出，便于其他工具解析和处理。

## 模块设计

每个二级模块对应一个类，实现特定领域的命令转换和执行。

### 当前支持的模块

1. **用户管理模块 (user)**：
   - 添加用户：`usc user add:chenxi home:/home/chenxi`
   - 删除用户：`usc user del:chenxi`
   - 修改用户：`usc user mod:chenxi shell:/bin/bash`
   - 列出用户：`usc user list:all`
   - 用户信息：`usc user info:chenxi groups:true`

2. **文件管理模块 (file)**：
   - 复制文件：`usc file cp:/path/to/src dest:/path/to/dest`
   - 移动文件：`usc file mv:/path/to/src dest:/path/to/dest`
   - 删除文件：`usc file rm:/path/to/file recursive:true`
   - 创建目录：`usc file mkdir:/path/to/dir parents:true`
   - 显示文件：`usc file cat:/path/to/file number:true`

3. **网络管理模块 (network)**：
   - 接口管理：`usc network iface:up name:eth0`
   - 网络连接：`usc network conn:list state:established`
   - 网络测试：`usc network ping:google.com count:4`
   - 端口管理：`usc network port:list proto:tcp`
   - 防火墙规则：`usc network firewall:add chain:INPUT rule:"-p tcp --dport 22 -j ACCEPT"`

4. **系统管理模块 (system)**：
   - 系统信息：`usc system info:all`
   - 日志查看：`usc system log:system lines:100 follow:true`
   - 定时任务：`usc system cron:add expression:"0 0 * * *" command:"/path/to/script"`
   - 系统关机：`usc system shutdown:shutdown time:10 message:"系统将在10分钟后关机"`

5. **包管理模块 (package)**：
   - 安装软件包：`usc package install:vim`
   - 删除软件包：`usc package remove:vim`
   - 更新软件包：`usc package update:vim`
   - 搜索软件包：`usc package search:nginx`
   - 列出已安装软件包：`usc package list:installed`
   - 显示软件包信息：`usc package info:vim`

6. **进程管理模块 (process)**：
   - 列出进程：`usc process list:all user:chenxi`
   - 终止进程：`usc process kill:1234 signal:9`
   - 进程树：`usc process tree:all format:pid`
   - 搜索进程：`usc process search:nginx exact:true`
   - 进程信息：`usc process info:1234 detail:true`
   - 调整优先级：`usc process nice:1234 priority:10`
   - 资源限制：`usc process limit:1234 resource:nofile value:4096`

7. **服务管理模块 (service)**：
   - 列出服务：`usc service list:all state:running`
   - 启动服务：`usc service start:nginx`
   - 停止服务：`usc service stop:nginx`
   - 重启服务：`usc service restart:nginx`
   - 服务状态：`usc service status:nginx`
   - 启用自启动：`usc service enable:nginx now:true`
   - 禁用自启动：`usc service disable:nginx now:true`
   - 屏蔽服务：`usc service mask:nginx`
   - 取消屏蔽：`usc service unmask:nginx`

8. **磁盘管理模块 (disk)**：
   - 列出磁盘：`usc disk list:all detail:true`
   - 磁盘信息：`usc disk info:/dev/sda`
   - 格式化分区：`usc disk format:/dev/sda1 type:ext4 label:data`
   - 挂载文件系统：`usc disk mount:/dev/sda1 path:/mnt/data options:defaults`
   - 卸载文件系统：`usc disk unmount:/mnt/data force:true`
   - 分区管理：`usc disk partition:create device:/dev/sdb size:10G`
   - 检查文件系统：`usc disk fsck:/dev/sda1 force:true`
   - 磁盘使用情况：`usc disk usage:/ human_readable:true`
   - UUID管理：`usc disk uuid:list`
