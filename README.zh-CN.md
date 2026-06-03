# Spec-Driven QA — 从 PRD 到上线决策的端到端流水线（Claude Code Skill）

[English](README.md) | 中文

把一份 PRD 喂进去，跑完一整套测试，最后吐出一个明确的"能不能上线"
（ship / 带病上线 / hold，三选一）。

大部分流水线其实是**传统软件测试**那套老东西 —— 需求图、等价类、边界值、
决策表、状态转换、pairwise —— 从 spec 里机械地铺开。AI 那一层（rubric
打分、OWASP LLM Top 10、一致性、agent trace 评估）薄薄盖在上面，只在
该用的地方用，不会脱离 classical backbone 单飞。原因不复杂：让 LLM
自由发挥"写测试用例"的人都见过结果 —— 出来的全是 happy path，没人去
打 boundary，没人去想 negative，更不会写"A 真 B 假"那种组合。所以这
个 skill 干脆 classical 先来、AI 后到，`verify.py` 还会拒绝那种"只有
rubric 没有 classical 兜底"的 AI feature。

这是个 **Claude Code skill**：一份 `SKILL.md` 加一堆 Python 脚本。判断
的活儿 Claude 干（读 PRD、写需求图、出 rubric、给 AI 输出打分），机械
的活儿脚本干（解析、生成 classical backbone、执行、打分、出报告、
自检）。分工不能混 —— 这是设计的核心。

---

## 安装

把这个 skill 文件夹丢到 Claude Code 的 skills 目录里，让它落在
`~/.claude/skills/spec-driven-qa/`（或者项目级的 `.claude/skills/`）。
纯 Markdown + Python，没有 build 步骤。

```bash
git clone https://github.com/stancsz/spec-driven-qa-skill.git
mkdir -p ~/.claude/skills
cp -r spec-driven-qa-skill ~/.claude/skills/spec-driven-qa
```

Windows PowerShell：

```powershell
git clone https://github.com/stancsz/spec-driven-qa-skill.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse spec-driven-qa-skill "$env:USERPROFILE\.claude\skills\spec-driven-qa"
```

装完直接跟 Claude Code 说话：

```
/spec-driven-qa
拿这份 PRD 测测我的退款客服
这个 feature 能上吗？
```

Claude 自己读 `SKILL.md`，然后把整条流水线跑起来。你不用动手敲脚本
（除非你想），下面那些命令就是 Claude 实际在跑的。

**依赖：** Python ≥ 3.10。可选（Claude 用到时会自己装）：`pypdf` /
`python-docx`（解析 PRD）、Playwright + Chromium（自检的视觉渲染）、
judge API key（想 headless 评分就配，不配也行 —— Claude 自己 inline
当裁判，免费）。

---

## 跑一遍完整流程

所有动作都在一个 **run 目录**里，每一步读上一步的 JSON、写自己的
（schema 在 `references/schemas.md`）。

```bash
cd ~/.claude/skills/spec-driven-qa
RUN=runs/$(date +%Y%m%d-%H%M%S); mkdir -p "$RUN"

# 1. UNDERSTAND —— 解析 PRD，Claude 写需求图
python scripts/ingest_prd.py PRD.pdf --out "$RUN"
#    -> Claude 写出 $RUN/01_requirements.json
python scripts/graph_tools.py "$RUN/01_requirements.json"     # 校验 + 标歧义

# 2A. GENERATE —— classical backbone（自动）
python scripts/generate_test_cases.py scaffold "$RUN/01_requirements.json" --out "$RUN/02_testcases.json"
python scripts/classical_tests.py model "$RUN/01_requirements.json" --out "$RUN/_test_model.json"
#    -> Claude 把变量 / 分区 / 边界 / 决策规则填进去
python scripts/classical_tests.py expand "$RUN/_test_model.json" --into "$RUN/02_testcases.json"

# 2B. GENERATE —— AI rubric + error recovery 用例叠上去
#    -> Claude 给 AI feature 加 rubric 用例，然后:
python scripts/generate_test_cases.py validate "$RUN/02_testcases.json" --graph "$RUN/01_requirements.json"

# 3. EXECUTE —— 真的去打你的 SUT
python scripts/run_suite.py "$RUN/02_testcases.json" --out "$RUN/03_results.json" --samples 3

# 5. EVALUATE —— 给 AI 输出打分
python scripts/judge.py emit "$RUN"        # Claude 打分 -> $RUN/_judge_scores.json
python scripts/judge.py ingest "$RUN"
python scripts/adversarial.py "$RUN" --target "$RUN/target.json" --inject-into body.input

# 6. REPORT —— 出报告，出上线决策
python scripts/score_release.py "$RUN"     # defects.json + readiness.json
python scripts/make_report.py "$RUN"       # report.html + report.md

# 7. VERIFY —— 强制自检，不许跳
#    -> Claude 先写 $RUN/limitations.md，然后:
python scripts/verify.py "$RUN" --strict   # lint + 把 report 渲染成 png；--strict 渲染失败直接挂
#    -> Claude 真的打开 report.png 用眼睛扫一遍版面，再拿给你看
```

（Layer 4 INTEGRATE 是可选的：`assets/ci/github-actions.yml` 是
GitHub Actions 的 CI 卡口模板。）

---

## 你最后拿到什么

| 产物 | 是什么 |
|---|---|
| `01_requirements.json` | 需求图：依赖关系、AI 标记、歧义、预测的覆盖空洞 |
| `02_testcases.json` | 测试套件 —— classical backbone + AI rubric + 对抗 |
| `03_results.json` | 执行结果（pass / fail / error / needs_eval / skipped） |
| `05_evaluations.json` | LLM 裁判的裁决 + 一致性、对抗结果、agent trace |
| `defects.json` | 缺陷清单，每条都带 severity 和复现路径 |
| `readiness.json` | 上线评分 + ship / ship-with-caveats / hold 三选一 |
| `report.html` / `report.md` | 给人看的报告（覆盖图、缺陷、限制） |
| `report.png` | 报告渲染图，强制要"用眼睛看一眼"的那张 |
| `limitations.md` | 老实交代：哪些没测、上线后还可能在哪儿翻车 |

---

## 这玩意儿凭什么不一样

**Classical 先来，AI 后到。** 你让 LLM "写测试用例"，出来的几乎全是
happy path。一个 "30 天退款窗口" 的需求，LLM 写一个 "20 天" 的用例就
觉得自己交差了，根本不会去打 29、30、31、0、365、-1、366 这些边界
（而 bug 偏偏全藏在边界上）。所以这个 skill 把传统测试设计先机械地
铺开 —— EP / BVA / decision table / state transition / pairwise —— AI
那层只能薄薄盖在 classical 之上。你写一份小小的 **test model**（输入
变量 + 分区 + 边界），expander 自动展开成几十个具体用例。`verify.py`
还会拒绝那种"只有 rubric 没有 classical 兜底"的 AI feature —— 这条
规矩是为了让 AI 测试不至于变成纯走过场。

**AI 输出怎么打分？rubric + 一致性。** 一句话进去、十种 valid 回答
出来，`assert output == "..."` 根本顶不住。所以 AI feature 配 **rubric**
（必须出现的 claim、不许出现的内容、格式、语气），让另一个 LLM 当裁判，
跑 N 次（默认 3 次）取 `pass_rate` 和 `score_stddev`。3 次过 2 次的
feature，平均分再好看也不能上 —— 这事得拿出来讲清楚。详见
`references/rubric_guide.md`。

**跑完别走，自己用眼睛看一眼。** `script exit 0 ≠ done`。Layer 7
会 lint 一遍（HTML entity 有没有泄露、TODO 有没有填完、AI 用例有没有
classical 兜底、限制有没有写……），然后把 report 渲染成图。Claude
（不是你）会真的打开那张图扫一眼：徽章丢了没、表格塌了没、版面崩了没。
配 `--strict` 渲染失败直接 fail，CI 里就这么挂。

**老实交代没测什么。** 全绿的报告最骗人 —— 没测的东西全藏起来了。
所以每跑一次都要交一份 `limitations.md`：哪些超出 scope、做了什么假设、
classical / AI / 对抗 三层各自够不到什么、生产环境还可能在哪儿翻车。
这个 skill 的承诺一直是"把你说的范围测完整"，从来不是"零缺陷上线"。
后者没人能承诺。

---

## 常用选项

- **多变量组合覆盖：** 一个需求 ≥2 个输入变量时，expander 自动跑
  pairwise（all-pairs）。要改成 full cartesian 或关掉，在 model 里设
  `"combinatorial": "pairwise" | "all" | "none"`。详见
  `references/classical_techniques.md`。
- **严格视觉卡口：** `python scripts/verify.py "$RUN" --strict` 渲染
  不出来直接 fail，CI 里挂上这个。
- **Judge backend：** inline（Claude 自己来，默认，免费）用
  `judge.py emit` / `ingest`；headless（CI 或大批量）用
  `judge.py run "$RUN" --provider anthropic|minimax|openai`，从环境
  变量读对应的 `*_API_KEY`。
- **Target 类型：** 测试用例可以打 `http` / `cli` / `python` / `manual`
  四种 target。`manual` 不会假装跑过 —— 老老实实标 untested。

---

## 翻车排查

- *ingest 报 "No text extracted"* —— PRD 是扫描件，先 OCR 再喂进来。
- *Verify 报 "AI tests grounded in classical tests"* —— 那个 AI feature
  对应的需求得加进 `_test_model.json`，重跑 expand。AI 用例必须坐在
  classical backbone 上，这是硬规矩。
- *Verify 警告 "report rasterized"（或 `--strict` 下直接 FAIL）* ——
  装个 headless 渲染器（Playwright + Chromium），或者手动开 `report.html`
  眼睛看。
- *Predicate 用例全报 error* —— 你的 predicate 引用了 sandbox 不给的
  builtin。sandbox 只放了 `str / len / int / float / abs / min / max /
  any / all / bool / sorted / round` 这几个，需要别的就改用 `python`
  target。

---

## 目录结构

```
spec-driven-qa/
├── SKILL.md                       Claude 走的流程
├── README.md                      英文版
├── README.zh-CN.md                中文版（你正在看）
├── scripts/                       流水线脚本（Claude 跑，你也可以手跑）
├── references/                    schema、classical 技术、rubric、OWASP、合规
└── assets/ci/github-actions.yml   可选的 CI 质量卡口
```

每个脚本、每一层的细节都在 `SKILL.md` 里。

## License

MIT。
