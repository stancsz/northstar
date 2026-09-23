# Q4 人机协作协议

这是一个可安装、可运行的 Skill，用后果风险和复杂度或不确定性来分配人和 AI 的协作权力。它明确区分 Intent、Initiative、Execution、Acceptance、Commit，而不是笼统地说“有人在环”。

模式包括 `AUTO`、`GUARD`、`COCREATE`、`CHALLENGE` 和真人否决边界 `HUMAN_ONLY`。高后果任务不能自动提交，分类证据不足时保守升级。

```powershell
py -3 scripts/q4_route.py --input assets/task-intake.json --output contract.json
py -3 scripts/validate_contract.py --input contract.json
py -3 -m unittest discover -s tests -v
py -3 scripts/package_skill.py --output q4-collaboration-protocol.zip
```

它是治理辅助工具，不替代组织控制、专业判断或法律义务。完整规则见 [SKILL.md](SKILL.md) 和 [references/protocol.md](references/protocol.md)。

## 配套 Skill：Codex Subagents

本仓库还包含一个可由 Codex 发现的独立 subagent 工作流 skill：[`.agents/skills/codex-subagents/SKILL.md`](.agents/skills/codex-subagents/SKILL.md)。适合并行委派时可用 `$codex-subagents` 调用；它默认由单个 agent 处理，只在确有并行收益时启用 subagents。
