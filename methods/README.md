# Methods

这个目录只放方法本体，不放运行入口。

如果你已经看过顶层 `README.md`，这里可以把它当成“只讲算法实现”的版本。

## 1. 方法主线

当前方法不是三个互相独立的脚本，而是一条逐阶段推进的搜索链：

`baseline -> stage_one -> stage_two -> stage_three`

这里的含义是：

- `stage_one` 先从 baseline 往前推进；
- `stage_two` 以前一阶段 winner 为 anchor；
- `stage_three` 再以前一阶段 winner 为 anchor；
- 每一阶段都先在自己的局部 trust region 内收敛，然后才把 winner 提升到下一阶段。

## 2. 这个目录里真正“在跑”的是什么

- `stage_one.py`
  - 第一阶段 tail-search 实现
- `stage_two.py`
  - 第二阶段 trigger-search 实现
- `stage_three.py`
  - 当前主线五段方法实现

运行入口不在这里，而是在：

- `../experiments/entrypoints/run_stage_one.py`
- `../experiments/entrypoints/run_stage_two.py`
- `../experiments/entrypoints/run_stage_three.py`

## 3. 三个阶段分别在做什么

| 阶段 | 结构变化 | 搜索维度 | 输出 |
| --- | --- | --- | --- |
| `stage_one` | 从三段扩到带 tail 的四段 | `first_rate`, `rest_minutes`, `third_rate`, `tail_rate` | 第一条四段 winner |
| `stage_two` | 在四段结构里加入触发电压边界 | `first_rate`, `rest_minutes`, `third_rate`, `trigger_voltage` | 事件触发式四段 winner |
| `stage_three` | 扩到 entry / monitor / hold / tail 的五段主线 | `first_rate`, `rest_minutes`, `third_rate`, `entry_rate`, `trigger_voltage`, `hold_rate`, `hold_minutes` | 当前最终 winner |

## 4. 三个阶段共同的搜索骨架

三个阶段共享同一个大框架：

1. 先把当前 anchor 协议编码成一个参数点。
2. 在当前 trust region 内生成一批候选。
3. 用已经评估过的点拟合 surrogate。
4. 用 acquisition 选择下一个点。
5. 把这个点送去真实仿真。
6. 如果它真的更好，就更新中心；如果没有更好，就缩小搜索半径。
7. 当半径缩到最小或预算用完时停止。

所以这里不是暴力枚举，也不是全局随机搜，而是局部、逐阶段的 BO。

## 5. 和 baseline 的 BO 哪里一样，哪里不一样

### 一样的地方

- 都属于 BO 路线；
- 都是在协议参数空间里提出候选，再用同一个仿真器评估；
- 都用 surrogate 帮助决定下一步试哪里。

### 不一样的地方

baseline 更像：

- fixed protocol family；
- direct BO；
- 单阶段。

当前方法更像：

- staged protocol family；
- trust-region BO；
- feasibility-aware BO；
- 分阶段晋级。

## 6. 各阶段的关键机制

### `stage_one`

- 一个 GP 预测搜索目标；
- 一个 GP 预测 `guard_pass_rate`；
- 在四维局部空间里做 feasibility-aware acquisition；
- 直到 `trust_region_floor` 才停止。

### `stage_two`

- 与 `stage_one` 相同的双 GP + trust-region 框架；
- 但空间从 `tail_rate` 改成了 `trigger_voltage`；
- 所以重点从“尾段大小”变成“何时触发切换”。

### `stage_three`

- 仍然是双 GP + trust-region 框架；
- 再加上 `sequence_feasibility_prior`；
- 同时支持 `entry_activation` 和 `stage_mask`；
- 可以通过 ablation 开关逐项关闭这些设计。

## 7. 当前最容易误解的点

- 误解：前两阶段只有摘要，不能运行。
  - 正解：三个阶段都能运行。
- 误解：我们已经完全不用 BO 了。
  - 正解：我们仍然是 BO，只是不是 baseline 的 direct BO。
- 误解：`stage_three` 是从零开始单独搜索的。
  - 正解：它是以前一阶段 winner 为 anchor 的第三阶段搜索。
- 误解：代码里偶尔出现旧协议 ID，说明命名没整理完。
  - 正解：旧 ID 主要用于对齐历史结果；公开命名已经统一成 `baseline`、`stage_one`、`stage_two`、`stage_three`。

## 8. 证据文件对应关系

- `stage_one`
  - `../experiments/runs/stage_one/results/stage_one_summary.json`
- `stage_two`
  - `../experiments/runs/stage_two/results/stage_two_summary.json`
- `stage_three`
  - `../experiments/runs/stage_three/results/stage_three_main_summary.json`

## 9. 推荐阅读顺序

1. `../README.md`
2. `../experiments/entrypoints/show_pipeline.py`
3. `stage_one.py`
4. `stage_two.py`
5. `stage_three.py`
6. `../experiments/runs/stage_one/results/stage_one_summary.json`
7. `../experiments/runs/stage_two/results/stage_two_summary.json`
8. `../experiments/runs/stage_three/results/stage_three_main_summary.json`
