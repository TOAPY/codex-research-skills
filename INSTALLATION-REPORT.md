# 科研 Skills 安装报告

本报告记录首次三套技能安装的历史结果。随后新增 K-Dense 的 173 个技能，另 4 个采用上游引用，当前中央仓库共 198 个目录；追加安装与验证结果见 [SCIENTIFIC-AGENT-SKILLS-REPORT.md](SCIENTIFIC-AGENT-SKILLS-REPORT.md)。

日期：2026-10-13（Asia/Shanghai）。范围仅限安装、配置、静态检查和同步验证；没有执行科研实验、启动 Autoresearch 控制器或发起模型研究调用。

## 已完成

| 项目 | 实际结果 |
|---|---|
| Git | Apple Git 2.39.5 可用；Codex 自带 Git 2.53.0 也可用。 |
| GitHub CLI | 从 cli/cli 官方 v2.102.0 下载 macOS ARM64 二进制，核验官方 SHA256，作为独立工具保存；没有安装 Homebrew 或修改全局 PATH。 |
| GitHub 登录 | 用户完成 GitHub 官方设备授权，TOAPY 账户认证成功，凭据保存在 keyring；未提交 Token。 |
| 私有仓库 | 已创建并推送 [TOAPY/codex-research-skills](https://github.com/TOAPY/codex-research-skills)，分支 main。 |
| 用户级安装 | 25 个完整技能目录、3474 个文件安装到 `~/.agents/skills/`，复制后逐文件 SHA256 校验通过。 |
| 原有技能 | 安装前原有 12 个可用技能，安装后全部保留；未覆盖或删除。 |
| Academic | Codex 原生 academic-research-suite，3.23.0，保留 ars/、codex/、scripts、references、模板、资产、许可证和嵌套上游锁；没有单独注册 Claude 工作流。 |
| Nature | 23 个目录，含 22 个工作流及 nature-shared；保留 scripts/references/static/assets/manifest.yaml 等必要文件；限制分发的第三方图例采用引用方案。 |
| Autoresearch | 完整 Skill、scripts、references、agents、docs、tests、LICENSE；保持显式调用策略，未启动实验。 |
| 跨平台脚本 | install-macos.sh、install-windows.ps1、sync-macos.sh、sync-windows.ps1、README.md 均已生成并提交。管理核心 Python 3.9+ 标准库；PowerShell 5.1/7 原生运行，不依赖 WSL 或 symlink。 |
| 来源记录 | 根 UPSTREAMS.json、每个技能 UPSTREAM.json、Academic 内含 manifest.json 和 NOTICE 记录来源和固定 SHA。 |
| Cloud 准备 | 中央仓库有已提交的 .agents/skills/；提供其他项目可重复使用的 vendor-project 命令及中央提交来源记录。 |

## 实际执行的验证

1. 使用 Codex 官方 skill-installer 的 Git 安装方式审查 Academic 固定提交；Autoresearch 用官方 installer 下载完整根 Skill；Nature 使用官方 update-codex-skills.sh 指定临时目标，全部 MATCH。最终已审查包统一由中央仓库管理，避免多套更新器交叉覆盖。
2. `manage.py validate`：25 个目录均有有效 SKILL.md 元数据，调用名唯一，必要脚本/共享文件存在。`nature-proposal-writer` 的实际调用名为 `$researchwrite`，这是上游兼容名称。
3. Nature 官方元数据检查函数检查了 23 个技能、agents/openai.yaml 和 340 个 manifest 引用路径，错误为 0；脚本通过 Python 3.12 语法解析。SKILL.md 的相对 Markdown 链接可解析，含角括号包裹的带空格文件名；没有 symlink。
4. Academic 官方静态质量 gate 8/8 通过。检查的是保留完整 plugin 结构的上游审查 checkout；本机采用 direct Skill 安装，没有安装第二份 plugin，也未启用 full-runtime/hooks。静态 topology 数据校验不是运行 topology 实验。
5. Autoresearch 的官方 test_structure.py 4/4 通过：元数据、脚本语法和相对 Markdown 链接完整。
6. 同步管理测试 10/10 通过：首次安装、重复执行、远端 fast-forward、本地仓库未提交修改、安装副本修改、未托管目录、相同调用名、capture 后推送、失败回滚、分支分叉、项目 vendoring 的相关测试场景均由小型合成技能夹具验证，没有科研运行。
7. 本机实际第一次安装更新 25/25；第二次运行更新 0/25。实际安装目录中的 3474 个文件逐字节和中央源码一致，且符合本机清单哈希。
8. Codex CLI 0.159.2 的原生 app-server `skills/list` 实测：普通项目目录发现 25 个科研用户级技能，全部 enabled=true，加载错误 0；加上原有技能总数为 37。中央仓库内发现 25 个 repo 技能；本机同时存在同名 user 副本，官方行为是同时显示，故此目录总数为 62。Cloud 使用仓库副本，不能据本机的双作用域显示推断云端有重复安装。
9. Git 字节校验与 .gitattributes 保留上游原始文件字节，防止跨平台换行破坏哈希锁。仓库忽略规则经检查未漏掉工具包或 credentials.mjs 这类处理凭据的源码模块；它们不含真实凭据。
10. 所有 Git 跟踪文件经过常见 Token/私钥与敏感文件名扫描。SSH/HTTPS 密钥、认证文件、安装清单、本机工具二进制、科研私人数据没有加入中央仓库。
11. 实际执行 `sync-macos.sh` 在线获取私有仓库：Git 返回 Already up to date，复制更新 0/25。再从 GitHub 做全新检出，对比 25 个技能目录、3474 个文件，字节差异为 0。GitHub REST API 确认 private=true、默认分支 main；最终提交已推送且远端 ref 与本机一致。此验证证明远端含完整源码，并不代替 Windows 或 Cloud VM 实机验证。

机器可读证据在 [verification/](verification/)；完整的原生响应仅留在工作临时目录，提交的发现报告已去除本机绝对路径。

## 许可证与路径适配

- Academic：CC BY-NC 4.0，Cheng-I Wu；保留完整许可及子来源署名。当前安装用途按非商业科研管理处理；商业使用需另获许可。
- Nature：Apache-2.0，根许可证在每个技能的 LICENSE.nature-skills；原有 Downloader/Image2PPT/patent-disclosure MIT 许可保留。Nature SKILL.md 加了有日期的 Codex 路径说明，Figure 审查例子及 Downloader 自身 Windows 安装路径已适配。
- Autoresearch：MIT，保留完整 LICENSE。其脚本可能创建提交、回滚或启动进程，因此本次只做结构检查，没有运行 start/init/finish 等实验入口。
- figures4papers：Nature 的 THIRD_PARTY_NOTICES.md 明确注明当时没有公开复制/分发许可。中央仓库和已安装技能不含这部分第三方脚本或图像；保留上游地址/版权说明，提供取得权限后下载到技能仓库之外的手动脚本。22 个 Nature 工作流及共享包都已安装，此例外影响第三方示例预览的直接复用，不影响原创绘图模板与共享资源。
- 没有修改 Codex 的 config.toml、模型、hooks.json、MCP 配置、shell 全局启动文件、系统计划任务或注册表。Git 作者身份和 HTTPS helper 仅作用于此中央 checkout。

## 仍需在另一台设备/云端操作

| 环境 | 需要你完成 |
|---|---|
| Windows | 安装缺少的 Git/Python/GitHub CLI，登录自己的 GitHub，克隆私有仓库，运行 install-windows.ps1。此机器没有 Windows 或 PowerShell 运行环境；已静态审查 PowerShell 语法/参数及公共管理核心，但不能声称已在 Windows 实机执行。首次运行后用 `/skills` 或原生枚举验证。 |
| 另一台 macOS | 同样认证、clone、运行 install-macos.sh；不要把带本机 credential helper 的整个 .git 目录直接拷过去。 |
| Codex Cloud | 为 Codex GitHub 连接授予私有仓库访问权；选择包含中央仓库或已 vendoring 的项目的 Cloud 环境与分支，发布/刷新环境，并在新任务验证技能。CLI 的 GitHub 登录不代替 Cloud 的连接授权。本次未创建云端任务、未实际运行 Cloud VM。 |
| 按需科研依赖 | Autoresearch 运行需 Python 3.11+；本机系统 Python 为 3.9.6，Codex 工作运行时为 3.12.14。各 Nature requirements、MCP/provider 凭据和浏览器能力需针对具体任务配置，未全量安装。Cloud 当前官方限制含 computer/browser use，相关功能要选择可用替代方式。 |
| 自动同步 | 已提供用户级 LaunchAgent/Windows 登录任务的方案；未经你的同意，没有创建计划任务。 |

OpenAI 官方资料：[本机/仓库技能目录](https://learn.chatgpt.com/docs/build-skills)、[Cloud 技能与本机目录不同步、环境配置](https://learn.chatgpt.com/docs/environments/cloud-environments)。

## 日常命令

中央 checkout 目录内，macOS 一键拉取/部署：`bash ./sync-macos.sh`；Windows：`.\sync-windows.ps1`。修改后先检查 diff、显式提交，再用 macOS `bash ./sync-macos.sh --push` 或 Windows `.\sync-windows.ps1 -Push`。安装副本已改过时先 `python3 scripts/manage.py capture --skill <目录名>`，Windows 用 `py -3`。完整命令及 Cloud 项目复用说明在 [README.md](README.md)。

本机 GitHub CLI 是 outputs/github-cli/gh；不在全局 PATH。此中央 checkout 的 HTTPS helper 指向该工具，用 keyring 认证。系统 Git 初始 HTTPS 推送出现临时 TLS 中断；在保持证书验证的情况下改用此 checkout 的 HTTP/2 后推送成功，没有修改 DNS、代理、系统网络或关闭 TLS 验证。后续若网络中断，同步会报错并保留本地技能。
