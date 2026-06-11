# Codex Browser / Computer Use 插件修复记录

日期：2026-06-11

## 现象

- Codex 设置页中：
  - `浏览器` 显示“应用内浏览器插件不可用”
  - `电脑操控` 显示“Computer Use 插件不可用”
- 问题背景：
  - 之前使用过 `codex++`
  - 后来切回官方 Codex
  - 切回后这两个官方插件失效

## 根因

这次不是“插件没启用”，而是“插件源和缓存版本错位”。

具体表现：

1. 官方桌面端版本已经升级到：
   - `OpenAI.Codex_26.608.1337.0`

2. 但本地 Codex 仍在使用旧的 bundled marketplace 源：
   - `C:\Users\eason\.codex\.tmp\bundled-marketplaces\openai-bundled`

3. 这个本地 marketplace 镜像已经损坏，只剩：
   - `plugins\chrome`
   - 缺少：
     - `plugins\browser`
     - `plugins\computer-use`

4. 同时本地缓存还残留旧版插件目录：
   - `26.602.40724`

所以设置页虽然还能看到插件条目，但实际加载源不完整，最终显示“不可用”。

## 关键定位点

### 1. 检查官方 app 版本

```powershell
Get-ChildItem 'C:\Program Files\WindowsApps' |
  Where-Object { $_.Name -like 'OpenAI.Codex*' } |
  Sort-Object Name |
  Select-Object Name, FullName
```

本次结果：

- `OpenAI.Codex_26.608.1337.0_x64__2p2nqsd0c76g0`

### 2. 检查当前 bundled marketplace 源

```powershell
Get-ChildItem -Force $env:USERPROFILE\.codex\.tmp\bundled-marketplaces\openai-bundled\plugins
```

异常表现：

- 只有 `chrome`
- 没有 `browser`
- 没有 `computer-use`

### 3. 检查官方安装包内的真实插件源

```powershell
Get-ChildItem 'C:\Program Files\WindowsApps\OpenAI.Codex_26.608.1337.0_x64__2p2nqsd0c76g0\app\resources\plugins\openai-bundled\plugins'
```

正常表现：

- `browser`
- `chrome`
- `computer-use`

这一步直接确认：

- 官方包里插件是完整的
- 损坏的是用户目录下的 marketplace 镜像/引用链

### 4. 检查 Codex 配置中 marketplace 指向

文件：

- `C:\Users\eason\.codex\config.toml`

原始异常项：

```toml
[marketplaces.openai-bundled]
source_type = "local"
source = "\\\\?\\C:\\Users\\eason\\.codex\\.tmp\\bundled-marketplaces\\openai-bundled"
```

这说明 Codex 还在读那个损坏的本地镜像。

### 5. 检查插件缓存版本

目录：

- `C:\Users\eason\.codex\plugins\cache\openai-bundled\browser`
- `C:\Users\eason\.codex\plugins\cache\openai-bundled\computer-use`

异常表现：

- 只有旧版 `26.602.40724`
- 没有当前版本目录
- `latest` 指向也不对

## 实际修复内容

### 修复 1：把 marketplace 源直接改到官方安装包

修改文件：

- `C:\Users\eason\.codex\config.toml`

把：

```toml
source = "\\\\?\\C:\\Users\\eason\\.codex\\.tmp\\bundled-marketplaces\\openai-bundled"
```

改成：

```toml
source = "\\\\?\\C:\\Program Files\\WindowsApps\\OpenAI.Codex_26.608.1337.0_x64__2p2nqsd0c76g0\\app\\resources\\plugins\\openai-bundled"
```

目的：

- 不再依赖会被刷新坏的临时镜像
- 直接读取官方安装包中的真实插件源

### 修复 2：补当前版本缓存目录

在下面两个目录中补了新版缓存：

- `C:\Users\eason\.codex\plugins\cache\openai-bundled\browser\26.608.12217`
- `C:\Users\eason\.codex\plugins\cache\openai-bundled\computer-use\26.608.12217`

来源：

- 从官方安装包的 `openai-bundled\plugins\browser`
- 从官方安装包的 `openai-bundled\plugins\computer-use`

### 修复 3：重建 `latest` 指针

重建为：

- `browser\latest -> browser\26.608.12217`
- `computer-use\latest -> computer-use\26.608.12217`

目的：

- 避免桌面端继续读旧版 `26.602.*` 缓存

## 为什么前一轮“补目录”不够

前一轮曾把缺失的 `browser` / `computer-use` 补回：

- `C:\Users\eason\.codex\.tmp\bundled-marketplaces\openai-bundled`

但重启后又被覆盖回只剩 `chrome`。

说明：

- 这个目录不是稳定的长期源
- Codex 启动时会刷新它
- 真正稳妥的修法不是反复补这个目录
- 而是直接改 `config.toml`，让 `openai-bundled` 指向官方安装包

## 最终验证

修复后需要：

1. 彻底退出所有 Codex 窗口
2. 确认后台没有残留：
   - `Codex.exe`
   - `codex.exe`
3. 重新启动 Codex
4. 进入设置页检查：
   - `浏览器`
   - `电脑操控`

本次结果：

- 两个插件均恢复可用

## 下次遇到同类问题的推荐流程

### 快速判断

如果出现：

- `浏览器插件不可用`
- `Computer Use 插件不可用`

优先怀疑：

- 官方 app 版本升级了
- 但 `~/.codex` 中 `openai-bundled` marketplace 源或缓存没有跟上

### 推荐排查顺序

1. 看官方 app 版本
2. 看 `config.toml` 中 `marketplaces.openai-bundled.source`
3. 看 `~/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins` 是否缺目录
4. 看官方安装包 `resources/plugins/openai-bundled/plugins` 是否完整
5. 看 `~/.codex/plugins/cache/openai-bundled/{browser,computer-use}` 是否仍停在旧版
6. 看 `latest` 是否仍指向旧版

### 推荐修复顺序

1. 先把 `config.toml` 的 `openai-bundled.source` 改到官方安装包
2. 再补新版缓存目录
3. 再重建 `latest`
4. 彻底退出并重启 Codex

## 关键路径汇总

官方插件源：

- `C:\Program Files\WindowsApps\OpenAI.Codex_26.608.1337.0_x64__2p2nqsd0c76g0\app\resources\plugins\openai-bundled`

Codex 主配置：

- `C:\Users\eason\.codex\config.toml`

损坏的临时 marketplace 镜像：

- `C:\Users\eason\.codex\.tmp\bundled-marketplaces\openai-bundled`

插件缓存：

- `C:\Users\eason\.codex\plugins\cache\openai-bundled`

## 备注

如果下次官方 Codex 版本继续升级，路径里的版本号需要同步替换，例如：

- `OpenAI.Codex_26.608.1337.0_x64__2p2nqsd0c76g0`

不要硬编码沿用旧版本目录。
