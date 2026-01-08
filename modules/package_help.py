
# 这些方法需要添加到package.py文件末尾

    def _help_install(self) -> Dict:
        """安装软件包操作的帮助信息"""
        return {
            "module": "package",
            "action": "install",
            "description": "安装软件包",
            "parameters": {
                "repo": "指定软件仓库",
                "arch": "指定架构",
                "version": "指定版本"
            },
            "usage": "usc package install:<package_name> repo:<repository> arch:<architecture> version:<version>"
        }

    def _help_remove(self) -> Dict:
        """删除软件包操作的帮助信息"""
        return {
            "module": "package",
            "action": "remove",
            "description": "删除软件包",
            "parameters": {
                "autoremove": "是否自动删除不需要的依赖，值为true/false",
                "purge": "是否完全删除包括配置文件，值为true/false"
            },
            "usage": "usc package remove:<package_name> autoremove:<true/false> purge:<true/false>"
        }

    def _help_update(self) -> Dict:
        """更新软件包操作的帮助信息"""
        return {
            "module": "package",
            "action": "update",
            "description": "更新软件包",
            "parameters": {
                "repo": "指定软件仓库",
                "security": "是否只更新安全补丁，值为true/false"
            },
            "usage": "usc package update:<package_name|all> repo:<repository> security:<true/false>"
        }

    def _help_search(self) -> Dict:
        """搜索软件包操作的帮助信息"""
        return {
            "module": "package",
            "action": "search",
            "description": "搜索软件包",
            "parameters": {
                "repo": "指定软件仓库",
                "arch": "指定架构",
                "exact": "是否精确匹配，值为true/false"
            },
            "usage": "usc package search:<keyword> repo:<repository> arch:<architecture> exact:<true/false>"
        }

    def _help_list(self) -> Dict:
        """列出软件包操作的帮助信息"""
        return {
            "module": "package",
            "action": "list",
            "description": "列出已安装的软件包",
            "parameters": {
                "repo": "指定软件仓库",
                "arch": "指定架构"
            },
            "usage": "usc package list:<all|installed|updates> repo:<repository> arch:<architecture>"
        }

    def _help_info(self) -> Dict:
        """显示软件包信息操作的帮助信息"""
        return {
            "module": "package",
            "action": "info",
            "description": "显示软件包详细信息",
            "parameters": {
                "repo": "指定软件仓库",
                "version": "指定版本"
            },
            "usage": "usc package info:<package_name> repo:<repository> version:<version>"
        }
