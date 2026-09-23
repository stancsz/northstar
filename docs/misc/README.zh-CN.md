# Northstar

**生产优先的 AI 工程实践，以 Markdown Skill 提供。**

Northstar 帮助 AI 在开始时厘清客户、痛点、商业价值和生产方向，主动研究技术问题，参考优秀同类产品，并通过批评、修复和验证，把工作做到真正可用。

## Skills

- [Northstar](../../skills/northstar/SKILL.md)：产品方向、竞品参考、自主执行、质量审查、验证和仓库维护。
- [Codex Subagents](../../skills/codex-subagents/SKILL.md)：任务委派、共享文档和清晰交接。

[安装说明](install.md) · [English](../../README.md)

## 项目文档

- [docs/northstar/](../northstar/README.md)：项目方向、用户标准、决策和待验证假设。
- [docs/goal/](../goal/README.md)：目标、进展和剩余工作。
- [docs/evals/](../evals/README.md)：实际观察、批评、修复和验证结果。
- [AGENTS.md](../../AGENTS.md)：阅读顺序和协作规范。

`docs/` 下只放子目录，不直接存放文件。安装说明、翻译和其他不属于方向、目标或评估的资料放在 `docs/misc/`。

所有 agent 与 subagent 都要保持仓库整洁，临时文件放在被忽略的 `tmp/`，提交信息应具体、有意义。整个项目共享 **100 GB** 产物上限，包含被忽略的缓存、下载、临时文件及项目相关副本；在大规模操作前估计峰值空间并检查用量，接近 80 GB 时主动处理膨胀。

这是工程实践 Skill。不要用新脚本、机器契约或填表流程代替实际的判断、交付和验证。
