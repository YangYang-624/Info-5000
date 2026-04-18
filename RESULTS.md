# Results

这个文件是面向第一次接触项目的人写的结果说明。

它尽量用最直白的话回答下面这些问题：

1. 我们最后到底做出来了什么。
2. 它比 baseline 到底好在哪里。
3. 这个结果现在有多可信。
4. 成本应该怎么理解。
5. 哪些话现在可以讲，哪些话不能讲。

## 1. 一句话结论

当前这个项目最核心的结论是：

- 在固定 GitHub/PyBaMM 评估合同下，`PSMS-v2` 找到了当前已验证最强的一条快充协议。

这条最终协议是：

- `UA5_PSMS_3.00C_rest10m_4.30C_e4.50_v4p18_h3.35_1p5m`

## 2. 这个结果到底比谁更好

我们主要和两类对象比较：

- 原始 GitHub baseline，代表是 `BO_3step_aggressive`
- 我们自己的前一代方法，代表是 `EVTBO`

所以你可以把结果理解成两层提升：

- 第一层：相对原始 baseline，我们明显更好
- 第二层：相对已经很强的 EVTBO，我们还进一步往前推了一点

## 3. 最核心的 nominal 数字

nominal 主结果如下：

- `BO_3step_aggressive`: `Q30 = 0.08990 Ah`
- `UA4_VTBO`: `Q30 = 0.09494 Ah`
- `UA4_EVTBO`: `Q30 = 0.09522 Ah`
- `UA5_PSMS`: `Q30 = 0.09636 Ah`

如果只看最重要的 headline 数字：

- baseline `BO_3step_aggressive` 是 `0.08990 Ah`
- 最终 `PSMS-v2` 是 `0.09636 Ah`

也就是：

- 绝对提升约 `0.00646 Ah`
- 相对提升约 `+7.19%`

如果和 EVTBO 比：

- EVTBO 是 `0.09522 Ah`
- `PSMS-v2` 是 `0.09636 Ah`

也就是：

- 绝对提升约 `0.00114 Ah`
- 相对提升约 `+1.20%`

## 4. 这个提升不是只看一个指标瞎讲的

整个项目不是只看 `Q30`。

固定使用的四个核心指标是：

- `Q30`
- `plating_loss`
- `sei_growth`
- `total_lli`

方向是：

- `Q30` 越大越好
- 其余三个越小越好

这很重要，因为如果只看单一 throughput 指标，很容易把一个“充得快但伤电池”的方案错讲成更好。

而我们现在的结果是：

- `Q30` 更高
- `plating_loss` 没有变差
- `sei_growth` 更低
- `total_lli` 也更低

所以这不是一种用寿命换充电量的表面提升。

## 5. 为什么说这个结果不只是 nominal 好看

主搜索不是只在单个 nominal 条件下选 winner。

每个候选都要在一个 5-scenario robust bundle 上评估：

- `nominal`
- `warm_cell`
- `hot_cell`
- `plating_stress`
- `sei_stress`

最终排序时会综合考虑：

- `success_rate`
- `guard_pass_rate`
- `worst_score`
- `robust_utility`

也就是说，主线结果不是“只在一个简单环境里最优”，而是在一个固定的鲁棒评估包下选出来的。

## 6. held-out 验证告诉了我们什么

为了避免只在 search bundle 里好看，我们又做了 held-out 组合应力验证。

held-out 上的结果是：

- `UA5_PSMS`: `guard_pass_rate = 1.0`, `robust_utility = 0.0706`
- `UA4_EVTBO`: `guard_pass_rate = 1.0`, `robust_utility = 0.0`
- `BO_3step_aggressive`: `guard_pass_rate = 0.0`, `robust_utility = -0.6077`

这意味着：

- `PSMS-v2` 不只是 search 时那组 scenario 里第一
- 到了 held-out 组合应力下，它仍然是 rank-1
- 而 baseline 在 held-out 上直接失去可行性

所以当前结果不是一种明显的 search-bundle 过拟合。

## 7. 我们的方法到底好在哪

如果用一句更工程化的话来讲，`PSMS-v2` 的优势主要来自两件事：

- 它能表示更丰富的 staged charging protocol
- 它在搜索时更认真地把 feasibility 放进决策里

### 7.1 协议表达更强

原始 3-step baseline 能表达的曲线比较简单。

而 `PSMS-v2` 允许：

- entry boost
- 电压触发切换
- hold 段
- tail 收尾

因此它能表达更细、更像真实快充工程设计会考虑的协议形状。

### 7.2 搜索更重视可行性

`PSMS-v2` 不是只盯着 nominal 最大化，而是在搜索闭环中考虑：

- 哪些候选更可能物理可行
- 哪些候选更可能通过 guard
- 哪些候选在鲁棒 ranking 下才真的值得保留

所以它找到的不是一个“看起来激进但不稳定”的点，而是一个更稳的 winner。

## 8. 成本应该怎么理解

这部分最容易被讲乱。

### 8.1 主线框架成本

如果比较的是“最终采用的主线框架本身”，那么 candidate-level eval 成本是：

- GitHub direct BO 3-step: `109`
- GitHub direct BO 5-step: `124`
- 我们的 promoted pipeline: `44`

这里的 `44` 不是只算“有效评估”。

只要一个候选真的进入了仿真评估，即使它最后：

- 不可行
- 失败
- guard 没过

它也已经算进成本了。

所以在这个主线成本口径下，可以安全说：

- 我们比 GitHub direct BO 更便宜
- 同时最终结果还更好

### 8.2 不能偷换成总研发成本

这个 `44` 不代表整个项目历史上从头到尾一共只做了 44 次尝试。

如果把所有：

- smoke
- ablation
- 历史支线
- warmstart
- validate

全部加起来，我们的总研发投入并不比 GitHub 更低。

所以一定要区分：

- 主线 promoted pipeline 成本
- 全历史研发总成本

前者可以说更便宜，后者不能这么说。

## 9. 当前结果可以讲到什么程度

当前可以安全讲：

- `PSMS-v2` 是当前固定 GitHub/PyBaMM 合同下的已验证最优线
- 它在 nominal 和 held-out 两层上都优于 baseline
- 它比 EVTBO 也更好
- 在主线 candidate-level eval 成本口径下，它比 GitHub direct BO 更便宜
- 这个主线成本已经包含失败候选

当前不能讲：

- 我们整个研发总成本更低
- 我们已经公平证明从头全局搜索一定优于所有 baseline optimizer
- 我们已经证明某一个单独模块就是全部原因
- 我们的结果已经适用于所有电池体系和所有快充任务

## 10. 为什么现在要强调 package-level improvement

因为现在的 ablation 说明的是：

- gain 不是 sequence prior 单独造成的
- 去掉 entry activation 又会退回 EVTBO

这意味着最稳的说法是：

- `PSMS-v2` 作为一个整体 package 更强

而不是：

- 某一个局部模块单独决定了一切

这会让故事更保守，但也更经得起问。

## 11. 如果你只想核最重要的证据，看哪些文件

最重要的文件是这几个。

主搜索结果：

- `experiments/main/run-psms-v2-main-v1/RESULT.json`
- `experiments/main/ua_psms_v1/results/ua_psms_v2_search_main_summary.json`

held-out 结果：

- `experiments/analysis/heldout_combo_validation/results/psms_v2_heldout_combo_v1_summary.json`

baseline 结果：

- `baselines/local/ax-pybamm-fastcharge/results/standard_baselines.json`

成本表：

- `experiments/analysis/framework_cost/framework_cost_table.md`

## 12. 如果你是第一次把项目发给别人，最推荐怎么介绍

最简单的介绍方式可以直接这样说：

“这是一个在固定 PyBaMM fast-charge benchmark 下做 staged protocol search 的项目。我们最终方法 `PSMS-v2` 在保持同一评价合同的前提下，把 nominal `Q30` 从 baseline 的 `0.08990 Ah` 提升到了 `0.09636 Ah`，held-out 上仍然 rank-1，而且在主线 candidate-level eval 成本口径下只用了 44 次真实评估，低于 GitHub direct BO 的 109/124 次。”

这句话现在是比较稳的。
