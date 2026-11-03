# 启动与日常操作

日常闭环：**你描述 Goal → MCP set_goal → Agent 在 Goal 内自主完成 → MCP get_goal_report → 你决定下一条 Goal。** 不需要你手写 job 文件、逐步派发角色、盯着每次错误重启。

当前安装位置是 `D:\github\northstar`。本机宿主服务、Docker MCP 网关和 Codex 的 `northstar_a2a` 连接条目已经设置。两个真实 Goal 已在无人纠偏下完成，其中一次包含控制进程故障和自动恢复。详细证据见仓库的 `docs/evals/a2a-stack/`。

## 首次安装（尚无运行中的宿主）

以下命令仅用于首次安装，要求尚无运行中的宿主进程；本机已经安装完成，无需重复执行。在 PowerShell 中从仓库根目录运行：

```powershell
Set-Location D:\github\northstar
uv venv tmp\a2a-stack\venv
uv pip install --python tmp\a2a-stack\venv\Scripts\python.exe -r a2a-stack\requirements.txt

# 首次安装时复制检查目录。已有本地定义时合并，不覆盖自定义检查。
if (-not (Test-Path tmp\a2a-stack\trusted-checks.json)) {
    Copy-Item a2a-stack\autonomy\checks.example.json tmp\a2a-stack\trusted-checks.json
}

& .\a2a-stack\agent\install-host-task.ps1 -Start
docker compose -p northstar-a2a -f a2a-stack\compose.yaml up -d --build --wait mcp-gateway
codex mcp add northstar_a2a --url http://127.0.0.1:18892/mcp
```

已有正常运行的宿主时，跳过上述安装代码块，不创建 venv、不重复注册或启动宿主。仅连接现有 MCP 即可。维护升级应先等待或明确停止活动 Goal，按文末维护步骤禁用健康触发并停止宿主，再更新依赖和文件，最后恢复启动。若从旧前台服务迁移，也应先核对任务并停止该服务，再注册计划任务。宿主计划任务有登录与每分钟健康触发，`IgnoreNew` 保留正在运行的实例，无执行时限，电池切换不停止。它检查宿主进程，不决定 Agent 团队或给 Goal 设定执行时间。

Codex 桌面、CLI 和 IDE 共用 MCP 配置。若已有会话没显示新工具，在 MCP 设置中重新连接／Restart，使用 `/mcp` 确认；不必改模型或认证。本地服务不要求 OAuth 登录。[官方配置说明](https://learn.chatgpt.com/docs/extend/mcp)

Claude Code 也可直接连接：

```powershell
claude --mcp-config a2a-stack/mcp/client-config.json --strict-mcp-config
```

## 你怎么下目标

向连接此 MCP 的主助手描述目标、验收和不能做的事。助手根据项目上下文填入工作区、写入范围和可用检查，不要求你自己拼接参数。当前宿主实例的授权工作区是 `D:/github/northstar`；不同工作区要明确配置授权，不能静默把路径改到别的项目。

主要工具：

| 工具 | 你的用途 |
| --- | --- |
| `set_goal` | 提交一个明确目标，返回 `goal_id`，后台主 Agent 开始自主工作 |
| `get_goal_report(goal_id)` | 查看状态、实际结果、候选审查、检查和真正需要你的事项 |
| `list_goals` | 查看目标列表 |
| `stop_goal(goal_id)` | 明确停止某条 Goal 及其任务，保留产物与证据 |
| `resume_goal(goal_id)` | 停止后或真实外部依赖解决后接回同一 Goal |
| `list_goal_checks` | 让助手选择适合此目标的已注册宿主检查 |

`set_goal` 的字段是 `workspace`、`goal`、`acceptance`、`write_paths`，可附加 `check_ids`、`constraints`、`required_inputs`、`user_gates`。最后两项仅记录真实的用户材料和保留决定，不把普通测试错误伪装成需要人工的事项。检查执行参数来自宿主可信目录，不接受网络传入的任意命令。

## 系统自己做什么

主 Agent 使用 Claude Code 原生循环，在 worker 队列外选择模板或自定义团队。它创建 A2A 角色和任务，实施者修改授权文件，verifier 运行真实检查，独立 reviewer 审查准确候选；失败时继续修复、重试或接回已有工作。角色、顺序和是否创建新 stack 由主 Agent 按目标决定。

原生中间重试不会被当成终态错误。控制进程退出会自动接回原 Goal/session；上下文确实损坏时，复位上下文并保留 Goal、任务绑定和产物。SQLite 保存各角色协议状态，进程身份监测避免重复写入或永久 WORKING。完成必须通过程序复核的实际实施来源、准确候选、独立 READY 和原始检查。

`COMPLETE` 后控制器退出，留下报告，等待你设置下一条 Goal。框架不会自行把整个项目或其他目标都做完。

## 查看与维护

Goal 报告和恢复轨迹在 `tmp/a2a-stack/autonomy/goals/<goal_id>/`；A2A 执行回执在 `tmp/a2a-stack/tasks/<task_id>/`。正常操作使用 MCP 报告即可，不需要人工改这些文件。

需要明确停掉整个宿主进行维护时，先停止活动 Goal，然后：

```powershell
Disable-ScheduledTask -TaskName Northstar-A2A-Host
Stop-ScheduledTask -TaskName Northstar-A2A-Host
# 维护结束
Enable-ScheduledTask -TaskName Northstar-A2A-Host
Start-ScheduledTask -TaskName Northstar-A2A-Host
```

不要删除 SQLite、Goal 状态或卷来“复位”；恢复应保留原有任务身份和有效产物。旧固定 delivery/supervisor scheduler 仅为可选诊断入口，当前暂停；它不承担日常 Goal 控制。
