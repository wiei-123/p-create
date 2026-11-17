
import io, re
from nsnppt import build_Piu, KOREC

# ----------------------------------------------------------------- templates
TPL = {
'REGISTERS': """'register value n <=> both variables = n (paper Fig. 6/8)'
@nsyn(r{r}_1, r{r}_2) = 1;  @nsyn(r{r}_2, r{r}_1) = 1;
@nfunc(r{r}_1) = 1*x+0 |1;  @nfunc(r{r}_2) = 1*x+0 |1;""",
'INPUT': """'paper Fig. 9'
@nsyn(in, in1) = -1;  @nsyn(in, in2) = -1;  @nsyn(in, in3) = 1;   @nsyn(in, in6) = 1;
@nsyn(in1, in2) = 1;  @nsyn(in2, in1) = 1;
@nsyn(in2, r{r1}_1) = -1;  @nsyn(in2, r{r1}_2) = -1;   'w=-1, pv=-1: register 1 gets +1'
@nsyn(in1, in3) = -1;
@nsyn(in3, in4) = 1;  @nsyn(in3, in5) = 1;
@nsyn(in4, in5) = 1;  @nsyn(in5, in4) = 1;
@nsyn(in4, in1) = -2; @nsyn(in4, in2) = -2;
@nsyn(in5, r{r2}_1) = 1;  @nsyn(in5, r{r2}_2) = 1;  @nsyn(in5, in6) = 1;
@nsyn(in6, in4) = -1; @nsyn(in6, in5) = -1; @nsyn(in6, l{lh}) = 1;
@nfunc(in) = 1*x+0 |1;   @nfunc(in1) = 1*x+0 |-1;  @nfunc(in2) = 1*x+0 |-1;
@nfunc(in3) = 0.5*x+0 |1; @nfunc(in4) = 1*x+0 |1; @nfunc(in5) = 1*x+0 |1;
@nfunc(in6) = 0.5*x+0 |1;""",
'OUTPUT': """'paper Fig. 6, halt neuron l22, reads register {r}'
@nsyn(l22, r{r}_1) = -1;  @nsyn(l22, r{r}_2) = -1;
@nsyn(l22, h1) = 1;  @nsyn(l22, h2) = 1;  @nsyn(l22, h3) = 1;
@nsyn(l22, h4) = -1; @nsyn(l22, h5) = -1;
@nsyn(h1, out) = 1;
@nsyn(h2, h3) = 1;  @nsyn(h3, h2) = 1;
@nsyn(h3, r{r}_1) = -1; @nsyn(h3, r{r}_2) = -1;
@nsyn(h3, h4) = -1;  @nsyn(h3, h5) = -1;  @nsyn(h3, h6) = 1;
@nsyn(r{r}_1, h4) = 1;  @nsyn(r{r}_2, h5) = 1;
@nsyn(h4, h6) = -1;  @nsyn(h5, h6) = 1;
@nsyn(h6, out) = 1;  @nsyn(h6, h2) = -1;  @nsyn(h6, h3) = -1;
@nfunc(l22) = 1*x+0 |1;  @nfunc(out) = 1*x+0 |1;
@nfunc(h1) = 1*x+0 |1;  @nfunc(h2) = 1*x+0 |1;  @nfunc(h3) = 1*x+0 |1;
@nfunc(h4) = 1*x+0 |1;  @nfunc(h5) = 1*x-1 |1;  @nfunc(h6) = 1*x+0 |1;""",
'ADD': """'paper Fig. 11'
@nsyn(l{i}, r{r}_1) = 1;  @nsyn(l{i}, r{r}_2) = 1;  @nsyn(l{i}, l{j}) = 1;
@nfunc(l{i}) = 1*x+0 |1;""",
'SUB': """'paper Fig. 3'
@nsyn(l{i}, r{r}_1) = -1;  @nsyn(l{i}, r{r}_2) = -1;
@nsyn(l{i}, l{i}_2) = 1;  @nsyn(l{i}, l{i}_3) = 1;
@nsyn(r{r}_1, l{i}_1) = 1;  @nsyn(r{r}_2, l{i}_2) = 1;
@nsyn(l{i}_1, l{i}_4) = -1;  @nsyn(l{i}_1, l{i}_5) = 1;
@nsyn(l{i}_2, l{i}_4) = 1;   @nsyn(l{i}_2, l{i}_5) = -1;
@nsyn(l{i}_3, l{i}_5) = 2;
@nsyn(l{i}_4, l{j}) = 1;  @nsyn(l{i}_5, l{k}) = 1;
@nfunc(l{i}) = 1*x+0 |1;    @nfunc(l{i}_1) = 1*x-1 |1;
@nfunc(l{i}_2) = 1*x+0 |1;  @nfunc(l{i}_3) = 1*x+0 |1;
@nfunc(l{i}_4) = 0.5*x+0 |1; @nfunc(l{i}_5) = 1*x+0 |1;""",
'ADD_ADD': """'paper Fig. 12, fused pair l17+l21'
@nsyn(l{i}, r{r1}_1) = 1;  @nsyn(l{i}, r{r1}_2) = 1;
@nsyn(l{i}, r{r2}_1) = 1;  @nsyn(l{i}, r{r2}_2) = 1;
@nsyn(l{i}, l{j}) = 1;
@nfunc(l{i}) = 1*x+0 |1;""",
'ADD_SUB': """'paper Fig. 13, fused pair l{i}+l{g}: ADD({r_add}) + SUB({r_sub})'
@nsyn(l{i}, r{r_sub}_1) = -1;  @nsyn(l{i}, r{r_sub}_2) = -1;
@nsyn(l{i}, l{i}_2) = 1;  @nsyn(l{i}, l{i}_3) = 1;
@nsyn(r{r_sub}_1, l{i}_1) = 1;  @nsyn(r{r_sub}_2, l{i}_2) = 1;
@nsyn(l{i}_1, l{i}_4) = -1;  @nsyn(l{i}_1, l{i}_5) = 1;
@nsyn(l{i}_2, l{i}_4) = 1;   @nsyn(l{i}_2, l{i}_5) = -1;
@nsyn(l{i}_3, l{i}_5) = 2;
@nsyn(l{i}_4, r{r_add}_1) = 1;  @nsyn(l{i}_4, r{r_add}_2) = 1;  @nsyn(l{i}_4, l{j}) = 1;
@nsyn(l{i}_5, r{r_add}_1) = 1;  @nsyn(l{i}_5, r{r_add}_2) = 1;  @nsyn(l{i}_5, l{k}) = 1;
@nfunc(l{i}) = 1*x+0 |1;    @nfunc(l{i}_1) = 1*x-1 |1;
@nfunc(l{i}_2) = 1*x+0 |1;  @nfunc(l{i}_3) = 1*x+0 |1;
@nfunc(l{i}_4) = 0.5*x+0 |1; @nfunc(l{i}_5) = 1*x+0 |1;""",
}

# calls in main(): (template, params, comment)
CALLS = [('REGISTERS', {}, '8 register pairs (r = 0..7)'),
         ('INPUT', {'r1': 1, 'r2': 2, 'lh': 0}, 'paper Fig. 9'),
         ('OUTPUT', {'r': 0}, 'reads register 0, paper Fig. 6')]
for (lab, kind, args) in KOREC:
    if lab in ('l5', 'l6', 'l9', 'l10', 'l17', 'l21', 'l22'):
        continue
    if kind == 'ADD':
        CALLS.append(('ADD', {'i': int(lab[1:]), 'r': args[0], 'j': args[1]},
                      '%s (Fig. 11)' % lab))
    else:
        CALLS.append(('SUB', {'i': int(lab[1:]), 'r': args[0],
                              'j': args[1], 'k': args[2]},
                      '%s (Fig. 3)' % lab))
CALLS += [('ADD_ADD', {'i': 17, 'r1': 2, 'r2': 3, 'j': 18},
           'l17, fused pair l17+l21 (Fig. 12)'),
          ('ADD_SUB', {'i': 5, 'r_add': 5, 'r_sub': 7, 'j': 7, 'k': 8},
           'l5, fused pair l5+l6 (Fig. 13)'),
          ('ADD_SUB', {'i': 9, 'r_add': 6, 'r_sub': 4, 'j': 0, 'k': 11},
           'l9, fused pair l9+l10 (Fig. 13)')]

def expand(tplname, params):
    s = TPL[tplname]
    for k, v in params.items():
        s = s.replace('{%s}' % k, str(v))
    return s

def expand_all():
    syn, funcs = set(), {}
    def grab(text):
        for m in re.finditer(r'@nsyn\((\S+), (\S+)\) = (-?\d+)', text):
            syn.add((m.group(1), m.group(2), int(m.group(3))))
        for m in re.finditer(r'@nfunc\((\S+)\) = ([^|]+)\|(-?\d+)', text):
            body = m.group(2).replace(' ', '')
            c, _, k = body.partition('*x')
            coeff = float(c) if '*' in body else float(body)
            const = float(k) if k else 0.0
            funcs[m.group(1)] = (coeff, const, float(m.group(3)))
    for (tpl, params, _) in CALLS:
        if tpl == 'REGISTERS':
            for r in range(8):
                grab(expand(tpl, {'r': r}))
        else:
            grab(expand(tpl, params))
    return syn, funcs

def main():
    net, order = build_Piu(optimized=True)

    # ---- consistency check: templates must reproduce the built net ----
    syn_t, func_t = expand_all()
    syn_real = set((s, d, int(w)) for (s, d, w) in net.syn)
    func_real = {n: ts[0] for n, ts in net.funcs.items()}   # Pi_u: all simple
    assert syn_t == syn_real, 'synapse mismatch: %s' % (
        (syn_t ^ syn_real))
    assert func_t == func_real, 'function mismatch: %s' % (set(func_t) ^ set(func_real))
    neurons_t = sorted(set([n for s in syn_t for n in s[:2]] + list(func_t)))
    assert neurons_t == sorted(order), 'neuron mismatch'

    # ---- emit the factored listing ----
    L = []
    n = 0
    def line(s=''):
        nonlocal n
        n += 1
        L.append('%3d  %s' % (n, s))

    line("@model <numerical_spiking_systems>")
    line("def main(){")
    line()
    line("@mu = {")
    for i, (lab, kind, args) in enumerate(KOREC):
        if kind == 'ADD':
            body = 'ADD(%d), l%d' % (args[0], args[1])
        elif kind == 'SUB':
            body = 'SUB(%d), l%d, l%d' % (args[0], args[1], args[2])
        else:
            body = 'HALT'
        line("    %s: (%s)%s" % (lab, body, ',' if i < len(KOREC) - 1 else ''))
    line("}  'Korec universal register machine Mu (paper Fig. 8)'")
    line("'registers: 8 pairs {sigma_r1, sigma_r2}, f = x|1, mutual +1 (paper Fig. 6/8)'")
    line("@all = 0  'initial values: every variable is zero'")
    line("@in: spike train 1 0^{h(x)-1} 1 0^{y-1} 1 at steps 1, h(x)+1, h(x)+y+1")
    line()
    line("'Pi_u construction: one call per instruction (+ fused pairs)'")
    for (tpl, params, comment) in CALLS:
        args = ', '.join(str(v) for v in params.values())
        line("call %s(%s);   '%s'" % (tpl, args, comment))
    line("}")
    line()
    seen = set()
    for (tpl, params, comment) in CALLS:
        if tpl in seen:
            continue
        seen.add(tpl)
        line("def %s(%s)" % (tpl, ', '.join(params)))
        line("{")
        for ln in TPL[tpl].split('\n'):
            line('    ' + ln)
        line("}")
        line()
    line("}  'end of Pi_u: %d neurons, %d synapses -- Theorem 2'"
         % (len(order), len(net.syn)))

    out = 'nsnppt_plingua_style.txt'
    io.open(out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('%s written: %d lines (factored). consistency check: synapses=%d,'
          ' functions=%d, neurons=%d -- all match build_Piu' %
          (out, n, len(syn_t), len(func_t), len(neurons_t)))

if __name__ == '__main__':
    main()
