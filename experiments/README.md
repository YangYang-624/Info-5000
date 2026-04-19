# Experiments

这个目录现在只放三类东西：

- `entrypoints/`
  - 所有运行和查看入口脚本
- `runs/`
  - 已跑出来的主实验结果
- `analysis/`
  - 主实验之后的验证和成本分析

## 第一次看建议顺序

1. `entrypoints/show_pipeline.py`
2. `runs/stage_three/results/stage_three_main_summary.json`
3. `analysis/external_validation/results/external_validation_summary.json`
4. `analysis/search_cost/search_cost_comparison.md`
5. `entrypoints/run_stage_three.py`

### `entrypoints/`

回答：

- 这个仓库应该从哪里运行
- 哪些脚本是真正执行实验
- 哪些脚本只是展示公开摘要

优先看：

- `entrypoints/run_stage_one.py`
- `entrypoints/run_stage_two.py`
- `entrypoints/run_stage_three.py`
- `entrypoints/run_baselines.py`
- `entrypoints/show_pipeline.py`

## 各部分分别回答什么

### `runs/`

回答：

- 当前主实验跑出了什么
- 当前 robust top protocol 是谁
- 前两阶段各自留下了什么公开证据

优先看：

- `runs/stage_one/results/`
- `runs/stage_two/results/`
- `runs/stage_three/results/stage_three_main_summary.json`

### `analysis/`

回答：

- 当前 winner 在外部验证下是否仍然最好
- 整条方法链的评估成本大概是多少

优先看：

- `analysis/external_validation/results/external_validation_summary.json`
- `analysis/search_cost/search_cost_comparison.md`

## 命名原则

- 方法代码在 `methods/`
- baseline 代码在 `baselines/`
- `experiments/` 放运行入口、结果、比较和分析

这是当前仓库最重要的结构约束。

补充说明：

- 所有 `run_*` / `show_*` 入口现在都在 `entrypoints/`
- 前两阶段的公开摘要现在也放在 `runs/stage_one/results/` 和 `runs/stage_two/results/`
- `runs/` 只放结果，不放方法实现
