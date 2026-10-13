# Codex Research Skills：macOS、Windows 与 Cloud

中央私有仓库：[TOAPY/codex-research-skills](https://github.com/TOAPY/codex-research-skills)。标准目录为 `.agents/skills/`；本机安装目录为 `~/.agents/skills/`（Windows：`%USERPROFILE%\.agents\skills\`）。包含 198 个完整技能目录：1 个 `academic-research-suite`，23 个 Nature 目录（22 个工作流 + `nature-shared` 支持包），1 个 `codex-autoresearch`，以及 K-Dense Scientific Agent Skills 2.72.0 的173 个技能（另外 4 个许可不明/专有技能采用上游引用）。

科研运行依赖按任务安装；安装/同步不会启动实验、安装浏览器、部署 MCP、改 Codex 模型或启用 hooks。Autoresearch 保留上游 `allow_implicit_invocation: false`。

## 首次安装

两台电脑分别需要 Git 和 Python 3.9+；推荐 Python 3.11+，Autoresearch 运行需要 3.11+。本仓库管理脚本只使用 Python 标准库。GitHub CLI 用于 GitHub 登录及仓库管理，技能文件同步本身使用 Git。

macOS（已有 Git/Python 时，不需要安装 Homebrew）：

```bash
# 安装 gh 的方式见 https://cli.github.com/ ，然后：
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
mkdir -p "$HOME/Documents/Codex"
git clone https://github.com/TOAPY/codex-research-skills.git "$HOME/Documents/Codex/codex-research-skills"
bash "$HOME/Documents/Codex/codex-research-skills/install-macos.sh"
```

Windows 原生 PowerShell 5.1 或 7（无需 WSL/Git Bash/管理员权限或符号链接）：

```powershell
# 仅在缺少工具时运行；安装后重新打开 PowerShell：
winget install --id Git.Git -e
winget install --id GitHub.cli -e
winget install --id Python.Python.3.12 -e

gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
$SkillsRepo = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Codex\codex-research-skills'
git clone -c core.longpaths=true https://github.com/TOAPY/codex-research-skills.git $SkillsRepo
& (Join-Path $SkillsRepo 'install-windows.ps1')
```

若当前执行策略阻止自己审阅过的脚本，只对这一次进程运行 `powershell -NoProfile -ExecutionPolicy Bypass -File <install-windows.ps1完整路径>`；不修改永久执行策略。不要把示例中的尖括号原样输入。Windows clone 设置仅作用于该仓库的 `core.longpaths=true`；最长仓库相对路径为 175 字符，遇长用户名/深层自选目录导致路径错误时改用较短的 clone 位置，不自动修改系统注册表。

若只携带一份已经审阅的安装脚本，脚本也支持自动下载中央仓库：

```bash
bash ./install-macos.sh --bootstrap https://github.com/TOAPY/codex-research-skills.git
```

```powershell
.\install-windows.ps1 -RepoUrl 'https://github.com/TOAPY/codex-research-skills.git'
```

再次执行 install 等同于 sync：获取中央 GitHub 仓库当前分支的新提交，再部署本机副本。不会自动追踪四个上游的 main；上游更新先审查并锁定 SHA，再提交中央仓库，其他设备同步中央仓库的已审查版本。

## 一键同步

在克隆目录内：

```bash
bash ./sync-macos.sh
```

```powershell
.\sync-windows.ps1
```

此机器的初始中央 checkout 位于安装报告中的 outputs 目录；在该目录执行同样命令即可，不必另克隆一份。`RESEARCH_SKILLS_PYTHON` 可设为所需 Python 的完整路径；不会写入 shell 配置。`--offline`（PowerShell：`-Offline`）只安装已审查的本地 checkout。

同步保护：先检查中央 checkout 的所有未提交/未跟踪文件，及上次安装清单中的逐文件 SHA256；再 fetch 和 fast-forward。任何未提交修改、已安装副本修改、重名目录/调用名、分支分叉、符号链接或目标归属冲突均停止。不使用 stash/reset，不覆盖已有未托管技能，不删除退休技能或无关文件。复制先暂存，再逐目录激活；失败回滚。管理状态只在本机 `.agents/research-skills-state.json`，不提交。崩溃遗留的 `.research-skills-sync.lock` 需确认无同步进程后手动处理。

所有脚本针对同一套标准目录，不会产生重复嵌套。macOS 与 Windows 都复制完整目录；不依赖仅 Windows 管理员才可创建的 symlink。`.gitattributes` 保留上游文件原始字节，避免 Windows 换行转换破坏上游内含的 SHA 锁；只为本仓库自己的管理脚本固定 LF。

## 修改、自定义与推送

优先直接编辑中央 checkout 的 `.agents/skills/<技能目录>/`；完成后检查 diff、只提交期望的文件，再运行 `sync --push`。安装副本若已经修改，先显式收回该一个目录：

```bash
python3 scripts/manage.py capture --skill nature-writing
# 导入本机的新自定义技能也一样：
python3 scripts/manage.py capture --skill my-custom-skill
git diff -- .agents/skills
git add -- .agents/skills/nature-writing
git commit -m "Customize nature-writing"
bash ./sync-macos.sh --push
```

```powershell
py -3 scripts/manage.py capture --skill nature-writing
git diff -- .agents/skills
git add -- .agents/skills/nature-writing
git commit -m "Customize nature-writing"
.\sync-windows.ps1 -Push
```

新技能导入时用自己的目录名替换示例，git add 也只指定对应目录。`capture` 保留本机修改并将它们显式复制回仓库；如果仓库副本也改过，会拒绝自动合并。多个设备同时产生提交时，先人工解决分叉，再同步。

推送前脚本扫描 Git 跟踪的凭据文件名、常见 GitHub/OpenAI 密钥格式和私钥头；不打印匹配值。`.gitignore` 排除凭据、运行缓存和研究数据目录。扫描不能判断任意文件是否包含私人科研内容，因此提交前必须检查自己的 diff；脚本不会自动 `git add -A`、自动提交或上传未提交文件。新增许可证遵守原作者要求，不以私有仓库替代授权。

## 上游与许可证

准确的 URL/commit SHA 在 [UPSTREAMS.json](UPSTREAMS.json)，每个技能也携带 `UPSTREAM.json`。必要子来源和版本记录保留在 Academic 的 `manifest.json` 和 `ars/` 原始文件中。

| 来源 | 许可与处理 |
|---|---|
| Imbad0202/academic-research-skills-codex | CC BY-NC 4.0，3.23.0；保留作者 Cheng-I Wu、完整 LICENSE、ars/NOTICE.md 及内含 experiment-agent 的许可。适用于符合许可的非商业用途；商业用途需另获许可。 |
| Yuan1z0825/nature-skills | 根许可 Apache-2.0；为每个 Nature 技能附上 LICENSE.nature-skills。Downloader、Image2PPT 和 patent-disclosure 的内含 MIT 许可原样保留。新增路径说明和文件修改均带日期标记。 |
| leo-lilinxiao/codex-autoresearch | MIT；保留完整根技能、scripts、references、agents、docs、tests 等和 LICENSE。未启动实验。 |
| K-Dense-AI/scientific-agent-skills | 根许可 MIT，2.72.0，各 SKILL.md 独立许可原样保留；173 个技能完整复制。glycoengineering/phylogenetics/primekg 为 Unknown，rowan 为 Proprietary，只保留上游引用，取得相应许可后可用 scripts/install-scientific-references.py 安装，默认不复制或云端分发。每个已复制目录保留完整 LICENSE.scientific-agent-skills.md；what-if-oracle 是 CC BY-NC-SA 4.0、deepspot-m 是 PolyForm Noncommercial、venue-templates 的 Elsevier 资产是 LPPL。原有文档/PDF 插件不受影响；上游此版本不包含 Anthropic 的四个文档技能。 |
| ChenLiu-1996/figures4papers | 上游没有明确 LICENSE，Nature 的 THIRD_PARTY_NOTICES.md 也明确限制复制/分发；不打包脚本/预览，只保留许可说明和上游链接。 |

只有在取得 figures4papers 复制许可后，才可以运行 `scripts/fetch-restricted-reference.py --permission-obtained --commit <40位SHA> --destination <技能仓库之外的新目录>`。脚本不会执行其代码，也禁止下载到中央仓库或 `.agents/`。这部分不会自动安装到 Windows 或 Cloud。不要把私人获权副本再推送到中央仓库。

官方安装依据：Academic README 的 Direct Skill Install，Nature README 5.3 的完整安装脚本（指定 `--dest`），Autoresearch README/INSTALL 的 skill-installer 和 Manual User Install。初始安装实际执行了官方 installer 和 Nature 脚本到临时审查目录，再由中央仓库管理已审查副本，防止与其他安装器相互覆盖。K-Dense 使用其 README Option 2 的 GitHub CLI，先以 `gh skill install <已锁定的本地上游检出> --from-local --all --agent codex --dir <全新审查目录>` 审查完整安装；中央副本保留原始 SKILL.md 字节及统一 UPSTREAM.json，避免提交 CLI 写入的本机路径。

更新上游时，先从相应 GitHub 上获取和审查具体提交、LICENSE 及第三方变化，然后用以下命令生成全新暂存目录：

```bash
python3 scripts/fetch-upstreams.py --nature-commit <40位SHA> --output work/upstream-review
```

新增 K-Dense 更新参数为 `--scientific-commit <40位SHA>`。Windows 同命令换成 `py -3`。不传覆盖参数时重新下载当前锁定版本；脚本不会运行上游脚本、覆盖在用技能或推送。复核 `work/upstream-review/UPSTREAMS.json` 和目录 diff，手动合并到 `.agents/skills/`（保留自己的修改），更新根锁文件，再提交及同步。新的许可证例外必须重新检查；初始审查不能替代新版审查。

## 可选科研运行依赖

完整技能文件与共享文件均已包含，但以下功能需要按任务配置，未全量 pip/npm 安装：

| 功能 | 运行依赖/限制 |
|---|---|
| Autoresearch 控制器 | Python 3.11+、Git、可用 Codex CLI 和 Git 作者身份；只有明确请求并确认实验范围后才运行。 |
| Nature Figure 碰撞审查 | nature-figure/requirements.txt 中的 PyMuPDF；Python/R 绘图选择对应工具。 |
| Image2PPT / Paper Trans / 专利文档 | 对应技能 requirements.txt，Image2PPT 要求 Python 3.10+；部分 PDF、PPT 和字体工具按任务选择。 |
| Academic Search MCP | 保留 mcp-server 全套文件；Python mcp/requests/toml/lxml 等，需 PUBMED_EMAIL；Scopus/Elsevier 等凭据可选，单独在本机或云端 secrets 管理。未把 Claude 安装脚本用于 Codex。 |
| 论文下载的浏览器/机构访问 | 可选 web-access-main 等不在本仓库；用 Codex 可用浏览器工具，机构凭据和服务权限另配。 |
| CNIPA 检索/OCR/模型接口 | 额外 requirements、Playwright Chromium 或模型凭据等只在需要时安装；不得将 Token、API key 或私人研究资料写进仓库。 |
| K-Dense Scientific Agent Skills | 各技能的 compatibility、references 和安装示例决定依赖；使用分开的环境，避免不兼容科学包版本。上游开发工具要求 Python 3.13+、uv，不是本仓库同步的先决条件；原生 Windows 可安装/同步/识别全部文件，但部分科研工具另需 WSL、Linux、CUDA 或特定系统软件。未安装 BYOK、MCP、API 凭据或全量科学包。 |
| Academic 高级运行时 | ars/requirements-dev.txt 为开发检查用途，PDF 内容分类器为单独的可选依赖；默认不启用 full-runtime hooks、跨模型上传或实验。 |

本机系统 `python3` 是 3.9.6；Codex 内置工作运行时是 Python 3.12.14（其路径见报告），可用于需要 3.11+ 的控制脚本。`python3 --version` 不代表所有科研依赖已满足。技能文件可被识别，与每一个科研功能可执行是两项不同的验证。

## Codex Cloud

OpenAI 官方说明：[技能目录与识别规则](https://learn.chatgpt.com/docs/build-skills)、[Cloud 环境及当前限制](https://learn.chatgpt.com/docs/environments/cloud-environments)。Cloud 可使用仓库内 Skills；本机用户目录不会自动同步到 Cloud。

1. 为 Codex/ChatGPT 的 GitHub 连接授予此私有仓库的读取权限。`gh auth login` 是本机 Git 认证，不会自动授权 Codex Cloud 的 GitHub 连接。
2. 桌面端选择云端，创建/选择包含 `TOAPY/codex-research-skills` 的云端环境，使用含 `.agents/skills/` 的已提交分支（初始为 main）。按当前 UI 发布环境并在新云端任务中验证；已有任务保存自己的文件状态，更新后可能需要重新发布和开启新任务。
3. 在新任务要求“只列出可用技能和路径，不运行实验”，核对 `$academic-research-suite`、`$nature-writing`/其他 Nature 工作流、`$codex-autoresearch`、`$scientific-writing`、`$scanpy` 等 K-Dense 技能。原始 Nature 目录 nature-proposal-writer 的调用名为 `$researchwrite`；`nature-shared` 是支持包，不单独作为科研工作流调用。
4. 已提交的副本无需联网下载技能。外部搜索、模型/API、MCP 或浏览器功能另受云端权限和网络限制；官方当前文档列出云端不支持 computer/browser use，因此这类 Nature 功能不能承诺与本机完全一致。

其他 GitHub 项目推荐将中央仓库的已审查副本复制并提交为该项目自己的仓库级技能：

```bash
# 在中央 Skills checkout 执行；目标项目应已有 Git 提交且工作区干净。
python3 scripts/manage.py vendor-project --project /absolute/path/to/another-project
# 在目标项目：将 .agents/research-skills-state.json 加入 .gitignore，
# 检查并提交 .agents/skills/ 与 .agents/research-skills-source.json，再推送。
```

Windows 使用 `py -3 scripts/manage.py vendor-project --project 'C:\src\another-project'`。脚本保留项目现有技能并拒绝冲突，记录中央仓库 SHA。目标项目的云端 checkout 因而可直接识别，不依赖本机目录、submodule 自动初始化或对中央私有仓库的第二次认证。之后先同步中央仓库，再对目标干净 checkout 重复 vendor-project、检查 diff 并提交。若本机同时有用户级副本及项目副本，官方说明两者可同时显示；请按路径选项目版本，不把重复显示当作安装损坏。

## 验证与登录后自动同步

```bash
python3 scripts/manage.py validate
python3 scripts/manage.py scan-secrets
```

Windows 用 `py -3`。macOS 实际验证、Codex 原生 skills/list 返回与跨平台测试证据见 INSTALLATION-REPORT.md；第四套技能的追加验证见 SCIENTIFIC-AGENT-SKILLS-REPORT.md。在新 Codex 会话中打开 `/skills` 或输入 `$`；若列表未刷新，重启 Codex。安装后下一轮可使用新技能。

可选登录后同步方案：macOS 用户级 LaunchAgent（RunAtLoad，延迟等待网络）；Windows 用户级任务计划程序（登录触发、延迟 60 秒、无管理员权限、单实例）。只运行拉取/部署命令，不带 --push；遇本地修改或无网络则失败并记录日志，不自动冲突解决。当前没有创建任何计划任务或修改 hooks。若以后要启用，先给出具体任务文件、命令和日志路径，并取得你的同意。
