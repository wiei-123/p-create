
## 目录结构

```
nsnppt/
├── README.md               本文件
├── requirements.txt        matplotlib
├── .gitignore
├── src/
│   ├── nsnppt.py              核心模拟器：NSNPPT 语义 + 全部模块构造
│   │                          （寄存器对 / ADD / SUB / OUTPUT / INPUT / Πu / 生成器）
│   ├── test_nsnppt.py         单元测试（SUB、ADD、OUTPUT、INPUT 模块与完整运行）
│   ├── muorbit.py             Korec Mu 的闭式轨道模型
│   ├── z.py                   fig_mu323_timeline / fig_mu323_halting
│   │                          从当前目录读 mu323_trace.csv
│   │                          
│   └── export_plingua_style.py  
├── web/
│   ├── nsnppt-simulation-en.html   浏览器端交互模拟页面
│   └── nsnppt_data.min.js          页面数据：Πu 全连接组 + Mu(323,2) 校验数据
│                                   
├── paper/
│   └── NSNPPT_Algorithms_and_Results_EN.pdf   算法与结果说明
└── data/
    └── mu323_trace.csv         31,024 条 Mu 指令的逐条 trace
                                （Mu 指令 / Πu-118 时刻 / Πu-115 时刻 / 寄存器值）
```

## 环境要求

- Python 3.8+
- matplotlib

```bash
pip install -r requirements.txt
```

## 快速开始



```bash
cd src

# 1. 跑单元测试（SUB/ADD/OUTPUT/INPUT 模块 + 完整 Mu(323,2) 运行）
python test_nsnppt.py

# 2. 生成论文图 1/2（输出到当前目录的 figs/）——先复制数据过来：
cp ../data/mu323_trace.csv .
python z.py
#    只调版式时可用合成数据（无需 CSV）：python z.py --demo

# 3. 闭式轨道模型 vs 全量模拟对拍（x<400 全扫描，约需数分钟；
#    x=323 因验证循环 cap=30000 < 31023 步会报 4 个 MISMATCH，
#    属容量截断而非模型错误，x=323 的正确性由 test_nsnppt.py 覆盖）
python muorbit.py

# 4. 导出 P-Lingua 风格的 Πu 声明式 listing
python export_plingua_style.py
```

### 作为库使用

```python
from nsnppt import build_Piu, run_mu

# 结果 = σout 前两次发射的间隔 = 寄存器 0 的值
net, order = build_Piu(optimized=True)   # 115 神经元；optimized=False 为 118
result, mu_steps = run_mu(323, 2)[:2]    # -> (1, 31023)


```

## web 交互模拟

直接用浏览器打开 `web/nsnppt-simulation-en.html`（无需服务器，
数据由同目录的 `nsnppt_data.min.js` 提供）。页面包含 Πu 的完整连接组、
逐步/自动播放模拟、以及 Mu(323,2) 运行的 Python 侧校验指纹
（FNV/SHA、指令序列 head、发射时刻）。

## 数据说明

`data/mu323_trace.csv` 每行一条已执行的 Mu 指令：

| 列 | 含义 |
|---|---|
| `#` | 序号（1–31024） |
| `Mu 指令` | Korec Mu 的指令标号 |
| `Πu-118 时刻` | 未优化 118 神经元系统的网络步（发射时刻） |
| `Πu-115 时刻` | 融合优化 115 神经元系统的网络步 |
| `Πu-115 指令` | 优化系统的指令标号 |
| `r0 … r7` | 该步的 8 个寄存器值 |

关键数字：Mu(323,2) 共执行 31,024 条指令；l22（停机）在
Πu-115 的网络步 61346 发出；σout 三次发射于 61339/61340/61341，
间隔 1 = 结果（寄存器 0 = 1）。


