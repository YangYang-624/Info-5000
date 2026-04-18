# Start Here

第一次打开这个项目，按下面顺序走就够了。

## 1. 配环境

推荐：

- `Python 3.10`
- 独立虚拟环境

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

## 2. 先看结论再看代码

先看这两个文件：

- `RESULTS.md`
- `README.md`

`RESULTS.md` 告诉你最终结果。

`README.md` 告诉你任务是什么、搜索空间是什么、`PSMS-v2` 为什么更强、成本该怎么讲。

## 3. 先跑 smoke

```bash
./run.sh smoke
```

这一步的目的只是确认主流程能跑通。

跑完主要看：

- `experiments/main/ua_psms_v1/results/ua_psms_v2_smoke_summary.json`

## 4. 跑主搜索

```bash
./run.sh search
```

跑完主要看：

- `experiments/main/ua_psms_v1/results/ua_psms_v2_search_main_summary.json`
- `experiments/main/run-psms-v2-main-v1/RESULT.json`

这两个文件会告诉你：

- 最终最优 protocol 是谁
- nominal 四个核心指标是多少
- robust top 是谁

## 5. 跑 held-out 验证

```bash
./run.sh heldout
```

跑完主要看：

- `experiments/analysis/heldout_combo_validation/results/psms_v2_heldout_combo_v1_summary.json`

这个文件会告诉你：

- `PSMS-v2` 在 held-out stress bundle 上是不是仍然 rank-1
- `success_rate`
- `guard_pass_rate`
- `robust_utility`

## 6. 如果要重跑 baseline

```bash
./run.sh baseline
```

结果看：

- `baselines/local/ax-pybamm-fastcharge/results/standard_baselines.json`

## 7. 如果你只想快速理解项目

直接读下面 5 个文件就够了：

- `RESULTS.md`
- `README.md`
- `paper/draft.md`
- `experiments/main/run-psms-v2-main-v1/RESULT.json`
- `experiments/analysis/heldout_combo_validation/results/psms_v2_heldout_combo_v1_summary.json`

## 8. 关于 fair-search

`./run.sh fair-search` 这个入口还在，但它不是当前主张的核心证据。

当前最稳妥的对外叙事是：

- 固定 GitHub/PyBaMM 合同
- 用 staged framework 找到更强协议
- 在主线 candidate-level eval 成本上低于 GitHub direct BO

不要把 `fair-search` 当成当前主文的主比较。
