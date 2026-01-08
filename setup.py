
from setuptools import find_packages, setup

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
)
