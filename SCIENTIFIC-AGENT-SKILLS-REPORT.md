# Scientific Agent Skills 追加安装报告

日期：2026-10-13。上游：[K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills)，版本 **2.72.0**，固定提交 **a1043ef544e3a100c28e70a736b6cf32554d0677**。

## 文件与许可

上游有 177 个独立技能。173 个技能完整纳入中央 `.agents/skills/`，包括原始 SKILL.md、scripts、references、assets、examples 等共 2008 个上游文件；这些文件与固定提交逐字节一致。每个目录另附上游完整 MIT 根许可证和 UPSTREAM.json，必要的独立许可证及 Elsevier LPPL 说明亦保留。没有合并成一个只有 SKILL.md 的目录，也没有安装第二套插件。

上游 README 的 Individual Skill Licenses 明确说技能可以有独立许可，不能将根 MIT 当作全部技能的许可。以下 4 个不复制到中央仓库，也没有激活到本机：

| 技能 | 上游声明 | 处理 |
|---|---|---|
| glycoengineering | Unknown | 上游 URL、固定 SHA 与许可记录 |
| phylogenetics | Unknown | 上游 URL、固定 SHA 与许可记录 |
| primekg | Unknown | 上游 URL、固定 SHA 与许可记录；数据/底层软件许可不能替代技能本身的声明 |
| rowan | Proprietary (API key required) | 上游 URL、固定 SHA 与许可记录；API key 不等同于复制/分发许可 |

这些记录在 `upstream-references/scientific-agent-skills.json`。如果以后获得适用许可，可在自己的设备运行：

```bash
python3 scripts/install-scientific-references.py --permission-obtained --skill primekg
```

Windows 换成 `py -3`。此脚本从固定上游直接获取完整目录，拒绝覆盖和中央仓库目标；未获得许可时拒绝下载。GitHub CLI 需 v2.90+，不在 PATH 时用 `--gh` 指定。它不运行科研代码、不提交或推送。未取得云端分发权前不要将这些目录 vendor 到其他项目；普通同步脚本不会安装这 4 个引用。

其他技能的独立声明原样保留，包括 what-if-oracle 的 CC BY-NC-SA 4.0、deepspot-m 的 PolyForm Noncommercial，以及 GPL/BSD/Apache 等。保留作者 metadata、已有 pacsomatic MIT 署名；Elsevier 的原始模板/样式保留版权头、完整 LPPL 文本和获得完整 bundle 的地址。第三方包、模型权重、数据库、商业 API 本身没有打包或下载。完整声明/依赖记录与固定许可证文本来源及 SHA256 在 `upstream-support/scientific-agent-skills/`。

## 实际验证

- 执行官方 README Option 2 的 GitHub CLI 安装器，对已锁定的上游本地检出运行 `gh skill install ... --from-local --all --agent codex --dir <新审查目录>`。审查目录中完整安装了上游 177 个技能；最终同步集遵守许可例外，仅复制上述 173 个。CLI 添加的本机绝对路径元数据不进入中央副本。
- 对最终 173 个技能执行上游静态 contract 的 10 类检查，共 **1730 项通过**：frontmatter、路径链接、514 个 Python 脚本语法、动态执行调用、个人路径、模块命名和 shell 语法等。未导入或执行科研脚本；`bash -n` 仅检查语法。检查也覆盖跨技能文档引用。
- 原有 25 个托管目录哈希检查通过；新增目录/调用名与它们没有冲突。中央集合 **198 个目录、5877 个文件**，`manage.py validate` 通过。上游 2008 个原始文件差异 **0**，没有 symlink。
- 管理脚本使用 Python 3.9+ 标准库，Windows 的安装/同步仍使用原生 PowerShell 5.1/7。K-Dense 最长技能相对路径 90 字符，没有新增 Windows 保留文件名需求。科学工作流的运行平台按各 compatibility 检查，不能把文件安装成功视为每个 Linux/CUDA/WSL 工具已就绪。
- 同步管理的 12 个合成夹具测试通过，包含重复执行、修改保护、冲突、回滚、许可引用内容阻止分发、BIDS 文件名扫描误报修复/真实密钥样式拒绝和项目 vendoring。安装器与上游刷新脚本参数/语法检查通过；没有运行许可门控的引用下载。
- 本机部署、Codex 原生识别及 GitHub 推送结果在后续验证节记录。

没有安装全量 Python/Node 科学包、uv 开发环境、BYOK 服务、模型权重或新的 API 凭据；没有进行科研实验、付费 API 调用、改变 hooks 或创建系统定时任务。静态检查并非所有未来科研执行的安全保证；按具体任务的参数、数据和服务权限执行。

## 另一台设备与 Cloud

已克隆中央仓库的设备，在仓库目录运行 macOS `bash ./sync-macos.sh` 或 Windows `.\sync-windows.ps1`。首次安装仍用 README 中的 `install-macos.sh`/`install-windows.ps1`；已有未提交修改会阻止覆盖。

Cloud 检出中央仓库最新 main 后，可识别已提交的 198 个仓库级技能。需授予 Codex Cloud 的 GitHub 连接读取私有仓库的权限，并更新/选择相应环境；本机 ~/.agents 不会自动复制过去。其他项目继续使用 `manage.py vendor-project --project <项目路径>`，审阅并提交。上游刷新新增 `--scientific-commit` 参数；锁定 SHA 与许可清单随审查结果一起更新。

在新一轮 Codex 会话输入 `$scientific-writing`、`$literature-review`、`$scanpy`、`$biopython` 等可调用已安装技能。另一台 Windows 和 Cloud VM 本次未实机执行；其安装/同步与访问授权仍需在对应环境完成。
