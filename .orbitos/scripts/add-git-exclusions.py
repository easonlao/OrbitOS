# -*- coding: utf-8 -*-
"""Synology git 锁防复发工具：把同步盘内所有 git 仓库的 .git 加入排除规则。

已归入 OrbitOS 项目流程（2026-08-08）：
  - 根 AGENTS.md「文件与数据」固定约束：同步盘内新建/克隆 git 仓库后运行本脚本
  - project-intake.md：代码型项目创建 repo/ 后检查 .git 排除

用法（新建 git 仓库后跑一次，或发现 git 锁时跑一次）：
  1. 运行本脚本（扫描缺失规则并追加到 blacklist.filter）
  2. 按提示重启 cloud-drive 进程
  3. 验证：无 failed to reload / session 移除

关键格式约束（daemon 原生格式，严格模仿）：
  - CRLF 换行；续行 ", \\r\\n"（逗号+空格）；中文用字面 \\xNN 转义；最后一条无逗号
"""
import os
import re

CONF = r"C:\Users\eason\AppData\Local\SynologyDrive\data\session\1\conf\blacklist.filter"
ROOT = r"E:\SynologyDrive"

def esc_path(p: str) -> str:
    """相对路径 → daemon 转义格式（非 ASCII 字符转字面 \\xNN 序列，如 项目→\\xe9\\xa1\\xb9\\xe7\\x9b\\xae）"""
    out = []
    for ch in p:
        if ord(ch) < 128:
            out.append(ch)
        else:
            for b in ch.encode("utf-8"):
                out.append("\\x%02x" % b)
    return "".join(out)

def scan_git_roots():
    found = []

    def walk(base, depth):
        if depth > 8:
            return
        try:
            entries = os.scandir(base)
        except (PermissionError, OSError):
            return
        for e in entries:
            try:
                if e.is_dir():
                    if e.name == ".git":
                        found.append(base)
                    elif e.name not in ("node_modules", ".git", "$RECYCLE.BIN", "System Volume Information"):
                        walk(e.path, depth + 1)
            except OSError:
                pass

    walk(ROOT, 0)
    return found

def main():
    # 读现有规则
    with open(CONF, "rb") as f:
        text = f.read().decode("latin-1")
    entries = set(re.findall(r'"([^"]+)"', text))

    root_norm = ROOT.replace("\\", "/")
    new_rules = []
    for parent in sorted(set(scan_git_roots())):
        rel = parent.replace("\\", "/").replace(root_norm, "")
        desc = esc_path(rel + "/.git")
        if desc not in entries and rel + "/.git" not in entries:
            new_rules.append(desc)

    if not new_rules:
        print("无新增规则（所有 git 仓库 .git 已排除）")
        return

    print("需新增 %d 条:" % len(new_rules))
    for r in new_rules:
        print("  +", r)

    # 备份
    bak = CONF + ".bak-auto"
    if not os.path.exists(bak):
        import shutil
        shutil.copy2(CONF, bak)
        print("备份 ->", bak)

    # 追加到 "/Workbuddy" 前（最后一条无逗号）
    block = "".join('"%s", \r\n' % r for r in new_rules)
    if '"/Workbuddy"' in text:
        text = text.replace('"/Workbuddy"', block + '"/Workbuddy"', 1)
    else:
        text = text.rstrip() + "\r\n" + block.rstrip("\r\n") + "\r\n"
    with open(CONF, "wb") as f:
        f.write(text.encode("latin-1"))

    print("\n已写入。请重启 cloud-drive：")
    print("  PowerShell: Stop-Process -Name cloud-drive-daemon,cloud-drive-connect,cloud-drive-ui -Force")
    print("  PowerShell: Start-Process 'C:\\Program Files\\Synology\\SynologyDrive\\bin\\launcher.exe'")
    print("  验证: 日志无 'failed to reload black list filter' / 'remove_session'")

if __name__ == "__main__":
    main()
