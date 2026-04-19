# Optimize Fast Charge Project

这是一个电池快充协议搜索项目。  
任务不是训练一个在线控制器，而是在固定的 PyBaMM 仿真合同下，搜索一条更好的 30 分钟分段充电协议。

## 0. 30 秒看懂这个项目

如果你是第一次进这个仓库，先记住下面五件事：

1. 任务是离线快充协议搜索，不是在线控制。
2. 主 baseline 是一个三段 BO 协议：`3.0C -> rest 10m -> 3.0C`。
3. 我们的方法仍然属于 BO，但不是 baseline 的 direct BO，而是分阶段、局部 trust-region、带 feasibility 约束的 BO。
4. 主线是 `baseline -> stage_one -> stage_two -> stage_three`，每一阶段收敛后才进入下一阶段。
5. 最终 `stage_three` 比 baseline 更强，而且完整三阶段公开搜索成本只有 `42` 次 eval，低于 GitHub direct BO 的 `109 / 124`。

## 0.1 一张表先看懂主线

| 方法 | 协议结构 | 搜索方式 | 公开成本 | 结果角色 |
| --- | --- | --- | ---: | --- |
| `baseline` | 三段：充电-静置-充电 | fixed-family direct BO | `109` | 主比较线 |
| `stage_one` | 四段：加入 tail | local trust-region BO | `15` | 第一阶段 winner |
| `stage_two` | 四段主结构 + 事件触发边界 | local trust-region BO + guard model | `13` | 第二阶段 winner |
| `stage_three` | 五段：entry / monitor / hold / tail | local trust-region BO + guard model + sequence prior | `14` | 当前 winner |
| 完整主线 | `baseline -> stage_one -> stage_two -> stage_three` | 分阶段收敛后晋级 | `42` | 最终公开 pipeline |

## 1. 这个任务到底是什么

这个项目研究的是一个离线协议搜索问题：

- 先定义一类可解释的充电协议模板；
- 每次给出一条具体协议；
- 用同一个 PyBaMM 仿真环境评估它；
- 按固定指标和固定排序规则，找出更好的快充方案。

这里优化的是“预先写好的分段充电配方”，不是运行时根据电池状态连续调流的强化学习策略。

如果用一句话概括：  
这个仓库回答的是“在同一个电池仿真合同下，怎样把 baseline 的三段快充协议，逐步扩展成更强的四段、五段协议，并且还能稳妥地通过鲁棒性验证”。

## 2. 我们怎么评估一个协议

整个仓库对外统一使用同一个四指标合同，定义在：

- `baselines/vendor/ax_pybamm_fastcharge/json/metric_contract.json`

四个核心指标是：

| 指标 | 含义 | 方向 |
| --- | --- | --- |
| `Q30` | 30 分钟内的充电容量 | 越大越好 |
| `plating_loss` | 锂析出损失 | 越小越好 |
| `sei_growth` | SEI 增长 | 越小越好 |
| `total_lli` | 总锂损失 | 越小越好 |

当前主 baseline 的四指标值是：

- `Q30 = 0.08990`
- `plating_loss = 0.32218`
- `sei_growth = 58.36217`
- `total_lli = 0.0140665`

主搜索不是只看 nominal 单点。后续阶段会在同一个 `followup_v1` 场景包上比较鲁棒性，场景包括：

- `nominal`
- `warm_cell`
- `hot_cell`
- `plating_stress`
- `sei_stress`

最终排序时综合看：

- `success_rate`
- `guard_pass_rate`
- `worst_score`
- `robust_utility`
- `mean_delta_Q30`

所以这里不是“只把 nominal `Q30` 最大的点拿出来”，而是在固定鲁棒合同下找 rank-1。

如果你只关心这个任务的判分标准，到这里已经够了；后面才是 baseline 和算法细节。

## 3. Baseline 是什么

本仓库保留并引用了 `baselines/vendor/ax_pybamm_fastcharge/` 里的 baseline family。当前对外保留的 baseline 主要有三条：

| Baseline | 策略 | 直观理解 |
| --- | --- | --- |
| `CCCV_2.0C` | 恒流恒压 | 工业常见参考线 |
| `LinearTaper_3.0C-0.5C` | 线性 taper | 前高后低的手工启发式充电 |
| `BO_3step_aggressive` | 单目标 BO | `charge -> rest -> charge` 的三段搜索结果 |

其中当前主比较线是：

- `baseline = BO_3step_aggressive`

### 3.1 三个 baseline 的策略例子

#### `CCCV_2.0C`

可以理解成：

- 先以 `2.0C` 恒流充电；
- 到电压上限 `4.2V` 后转恒压；
- 在这个仓库里，为了和离散分段协议兼容，近似成一条单段参考线。

这是标准工业参考，但它几乎没有结构自由度。

#### `LinearTaper_3.0C-0.5C`

这条线把 30 分钟切成 6 段，电流从 `3.0C` 线性下降到 `0.5C`。  
直觉上就是：

- 前面倍率高一些，尽快充进去；
- 后面倍率低一些，尽量减少高 SOC 区域的风险。

它是一个很自然的手工启发式，但依然没有事件触发，也没有“中间先快后稳”的结构。

#### `BO_3step_aggressive`

这是当前主 baseline，也是整个项目的主要比较对象。  
它的具体策略是：

- 第 1 段：`3.0C` 充电 10 分钟
- 第 2 段：`0C` 静置 10 分钟
- 第 3 段：`3.0C` 再充 10 分钟

也就是：

`3.0C -> rest 10 min -> 3.0C`

这条线已经比手工 baseline 强，但它本质上仍然只是一个三段协议：

- 没有单独的 tail 段；
- 没有事件触发切换；
- 没有 entry / hold 这样的细化控制；
- 搜索空间也比较窄。

这正是我们后续方法要继续往前推的起点。

### 3.2 baseline 的 BO 是怎么做的

这里要区分两件事：

- 当前仓库里保留了 baseline 的协议定义和结果；
- 但没有把原始 GitHub direct BO notebook 作为当前主线代码继续发布。

从当前保留证据看，baseline 的思路是：

- 先固定一个协议模板，例如 3-step 或 5-step；
- 然后直接在这个固定模板的参数空间里做贝叶斯优化；
- 最后输出在这个固定空间里找到的最优协议。

所以 baseline 的 BO 可以概括成：

- direct BO；
- fixed protocol family；
- 单阶段搜索；
- 不分 `stage_one -> stage_two -> stage_three` 这样的层级推进。

当前仓库里还能直接看到的 baseline 证据主要是：

- 协议定义：
  - `baselines/vendor/ax_pybamm_fastcharge/multi_objective/utils/baseline_protocols.py`
- baseline 重评估入口：
  - `baselines/vendor/ax_pybamm_fastcharge/run_standard_baselines.py`
- 成本记录：
  - `experiments/analysis/search_cost/search_cost_comparison.md`

也就是说，当前发布版里的 baseline 更像是：

- “保留原始 GitHub BO 找到的代表性协议，再在同一仿真合同下重新评估”

而不是继续把原始 direct BO notebook 当成主线算法入口。

如果只用一句话概括 baseline：

- baseline 是“在固定协议模板里直接做 BO”。

## 4. 我们的方法和 baseline 相比改了什么

最核心的变化有两类：

### 4.1 协议结构变得更丰富

baseline 的主线只有三段：

- 充电
- 静置
- 充电

我们的主线会逐步扩展成：

- `stage_one`
  - 在 baseline 结构后面显式加入 tail 段
- `stage_two`
  - 在四段结构里加入事件触发边界
- `stage_three`
  - 再加入 entry / monitor / hold / tail 的更细分 staged 结构

### 4.2 搜索方式也变了

我们不是每个阶段都从头盲搜，而是：

- 先选定一个 anchor 协议；
- 围绕这个 anchor，在一个局部 trust region 里搜索；
- 用同一套指标合同来判断新候选是否真的比 anchor 更好；
- 只有当候选在鲁棒合同上也过关时，才把它当成有效提升。

所以这个项目的主线不是“换个名字重跑 BO”，而是：

- 同一个评价合同；
- 逐步扩展协议表达能力；
- 每阶段围绕前一阶段 winner 做受约束的局部搜索。

### 4.3 我们和 baseline 哪里一样，哪里不一样

这点非常关键，因为我们的方法不是“完全不用 BO”。

#### 一样的地方

- baseline 和我们都属于贝叶斯优化这一类方法；
- 都是在协议参数空间里提出候选，再送去同一个仿真器评估；
- 都用 surrogate 辅助决定下一步试哪里。

#### 不一样的地方

baseline 的 direct BO 更像是：

- 固定一个协议结构；
- 直接在这个固定空间里搜；
- 目标是在这个固定 family 里找到最优点。

我们的三阶段方法更像是：

- 先逐阶段扩展协议结构，而不是从一开始就把所有复杂结构放在一起搜；
- 每一阶段都以前一阶段 winner 为 anchor；
- 在 anchor 周围的 trust region 内做局部 BO；
- 不只拟合一个目标 surrogate，还显式拟合一个 guard / feasibility surrogate；
- `stage_three` 里又额外引入了 sequence prior 和 stage mask 这样的结构约束。

所以更准确的说法不是：

- “baseline 用 BO，我们不用 BO”

而是：

- “baseline 是 direct BO on a fixed protocol family”
- “我们是 staged, trust-region, feasibility-aware BO”

这一点可以直接理解成：

- baseline 的重点是“在固定结构里找最好参数”；
- 我们的重点是“先逐步扩结构，再在每个阶段里做局部 BO”。

## 5. 我们的方法到底怎么搜

三个阶段共享同一个搜索框架，只是搜索空间不同。

公共的控制器逻辑是：

1. 先把当前 anchor 协议在全部场景上评估一遍。
2. 把协议写成一个参数向量，例如 `first_rate`、`rest_minutes`、`trigger_voltage` 这些维度。
3. 在 anchor 周围先生成一批 seed 候选。
4. 用已评估点拟合两个高斯过程模型：
   - 一个预测搜索目标；
   - 一个预测 guard / feasibility 表现。
5. 用 `guard_feasibility_weighted_expected_improvement` 提议下一个候选。
6. 如果新点的 `guard_pass_rate` 没达到阈值，或者没有真正超过当前 best，就缩小 trust region。
7. 如果连续出现有效改进，就扩大 trust region。
8. 当半径缩到最小、没有新点，或者预算用完时停止。

换句话说，这不是全局暴力搜索，而是：

- 先围绕 anchor 做工程上合理的局部探索；
- 再用 surrogate 帮忙决定下一步往哪试；
- 同时把“是否可行”放进搜索闭环。

如果用更算法化的话说，当前三阶段的共同骨架是：

- 一个 GP 预测搜索目标；
- 一个 GP 预测 `guard_pass_rate`；
- 一个候选池采样器在当前 trust region 内生成候选；
- 一个 acquisition 函数把
  - expected improvement、
  - 不确定性 bonus、
  - feasibility probability
  合在一起；
- 然后只把 acquisition 最高的点送去真实仿真。

所以“在这个范围内怎么搜”的准确答案是：

- 我们仍然是 BO；
- 但不是 baseline 那种直接在固定大空间里跑的 direct BO；
- 而是局部、分阶段、带 feasibility 约束的 BO。

如果你只想抓住最关键的机制，可以把每一阶段理解成：

- 先拿当前 winner 当 anchor；
- 再在 anchor 周围提一批候选；
- 用 GP + acquisition 选下一个最值得试的点；
- 一旦当前局部区域收敛，就停止并把 winner 提升到下一阶段。

还有一个非常重要的点：  
三个阶段不是并行乱跑，也不是随便切换。当前公开主线是：

- `stage_one` 先在自己的 trust region 里收敛；
- 达到 `trust_region_floor` 或当前预算上限后，才把 winner 提升成下一阶段 anchor；
- `stage_two` 再围绕这个 winner 继续收敛；
- 最后才进入 `stage_three`。

也就是说，这条主线是一个明确的“逐阶段收敛 -> 提升 winner -> 进入下一阶段”的层级搜索流程。

## 6. 三个阶段分别在搜什么

当前公开主线是：

`baseline -> stage_one -> stage_two -> stage_three`

但要注意一个细节：

- `stage_one` 的代码搜索是从一个固定三段 seed 协议开始；
- 然后再用同一个 baseline 合同去比较；
- `stage_two` 和 `stage_three` 才是严格以前一阶段 winner 为 anchor 继续往前推。

### 6.1 Stage One：四段 tail-search

`stage_one` 的目标是先从三段协议走到一个更合理的四段协议。  
它的公开搜索空间是 4 维：

| 维度 | 含义 | 范围 | 步长 |
| --- | --- | --- | --- |
| `first_rate` | 第一段充电倍率 | `2.9` 到 `3.1` | `0.05` |
| `rest_minutes` | 静置时长 | `8` 到 `12` 分钟 | `1` |
| `third_rate` | 第三段倍率 | `4.05` 到 `4.30` | `0.05` |
| `tail_rate` | 尾段倍率 | `1.5` 到 `3.5` | `0.05` |

它生成的协议结构是：

1. 第一段高速充电
2. 静置
3. 第三段主充电
4. 固定 3 分钟 tail 收尾

其中：

- 总时长固定是 30 分钟；
- `tail_minutes` 固定为 3 分钟；
- 当 `rest_minutes` 改变时，前面主充电时间会自动重分配。

当前 `stage_one` 的公开 winner 例子是：

- `3.0C` 充 10 分钟
- `rest` 10 分钟
- `4.25C` 再充 7 分钟
- `2.40C` tail 3 分钟

也就是：

`3.0C -> rest 10m -> 4.25C -> 2.40C tail`

这一步的意义很直接：  
先把 baseline 最后那一大段“统一处理”的充电，拆成“主充电 + tail 收尾”，让后段更可控。

当前保留结果里，`stage_one` 一共评估了 `15` 个候选，最终停止原因是：

- `trust_region_floor`

也就是说，它不是无限往外搜，而是在当前局部搜索空间收敛后停止。

### 6.2 Stage Two：四段 trigger-search

`stage_two` 以前一阶段的 winner 为 anchor。  
它的搜索空间仍然是 4 维，但最后一个维度已经不再是 `tail_rate`，而是触发电压：

| 维度 | 含义 | 范围 | 步长 |
| --- | --- | --- | --- |
| `first_rate` | 第一段充电倍率 | `2.9` 到 `3.1` | `0.05` |
| `rest_minutes` | 静置时长 | `8` 到 `12` 分钟 | `1` |
| `third_rate` | 主监控段倍率 | `4.05` 到 `4.30` | `0.05` |
| `trigger_voltage` | 事件触发电压 | `4.14` 到 `4.19V` | `0.01V` |

`stage_two` 生成的协议结构更细一些：

1. 第一段高速充电
2. 静置
3. 一个固定 2 分钟的 guard / entry 段
4. 一个“充到超时或触发电压”的 monitor 段
5. 一个固定 3 分钟的 tail 段

虽然代码里最终会展开成 5 个执行 step，但对外理解时，它仍然是“在四段主结构里加入事件触发边界”的那一步。

当前 `stage_two` 的公开 winner 例子是：

- `3.0C` 充 10 分钟
- `rest` 10 分钟
- `4.30C` 先充 2 分钟
- `4.30C` 再充 5 分钟，或者到 `4.16V` 就切换
- `3.05C` tail 3 分钟，或者到 `4.20V` 停止

也就是：

`3.0C -> rest 10m -> 4.30C guard -> 4.30C until 4.16V -> 3.05C tail`

这一步相对 `stage_one` 的关键变化是：

- 不再只靠固定时长；
- 开始允许“到某个电压就切换”；
- 所以后段协议不只是一个静态 taper，而是有了事件触发边界。

当前保留结果里，`stage_two` 一共评估了 `13` 个候选，最终也停在：

- `trust_region_floor`

然后才把它的 winner 提升成 `stage_three` 的 anchor。

### 6.3 Stage Three：五段 staged search

`stage_three` 以前一阶段的 winner 为 anchor，是当前主线方法。  
它的搜索空间扩展到 7 维：

| 维度 | 含义 | 范围 | 步长 |
| --- | --- | --- | --- |
| `first_rate` | 第一段充电倍率 | `2.9` 到 `3.1` | `0.05` |
| `rest_minutes` | 静置时长 | `8` 到 `12` 分钟 | `1` |
| `third_rate` | monitor 段倍率 | `4.05` 到 `4.30` | `0.05` |
| `entry_rate` | entry 段倍率 | `4.05` 到 `4.50` | `0.05` |
| `trigger_voltage` | monitor 段切换电压 | `4.14` 到 `4.19V` | `0.01V` |
| `hold_rate` | hold 段倍率 | `2.20` 到 `3.60` | `0.05` |
| `hold_minutes` | hold 段时长 | `0` 到 `2` 分钟 | `0.5` |

这一阶段的协议结构是：

1. 第一段高速充电
2. 静置
3. 固定 2 分钟 entry 段
4. 监控段，直到触发电压
5. 可选 hold 段
6. 固定 3 分钟 tail 段

这里真正新增的能力有三件事：

- `entry_rate`
  - 让“进入后半程”的两分钟和后面的 monitor 段分开控制
- `hold_rate + hold_minutes`
  - 允许在尾段前插一个短暂 hold 段
- `stage mask`
  - 允许 hold 段按条件打开或关闭，而不是永远存在

当前 `stage_three` 的公开 winner 例子是：

- `3.0C` 充 10 分钟
- `rest` 10 分钟
- `4.50C` entry 2 分钟
- `4.30C` monitor 3.5 分钟，或直到 `4.18V`
- `3.35C` hold 1.5 分钟
- `2.80C` tail 3 分钟

也就是：

`3.0C -> rest 10m -> 4.50C entry -> 4.30C until 4.18V -> 3.35C hold 1.5m -> 2.80C tail`

这一步相对 `stage_two` 的关键变化是：

- 进入后半段时，允许先用更激进的 `entry_rate` 把容量推上去；
- 再用单独的 `monitor` 段控制风险；
- 如果需要，再插一个可选 `hold` 段做更细的收尾；
- 最后仍保留明确的 tail。

当前保留结果里，`stage_three` 一共评估了 `14` 个候选，最终同样停在：

- `trust_region_floor`

所以这三步不是简单堆预算，而是三个“收敛后再晋级”的局部搜索阶段。

到这里为止，外部读者应该能回答两个核心问题：

- 我们到底比 baseline 多了哪些结构能力？
- 我们是不是还在用 BO，以及 BO 到底怎么变了？

## 7. Stage Three 里额外加了哪些算法设计

`stage_three` 不只是维度更多，还多了三类显式设计：

### 7.1 Sequence Prior

代码里会对候选协议施加一个 sequence feasibility prior。  
直觉上，它是在搜索前就给“更像合理快充曲线”的候选更高优先级，减少明显不靠谱的组合。

### 7.2 Entry Activation

如果不开这个设计，`entry_rate` 就会退回接近 `third_rate`，相当于前两分钟的 aggressive entry 消失。  
这也是为什么 `stage_three` 可以单独做 `--disable-entry-activation` 消融。

### 7.3 Stage Mask

`hold` 段不是强制存在的。  
代码里会根据 `hold_minutes` 是否达到阈值，决定这一段是否真的打开。这样做的好处是：

- 搜索空间更灵活；
- 不会为了“凑五段”而硬塞一个没必要的 hold。

## 8. 当前方法的核心创新点是什么

现在可以比较清楚地说，创新点主要是下面四件事：

1. 不是继续在 baseline 的三段协议里微调，而是逐阶段扩展协议结构。
2. 不是每次从头盲搜，而是以前一阶段 winner 为 anchor 做局部 trust-region 搜索。
3. 搜索目标里不只看 nominal 容量，还把 guard / feasibility 放进闭环。
4. 在 `stage_three` 里，entry / monitor / hold / tail 被分成了更细的角色，并且支持结构化消融。

更稳妥的说法是：  
这是一个“更强的协议表示 + 受约束的分阶段搜索”方法包，而不是单个组件单独解释全部收益。

如果只压成一句对外表述，可以说：

- 在同一个 PyBaMM 合同下，我们把 baseline 的 direct BO 扩展成了一条 staged, trust-region, feasibility-aware BO 主线。

## 9. 当前效果怎么样

当前最优公开方法是 `stage_three`。

主结果可以先看这张表：

| 方法 | nominal Q30 | 角色 |
| --- | ---: | --- |
| `baseline` | `0.08990` | 主 baseline |
| `stage_one` | `0.09494` | 第一阶段 winner |
| `stage_two` | `0.09522` | 第二阶段 winner |
| `stage_three` | `0.09636` | 当前 winner |

可以安全对外说的结论是：

- `stage_one` 已经明显强于 `baseline`；
- `stage_two` 又在 `stage_one` 上继续提升；
- `stage_three` 是当前最强主线；
- 提升不只体现在 nominal `Q30`，同时没有把三个退化指标做坏。
- 这条主线不是靠更高公开搜索成本硬堆出来的。

当前最重要的主结果文件是：

- `experiments/runs/stage_three/results/stage_three_main_summary.json`

## 10. 我们还做了哪些额外实验

为了证明当前方法不是偶然结果，仓库里还保留了三类额外证据。

### 10.1 外部组合应力验证

文件：

- `experiments/analysis/external_validation/results/external_validation_summary.json`

这个实验会把：

- `stage_three`
- `stage_two`
- `baseline`

放到搜索 bundle 之外的 `combined_stress_v1` 条件下重新比较。

当前结论是：

- `stage_three` 在 held-out 组合应力下仍然 rank-1；
- `stage_two` 仍然可行，但落后于 `stage_three`；
- `baseline` 在 held-out guard 上失败。

### 10.2 搜索成本比较

文件：

- `experiments/analysis/search_cost/search_cost_comparison.md`

这个分析回答的是：  
我们的分阶段方法是不是只是因为“多跑了很多次”。

当前保留结果显示：

- GitHub direct BO 3-step：`109` 次 eval
- GitHub direct BO 5-step：`124` 次 eval
- `stage_one`：`15` 次 eval
- `stage_two`：`13` 次 eval
- `stage_three`：`14` 次 eval
- 完整三阶段主线：`42` 次 eval

这意味着两件事：

1. 我们不是靠“比 baseline 多搜很多倍”才拿到更好结果。
2. 当前公开主线用 `42` 次 candidate-level eval，就完成了从 baseline 到最终 winner 的整条搜索链；这个成本明显低于 GitHub direct BO 的 `109` 和 `124`。

所以 README 里最应该强调的一句话其实是：

- 我们是在同一个评价合同下，用更低的公开搜索成本，得到了一条比 baseline 更强、并且能通过外部验证的协议。

### 10.3 结构化消融

当前 `stage_three` 支持以下消融开关：

- `--disable-sequence-prior`
- `--disable-entry-activation`
- `--disable-stage-mask`

这些消融不是为了说“某一个模块单独赢了全部”，而是为了回答：

- 如果去掉 sequence prior，会不会整条方法直接崩掉？
- 如果去掉 entry activation，会不会退回前一阶段？
- 如果去掉 stage mask，五段结构还有没有意义？

当前更稳妥的结论仍然是：  
提升是 package-level improvement，不是单个开关单独解释全部收益。

## 11. 怎么运行

先准备环境：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

建议直接使用 Python `3.12`。当前这套依赖在 Python `3.13` 上不稳定，尤其 `PyBaMM` 很容易在安装阶段失败。

如果你的默认镜像源提示找不到 `pybamm`，直接改用官方 PyPI：

```bash
python -m pip install --index-url https://pypi.org/simple -r requirements.txt
```

常用命令：

```bash
./run.sh smoke
./run.sh search
./run.sh stage-one --mode smoke
./run.sh stage-two --mode smoke
./run.sh validate
./run.sh baseline
./run.sh show-stage-one
./run.sh show-stage-two
./run.sh show-pipeline
```

含义分别是：

- `smoke`
  - 快速检查 `stage_three` 主流程
- `search`
  - 运行 `stage_three` 主搜索
- `stage-one`
  - 运行第一阶段搜索
- `stage-two`
  - 运行第二阶段搜索
- `validate`
  - 运行外部组合应力验证
- `baseline`
  - 重跑保留 baseline
- `show-stage-one`
  - 查看第一阶段公开摘要
- `show-stage-two`
  - 查看第二阶段公开摘要
- `show-pipeline`
  - 查看三阶段方法总览

## 12. 项目结构怎么读

如果你只想快速理解项目，建议最后再看代码结构：

- `methods/`
  - 我们方法本体
  - `stage_one.py`、`stage_two.py`、`stage_three.py`
- `baselines/`
  - baseline 封装与 vendor baseline 包
- `experiments/entrypoints/`
  - 所有运行入口和查看入口
- `experiments/runs/`
  - 已保留的阶段结果
- `experiments/analysis/`
  - 外部验证和成本分析
- `paper/`
  - 对外论文草稿

## 13. 第一次进入仓库应该怎么看

建议按这个顺序：

1. `README.md`
2. `RESULTS.md`
3. `SUMMARY.md`
4. `experiments/entrypoints/show_pipeline.py`
5. `experiments/runs/stage_three/results/stage_three_main_summary.json`
6. `experiments/analysis/external_validation/results/external_validation_summary.json`
7. `experiments/analysis/search_cost/search_cost_comparison.md`
8. `methods/README.md`
9. `paper/draft.md`

如果你只想知道当前最稳妥的项目结论，优先看：

- `RESULTS.md`
