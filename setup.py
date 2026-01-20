
import os
import shutil
import sys

from setuptools import find_packages, setup
from setuptools.command.install import install

# 导入依赖检查模块
try:
    from check_dependencies import check_dependencies, print_results, suggest_package_installs
except ImportError:
    # 如果在开发环境中，直接导入
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from check_dependencies import check_dependencies, print_results, suggest_package_installs


class InstallConfigFilesCommand(install):
    """自定义安装命令，在安装后配置文件"""

    def run(self):
        # 先执行标准安装
        install.run(self)

        # 安装配置文件
        self.install_config_files()

    def install_config_files(self):
        """安装配置文件到/etc/usc/"""
        config_source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
        config_target_dir = "/etc/usc"

        # 检查config目录是否存在
        if not os.path.exists(config_source_dir):
            print(f"警告：配置目录不存在: {config_source_dir}")
            return

        try:
            # 创建目标配置目录
            if not os.path.exists(config_target_dir):
                print(f"创建配置目录: {config_target_dir}")
                os.makedirs(config_target_dir, mode=0o755)

            # 复制所有配置文件
            config_files = [f for f in os.listdir(config_source_dir) if f.endswith('.toml')]

            for config_file in config_files:
                source_file = os.path.join(config_source_dir, config_file)
                target_file = os.path.join(config_target_dir, config_file)

                # 如果目标文件已存在，跳过（保留用户配置）
                if os.path.exists(target_file):
                    print(f"配置文件已存在，跳过: {target_file}")
                else:
                    shutil.copy2(source_file, target_file)
                    print(f"安装配置文件: {target_file}")

            print(f"\n配置文件安装完成！")
            print(f"配置目录: {config_target_dir}")
            print(f"提示: 可以使用 'usc config list:all' 查看配置状态")
            print(f"      可以使用 'usc config edit:{{模块名}}' 修改配置")

        except PermissionError:
            print(f"警告：权限不足，无法安装配置文件到 {config_target_dir}")
            print(f"请使用 sudo 运行安装命令，或手动复制配置文件：")
            print(f"  sudo mkdir -p {config_target_dir}")
            print(f"  sudo cp {config_source_dir}/*.toml {config_target_dir}/")
        except Exception as e:
            print(f"警告：安装配置文件失败: {e}")


class CheckDependenciesCommand(install):
    """自定义安装命令，在安装前检查依赖"""

    def run(self):
        # 检查所有依赖
        results = check_dependencies()

        # 打印结果
        all_good = print_results(results)

        if not all_good:
            # 收集缺失的命令
            missing_commands = []
            for category, commands in results.items():
                for command, exists, _ in commands:
                    if not exists:
                        missing_commands.append(command)

            # 建议安装的包
            suggestions = suggest_package_installs(missing_commands)

            if suggestions:
                print("建议安装以下包来满足依赖:")
                for manager, packages in suggestions.items():
                    print(f"使用 {manager} 安装:")
                    print(f"  sudo {manager} install {' '.join(packages)}")

            # 询问用户是否继续安装
            response = input("是否继续安装USC？(y/N): ").strip().lower()
            if response not in ["y", "yes"]:
                print("安装已取消。")
                sys.exit(1)

        # 继续执行标准安装
        install.run(self)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="usc",
    version="0.1.0",
    author="hotch9507",
    author_email="hotch9507@aliyun.com",
    description="Unified Shell Command - Linux命令统一翻译兼容层",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "usc=usc:main",
        ],
    },
    cmdclass={
        "install": InstallConfigFilesCommand,
    },
    # 包含配置文件
    package_data={
        "usc": ["config/*.toml"],
    },
    include_package_data=True,
)
