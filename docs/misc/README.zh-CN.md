# Northstar

**面向项目交付和企业运营的 AI 工作体系，以 Markdown Skill 提供；工程任务先交付可用 MVP，再逐步完善。**

Northstar 帮助 AI 在开始时厘清客户、痛点、商业价值和生产方向，主动研究技术问题，参考优秀同类产品，并通过批评、修复和验证，把工作做到真正可用。

[运作体系](../../skills/northstar/references/operating-system.md)把目标、资源、责任、执行、验收、运营结果和复盘接成闭环。必要的仪式必须保留：目标对齐、checkpoint 复盘、分歧辩论、上级主持的小型决策会、专家会诊、运营检视和交接。每次产出依据、决定、负责人和下一步；精简重复汇报与无效审批。单 agent 自己复盘，多 agent 由相关成员提供真实意见，不伪造会议或一致同意。

执行层默认使用能胜任的较低成本模型，较强推理能力用于关键指挥、整合与难题。模型升级不重置失败次数，指挥官接管必须记为救援；效率评价包括指挥、执行、复盘、专家与返工的总成本。没有使用量或对照数据，就不宣称省钱。详见[能力与成本分配](../../skills/codex-subagents/SKILL.md#allocate-capability-and-cost)。

## 避免重复绕圈

目标是用最少时间和总 tokens 办成最多有价值的事：lean first、functioning first，leanest、cleanest、最大有效复用。职责清楚、数据流直观、共享规则只实现一次；不堆补丁、不复制逻辑、不为假想需求造框架。认真处理难以逆转的选择，用最少的必要边界保留扩展空间。代码通过功能检查后仍需检查重复和耦合；一句话说清的事不写一段，也不为追求一行代码牺牲可读性。详见 [精简实现与优秀设计](../../skills/northstar/SKILL.md#excellent-design-with-minimal-machinery)。

长期目标和本次交付分别记录。本次只完成一个可用的完整流程，明确必过条件、运行环境和后续增量。已有成果与适用的验证证据应当复用；只有相关改动、新需求、矛盾证据或检查缺口才重开。对同一阻塞尝试两次仍无新信息或进展，就换诊断或实现路径。达到本次条件即交付，额外完善进入后续工作。具体规则见 [MVP 与增量交付](../../skills/northstar/SKILL.md#deliver-a-usable-mvp-then-improve-in-increments)。

给负责写 Codex 提示词的 GPT，可以直接使用：

> 按 Northstar 工作：最少时间和总 tokens，最大有效成果。Lean first、functioning first；代码精简清晰、最大有效复用、无屎山；表达能一句说清就一句。先复用已有成果和证据，锁定本次完整流程与验收条件，直接实现验证。认真处理难以逆转的决定，保留扩展边界，不预建框架、不削减明确需求和必要质量。重做须有理由；同一阻塞两次无新进展就换路径。达标即交付结果、证据、限制和下一增量；只继续已授权的工作。

长会话使用 [恢复检查点](../../skills/northstar/SKILL.md#recover-from-a-stall)：在现有目标或任务报告里保留未达标条件、已验证状态、失败尝试、排除路径、剩余调查窗口和下一检查。换 agent 或压缩上下文不能重置尝试次数；恢复仍无进展就标明具体阻塞和解除条件，继续独立工作。

MVP 验收不等于已上线、商业模式已验证或达到竞品完整度。这些目标继续保留。规则是 Markdown 指导，不是防止所有循环的运行时保证。

## Skills

**原生面向 Codex，也可供 Claude Code、OpenCode 及其他 agent 使用。** 名称里的 `Codex` 表示来源，不限制使用者。安装 agent 不得仅因名字包含 Codex 就跳过技能；应完整保留四个技能及其名称，按宿主环境适配加载方式和工具，并把这条说明带给使用它们的 agent。具体见[跨 agent 安装说明](install.md#installing-from-another-agent)；Advisor 的服务依赖仍需具备。

- [Northstar](../../skills/northstar/SKILL.md)：产品方向、竞品参考、自主执行、质量审查、验证和仓库维护。
- [Codex QA](../../skills/codex-qa/SKILL.md)：先明确质量标准，再检查真实功能、渲染视觉、对抗场景和代码结构；实质缺陷修复复验，缺证据不能算通过，偏好建议不阻塞交付。
- [Codex Subagents](../../skills/codex-subagents/SKILL.md)：任务委派、共享文档和清晰交接。

统一安装 `skills/` 下四个并列目录：`northstar`、`codex-qa`、`codex-subagents`、`codex-advisor`。`$northstar` 是总入口，其他三个仍可直接调用。Northstar QA 更名为 Codex QA；[Codex Advisor](../../skills/codex-advisor/SKILL.md) 从 Subroute 迁入，原名 Luna Advisor。四个技能按需协作，不代表每次都启动四个 agent。咨询后的实现和开发自检仍由执行者负责，独立验收由未参与该成果创作的 reviewer 负责。服务和可选 Pi reader 需要单独具备；安装不会启动服务或自动调用模型。升级时保留本地定制，再停用旧名 `northstar-qa` 和 `luna-advisor-escalation`，详见[安装说明](install.md)。

管理者使用 [orchestrator 模板](../../skills/codex-subagents/templates/orchestrator.md) 或 [supervisor 模板](../../skills/codex-subagents/templates/supervisor.md)，只加载当前角色。由派活的 agent 填入已有授权及来源、目标、依赖接口、写入范围、集成人和恢复记录，不让用户重复交代。管理者负责解决问题并验收真实工作流；遇到停滞须诊断、调整或接手，不能只催进度和转述报告。已授权工作直接继续；只有真正缺失的用户决定才提问，工具强制权限限制需另行说明。

流程按实际需要增减：任务只需讲清结果、验收、自主范围、协调边界和交付。内部实现自行决定；共享接口由相关负责人协调；不能擅自放宽授权、明确预算或验收要求。小改动复用现有目标，同一 agent 不模拟多层审批；有效证据跨角色复用。调查窗口是重新判断的节点，不能机械变成请示，也不能借此重置无进展的重试。仓库明确要求的记录仍需保留。

[安装说明](install.md) · [English](../../README.md)

## 使用记录与技能反馈

**Self-learning loop 是核心执行责任。** 行动前先查适用经验；每到有实质结果的 checkpoint，回看目标和验收，检查 what worked / what didn't work，决定保留、调整或停止什么，再把结论带进下一步。失败、恢复窗口结束、重要用户纠正以及交接前也要复盘；同一结果合并一次，不为每次工具调用开会。

一个 agent 自己复盘；多 agent 通过已有报告做短而异步的会合，由负责人核对证据、处理矛盾并记录一次决定，不要求全员到齐。记录成功方法的适用条件、失败路径和允许重试的变化条件；下次优先复用有效方法，不原样重试已失败路径。旧经验失效时标记替代关系并保留依据，不能把偶然成功变成永久真理，也不能借复盘重置失败次数。

经验保存在项目已有记录里，换会话先核实当前条件再使用。没有新经验就简短说明；没有持久存储就明确后续不保证能取回。这是可检查的防漂移实践，不是自动训练模型或保证永不漂移。详见 [核心学习循环](../../skills/northstar/SKILL.md#learn-from-every-use)。

遇到有价值的新经验，向用户简短说明记录位置，以及它能怎样帮助改进技能，并建议反馈到 [Northstar Issues](https://github.com/stancsz/northstar/issues)。技能问题统一提交到这里，应用自身的问题仍留在应用项目。提交前整理脱敏内容、检查重复；已有明确提交授权就直接执行，没有授权则展示草稿后询问。无法提交时保留草稿并明确未提交，成功后记录 Issue 链接。详见 [记录与反馈实践](../../skills/northstar/references/skill-feedback.md)。

## 项目文档

以下是本仓库的目录约定，不是其他项目的安装前提。实际使用时优先复用项目已有 issue、任务文件、计划和评审记录；信息齐全即可，不另建平行目录。默认直接实现与验证，跨会话或交接时保留恢复状态，有独立工作流才委派，按交付表面和风险使用 QA。明确的任务和仓库要求仍须遵守。

- [docs/northstar/](../northstar/README.md)：orchestrator 负责维护和使用，记录项目方向、用户标准、决策和待验证假设。
- [docs/goal/](../goal/README.md)：supervisor 负责各自的 GOAL.md 和目标索引条目，分配任务、整合成果并记录验收。
- [docs/reports/](../reports/README.md)：worker 交付实际成果后写任务报告，记录产物、检查结果、未完成事项及下一步；受阻或部分完成也要交接。
- [docs/evals/](../evals/README.md)：实际观察、批评、修复和验证结果。
- [AGENTS.md](../../AGENTS.md)：阅读顺序和协作规范。

supervisor 阅读报告并检查实际成果，再决定接受任务或要求修复；orchestrator 对照 North Star 决定目标是否完成。报告本身不代表通过验收。

`docs/` 下只放子目录，不直接存放文件。安装说明、翻译和其他不属于方向、目标、任务报告或评估的资料放在 `docs/misc/`。

所有 agent 与 subagent 都要保持仓库整洁，临时文件放在被忽略的 `tmp/`，提交信息应具体、有意义。整个项目共享 **100 GB** 产物上限，包含被忽略的缓存、下载、临时文件及项目相关副本；在大规模操作前估计峰值空间并检查用量，接近 80 GB 时主动处理膨胀。

这是工程实践 Skill。不要用新脚本、机器契约或填表流程代替实际的判断、交付和验证。

## 职能与独立验收

指挥官使用并下放用户已给的持续授权：先把目标、价值、验收、可用资源、行动建议和失败时的判断依据讲清楚；下级解决不了的授权内问题，由指挥官按价值、总成本、时效、代价和可回退性决定并执行。Notion 配置好且项目运营已授权后，直接读写对应项目记录，不逐页、逐项重复询问权限。真实连接故障由指挥官先排查和寻找已授权替代路径，只有不可替代的人类凭据或范围外决定才提出一个具体问题。详见[指挥授权规则](../../skills/northstar/SKILL.md#ask-only-for-decisions-the-user-owns)。

按[职能 profiles](../../skills/codex-subagents/references/role-profiles.md)覆盖产品与结果、架构与接口、构建与集成、独立 QA、体验与品味、运营以及领域研究。按需启用，兼容职能可以合并，不照搬人类部门数量。构建者可以做开发自检和个人复盘，但不能兼任自己成果的独立测试、QA 或品味评审。管理者接手修改后也受同样约束；改名或清空上下文不能消除创作关系。没有独立 reviewer 时保留未验收状态，不能自签通过。[Agent 交接规则](../../skills/codex-subagents/references/agent-handoffs.md)保留成果版本、授权和恢复历史；本包不实现 A2A 传输协议。
