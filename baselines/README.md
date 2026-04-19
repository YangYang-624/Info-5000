# Baselines

这个目录现在只保留 baseline 本体，不放运行入口。

## 目录结构

- `protocols.py`
  - baseline 协议公开接口
- `simulator.py`
  - baseline 仿真器公开接口

## 当前结构

可以把 baseline 层理解成：

`public wrappers -> vendor baseline package -> baseline results / metric contract`

## 两层结构怎么理解

### 外层公开接口

- `protocols.py`
- `simulator.py`

这些文件负责把 baseline 能力暴露成当前仓库可直接导入的接口。

### 内层 vendor 包

- `vendor/ax_pybamm_fastcharge/multi_objective/utils/baseline_protocols.py`
- `vendor/ax_pybamm_fastcharge/multi_objective/utils/pybamm_simulator.py`
- `vendor/ax_pybamm_fastcharge/json/metric_contract.json`
- `vendor/ax_pybamm_fastcharge/results/standard_baselines.json`

这里是当前仍被主方法和验证脚本实际依赖的 baseline 实现与证据文件。

这里补充一个实现层文件：

- `vendor/ax_pybamm_fastcharge/run_standard_baselines.py`

它不是临时脚本，而是 vendor baseline 包的一部分。

## 哪些结果文件当前会被主方法读取

- `vendor/ax_pybamm_fastcharge/json/metric_contract.json`
- `vendor/ax_pybamm_fastcharge/results/standard_baselines.json`

`stage_three` 和外部验证都会读这两个文件，所以现在不能删。

## 最容易误解的点

- 误解：`vendor/` 只是备份或缓存。
- 正解：`vendor/` 是当前 baseline 正式实现根目录。

- 误解：`baselines/` 里应该放运行脚本。
- 正解：当前仓库把所有运行入口统一放在 `experiments/entrypoints/`。

## 设计原则

- `baselines/` 只保留 baseline 本体
- 所有 `run_*` 入口统一放在 `experiments/entrypoints/`
- `vendor/` 不是临时目录，也不是缓存目录
