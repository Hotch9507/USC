
#!/bin/bash

# USC命令补全安装脚本

# 检查是否有root权限
if [[ $EUID -ne 0 ]]; then
   echo "此脚本需要root权限运行" 
   exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 复制补全脚本到系统目录
echo "安装USC命令补全..."
cp "$SCRIPT_DIR/usc-completion.bash" /etc/bash_completion.d/

# 添加到/etc/profile确保所有用户都能使用
if ! grep -q "usc-completion.bash" /etc/profile; then
    echo "# USC命令补全" >> /etc/profile
    echo "source /etc/bash_completion.d/usc-completion.bash" >> /etc/profile
fi

# 为当前用户激活补全
source /etc/bash_completion.d/usc-completion.bash

echo "USC命令补全安装完成！"
echo "请重新登录或运行 'source /etc/bash_completion.d/usc-completion.bash' 来激活补全功能。"
echo ""
echo "使用示例："
echo "  usc <Tab>          # 补全模块名"
echo "  usc user <Tab>     # 补全用户模块操作"
echo "  usc user add <Tab>  # 补全add操作的参数"
