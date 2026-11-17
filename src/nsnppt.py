

from collections import defaultdict
import random


class NSNPPT:
    def __init__(self):
        self.x = {}                    # neuron -> variable value
        self.funcs = {}                # neuron -> [(coeff, const, T)]
        self.plain = set()             # neurons without functions
        self.syn = []
        self.out_edges = defaultdict(list)
        self.in_edges = defaultdict(list)
        self.out_name = None
        self.ext = defaultdict(list)   # step -> [(neuron, value)]
        self.nondet_log = []

    # -- construction ----------------------------------------------------
    def neuron(self, name, init=0.0):
        self.x.setdefault(name, float(init))
        return name

    def func(self, name, coeff=1.0, const=0.0, T=1.0):
        self.x.setdefault(name, 0.0)
        self.plain.discard(name)
        self.funcs.setdefault(name, []).append((float(coeff), float(const), float(T)))

    def nofunc(self, name, init=0.0):
        self.x[name] = float(init)
        self.plain.add(name)
        self.funcs.pop(name, None)

    def synapse(self, src, dst, w):
        assert src != dst, "NSNPPT synapses require i != j (%s)" % src
        self.syn.append((src, dst, float(w)))
        self.out_edges[src].append((dst, float(w)))
        self.in_edges[dst].append((src, float(w)))

    def feed(self, step, name, val=1.0):
        self.ext[step].append((name, float(val)))

    # -- one synchronous step --------------------------------------------
    def step(self, t, rng=None):
        for (n, v) in self.ext.pop(t, []):
            self.x[n] += v
        fired = {}
        for name, fl in self.funcs.items():
            if len(fl) > 1:
                f = rng.choice(fl) if rng is not None else fl[0]
                self.nondet_log.append((t, name, f))
            else:
                f = fl[0]
            coeff, const, T = f
            pv = coeff * self.x[name] + const
            self.x[name] = 0.0            # zero-on-production (always)
            if pv >= T:
                fired[name] = pv
        incoming = defaultdict(float)
        for name, pv in fired.items():
            for (dst, w) in self.out_edges[name]:
                incoming[dst] += w * pv
        for dst, val in incoming.items():
            if dst in self.x:
                self.x[dst] += val
        env = fired.get(self.out_name, 0.0) if self.out_name else 0.0
        return fired, env

    def run(self, steps, rng=None):
        spikes = []
        states = []
        for t in range(steps):
            fired, env = self.step(t, rng)
            if env != 0:
                spikes.append((t, env))
            states.append(dict(self.x))
        return spikes, states


# ======================================================================
# module builders (exact wiring from Figs. 1, 3, 6, 9, 11, 12, 13)
# ======================================================================

def register_pair(net, r):
    """Register r: sigma_r1/sigma_r2, f = x|1, mutual +1 (value circulates)."""
    a, b = 'r%d_1' % r, 'r%d_2' % r
    net.neuron(a); net.neuron(b)
    net.func(a); net.func(b)
    net.synapse(a, b, 1)
    net.synapse(b, a, 1)
    return a, b


def add_det(net, label, r, lj):
    """Deterministic ADD module (Fig. 11): li:(ADD(r), lj)."""
    net.neuron(label); net.func(label)
    net.synapse(label, 'r%d_1' % r, 1)
    net.synapse(label, 'r%d_2' % r, 1)
    net.synapse(label, lj, 1)


def add_gen(net, label, r, lj, lk):
    """Nondeterministic ADD module (Fig. 1): li:(ADD(r), lj, lk)."""
    i1, i2 = label + '_1', label + '_2'
    net.neuron(label); net.func(label)
    net.neuron(i1)
    net.func(i1, coeff=1.0, T=1.0)      # f  = x |1
    net.func(i1, coeff=1.0, T=2.0)      # f' = x |2  (nondeterministic branch)
    net.neuron(i2); net.func(i2)
    net.synapse(label, 'r%d_1' % r, 1)
    net.synapse(label, 'r%d_2' % r, 1)
    net.synapse(label, i1, 1)
    net.synapse(label, i2, 1)
    net.synapse(i1, lj, 1)
    net.synapse(i1, lk, -1)
    net.synapse(i2, lk, 1)


def sub_module(net, label, r, lj, lk):
    """SUB module (Fig. 3).  Also used inside the ADD-SUB fusion (Fig. 13)."""
    ra, rb = 'r%d_1' % r, 'r%d_2' % r
    i1, i2, i3, i4, i5 = (label + '_%d' % k for k in range(1, 6))
    net.neuron(label); net.func(label)
    net.neuron(i1); net.func(i1, coeff=1.0, const=-1.0, T=1.0)   # (x-1)|1
    net.neuron(i2); net.func(i2)
    net.neuron(i3); net.func(i3)
    net.neuron(i4); net.func(i4, coeff=0.5)                      # (1/2 x)|1
    net.neuron(i5); net.func(i5)
    net.synapse(label, ra, -1)
    net.synapse(label, rb, -1)
    net.synapse(label, i2, 1)
    net.synapse(label, i3, 1)
    net.synapse(ra, i1, 1)
    net.synapse(rb, i2, 1)
    net.synapse(i1, i4, -1)
    net.synapse(i1, i5, 1)
    net.synapse(i2, i4, 1)
    net.synapse(i2, i5, -1)
    net.synapse(i3, i5, 2)
    net.synapse(i4, lj, 1)
    net.synapse(i5, lk, 1)


def output_module(net, halt_label, r):
    """OUTPUT module (Fig. 6) reading register pair of register r."""
    ra, rb = 'r%d_1' % r, 'r%d_2' % r
    net.neuron(halt_label); net.func(halt_label)
    for k in range(1, 7):
        net.neuron('h%d' % k)
    net.neuron('out'); net.func('out')
    net.out_name = 'out'
    for k in range(1, 7):
        net.func('h%d' % k)
    net.funcs['h5'] = [(1.0, -1.0, 1.0)]           # f_h5 = (x-1)|1 (replace, not append)
    net.synapse(halt_label, ra, -1)
    net.synapse(halt_label, rb, -1)
    net.synapse(halt_label, 'h1', 1)
    net.synapse(halt_label, 'h2', 1)
    net.synapse(halt_label, 'h3', 1)
    net.synapse(halt_label, 'h4', -1)
    net.synapse(halt_label, 'h5', -1)
    net.synapse('h1', 'out', 1)
    net.synapse('h2', 'h3', 1)
    net.synapse('h3', 'h2', 1)
    net.synapse('h3', ra, -1)
    net.synapse('h3', rb, -1)
    net.synapse('h3', 'h4', -1)
    net.synapse('h3', 'h5', -1)
    net.synapse('h3', 'h6', 1)
    net.synapse(ra, 'h4', 1)
    net.synapse(rb, 'h5', 1)
    net.synapse('h4', 'h6', -1)
    net.synapse('h5', 'h6', 1)
    net.synapse('h6', 'out', 1)
    net.synapse('h6', 'h2', -1)
    net.synapse('h6', 'h3', -1)


def input_module(net):
    """INPUT module (Fig. 9).  External spike train feeds sigma_in."""
    net.neuron('in'); net.func('in')
    for k in range(1, 7):
        net.neuron('in%d' % k)
    net.func('in1', T=-1.0)             # f = x |-1
    net.func('in2', T=-1.0)             # f = x |-1
    net.func('in3', coeff=0.5)          # f = 1/2 x |1
    net.func('in4')                     # f = x |1
    net.func('in5')                     # f = x |1
    net.func('in6', coeff=0.5)          # f = 1/2 x |1
    net.synapse('in', 'in1', -1)
    net.synapse('in', 'in2', -1)
    net.synapse('in', 'in3', 1)
    net.synapse('in', 'in6', 1)
    net.synapse('in1', 'in2', 1)        # pv = -1 sent over w=+1: "exchange -1"
    net.synapse('in2', 'in1', 1)
    net.synapse('in2', 'r1_1', -1)      # fires -1, w -1 => +1 into register 1
    net.synapse('in2', 'r1_2', -1)
    net.synapse('in1', 'in3', -1)       # fires -1, w -1 => +1 into in3
    net.synapse('in3', 'in4', 1)
    net.synapse('in3', 'in5', 1)
    net.synapse('in4', 'in5', 1)
    net.synapse('in5', 'in4', 1)
    net.synapse('in4', 'in1', -2)
    net.synapse('in4', 'in2', -2)
    net.synapse('in5', 'r2_1', 1)
    net.synapse('in5', 'r2_2', 1)
    net.synapse('in5', 'in6', 1)
    net.synapse('in6', 'in4', -1)
    net.synapse('in6', 'in5', -1)
    net.synapse('in6', 'l0', 1)


# ======================================================================
# Korec's universal register machine Mu (Fig. 8)
# ======================================================================

KOREC = [
    ('l0',  'SUB', (1, 1, 2)),
    ('l1',  'ADD', (7, 0)),
    ('l2',  'ADD', (6, 3)),
    ('l3',  'SUB', (5, 2, 4)),
    ('l4',  'SUB', (6, 5, 3)),
    ('l5',  'ADD', (5, 6)),
    ('l6',  'SUB', (7, 7, 8)),
    ('l7',  'ADD', (1, 4)),
    ('l8',  'SUB', (6, 9, 0)),
    ('l9',  'ADD', (6, 10)),
    ('l10', 'SUB', (4, 0, 11)),
    ('l11', 'SUB', (5, 12, 13)),
    ('l12', 'SUB', (5, 14, 15)),
    ('l13', 'SUB', (2, 18, 19)),
    ('l14', 'SUB', (5, 16, 17)),
    ('l15', 'SUB', (3, 18, 20)),
    ('l16', 'ADD', (4, 11)),
    ('l17', 'ADD', (2, 21)),
    ('l18', 'SUB', (4, 0, 22)),
    ('l19', 'SUB', (0, 0, 18)),
    ('l20', 'ADD', (0, 0)),
    ('l21', 'ADD', (3, 18)),
    ('l22', 'HALT', ()),
]


def run_mu(hx, y, max_steps=200000):
    """Direct execution of Mu with registers 1 = hx, 2 = y; result in R0."""
    R = [0] * 8
    R[1], R[2] = hx, y
    lab = 'l0'
    n = 0
    seq = []
    while lab != 'l22':
        kind, args = next((k, a) for (l, k, a) in KOREC if l == lab)
        if kind == 'ADD':
            R[args[0]] += 1
            lab = 'l%d' % args[1]
        else:
            if R[args[0]] > 0:
                R[args[0]] -= 1
                lab = 'l%d' % args[1]
            else:
                lab = 'l%d' % args[2]
        n += 1
        seq.append(lab)
        if n > max_steps:
            return None, n, seq
    return R[0], n, seq


# ======================================================================
# Theorem 2: universal system Pi_u  (118 neurons; 115 optimized)
# ======================================================================

def build_Piu(optimized=True):
    net = NSNPPT()
    # l6/l10/l21 disappear; l5/l9/l17 are rebuilt as fused modules below,
    # so the plain loop must skip all six.
    dropped = {'l5', 'l6', 'l9', 'l10', 'l17', 'l21'} if optimized else set()

    for r in range(8):
        register_pair(net, r)
    input_module(net)
    output_module(net, 'l22', 0)

    for (lab, kind, args) in KOREC:
        if lab in dropped:
            continue
        if kind == 'ADD':
            add_det(net, lab, args[0], 'l%d' % args[1])
        elif kind == 'SUB':
            sub_module(net, lab, args[0], 'l%d' % args[1], 'l%d' % args[2])
        # HALT handled by output_module (sigma_l22)

    if optimized:
        # ADD-ADD (Fig. 12): l17:(ADD(2),l21), l21:(ADD(3),l18)
        net.neuron('l17'); net.func('l17')
        net.synapse('l17', 'r2_1', 1)
        net.synapse('l17', 'r2_2', 1)
        net.synapse('l17', 'r3_1', 1)
        net.synapse('l17', 'r3_2', 1)
        net.synapse('l17', 'l18', 1)
        # ADD-SUB (Fig. 13): l5:(ADD(5),l6), l6:(SUB(7),l7,l8).
        # li activates the SUB machinery (i2, i3) and decrements r; the ADD's
        # +1 on r5 is delivered by whichever of i4/i5 fires (both branches).
        net.neuron('l5'); net.func('l5')
        net.synapse('l5', 'r7_1', -1)
        net.synapse('l5', 'r7_2', -1)
        i1, i2, i3, i4, i5 = ('l5_%d' % k for k in range(1, 6))
        for nm in (i1, i2, i3, i4, i5):
            net.neuron(nm)
        net.func(i1, coeff=1.0, const=-1.0, T=1.0)
        net.func(i2); net.func(i3)
        net.func(i4, coeff=0.5)
        net.func(i5)
        net.synapse('l5', i2, 1)
        net.synapse('l5', i3, 1)
        net.synapse('r7_1', i1, 1)
        net.synapse('r7_2', i2, 1)
        net.synapse(i1, i4, -1)
        net.synapse(i1, i5, 1)
        net.synapse(i2, i4, 1)
        net.synapse(i2, i5, -1)
        net.synapse(i3, i5, 2)
        net.synapse(i4, 'r5_1', 1)
        net.synapse(i4, 'r5_2', 1)
        net.synapse(i4, 'l7', 1)
        net.synapse(i5, 'r5_1', 1)
        net.synapse(i5, 'r5_2', 1)
        net.synapse(i5, 'l8', 1)
        # ADD-SUB (Fig. 13): l9:(ADD(6),l10), l10:(SUB(4),l0,l11)
        net.neuron('l9'); net.func('l9')
        net.synapse('l9', 'r4_1', -1)
        net.synapse('l9', 'r4_2', -1)
        i1, i2, i3, i4, i5 = ('l9_%d' % k for k in range(1, 6))
        for nm in (i1, i2, i3, i4, i5):
            net.neuron(nm)
        net.func(i1, coeff=1.0, const=-1.0, T=1.0)
        net.func(i2); net.func(i3)
        net.func(i4, coeff=0.5)
        net.func(i5)
        net.synapse('l9', i2, 1)
        net.synapse('l9', i3, 1)
        net.synapse('r4_1', i1, 1)
        net.synapse('r4_2', i2, 1)
        net.synapse(i1, i4, -1)
        net.synapse(i1, i5, 1)
        net.synapse(i2, i4, 1)
        net.synapse(i2, i5, -1)
        net.synapse(i3, i5, 2)
        net.synapse(i4, 'r6_1', 1)
        net.synapse(i4, 'r6_2', 1)
        net.synapse(i4, 'l0', 1)
        net.synapse(i5, 'r6_1', 1)
        net.synapse(i5, 'r6_2', 1)
        net.synapse(i5, 'l11', 1)

    order = sorted(net.x, key=lambda s: (s.split('_')[0], len(s), s))
    return net, order


# ======================================================================
# Theorem 1: generative system Pi_M (nondeterministic ADD, register 1 out)
# ======================================================================

def build_generator(instructions, n_registers):
    """instructions: list of (label, kind, args) with
       ADD: (r, lj, lk)   SUB: (r, lj, lk)   HALT: ()."""
    net = NSNPPT()
    for r in range(1, n_registers + 1):
        register_pair(net, r)
    for (lab, kind, args) in instructions:
        if kind == 'HALT':
            output_module(net, lab, 1)     # generative output register = 1
    for (lab, kind, args) in instructions:
        if kind == 'ADD':
            add_gen(net, lab, args[0], args[1], args[2])
        elif kind == 'SUB':
            sub_module(net, lab, args[0], args[1], args[2])
    order = sorted(net.x, key=lambda s: (s.split('_')[0], len(s), s))
    return net, order
