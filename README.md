# Optimize Fast Charge Project

这是当前对外可分享的整理版本。它回答四个核心问题：

1. 这个任务到底是什么。
2. 我们到底在优化什么协议。
3. `PSMS-v2` 比 baseline 好在哪里。
4. 现在有哪些结果已经验证过，哪些话可以说，哪些不能说。

如果你是第一次看这个项目，建议按这个顺序浏览：

1. `START_HERE.md`
2. `RESULTS.md`
3. `README.md`
4. `paper/draft.md`

## 1. 任务是什么

这个项目研究的是一个固定电池模型下的离线快充协议搜索问题。

不是做在线控制，也不是训练一个会实时看电池状态再连续调电流的策略。这里做的是：

- 先规定一类可解释的充电协议模板
- 每次给出一个具体配方
- 用 PyBaMM 仿真去评估这个配方
- 在固定评价合同下搜索更好的配方

这里的“协议”可以理解成一条分段充电曲线。每个候选协议在运行前就已经确定好结构，只允许在预先定义的参数范围内变化。

## 2. 我们到底在优化什么

### 2.1 baseline 在做什么

GitHub baseline 的代表方法是 `BO_3step_aggressive`。它本质上是一个 3 段协议：

- 第一段充电
- 中间静置
- 最后一段充电

它的最优 3-step aggressive 配方是：

- `3.0C -> rest 10min -> 3.0C`

对应 nominal `Q30 = 0.08990 Ah`。

### 2.2 我们的方法在做什么

我们最终方法是 `PSMS-v2`，属于一个更丰富的 5 段 staged protocol family。

可以把它理解成：

- 第一段固定预充电 `first_rate`
- 第二段静置 `rest_minutes`
- 第三段高倍率入口段 `entry_rate`
- 第四段监控段 `third_rate`，直到触发电压 `trigger_voltage`
- 第五段可选 hold/tail 收尾段 `hold_rate + hold_minutes`

最终会再导出一个尾段电流 `tail_rate`。因此代码里的真实搜索维度是 7 维，见 [robust_protocol_search.py](/data/yangyang/class/info5000/project/experiments/main/ua_psms_v1/robust_protocol_search.py#L107)：

- `first_rate`
- `rest_minutes`
- `third_rate`
- `entry_rate`
- `trigger_voltage`
- `hold_rate`
- `hold_minutes`

这些维度不是完全连续自由的，而是按固定步长离散化取值，见 [robust_protocol_search.py](/data/yangyang/class/info5000/project/experiments/main/ua_psms_v1/robust_protocol_search.py#L125)：

- `first_rate` 步长 `0.05`
- `rest_minutes` 步长 `1.0`
- `third_rate` 步长 `0.05`
- `entry_rate` 步长 `0.05`
- `trigger_voltage` 步长 `0.01`
- `hold_rate` 步长 `0.05`
- `hold_minutes` 步长 `0.5`

所以这是一个有限但不小的离散搜索空间。

## 3. 最终最优协议是什么

当前最终验证通过的协议是：

- `UA5_PSMS_3.00C_rest10m_4.30C_e4.50_v4p18_h3.35_1p5m`

它对应的直观解释是：

- 先用 `3.00C` 充一段
- `rest 10 min`
- 再以 `4.50C` 做一个入口段
- 然后以 `4.30C` 继续充到 `4.18V`
- 再以 `3.35C` hold `1.5 min`
- 最后导出 tail 收尾

这条协议不是运行时根据任意状态连续调参的 controller，而是一条预定义结构下、带少量事件触发的固定协议模板。

## 4. 评价指标是什么

整个项目固定用 4 个核心指标：

- `Q30`
- `plating_loss`
- `sei_growth`
- `total_lli`

方向是：

- `Q30` 越大越好
- 其余 3 个越小越好

主搜索不是只看 nominal 单点。每个候选都要在 `followup_v1` 的 5 个 scenario 上评估：

- `nominal`
- `warm_cell`
- `hot_cell`
- `plating_stress`
- `sei_stress`

最终排序时会同时看：

- `success_rate`
- `guard_pass_rate`
- `worst_score`
- `robust_utility`
- `mean_delta_Q30`

所以这里不是“只把 nominal Q30 最大的点拿出来”，而是在一个固定鲁棒合同下选 rank-1。

## 5. baseline、任务、方法之间的关系

可以把整个项目理解成同一个任务上的一条方法演化链：

- GitHub direct BO: 3-step baseline family
- `UA3 / TRBO / FA-TRBO`: 在旧协议族里继续往前推
- `VTBO`: 引入 tail-aware 的 4-step 结构
- `EVTBO`: 引入 event-triggered 的 4-step 结构
- `PSMS-v2`: 进入 5-step masked multi-stage family

真正的任务一直没变：

- 固定 GitHub/PyBaMM 合同
- 固定 4 个核心指标
- 固定 robust ranking 规则
- 在这个合同下找更好的快充协议

## 6. `PSMS-v2` 到底好在哪里

当前最稳妥的说法不是“我们发明了一个全新的全局最优搜索器”，而是下面这句：

- `PSMS-v2` 在固定 GitHub/PyBaMM 合同下，用更丰富的 staged protocol family 加上 feasibility-aware local search，找到了一个比 baseline 和 EVTBO 都更好的已验证协议。

具体好在三层。

### 6.1 协议表达更强

相比 3-step baseline，`PSMS-v2` 不再只能在“充电-静置-充电”里调。

它允许：

- 高倍率 entry boost
- 电压触发切换
- 可选 hold 段
- 更平滑的 tail 收尾

这让协议族本身能表示更细的快充形状。

### 6.2 搜索时更重视可行性

`PSMS-v2` 不是纯粹追 nominal 最优，而是把 feasibility 和 robust ranking 放进搜索闭环里。代码里主控制器是 trust-region 局部搜索，提前偏向更像可行快充曲线的候选，并把 `guard_pass_rate` 纳入改进判据。

### 6.3 最终结果确实更强

nominal 指标上：

- `BO_3step_aggressive`: `Q30 = 0.08990 Ah`
- `UA4_VTBO`: `Q30 = 0.09494 Ah`
- `UA4_EVTBO`: `Q30 = 0.09522 Ah`
- `UA5_PSMS`: `Q30 = 0.09636 Ah`

所以：

- 相对 baseline，`PSMS-v2` 的 `Q30` 提升约 `+7.19%`
- 相对 EVTBO，`PSMS-v2` 的 `Q30` 提升约 `+1.20%`

在 held-out 组合应力验证上，`PSMS-v2` 仍然是 rank-1：

- `success_rate = 1.0`
- `guard_pass_rate = 1.0`
- `robust_utility = 0.0706`

而 `BO_3step_aggressive` 在 held-out bundle 上 `guard_pass_rate = 0.0`。

## 7. 成本应该怎么讲

这是最容易讲错的部分。

### 7.1 可以安全讲的成本

如果比较的是“最终采用的主线框架本身”，那么成本口径是：

- GitHub direct BO 3-step: `109` 次 candidate-level eval
- GitHub direct BO 5-step: `124` 次 candidate-level eval
- 我们最终 promoted pipeline: `44` 次 candidate-level eval

这里的 `44` 不是只算成功点，它已经包含了主线里那些失败点、guard 没过的点。见 [framework_cost_table.md](/data/yangyang/class/info5000/project/experiments/analysis/framework_cost/framework_cost_table.md#L5)。

所以围绕主线框架本身，可以安全说：

- 我们用更少的真实评估，找到了更强的最终协议。

### 7.2 不能乱讲的成本

`44` 不是整个研发历史总成本。

如果把所有 smoke、ablation、warmstart、被淘汰路线、validate 都算上，我们的历史研发投入明显大于 GitHub baseline。因此不能说：

- “我们的整个研发总成本低于 GitHub”

这句话不成立。

## 8. 现有 ablation 说明了什么

当前已经有两条与主线最相关的 matched rerun：

- `noprior`
- `noentry`

结论是：

- 去掉 sequence prior，仍然能找回 PSMS winner family
- 去掉 entry activation，结果退回 EVTBO anchor

这说明：

- gain 不是 sequence prior 单独造成的
- 但 entry activation 也不能单独拿出来吹成全部原因

因此当前最安全的论文口径是：

- 这是一个 package-level improvement
- 不是单一模块胜利

## 9. 现在到底能 claim 什么

当前可以安全说：

- 在固定 GitHub/PyBaMM 合同下，`PSMS-v2` 是当前已验证最优线。
- 在主线 promoted pipeline 成本口径下，我们比 GitHub direct BO 更便宜。
- 这个主线成本已经包含失败/非法候选，只要它们真的进了仿真评估，就已经被计入。
- `PSMS-v2` 在 held-out stress bundle 上仍然 rank-1。

当前不能说：

- 我们已经公平证明从头全局搜索一定优于所有 baseline optimizer。
- 我们整个研发总成本低于 GitHub baseline。
- 我们的方法已经证明对所有电池体系都最优。
- 我们已经隔离出某一个单独模块就是唯一关键因素。

## 10. 第一次运行怎么做

推荐环境：

- `Python 3.10`
- 当前本地验证环境：`Python 3.10.19`

安装：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

如果镜像源缺少 `pybamm`：

```bash
python -m pip install -r requirements.txt -i https://pypi.org/simple
```

统一入口：

```bash
./run.sh smoke
./run.sh search
./run.sh heldout
./run.sh baseline
```

含义分别是：

- `smoke`: 快速确认主流程能跑通
- `search`: 运行 `PSMS-v2` 主搜索
- `heldout`: 运行最终 held-out 验证
- `baseline`: 重跑 baseline family

`fair-search` 入口保留在代码里，但它不是当前主论文叙事的核心证据，不建议把它当成对外主比较。

## 11. 结果文件去哪里看

最重要的结果文件如下。

主搜索：

- `experiments/main/ua_psms_v1/results/ua_psms_v2_search_main_summary.json`
- `experiments/main/run-psms-v2-main-v1/RESULT.json`

held-out：

- `experiments/analysis/heldout_combo_validation/results/psms_v2_heldout_combo_v1_summary.json`

baseline：

- `baselines/local/ax-pybamm-fastcharge/results/standard_baselines.json`

成本表：

- `experiments/analysis/framework_cost/framework_cost_table.md`

论文材料：

- `paper/draft.md`
- `paper/evidence_ledger.md`
- `paper/paper_experiment_matrix.md`

## 12. 目录说明

- `baselines/local/ax-pybamm-fastcharge`
  - baseline 代码与结果
- `experiments/main/ua_psms_v1`
  - `PSMS-v2` 主算法代码
- `experiments/main/run-psms-v2-main-v1`
  - 最终主实验记录
- `experiments/analysis/heldout_combo_validation`
  - held-out 组合应力验证
- `experiments/analysis/framework_cost`
  - 成本统计表
- `paper`
  - 论文草稿、证据账本、实验矩阵
- `archive`
  - 历史整理材料，主线阅读一般不需要先看
