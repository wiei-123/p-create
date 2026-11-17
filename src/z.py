import csv
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ======================================================================
# STYLE BLOCK
# ======================================================================
STYLE = {
    # ---- figure sizes (IEEE single column = 3.5 in) -------------------
    'fig1_size': (3.5, 2.7),   # timeline
    'fig2_size': (3.5, 1.62),  # halt + emissions
    'dpi': 600,

    # ---- colours -----------------------------------------------------
    # 低饱和度的学术配色：深钢蓝 vs 砖红，灰度打印时明度差足够。
    'c_pi1': '#2F5D8A',
    'c_pi2': '#C8553D',
    'c_ink': '#222222',
    'c_band': '#D7E0E8',       # 两条曲线之间的浅灰蓝填充
    'c_gap_alpha': 1.0,
    'ls_pi1': '-',
    'ls_pi2': '-',

    # ---- fonts (pt) --------------------------------------------------
    'font_base': 8,            # IEEE 图内文字建议 >= 8 pt
    'font_axis': 8,
    'font_tick': 7.5,
    'font_legend': 8,
    'font_annot': 7,
    'serif': True,             # Times-like text to match IEEE body text
    'font_serif': ['Times New Roman', 'Nimbus Roman No9 L',
                   'Liberation Serif', 'DejaVu Serif'],

    # ---- line widths (pt) -------------------------------------------
    'lw_curve': 1.0,
    'lw_axis': 0.6,
    'lw_annot': 0.7,

    # ---- shared data handling ---------------------------------------
    'rasterize': True,         # 31k-point artists -> embedded bitmap, small PDF

    # ---- fig. 1 ------------------------------------------------------
    'a_mode': 'timeline',      # 'timeline' = 两条阶梯曲线；'delta' = 只画累计节省
    'a_ylim_top': None,        # None = 按数据自动（停机步 × 1.05）；也可写死 68000
    'a_ytick_step': 20000,
    'a_xtick_step': 10000,
    'a_gap_x': 0.93,           # x of the Delta-t arrow, in units of n
    'a_gap_dy': 1500,          # vertical offset of the Delta-t text
    'a_show_gap': False,       # timeline 模式：是否画 Delta-t 标尺与文字
    'a_hide_zero': 'both',        # 隐藏原点处的 0 刻度：'none'|'x'|'y'|'both'
    'a_delta_annot_xy': (0.55, 1.13),  # delta 模式终点标注：相对 n 与 DT
    'a_delta_slope_xy': (0.03, 0.70),  # delta 模式斜率文字：轴坐标 0-1

    # ---- fig. 2 ------------------------------------------------------
    'b_marker_ms': 4.5,
    'b_bracket_dy': 0.42,
    'b_time_label_dy': 0.14,

    # ---- 配色主题 ------------------------------------------------------
    'theme': 'muted',          # 'muted' | 'ink' | 'mono'
}

# 配色预设：改 STYLE['theme'] 即可整体换色（覆盖上面的 c_pi1/c_pi2/c_band）
THEMES = {
    'muted': {'c_pi1': '#2F5D8A', 'c_pi2': '#C8553D', 'c_band': '#D7E0E8'},
    'ink':   {'c_pi1': '#1A1A1A', 'c_pi2': '#B5472B', 'c_band': '#DEDEDE'},
    'mono':  {'c_pi1': '#1A1A1A', 'c_pi2': '#7A7A7A', 'c_band': '#E8E8E8'},
}
STYLE.update(THEMES[STYLE['theme']])

plt.rcParams.update({
    'font.size': STYLE['font_base'],
    'axes.labelsize': STYLE['font_axis'],
    'legend.fontsize': STYLE['font_legend'],
    'xtick.labelsize': STYLE['font_tick'],
    'ytick.labelsize': STYLE['font_tick'],
    'axes.linewidth': STYLE['lw_axis'],
    'lines.linewidth': STYLE['lw_curve'],
    'xtick.major.size': 2.5, 'ytick.major.size': 2.5,
    'xtick.major.width': STYLE['lw_axis'],
    'ytick.major.width': STYLE['lw_axis'],
})
if STYLE['serif']:
    plt.rcParams.update({'font.family': 'serif',
                         'font.serif': STYLE['font_serif'],
                         'mathtext.fontset': 'stix',
                         'axes.unicode_minus': False})

C1, C2, INK = STYLE['c_pi1'], STYLE['c_pi2'], STYLE['c_ink']
CSV_NAME = 'mu323_trace.csv'
HEADER_118, HEADER_115 = 'Πu-118 时刻', 'Πu-115 时刻'


# ======================================================================
# data loading
# ======================================================================
def load_rows(path):
    """Read the trace with a UTF-8 (BOM) first try and a GBK fallback."""
    last = None
    for enc in ('utf-8-sig', 'gbk'):
        try:
            with open(path, encoding=enc, newline='') as f:
                reader = csv.DictReader(f)
                return list(reader.fieldnames or []), list(reader)
        except UnicodeDecodeError as exc:      # pragma: no cover
            last = exc
    raise last


def pick_column(fields, token, fallback):
    """Column whose name contains `token`; falls back to the known header."""
    for name in fields:
        if token in name:
            return name
    if fallback in fields:
        return fallback
    raise KeyError('no column for %r in %r' % (token, fields))


def demo_rows(n=31024, t_last_115=61337, gap=3568, first=328):
    """Synthetic trace with the same statistics, for layout previews only."""
    fused_at = (n // 4, n // 2, 3 * n // 4)
    rows, t115, seen = [], [], 0
    for i in range(1, n + 1):
        base = first + round((t_last_115 - first) * (i - 1) / (n - 1))
        if i in fused_at:
            seen += 1
        t115.append(base)
        t118 = base + round(gap * seen / len(fused_at))
        rows.append({HEADER_118: t118, HEADER_115: t115[-1]})
    return [HEADER_118, HEADER_115], rows


if '--demo' in sys.argv:                       # --demo 优先，便于单独调版式
    fields, rows = demo_rows()
    print('[demo] synthetic data, layout preview only.')
elif os.path.exists(CSV_NAME):
    fields, rows = load_rows(CSV_NAME)
else:
    sys.exit('missing %s (use --demo for a layout preview)' % CSV_NAME)

c118 = pick_column(fields, '118', HEADER_118)
c115 = pick_column(fields, '115', HEADER_115)
t118 = [int(r[c118]) for r in rows]
t115 = [int(r[c115]) for r in rows]
n = len(rows)

# headline numbers, all derived from the data
THALT1, THALT2 = t118[-1], t115[-1]
DT = THALT1 - THALT2
if n != 31024:
    print('[warn] %d rows (expected 31024 for Mu(323,2)); continuing.' % n)
assert DT > 0, 'fused build must stop earlier'

# emission columns are optional: without them Fig. 2 is schematic
em118 = [int(r[c]) for c in fields if '118' in c and ('emit' in c.lower() or '发' in c) for r in rows]
em115 = [int(r[c]) for c in fields if '115' in c and ('emit' in c.lower() or '发' in c) for r in rows]
em118 = sorted({v for v in em118 if v})
em115 = sorted({v for v in em115 if v})
if len(em118) >= 2 and len(em115) >= 2:
    REL1 = [t - THALT1 for t in em118[:3]]
    REL2 = [t - THALT2 for t in em115[:3]]
    assert REL1[1] - REL1[0] == REL2[1] - REL2[0], 'interval mismatch'
    EMIT_NOTE = ''
else:
    REL1 = REL2 = [2, 3, 4]
    EMIT_NOTE = ' (schematic: no emission columns in %s)' % CSV_NAME
    print('[warn] no emission columns found: Fig. 2 emissions are schematic.')

# ======================================================================
# fig. 1: execution timeline
# ======================================================================
idx = range(1, n + 1)
fig, ax = plt.subplots(figsize=STYLE['fig1_size'])
fig.subplots_adjust(left=0.175, right=0.975, top=0.955, bottom=0.205)


def kfmt(v):
    return '0' if v == 0 else ('%dk' % (v // 1000) if v % 1000 == 0
                               else format(v, ','))


if STYLE['a_mode'] == 'delta':
    # 只画累计节省：两条几乎重合的曲线 -> 一条阶梯曲线
    delta = [a - b for a, b in zip(t118, t115)]
    fill = ax.fill_between(idx, 0, delta, step='post', lw=0,
                           color=C1, alpha=0.13)
    curve, = ax.step(idx, delta, where='post', color=C1,
                     label='$\\Delta(i)=t_{\mathrm{halt}}^{as}(i)-t_{\mathrm{halt}}^{op}(i)$')
    if STYLE['rasterize']:
        fill.set_rasterized(True)
        curve.set_rasterized(True)
    ax.set_ylabel('steps saved $\\Delta(i)$')
    ax.set_ylim(0, DT * 1.25)
    ax.annotate('$\\Delta=%s$ steps\n$=%.2f\\%%$ of $t_{118}$'
                % (format(DT, ','), 100.0 * DT / THALT1),
                xy=(n, DT),
                xytext=(n * STYLE['a_delta_annot_xy'][0],
                        DT * STYLE['a_delta_annot_xy'][1]),
                ha='right', va='center', fontsize=STYLE['font_annot'],
                color=INK,
                arrowprops=dict(arrowstyle='-', lw=STYLE['lw_annot'],
                                color=INK, shrinkA=1, shrinkB=2))
    ax.text(*STYLE['a_delta_slope_xy'],
            'slope $\\approx%.3f$ step per instruction' % (DT / n),
            transform=ax.transAxes, fontsize=STYLE['font_annot'], color=INK)
    ys = list(range(0, int(DT * 1.25), 1000))
else:
    fill = ax.fill_between(idx, t115, t118, step='post', lw=0,
                           color=STYLE['c_band'],
                           alpha=STYLE['c_gap_alpha'])
    l1, = ax.step(idx, t118, where='post', color=C1, ls=STYLE['ls_pi1'],
                  label='$\\Pi_{as}$')
    l2, = ax.step(idx, t115, where='post', color=C2, ls=STYLE['ls_pi2'],
                  label='$\\Pi_{op}$')
    if STYLE['rasterize']:
        for art in (fill, l1, l2):
            art.set_rasterized(True)

    if STYLE['a_show_gap']:
        xg = n * STYLE['a_gap_x']
        cap = n * 0.012
        ax.plot([xg, xg], [THALT2, THALT1], color=INK, lw=STYLE['lw_annot'],
                clip_on=False, zorder=4)
        for yy in (THALT1, THALT2):
            ax.plot([xg - cap, xg + cap], [yy, yy], color=INK,
                    lw=STYLE['lw_annot'], clip_on=False, zorder=4)
        ax.text(xg - cap - n * 0.008,
                (THALT1 + THALT2) / 2 + STYLE['a_gap_dy'],
                '$\\Delta t=%s$\nat $l_{22}$' % format(DT, ','),
                ha='right', va='center', fontsize=STYLE['font_annot'],
                color=INK)

    ax.set_ylabel('network update step $t$')
    ylim_top = STYLE['a_ylim_top'] or THALT1 * 1.05
    ax.set_ylim(0, ylim_top)
    ys = list(range(0, int(ylim_top), STYLE['a_ytick_step']))
    ax.legend(loc='upper left', frameon=False, handlelength=1.6,
              borderaxespad=0.3)

ax.set_xlabel('$M_u$ instruction index $i$')
ax.set_xlim(0, n)
xs = list(range(0, n + 1, STYLE['a_xtick_step']))
ax.set_xticks(xs)
_hz = STYLE['a_hide_zero']


def _lab(v, axis):
    return '' if (v == 0 and _hz in (axis, 'both')) else kfmt(v)


ax.set_xticklabels([_lab(v, 'x') for v in xs])
ax.set_yticks(ys)
ax.set_yticklabels([_lab(v, 'y') for v in ys])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

os.makedirs('figs', exist_ok=True)
fig.savefig('figs/fig_mu323_timeline.pdf')
fig.savefig('figs/fig_mu323_timeline.png', dpi=STYLE['dpi'])
plt.close(fig)

# ======================================================================
# fig. 2: halt and the three emissions (halt-relative time)
# ======================================================================
fig, ax = plt.subplots(figsize=STYLE['fig2_size'])
fig.subplots_adjust(left=0.135, right=0.975, top=0.99, bottom=0.235)

tracks = [(1.0, THALT1, C1, STYLE['ls_pi1'], '\\Pi_1', REL1),
          (0.0, THALT2, C2, STYLE['ls_pi2'], '\\Pi_2', REL2)]
xmax = max(REL1 + REL2) + 0.8
for y, thalt, c, ls, name, rel in tracks:
    ax.plot([0, xmax], [y, y], color=c, lw=0.7, alpha=0.55, ls=ls, zorder=1)
    ax.plot([0], [y], marker='s', color=INK,
            ms=STYLE['b_marker_ms'], zorder=3)
    ax.text(0, y - 0.13, format(thalt, ','), ha='center', va='top',
            fontsize=STYLE['font_annot'], color=INK)
    ax.plot(rel, [y] * len(rel), ls='none', marker='o', color=c,
            ms=STYLE['b_marker_ms'], zorder=3)
    for xr, te in zip(rel, [thalt + d for d in rel]):
        ax.text(xr, y + STYLE['b_time_label_dy'], format(te, ','),
                ha='center', va='bottom', fontsize=STYLE['font_annot'],
                color=c)

yb = tracks[0][0] + STYLE['b_bracket_dy']
ax.annotate('', xy=(REL1[1], yb), xytext=(REL1[0], yb),
            arrowprops=dict(arrowstyle='<->', color=INK,
                            lw=STYLE['lw_annot']))
ax.text((REL1[0] + REL1[1]) / 2, yb + 0.10,
        '$1=r_0$', ha='center', va='bottom',
        fontsize=STYLE['font_annot'], color=INK)

ax.set_xlabel('time relative to the halt instruction $l_{22}$ (steps)')
ax.set_xlim(-0.55, xmax + 0.3)
ax.set_ylim(-0.62, 1.80)
ax.set_yticks([0, 1])
ax.set_yticklabels(['$\\Pi_2$', '$\\Pi_1$'])
ax.set_xticks(range(0, int(xmax) + 1))
ax.spines['left'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='y', length=0)

if EMIT_NOTE:
    ax.text(0.99, 0.12, EMIT_NOTE.strip(), transform=ax.transAxes,
            ha='right', va='bottom', fontsize=STYLE['font_annot'] - 0.5,
            color=INK, style='italic')

fig.savefig('figs/fig_mu323_halting.pdf')
fig.savefig('figs/fig_mu323_halting.png', dpi=STYLE['dpi'])
plt.close(fig)

print('rows = %d | halt Pi1 = %d, Pi2 = %d, dt = %d (%s of halt step)'
      % (n, THALT1, THALT2, DT, '%.2f%%' % (100.0 * DT / THALT1)))
print('emissions Pi1 = %s | Pi2 = %s%s'
      % ([THALT1 + d for d in REL1], [THALT2 + d for d in REL2], EMIT_NOTE))
print('saved figs/fig_mu323_timeline.pdf/.png and figs/fig_mu323_halting.pdf/.png')
