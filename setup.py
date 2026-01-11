
import os
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
        "install": CheckDependenciesCommand,
    },
)
