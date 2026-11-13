# 在命令解释器中加载本文件，提供按需启停与恢复代理环境的命令。
pcvpn-on() {
    local key
    if [[ ${_PCVPN_ACTIVE:-0} != 1 ]]; then
        declare -gA _PCVPN_OLD_VALUES _PCVPN_OLD_PRESENT
        for key in HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy NO_PROXY no_proxy; do
            if [[ -v $key ]]; then _PCVPN_OLD_PRESENT[$key]=1; _PCVPN_OLD_VALUES[$key]=${!key}; else _PCVPN_OLD_PRESENT[$key]=0; fi
        done
    fi
    . "$HOME/.config/pcvpn/environment.sh"
    _PCVPN_ACTIVE=1
    printf '%s\n' '当前命令解释器及之后启动的子进程已启用个人代理。'
}
pcvpn-off() {
    local key
    if [[ ${_PCVPN_ACTIVE:-0} == 1 ]]; then
        for key in HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy NO_PROXY no_proxy; do
            if [[ ${_PCVPN_OLD_PRESENT[$key]:-0} == 1 ]]; then export "$key=${_PCVPN_OLD_VALUES[$key]}"; else unset "$key"; fi
        done
        unset _PCVPN_ACTIVE _PCVPN_OLD_VALUES _PCVPN_OLD_PRESENT
    fi
    printf '%s\n' '当前命令解释器已恢复原代理环境。'
}
pcvpn-run() { "$HOME/.local/bin/pcvpn-run" "$@"; }
pcvpn-test() { "$HOME/.local/bin/pcvpn-test" "$@"; }
