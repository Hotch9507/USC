# USC - Unified Shell Command

一个为Linux命令设计的统一命令翻译兼容层，提供统一的参数和命令格式。

## 设计哲学

参考PowerShell和H3C路由器交互的命令设计哲学，提供一致、直观的命令结构。

## 设计初衷

一个想要为Linux提供统一命令入口的运维-.-
所有命令秉承绝不直接修改系统文件操作,只是通过现有系统命令,完成自己想要的操作
本代码均出自AI之手,本人的Python水平一般,正在每个模块校验设计一致性
当前进度:
- user: 100%
- group: 100%

## 安装教程

### 方法一：使用安装脚本（推荐）

使用安装脚本可以自动检查系统依赖并安装USC：

```bash
# 克隆仓库
git clone https://github.com/Hotch9507/usc.git
cd usc

# 运行安装脚本
chmod +x install.sh
./install.sh
```

安装脚本会：
1. 检查Python版本（需要3.6+）
2. 检查系统命令依赖
3. 如果发现缺失的依赖，会显示安装建议
4. 安装Python依赖和USC

### 方法二：从源码安装

```bash
# 克隆仓库
git clone https://github.com/Hotch9507/usc.git
cd usc

# 检查系统依赖
python3 check_dependencies.py

# 安装依赖
pip3 install -r requirements.txt

# 安装
python3 setup.py install
```

### 方法二：使用PyInstaller创建可执行文件

```bash
# 克隆仓库
git clone https://github.com/Hotch9507/usc.git
cd usc

# 安装依赖
pip install -r requirements.txt

# 安装PyInstaller
pip install pyinstaller

# 创建可执行文件
pyinstaller --onefile --name usc --clean usc.py

# 可执行文件位于 dist/usc
```

### 方法三：安装命令补全功能

为了提高使用效率，建议安装USC的命令不全功能，它可以通过Tab键自动补全命令、模块和参数。

```bash
# 克隆仓库
git clone https://github.com/Hotch9507/usc.git
cd usc

# 使用root权限安装补全
sudo ./install_completion.sh
```

这将：
1. 将补全脚本复制到 `/etc/bash_completion.d/` 目录
2. 添加到 `/etc/profile` 确保所有用户都能使用
3. 为当前用户立即激活补全功能

如果您没有root权限，也可以进行用户级安装：

```bash
# 将补全脚本复制到用户目录
mkdir -p ~/.config/usc
cp usc-completion.bash ~/.config/usc/

# 添加到~/.bashrc
echo "source ~/.config/usc/usc-completion.bash" >> ~/.bashrc

# 重新加载配置
source ~/.bashrc
```

安装完成后，您可以使用Tab键进行命令补全：
- `usc <Tab>` - 补全模块名
- `usc user <Tab>` - 补全用户模块操作
- `usc user add:chenxi <Tab>` - 补全参数

### 命令格式

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

## 卸载USC

### 方法一：使用卸载脚本（推荐）

```bash
# 克隆仓库（如果尚未下载）
git clone https://github.com/Hotch9507/usc.git
cd usc

# 运行卸载脚本
chmod +x uninstall.sh
sudo ./uninstall.sh
```

卸载脚本会：
1. 查找并删除USC可执行文件和Python模块
2. 询问是否删除配置文件
3. 询问是否删除命令补全文件

### 方法二：使用Python卸载工具

```bash
# 克隆仓库（如果尚未下载）
git clone https://github.com/Hotch9507/usc.git
cd usc

# 运行Python卸载工具
sudo python3 uninstall.py
```

### 方法三：手动卸载

```bash
# 使用pip卸载
pip3 uninstall usc

# 或者手动删除
sudo rm -f $(which usc)
sudo rm -rf $(python3 -c "import usc; print(usc.__file__)" | sed 's|/__init__.py||')
```

## 系统依赖

USC依赖于一系列Linux系统命令，按功能分类如下：

- **基础命令**: which, sudo, grep, awk, sort, tail, echo, cat, column
- **系统信息**: uname, uptime, free, df, lscpu, ip
- **用户管理**: useradd, usermod, userdel, passwd, chage, getent, id
- **进程管理**: ps, kill, pgrep, pstree, renice, prlimit
- **磁盘管理**: lsblk, fdisk, parted, mkfs.*, mount, umount, fsck, blkid, tune2fs
- **网络管理**: ip, ss, ping, netstat, nc, iptables, dig, resolvconf, nsupdate, nmap
- **服务管理**: systemctl, service, chkconfig
- **防火墙管理**: firewall-cmd, ufw, iptables
- **日志管理**: journalctl
- **定时任务**: crontab
- **包管理**: dnf, yum, apt, apt-get, zypper, pacman, dpkg, apt-cache
- **系统关机**: shutdown, reboot, halt, poweroff

在安装前，可以使用以下命令检查依赖：

```bash
python3 check_dependencies.py
```

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
