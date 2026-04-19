# Results

这个文件只回答五个问题：

1. 当前最好的协议是谁。
2. 它比 `baseline` 和前一阶段强在哪里。
3. 为什么这个结果不是靠更高搜索成本硬堆出来的。
4. 这条主线是怎么逐阶段收敛出来的。
5. 现在哪些结论可以稳妥对外说。

## 1. 当前 winner

当前对外公开的最优线直接叫：

- `stage_three`

它对应的一条直观协议是：

- `3.0C -> rest 10 min -> 4.5C entry 2 min -> 4.3C until 4.18V -> 3.35C hold 1.5 min -> 2.8C tail 3 min`

如果只看结果角色，可以把整条方法链理解成：

`baseline -> stage_one -> stage_two -> stage_three`

## 2. 关键比较

| 方法 | nominal Q30 | 角色 |
| --- | ---: | --- |
| `baseline` | `0.08990` | GitHub / vendor 主 baseline |
| `stage_one` | `0.09494` | 第一阶段 winner |
| `stage_two` | `0.09522` | 第二阶段 winner |
| `stage_three` | `0.09636` | 当前 winner |

当前最关键的事实是：

- `stage_one` 已经明显强于 `baseline`；
- `stage_two` 在 `stage_one` 基础上继续提升；
- `stage_three` 进一步超过 `stage_two`；
- `stage_three` 不只是 nominal 更高，在外部组合应力验证里也仍然排第一。

## 3. 为什么这个结果有意义

如果只说“效果更好”，别人会自然怀疑：

- 你是不是只是多搜了很多轮？
- 你是不是成本比 baseline 高很多？

当前仓库保留的成本证据恰恰说明不是这样。

### 3.1 搜索成本比较

文件：

- `experiments/analysis/search_cost/search_cost_comparison.md`

当前保留结果是：

- GitHub direct BO 3-step：`109` 次 eval
- GitHub direct BO 5-step：`124` 次 eval
- `stage_one`：`15` 次 eval
- `stage_two`：`13` 次 eval
- `stage_three`：`14` 次 eval
- 完整三阶段主线：`42` 次 eval

这说明：

- 我们不是靠“公开搜索预算比 baseline 更大”才得到更强协议；
- 相反，当前公开主线总成本是 `42` 次 candidate-level eval，明显低于 GitHub direct BO 的 `109` 和 `124`；
- 所以这条结果的意义在于：在同一个评价合同下，我们用更低的公开搜索成本，找到了更强的协议。

## 4. 这条主线是怎么收敛出来的

三阶段主线不是并行乱跑，也不是把所有预算混在一起。

它的流程是：

1. `stage_one` 先围绕自己的 anchor 搜索。
2. 当当前 trust region 收敛到最小半径，或者预算用完时停止。
3. 把这一阶段的 winner 提升成下一阶段 anchor。
4. `stage_two` 再重复同样的局部收敛过程。
5. 最后 `stage_three` 才继续往前推进。

当前保留结果里，三个阶段的停止方式都很一致：

- `stage_one`：`15` 次 eval，`stop_reason=trust_region_floor`
- `stage_two`：`13` 次 eval，`stop_reason=trust_region_floor`
- `stage_three`：`14` 次 eval，`stop_reason=trust_region_floor`

所以这不是一条“越跑越久直到碰巧找到好点”的路线，而是一条：

- 每阶段先在局部 trust region 内收敛；
- 再把收敛后的 winner 提升到下一阶段；
- 最后用三次局部收敛拼出一条层级搜索主线。

## 5. 额外证据

### 5.1 外部组合应力验证

文件：

- `experiments/analysis/external_validation/results/external_validation_summary.json`

这个实验把：

- `stage_three`
- `stage_two`
- `baseline`

放到搜索 bundle 之外的 `combined_stress_v1` 条件下重比一次。

当前结论是：

- `stage_three` 在 held-out 组合应力下仍然 rank-1；
- `stage_two` 仍然可行，但落后于 `stage_three`；
- `baseline` 在 held-out guard 上失败。

### 5.2 含义

这一步很重要，因为它说明：

- `stage_three` 不是只在它自己搜索时见过的场景上赢；
- 即使换到外部组合应力条件下，它仍然保持第一；
- 所以当前 winner 不是一个只对原搜索 bundle 偶然成立的点。

## 6. 当前最重要的证据文件

- 主搜索摘要：`experiments/runs/stage_three/results/stage_three_main_summary.json`
- 外部验证摘要：`experiments/analysis/external_validation/results/external_validation_summary.json`
- 成本比较：`experiments/analysis/search_cost/search_cost_comparison.md`
- baseline 结果：`baselines/vendor/ax_pybamm_fastcharge/results/standard_baselines.json`
- stage one 摘要：`experiments/runs/stage_one/results/stage_one_summary.json`
- stage two 摘要：`experiments/runs/stage_two/results/stage_two_summary.json`

## 7. 当前稳妥结论

现在可以稳妥对外说的是：

- 这是一个固定 GitHub / PyBaMM 合同下的离线快充协议搜索项目。
- 当前 `stage_three` 是整条主线里最强的已验证协议。
- 它比 `baseline` 和 `stage_two` 都更好。
- 这个结果不只是 nominal 更高，在外部组合应力验证中也仍然保持第一。
- 这条结果不是靠更大的公开搜索成本堆出来的；完整三阶段主线只用了 `42` 次 eval。
- 三个阶段都是“当前阶段收敛后，再进入下一阶段”的层级搜索流程。

不建议现在说得过满的话：

- “已经证明全局最优”
- “对所有电池模型都成立”
- “我们的整个历史研发成本低于所有 baseline”
- “某一个单独模块已经被完全证明是唯一关键因素”
