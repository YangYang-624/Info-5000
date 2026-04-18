# Paper Draft

这个文件是论文材料的通俗入口。

如果你不想一上来就看长篇论文正文，可以先看这里。它会告诉你：

1. 这篇论文到底在研究什么问题。
2. 我们的方法和 baseline 的关系是什么。
3. 当前主结果是什么。
4. 这篇论文现在能讲到什么程度。

正式论文正文在：

- `paper/draft.md`

如果已经编译出 PDF，位置在：

- `paper/build/main.pdf`

如果你接下来要继续修改论文，优先编辑：

- `paper/draft.md`

## 1. 论文在讲什么

这篇论文研究的是一个固定仿真合同下的电池快充协议搜索问题。

更具体地说：

- 我们不是在做一个实时控制器
- 不是让算法在充电过程中持续观察电池状态，再连续调整电流
- 而是在一个固定的协议模板空间里，搜索一条更好的快充配方

所以这篇论文的核心不是“智能控制”，而是：

- 在同一个 GitHub/PyBaMM 评估合同下
- 用更好的协议表示方式
- 配合更稳妥的搜索策略
- 找到更强、而且经过验证的快充协议

## 2. baseline 是什么

这篇论文默认的 headline baseline 是：

- `BO_3step_aggressive`

它来自原始 GitHub fast charge baseline。

这个 baseline 的协议结构比较简单，本质上是一个 3-step 方案：

- 先充电
- 然后静置
- 再充电

它的 nominal 主指标是：

- `Q30 = 0.08990 Ah`

这是我们后续所有提升的起点。

## 3. 我们的方法是什么

我们最终方法是：

- `PSMS-v2`

全称可以理解为：

- physics-prior masked multi-stage search

它和 baseline 最大的区别不是“只是多搜了几个点”，而是它允许的协议结构更丰富。

baseline 只能表达比较简单的 3-step 曲线。

`PSMS-v2` 则允许一种更细的 staged protocol：

- 第一段预充
- 静置段
- 高倍率入口段
- 监控段
- 可选 hold 段
- 最后再导出 tail 收尾

从搜索空间的角度看，`PSMS-v2` 实际优化的是一个 7 维离散空间，包含：

- `first_rate`
- `rest_minutes`
- `third_rate`
- `entry_rate`
- `trigger_voltage`
- `hold_rate`
- `hold_minutes`

所以这篇论文的主张不是：

- “我们证明了一个新的全局最优 BO 算法”

而是：

- “在固定 GitHub/PyBaMM 合同下，更丰富的 staged protocol family 加上 feasibility-aware local search，可以找到一个更好的已验证协议”

## 4. 当前最优协议是什么

当前主线最优协议是：

- `UA5_PSMS_3.00C_rest10m_4.30C_e4.50_v4p18_h3.35_1p5m`

从直觉上理解，这条协议做了这些事情：

- 先用 `3.00C` 充一段
- `rest 10 min`
- 进入 `4.50C` 的 entry 段
- 再以 `4.30C` 继续充到 `4.18V`
- 再以 `3.35C` hold `1.5 min`
- 然后做 tail 收尾

它不是一个任意复杂的黑盒控制器，而是一条可以读得懂的工程化快充配方。

## 5. 当前主结果是什么

nominal 对比结果如下：

- `BO_3step_aggressive`: `Q30 = 0.08990 Ah`
- `UA4_VTBO`: `Q30 = 0.09494 Ah`
- `UA4_EVTBO`: `Q30 = 0.09522 Ah`
- `UA5_PSMS`: `Q30 = 0.09636 Ah`

因此：

- 相对 baseline，`PSMS-v2` 提升约 `+7.19%`
- 相对 EVTBO，`PSMS-v2` 提升约 `+1.20%`

这说明我们的主结果不是只比最老的 baseline 好一点，而是连前一代 EVTBO 也超过了。

## 6. 为什么这个结果是可信的

这篇论文现在最重要的优点，不只是“结果更高”，而是结果边界比较清楚。

### 6.1 评价合同是固定的

全篇一直使用同一个 4 指标合同：

- `Q30`
- `plating_loss`
- `sei_growth`
- `total_lli`

方向是：

- `Q30` 越大越好
- 其余三个越小越好

所以不是靠偷偷换指标把结果讲好看。

### 6.2 不只看 nominal

主搜索不是只盯着 nominal 单点，而是在一个 5-scenario robust bundle 上排序：

- `nominal`
- `warm_cell`
- `hot_cell`
- `plating_stress`
- `sei_stress`

因此被选出来的 winner，不是一个只在单个场景下好看的点。

### 6.3 有 held-out 验证

我们还做了一个 search bundle 之外的 held-out 组合应力验证。

结果是：

- `PSMS-v2` 仍然 rank-1
- `guard_pass_rate = 1.0`
- `robust_utility = 0.0706`

而 baseline `BO_3step_aggressive` 在这个 held-out bundle 上：

- `guard_pass_rate = 0.0`

这说明 `PSMS-v2` 不是只对搜索时那组场景过拟合。

## 7. 成本该怎么讲

这是论文里最需要谨慎的一段。

### 7.1 可以安全讲的版本

如果比较的是“最终采用的主线框架本身”，那么 candidate-level eval 成本是：

- GitHub direct BO 3-step: `109`
- GitHub direct BO 5-step: `124`
- 我们的 promoted pipeline: `44`

这里的 `44` 不是只算成功点。

只要某个候选真的进入了仿真评估，即使它失败、非法、或者 guard 没过，也已经算进去了。

所以在这条主线口径下，可以说：

- 我们用更少的真实评估，找到了更强的最终协议

### 7.2 不能乱讲的版本

这个 `44` 不是整个研发历史总成本。

如果把 smoke、ablation、历史支线、warmstart、validate 全算上，我们的总研发投入并不比 GitHub 更低。

所以论文里不能写成：

- “我们的整个研发总成本低于 GitHub baseline”

这个说法不成立。

## 8. 论文现在能 claim 什么

当前这版论文可以安全 claim：

- `PSMS-v2` 是当前固定 GitHub/PyBaMM 合同下的已验证最优线
- 它在 nominal 和 held-out 两层上都优于 baseline
- 在主线 candidate-level eval 成本口径下，它比 GitHub direct BO 更便宜
- 这个主线成本已经包含失败候选

当前不应该 claim：

- 我们已经公平证明从头全局搜索一定优于所有 baseline optimizer
- 我们已经证明整个历史研发总成本更低
- 我们已经证明某一个单独模块就是唯一关键因素
- 我们对所有电池体系都成立

## 9. 为什么论文里还要强调“package-level improvement”

因为现有 ablation 的结论是：

- 去掉 sequence prior，仍然能找回 PSMS winner family
- 去掉 entry activation，结果会退回 EVTBO anchor

这说明：

- gain 不是 sequence prior 单独带来的
- 也不能把所有功劳简单粗暴地归到一个模块上

因此这篇论文最稳的写法是：

- 把 `PSMS-v2` 作为一个 package-level improvement 来讲

而不是讲成：

- “我们发现了一个决定性模块”

## 10. 建议怎么读论文材料

如果你是第一次看，建议按下面顺序读：

1. `RESULTS.md`
2. `README.md`
3. `PAPER_DRAFT.md`
4. `paper/draft.md`
5. `paper/build/main.pdf`

如果你想快速核对证据，优先看：

- `experiments/main/ua_psms_v1/results/ua_psms_v2_search_main_summary.json`
- `experiments/analysis/heldout_combo_validation/results/psms_v2_heldout_combo_v1_summary.json`
- `experiments/analysis/framework_cost/framework_cost_table.md`

## 11. 接下来如果还要改论文，应该优先改什么

如果后续还要继续打磨论文，优先级建议是：

1. 继续保证 README、RESULTS、PAPER_DRAFT 和 `paper/draft.md` 四个口径完全一致
2. 明确区分“主线成本”与“总研发成本”
3. 一直坚持 package-level claim，不夸大为单模块胜利
4. 如果后面还补实验，也只补能增强当前主张的，不要重新打开不公平的全局搜索叙事
