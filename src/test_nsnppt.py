from nsnppt import *

PASS = 0
FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  [OK]   %s %s" % (name, detail))
    else:
        FAIL += 1
        print("  [FAIL] %s %s" % (name, detail))


# ---------------------------------------------------------------- SUB module
def test_sub():
    print("== SUB module (Fig. 3) ==")
    instrs = [('l0', 'SUB', (2, 'l1', 'l2')),
              ('l1', 'ADD', (1, 'l1', 'l1')),
              ('l2', 'ADD', (1, 'l2', 'l2')),
              ('lh', 'HALT', ())]
    for vr in (0, 1, 2, 5):
        net, order = build_generator(instrs, 2)
        net.neurons = None if False else None
        # seed: x_l0 = 1, register 2 = vr
        net.x['l0'] = 1.0
        net.x['r2_1'] = float(vr)
        net.x['r2_2'] = float(vr)
        for t in range(5):
            net.step(t)
        xl1 = net.x['l1']
        xl2 = net.x['l2']
        xr = net.x['r2_1']
        want_branch = 'l1' if vr > 0 else 'l2'
        got_branch = 'l1' if xl1 == 1 else ('l2' if xl2 == 1 else '?')
        want_r = vr - 1 if vr > 0 else 0
        check("SUB vr=%d" % vr, got_branch == want_branch and xr == want_r,
              "branch %s (want %s), x_r2_1=%g (want %g)" %
              (got_branch, want_branch, xr, want_r))


# ---------------------------------------------------------------- ADD module
def test_add():
    print("== ADD module (Fig. 1, generative; Fig. 11 deterministic) ==")
    # deterministic ADD (Pi_u style): l1 fires at step 0 -> r7 += 1, l0 = 1.
    # (l0 itself fires at step 1, so the assertion must look at step 1's end.)
    net, order = build_Piu(optimized=True)
    for n in net.x:
        net.x[n] = 0.0
    net.x['l1'] = 1.0              # l1: (ADD(7), l0)
    net.x['r7_1'] = 3.0
    net.x['r7_2'] = 3.0
    net.step(0)
    check("ADD det: r7 = 4, l0 active",
          net.x['r7_1'] == 4.0 and net.x['l0'] == 1.0,
          "r7=%g l0=%g" % (net.x['r7_1'], net.x['l0']))

    # generative nondeterministic ADD: both branches over trials
    instrs = [('l0', 'ADD', (2, 'l0', 'l1')),
              ('l1', 'HALT', ())]
    branches = set()
    for trial in range(40):
        net, order = build_generator(instrs, 2)
        net.x['l0'] = 1.0
        rng = random.Random(trial)
        for t in range(4):
            net.step(t, rng)
        if net.x['l1'] == 1.0:
            branches.add('l1')
        elif net.x['l0'] == 1.0:
            branches.add('l0')
    check("ADD gen: nondeterministic branches", branches == {'l0', 'l1'},
          "seen: %s" % branches)


# ------------------------------------------------------------- OUTPUT module
def test_output():
    print("== OUTPUT module (Fig. 6) vs Figure 7 trace ==")
    instrs = [('lh', 'HALT', ())]
    for v1 in (1, 2, 5):
        net, order = build_generator(instrs, 1)
        # Figure 7 configuration at step t: the module's steady state under
        # register value v1 (h4 = h5 = v1, h6 = -1), with lh just active.
        net.x['lh'] = 1.0
        net.x['r1_1'] = float(v1)
        net.x['r1_2'] = float(v1)
        net.x['h4'] = float(v1)
        net.x['h5'] = float(v1)
        net.x['h6'] = -1.0
        spikes = []
        for t in range(v1 + 8):
            fired, env = net.step(t)
            if env != 0:
                spikes.append(t)
        # Fig. 7: out fires at t+2, t+v1+2 (interval = v1 = the result) and,
        # as the paper's own table shows (row t+v1+3, x_out = 1), once more
        # at t+v1+3 before everything resets to 0 at t+v1+4.
        want = [2, v1 + 2, v1 + 3]
        ok_mod = all(net.x[n] == 0 for n in
                     ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'out', 'lh'))
        check("OUTPUT v1=%d" % v1, spikes == want,
              "spikes %s (want %s)" % (spikes, want))
        check("OUTPUT v1=%d halt-zeros" % v1, ok_mod,
              "" if ok_mod else
              str({n: net.x[n] for n in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                                         'out', 'lh')}))


# -------------------------------------------------------------- INPUT module
def test_input():
    print("== INPUT module (Fig. 9) vs Figure 10 trace ==")
    hx, y = 3, 5
    net, order = build_Piu(optimized=True)
    for n in net.x:
        net.x[n] = 0.0
    feed = {1, hx + 1, hx + y + 1}
    # Figure 10 reference (x_in, x_11, x_12, x_21, x_22, x_in1, x_in2, x_in3,
    #                       x_in4, x_in5, x_in6, x_l0); y >= 3 keeps every
    # listed row distinct (for y <= 3 rows hx+3 and hx+y+1 coincide and the
    # paper's hx+y+1 template no longer applies).
    ref = {
        1: (1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        2: (0, 0, 0, 0, 0, -1, -1, 1, 0, 0, 1, 0),
        3: (0, 1, 1, 0, 0, -1, -1, 1, 0, 0, 0, 0),
        4: (0, 2, 2, 0, 0, -1, -1, 1, 0, 0, 0, 0),
        hx + 1: (1, hx - 1, hx - 1, 0, 0, -1, -1, 1, 0, 0, 0, 0),
        hx + 2: (0, hx, hx, 0, 0, -2, -2, 2, 0, 0, 1, 0),
        hx + 3: (0, hx, hx, 0, 0, 0, 0, 0, 1, 1, 0, 0),
        hx + 4: (0, hx, hx, 1, 1, -2, -2, 0, 1, 1, 1, 0),
        hx + 5: (0, hx, hx, 2, 2, -2, -2, 0, 1, 1, 1, 0),
        hx + y + 1: (1, hx, hx, y - 2, y - 2, -2, -2, 0, 1, 1, 1, 0),
        hx + y + 2: (0, hx, hx, y - 1, y - 1, -3, -3, 1, 1, 1, 2, 0),
        hx + y + 3: (0, hx, hx, y, y, -2, -2, 0, 0, 0, 1, 1),
    }
    names = ['in', 'r1_1', 'r1_2', 'r2_1', 'r2_2', 'in1', 'in2', 'in3',
             'in4', 'in5', 'in6', 'l0']
    all_ok = True
    for t in range(1, hx + y + 3):
        if t in feed:
            net.feed(t, 'in')
        net.step(t)
        # end state of step(t) equals Figure 10's row "at step t+1", except
        # that on arrival rows the incoming spike sits in sigma_in at the
        # start of step t+1 (it is consumed during that step).
        if (t + 1) in ref:
            got = tuple(net.x[n] for n in names)
            if (t + 1) in feed:
                got = (1.0,) + got[1:]
            want = ref[t + 1]
            ok = all(abs(g - w) < 1e-9 for (g, w) in zip(got, want))
            if not ok:
                all_ok = False
                print("    step %d MISMATCH got %s want %s" % (t, got, want))
    check("INPUT: Fig.10 trace match (hx=%d, y=%d)" % (hx, y), all_ok)


# ------------------------------------------------------- full system vs Mu
def test_full():
    print("== Full system Pi_u vs direct Mu execution ==")
    # Korec's h(x) encoding is defined only in Korec (1996); working inputs
    # were located by scanning the machine's behaviour (muorbit.py).
    #   Mu(323, 2) = 1  (the program "r0++; halt"), 31023 instructions;
    #   Mu(1, 2)   = 0  (halts in 57 instructions -- used for the exact
    #                    instruction-sequence check only, since the OUTPUT
    #                    module cannot represent v1 = 0).
    hx, y, ref, n_ref = 323, 2, 1, 31023
    assert run_mu(hx, y, max_steps=200000)[:2] == (ref, n_ref)

    for optimized in (True, False):
        net, order = build_Piu(optimized=optimized)
        for n in net.x:
            net.x[n] = 0.0
        net.feed(1, 'in')
        net.feed(hx + 1, 'in')
        net.feed(hx + y + 1, 'in')
        spikes = []
        instruction_events = []
        halt_snapshot = None
        settle_at = None
        t = 0
        limit = 40 * n_ref + 4000
        while t < limit and (len(spikes) < 2 or t < settle_at):
            before = {r: net.x['r%d_1' % r] for r in range(8)}
            fired, env = net.step(t)
            if 'l22' in fired:
                halt_snapshot = before
            instruction_events.extend(
                nm for nm in fired if nm.startswith('l') and '_' not in nm)
            if env != 0:
                spikes.append(t)
                if len(spikes) == 2:
                    settle_at = t + 6
            t += 1
        got = spikes[1] - spikes[0] if len(spikes) >= 2 else None
        check("Pi_u opt=%s Mu(%d,%d)" % (optimized, hx, y),
              got == ref,
              "out=%s want=%s (T=%d)" % (got, ref, t))
        expected_spikes = [64907, 64908, 64909] if not optimized else \
                          [61339, 61340, 61341]
        expected_steps = 64914 if not optimized else 61346
        check("Pi_u opt=%s complete output transient" % optimized,
              spikes == expected_spikes and t == expected_steps,
              "spikes=%s, T=%d" % (spikes, t))

        expected_events = ['l0'] + run_mu(hx, y, max_steps=200000)[2]
        if optimized:
            fused = {('l5', 'l6'), ('l9', 'l10'), ('l17', 'l21')}
            collapsed = []
            i = 0
            while i < len(expected_events):
                if i + 1 < len(expected_events) and \
                        (expected_events[i], expected_events[i + 1]) in fused:
                    collapsed.append(expected_events[i])
                    i += 2
                else:
                    collapsed.append(expected_events[i])
                    i += 1
            expected_events = collapsed
        check("Pi_u opt=%s Mu instruction-event trace" % optimized,
              instruction_events == expected_events,
              "events=%d, expected=%d" %
              (len(instruction_events), len(expected_events)))
        check("Pi_u opt=%s halt registers" % optimized,
              halt_snapshot == {0: 1.0, 1: 323.0, 2: 3.0, 3: 1.0,
                                4: 0.0, 5: 0.0, 6: 5.0, 7: 0.0},
              "snapshot=%s" % halt_snapshot)

    # instruction-sequence cross-check vs direct Mu (unoptimized build: no
    # fused modules, so the fired instruction sequence matches Mu exactly;
    # run_mu's seq lists each jump target, i.e. the executed instructions from
    # the second one on, plus the final l22; Pi_u additionally fires sigma_l0).
    hx2, y2 = 1, 2
    ref2, n_ref2, ref_seq = run_mu(hx2, y2, max_steps=200000)
    net, order = build_Piu(optimized=False)
    for n in net.x:
        net.x[n] = 0.0
    net.feed(1, 'in')
    net.feed(hx2 + 1, 'in')
    net.feed(hx2 + y2 + 1, 'in')
    instr_seq = []
    t = 0
    limit = 40 * n_ref2 + 2000
    while t < limit and len(instr_seq) < n_ref2 + 1:
        fired, env = net.step(t)
        for nm in fired:
            if nm.startswith('l') and '_' not in nm:
                instr_seq.append(nm)
        t += 1
    want_seq = ['l0'] + ref_seq
    check("Pi_u instruction sequence == Mu trace (%d instr)" % n_ref2,
          instr_seq == want_seq,
          "" if instr_seq == want_seq else
          "first diff at %d: %s vs %s" %
          (next((i for i, (a, b) in enumerate(zip(instr_seq, want_seq)) if a != b),
                min(len(instr_seq), len(want_seq))),
           instr_seq[-4:], want_seq[-4:]))


# ------------------------------------------------- generator (Theorem 1)
def test_generator():
    print("== Generative system Pi_M (Theorem 1): N(M) = {1,2,3,...} ==")
    instrs = [('l0', 'ADD', (2, 'l0', 'l1')),   # r2 += 1, loop or exit
              ('l1', 'SUB', (2, 'l2', 'l3')),   # r2 -= 1: >0 -> l2 else l3
              ('l2', 'ADD', (1, 'l1', 'l1')),   # r1 += 1, back to l1
              ('l3', 'ADD', (1, 'l4', 'l4')),   # r1 += 1, halt
              ('l4', 'HALT', ())]
    results = []
    for trial in range(60):
        net, order = build_generator(instrs, 2)
        net.x['l0'] = 1.0                  # activate the start instruction
        rng = random.Random(1000 + trial)
        spikes = []
        for t in range(400):
            fired, env = net.step(t, rng)
            if env != 0:
                spikes.append(t)
            if len(spikes) == 2:
                break
        if len(spikes) == 2:
            results.append(spikes[1] - spikes[0])
    # every trial halts; the machine's minimum output is 2 (the exit choice
    # itself consumes one ADD(2)), so generated values run over {2,3,4,...}.
    check("Pi_M generates {2,3,4,...}", len(results) == 60 and
          all(v >= 2 for v in results) and {2, 3} <= set(results),
          "generated set: %s" % sorted(set(results)))


if __name__ == '__main__':
    test_sub()
    test_add()
    test_output()
    test_input()
    test_full()
    test_generator()
    print("\nPASS=%d FAIL=%d" % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)
    print("ALL TESTS PASSED")
