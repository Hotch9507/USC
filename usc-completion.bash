
#!/bin/bash

# USC命令补全脚本
# 安装方法:
# 1. 将此文件复制到 /etc/bash_completion.d/ 目录
# 2. 或者将此文件内容添加到 ~/.bashrc 文件中

_usc_completion() {
    local cur prev words cword
    _init_completion || return

    # 获取当前命令行分割后的单词
    words=("${COMP_WORDS[@]}")
    cword=$COMP_CWORD

    # 根据当前光标位置决定补全内容
    case $cword in
        1)
            # 补全模块名
            local modules=$(usc help 2>/dev/null | grep -E '^\s+[a-z]+\s+-' | awk '{print $1}' | tr '
' ' ')
            COMPREPLY=($(compgen -W "$modules" -- "$cur"))
            ;;
        2)
            # 补全操作名
            local module=${words[1]}
            if [[ -n "$module" ]]; then
                local actions=$(usc help module:$module 2>/dev/null | grep -E '^\s+action\s+=' | cut -d'"' -f2 | tr '
' ' ')
                COMPREPLY=($(compgen -W "$actions" -- "${cur%%:*}"))
            fi
            ;;
        3)
            # 补全参数名
            local module=${words[1]}
            local action=${words[2]%%:*}

            if [[ -n "$module" && -n "$action" ]]; then
                # 获取特定操作的参数提示
                local param_help=$(usc help action:$module.$action 2>/dev/null)

                if [[ -n "$param_help" ]]; then
                    # 从帮助信息中提取参数名
                    local params=$(echo "$param_help" | grep -E '^\s+[a-z]+\s*=' | awk -F'=' '{print $1}' | tr '
' ' ')
                    COMPREPLY=($(compgen -W "$params" -- "${cur%%:*}"))
                fi
            fi
            ;;
        *)
            # 对于更高级的补全，可以继续扩展
            # 例如补全文件路径、用户名等
            if [[ "$cur" == *:* ]]; then
                # 如果当前输入包含冒号，可能是参数值
                local param_name=${cur%%:*}
                local param_value=${cur#*:}

                # 根据参数类型提供不同的补全
                case $param_name in
                    home|path|dest)
                        # 文件路径补全
                        COMPREPLY=($(compgen -d -- "$param_value"))
                        ;;
                    shell)
                        # Shell路径补全
                        COMPREPLY=($(compgen -W "/bin/bash /bin/sh /bin/zsh /bin/fish /bin/csh /bin/tcsh /bin/ksh" -- "$param_value"))
                        ;;
                    user)
                        # 用户名补全
                        COMPREPLY=($(compgen -u -- "$param_value"))
                        ;;
                    *)
                        # 默认不提供补全
                        ;;
                esac
            fi
            ;;
    esac

    # 添加冒号到补全结果中（如果还没有的话）
    for ((i=0; i<${#COMPREPLY[@]}; i++)); do
        if [[ "${COMPREPLY[$i]}" != *:* && $cword -ge 2 && $cword -le 3 ]]; then
            COMPREPLY[$i]="${COMPREPLY[$i]}:"
        fi
    done
}

# 注册补全函数
complete -F _usc_completion usc
