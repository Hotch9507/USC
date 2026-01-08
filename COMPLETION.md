
# USC命令补全功能

USC提供了强大的命令行补全功能，可以大大提高命令输入效率。

## 安装方法

### 系统级安装（推荐）

使用root权限运行安装脚本：

```bash
sudo ./install_completion.sh
```

这将会：
1. 将补全脚本复制到 `/etc/bash_completion.d/` 目录
2. 添加到 `/etc/profile` 确保所有用户都能使用
3. 为当前用户立即激活补全功能

### 用户级安装

如果您没有root权限，可以将补全脚本添加到个人配置：

```bash
# 将usc-completion.bash复制到用户目录
cp usc-completion.bash ~/.config/usc/

# 添加到~/.bashrc
echo "source ~/.config/usc/usc-completion.bash" >> ~/.bashrc

# 重新加载配置
source ~/.bashrc
```

## 使用方法

安装完成后，您可以使用Tab键进行命令补全：

1. **模块补全**
   ```bash
   usc <Tab>
   # 将显示所有可用模块：user, file, network, system, process, service, disk, package
   ```

2. **操作补全**
   ```bash
   usc user <Tab>
   # 将显示user模块的所有操作：add, del, mod, list, info
   ```

3. **参数补全**
   ```bash
   usc user add: <Tab>
   # 将显示add操作的所有参数：home, shell, groups, password
   ```

4. **参数值补全**
   ```bash
   usc user add:chenxi home:<Tab>
   # 将补全目录路径
   ```

5. **复合补全**
   ```bash
   usc user add:chenxi home:/home/chenxi <Tab>
   # 将继续补全其他参数
   ```

## 高级功能

补全脚本还提供了一些智能补全功能：

- **文件路径补全**：对于home、path、dest等参数，提供目录和文件补全
- **用户名补全**：对于user参数，提供系统用户名补全
- **Shell路径补全**：对于shell参数，提供常见Shell路径补全

## 自定义补全

如果您想为自定义模块添加补全支持，可以在模块中实现`_help_<action>()`方法，返回包含参数信息的字典。

例如：

```python
def _help_custom(self) -> Dict:
    """自定义操作的帮助信息"""
    return {
        "module": "mymodule",
        "action": "custom",
        "description": "自定义操作描述",
        "parameters": {
            "param1": "参数1描述",
            "param2": "参数2描述"
        },
        "usage": "usc mymodule custom:<value> param1:<value> param2:<value>"
    }
```

## 故障排除

如果补全功能不工作：

1. 确认已正确安装补全脚本
2. 检查是否有bash-completion包：`dpkg -l | grep bash-completion`
3. 确认usc命令在PATH中：`which usc`
4. 尝试手动加载补全脚本：`source /etc/bash_completion.d/usc-completion.bash`

如果问题仍然存在，可以查看补全脚本中的调试信息。
