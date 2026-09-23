# Northstar

**生产优先的 AI 工程。**把含糊的想法变成经得起检验的产品方向，再让每一步研究和实现都指向真实的用户与商业价值。

Northstar 要求 AI 在写代码前挑战产品论点：谁需要它、它解决什么痛点、用户为什么会选择或付费，以及商业模型和交付路径是否站得住脚。答案薄弱时，下一步应是有针对性的验证，而不是做完就丢的 research prototype。

方向可信后，AI 应在约定边界内主动研究实现问题并持续推进。到达不可逆点之前则必须停下：生产发布、破坏性变更、支出、权限调整和其他外部承诺，都要按协作契约取得明确批准。

本 Skill 把目标驱动工程（以 `GOAL.md` 作为持久、可验证的工作单元）与按后果分配权限的路由结合起来（`AUTO`、`GUARD`、`COCREATE`、`CHALLENGE`、`HUMAN_ONLY`）。见 [SKILL.md](SKILL.md) 和 [references/goal-driven-engineering.md](references/goal-driven-engineering.md)。

## 快速开始

```powershell
py -3 scripts/northstar_route.py --input assets/task-intake.json --output contract.json
py -3 scripts/validate_contract.py --input contract.json
py -3 -m unittest discover -s tests -v
py -3 scripts/package_skill.py --output northstar.zip
```

`northstar_route.py` 根据任务输入生成协作契约；`validate_contract.py` 检查审批关口、验收证据、回滚信息、超时处理和范围边界。

Northstar 是决策与执行辅助工具，不能代替客户证据、专业判断或组织控制。

## 配套 Skill：Codex Subagents

仓库还包含独立的 Codex 子代理工作流：[`.agents/skills/codex-subagents/SKILL.md`](.agents/skills/codex-subagents/SKILL.md)。确有并行收益时用 `$codex-subagents`；默认由一个 agent 执行。
