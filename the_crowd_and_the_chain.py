"""The crowd and the chain, in standard gates. Companion to Quest for Entropy #19, Evidence Adds Up to a Fact.

    python the_crowd_and_the_chain.py

Standard Qiskit gates, qiskit.quantum_info statevectors, numpy. No hardware, no backend, no token, no network.
Every row is printed beside its closed form; the last line says whether all of them agree.

THE INSTRUMENT
  The look.  A witness W looks at a particle X with CRY(2 phi), control X, target W, W starting in |0>. The two
             conditional witness states have overlap cos(phi): phi = 90 degrees is a full copy (a CNOT up to phase),
             phi = 0 sees nothing.
  The particle.  P = qubit 0, prepared RY(pi/3) then P(pi/3): amplitudes sqrt(3/4) and sqrt(1/4) e^{i pi/3}, the
             bench's 3:1 preset. V0 = 2 |z0| |z1| = sqrt(3)/2 is its fringe visibility before any witness.
  The reading.  V = 2 |rho_01| of P with every witness traced out; F = V / V0 is the fraction of the fringe that
             came back.
  The wirings.  star: every witness looks at P. chain: W_1 looks at P, W_j at W_(j-1). ladder: P and the one before.
             braid: the two before. bitcoin: P and every earlier witness. random: two parents drawn from P and the
             earlier witnesses (numpy default_rng(259), a fresh wiring per d). A look with several parents turns the
             witness once where ANY parent reads 1.
  The undo.  A reached witness has its look undone by the inverse gate CRY(-2 phi) on the same control, last look
             first; a missed witness is traced out with its look left in place.
"""
import sys; sys.dont_write_bytecode = True
import math
from itertools import combinations

import numpy as np
import qiskit
from qiskit import QuantumCircuit
from qiskit.circuit.library import RYGate
from qiskit.quantum_info import DensityMatrix, Statevector, partial_trace

sys.stdout.reconfigure(newline="\n")

V0 = math.sqrt(3) / 2
TOL, TOL0 = 1e-10, 1e-12
PHI60 = math.pi / 3
KINDS = ("star", "chain", "ladder", "braid", "random", "bitcoin")

# ------------------------------------------------------------------------------------------------ the instrument
def look(qc, parents, w, phi):
    """Witness w looks at its parents. One parent: CRY(2 phi). Several: turn once where ANY parent reads 1."""
    if len(parents) == 1:
        qc.cry(2 * phi, parents[0], w)
    else:
        qc.ry(2 * phi, w)
        qc.append(RYGate(-2 * phi).control(len(parents), ctrl_state=0), [*parents, w])


def wiring(kind, d, phi, rng=None):
    """d witnesses as (parent qubits, witness qubit, phi). Labels: P = 1 here, W_j = j + 1; qubits are one lower."""
    links = []
    for k in range(d):
        t = k + 2
        earlier = list(range(2, t))
        if kind == "star":
            labels = [1]
        elif kind == "chain":
            labels = [earlier[-1]] if earlier else [1]
        elif kind == "ladder":
            labels = [1] + ([earlier[-1]] if earlier else [])
        elif kind == "braid":
            labels = ([1] + earlier)[-2:]
        elif kind == "bitcoin":
            labels = [1] + earlier
        elif kind == "random":
            pool = [1] + earlier
            labels = sorted(rng.choice(pool, size=min(2, len(pool)), replace=False).tolist())
        else:
            raise ValueError(kind)
        links.append((tuple(a - 1 for a in labels), k + 1, phi))
    return links


def fringe(links, missed=()):
    """V of P after the looks and the undo of every reached witness (last first); missed witnesses are traced out."""
    qc = QuantumCircuit(1 + len(links))
    qc.ry(math.pi / 3, 0)
    qc.p(math.pi / 3, 0)
    for parents, w, phi in links:
        look(qc, parents, w, phi)
    for parents, w, phi in reversed(links):
        if w not in missed:
            look(qc, parents, w, -phi)
    sv = Statevector.from_instruction(qc)
    rho = partial_trace(sv, list(range(1, qc.num_qubits))) if qc.num_qubits > 1 else DensityMatrix(sv)
    return float(2 * abs(rho.data[0, 1]))


def frac(links, missed=()):
    return fringe(links, missed) / V0


def members(mask, n):
    return {j for j in range(1, n + 1) if mask >> (j - 1) & 1}


def star_F(phi, missed):
    return math.cos(phi) ** len(missed)


def root_F(phi, j):
    return 1 - (1 - math.cos(phi)) * math.sin(phi) ** (2 * (j - 1))


def chain_F(phi, missed):
    return 1.0 if not missed else root_F(phi, min(missed))


def fmt(x):
    return f"{x:.12f}"


def sci(x):
    return f"{x:.1e}"


def cut(sv):
    """Singular values of the amplitude matrix across {P, D, W1, W2} | {O}; O is qubit 4, the top index bit."""
    return np.linalg.svd(sv.data.reshape(2, 16), compute_uv=False)


# ------------------------------------------------------------------------------------------------ stage A
def stage_a():
    print("\nSTAGE A - the article rows (phi = 60 degrees, V0 = sqrt(3)/2 = " + fmt(V0) + ")")
    devs = []
    print("A1  star, d witnesses each looking at P:  V(d) = V0 (1/2)^d")
    print("      d  V (gates)       V0 (1/2)^d      |dev|")
    for d in range(9):
        v = fringe(wiring("star", d, PHI60), set(range(1, d + 1)))
        law = V0 * 0.5 ** d
        devs.append(abs(v - law))
        print(f"      {d}  {fmt(v)}  {fmt(law)}  {sci(abs(v - law))}")
    print("A2  chain, copies of copies:  V(d) = V0 / 2 for every d >= 1")
    print("      d  V (gates)       law             |dev|")
    for d in range(9):
        v = fringe(wiring("chain", d, PHI60), set(range(1, d + 1)))
        law = V0 if d == 0 else V0 / 2
        devs.append(abs(v - law))
        print(f"      {d}  {fmt(v)}  {fmt(law)}  {sci(abs(v - law))}")
    print("A3  star, d = 4, the eraser reaches k of the 4 (every choice of which k):  V = V0 (1/2)^(d-k)")
    print("      k  V (gates, k first)  V law           spread over the choices  |dev|")
    links = wiring("star", 4, PHI60)
    for k in range(5):
        vs = [fringe(links, set(range(1, 5)) - set(reach)) for reach in combinations(range(1, 5), k)]
        law = V0 * 0.5 ** (4 - k)
        devs.append(max(abs(x - law) for x in vs))
        print(f"      {k}  {fmt(vs[0])}  {fmt(law)}  {sci(max(vs) - min(vs))}                  "
              f"{sci(max(abs(x - law) for x in vs))}")
    print("A4  chain of 4, the eraser misses witness j:  F = 1 - (1 - cos phi) sin^(2(j-1)) phi  (the chain's root law)")
    print("      missed set   F (gates)       F law           |dev|")
    links = wiring("chain", 4, PHI60)
    for label, missed, root in (("{1}", {1}, 1), ("{2}", {2}, 2), ("{3}", {3}, 3), ("{4}", {4}, 4),
                                ("{2,3}", {2, 3}, 2), ("{1,4}", {1, 4}, 1)):
        f = frac(links, missed)
        law = root_F(PHI60, root)
        devs.append(abs(f - law))
        print(f"      {label:10s}   {fmt(f)}  {fmt(law)}  {sci(abs(f - law))}"
              + ("   (= F({%d}))" % root if len(missed) > 1 else ""))
    print("A5  bits of finality per unreached direct witness, -log2 cos phi (star, one witness missed, F from gates)")
    print("      phi (deg)  cos phi         F (gates)       bits")
    for deg in (30, 45, 60, 75, 90):
        phi = math.radians(deg)
        f = frac(wiring("star", 1, phi), {1})
        bits = float("inf") if f <= TOL0 else -math.log2(f)
        print(f"      {deg:3d}        {fmt(math.cos(phi))}  {fmt(f)}  {'inf' if math.isinf(bits) else fmt(bits)}")
    cf = max(devs)
    print(f"    Stage A rows against their closed forms: max|dev| {sci(cf)}   {'PASS' if cf <= TOL else 'FAIL'}")
    return cf


# ------------------------------------------------------------------------------------------------ stage T
def stage_t():
    print("\nSTAGE T - six wirings at phi = 60 degrees, nothing undone, d = 0..6 witnesses: V = V0 cos^(direct looks at P)")
    worst = 0.0
    for kind in KINDS:
        rng = np.random.default_rng(259) if kind == "random" else None
        v, direct = [], []
        for d in range(7):
            links = wiring(kind, d, PHI60, rng)
            v.append(fringe(links, set(range(1, d + 1))))
            direct.append(sum(1 for parents, _, _ in links if 0 in parents))
        law_dev = max(abs(a - V0 * math.cos(PHI60) ** n) for a, n in zip(v, direct))
        worst = max(worst, law_dev)
        print(f"    {kind:7s} V(d=0..6): " + " ".join(fmt(x) for x in v))
        print(f"            direct looks at P: {direct}   V0 cos^d law dev {sci(law_dev)}")
    print(f"    a witness of a witness adds a listener, not a look: max|dev| {sci(worst)}   {'PASS' if worst <= TOL else 'FAIL'}")
    return worst


# ------------------------------------------------------------------------------------------------ stage N
def stage_n():
    print("\nSTAGE N - known negatives")
    d0 = 0.0
    for topo in ("star", "chain"):
        for d in range(9):
            d0 = max(d0, abs(fringe(wiring(topo, d, 0.0), set(range(1, d + 1))) - V0))
    vmax = 0.0
    for topo in ("star", "chain"):
        for d in range(1, 9):
            vmax = max(vmax, fringe(wiring(topo, d, math.pi / 2), set(range(1, d + 1))))
    ok = d0 <= TOL0 and vmax <= TOL0
    print(f"    phi = 0, star and chain, d = 0..8: max|V - V0| {sci(d0)} (nothing recorded, nothing lost)")
    print(f"    phi = 90 (full copy), witnesses missed, d = 1..8: max V {sci(vmax)} (< 1e-12)   {'PASS' if ok else 'FAIL'}")
    return max(d0, vmax)


# ------------------------------------------------------------------------------------------------ stage B
def stage_b():
    rho, phi = 0.8, math.pi / 4
    c, s2 = math.cos(phi), math.sin(phi) ** 2
    print("\nSTAGE B - the reach averages: E_N = sum over masks of rho^(reached) (1-rho)^(missed) F, phi = pi/4, rho = 0.8")
    res = {"star": [], "chain": []}
    for topo in ("star", "chain"):
        for n in range(1, 9):
            links = wiring(topo, n, phi)
            e = 0.0
            for mask in range(1 << n):
                missed = members(mask, n)
                e += rho ** (n - len(missed)) * (1 - rho) ** len(missed) * frac(links, missed)
            res[topo].append(e)
    star_cf = [(rho + (1 - rho) * c) ** n for n in range(1, 9)]
    chain_cf = [1 - (1 - c) * (1 - rho) * (1 - (rho * s2) ** n) / (1 - rho * s2) for n in range(1, 9)]
    print("      N  E_star gates    closed form     |dev|    E_chain gates   closed form     |dev|")
    for n in range(8):
        print(f"      {n + 1}  {fmt(res['star'][n])}  {fmt(star_cf[n])}  {sci(abs(res['star'][n] - star_cf[n]))}  "
              f"{fmt(res['chain'][n])}  {fmt(chain_cf[n])}  {sci(abs(res['chain'][n] - chain_cf[n]))}")
    cf_dev = max(max(abs(a - b) for a, b in zip(res["star"], star_cf)),
                 max(abs(a - b) for a, b in zip(res["chain"], chain_cf)))
    limit = 1 - (1 - c) * (1 - rho) / (1 - rho * s2)
    print(f"    closed forms: star (rho + (1-rho)c)^N, chain 1 - (1-c)(1-rho)(1 - (rho s^2)^N)/(1 - rho s^2); "
          f"max|dev| {sci(cf_dev)}")
    print(f"    chain limit 1 - (1-c)(1-rho)/(1-rho s^2) = {fmt(limit)}; E_chain(N=8) - limit = "
          f"{sci(res['chain'][7] - limit)} (the gap shrinks as (rho s^2)^N = 0.4^N)")
    print(f"    B: gates against the closed forms   {'PASS' if cf_dev <= TOL else 'FAIL'}")
    return cf_dev


# ------------------------------------------------------------------------------------------------ stage C
def stage_c():
    print("\nSTAGE C - the cat is a fork: the box {P, D, W1, W2}, the observer O outside (full looks, CRY(pi))")
    qc = QuantumCircuit(5)
    qc.ry(math.pi / 3, 0)
    qc.p(math.pi / 3, 0)
    qc.cry(math.pi, 0, 1)
    qc.cry(math.pi, 1, 2)
    qc.cry(math.pi, 1, 3)
    before = Statevector.from_instruction(qc)
    qc.cry(math.pi, 1, 4)
    after = Statevector.from_instruction(qc)
    sb, sa = cut(before), cut(after)
    rb, ra = float(sb[1] / sb[0]), float(sa[1] / sa[0])
    lines = [float(x) for x in sa ** 2 / np.sum(sa ** 2)]
    odds_b, odds_a = float(before.probabilities([4])[0]), float(after.probabilities([4])[0])
    print(f"    before O's first link: second singular value s2/s1 = {fmt(rb)} (raw s2 = {fmt(float(sb[1]))}); "
          f"O's odds of 0: {fmt(odds_b)}")
    print(f"    after  O copies D    : second singular value s2/s1 = {fmt(ra)} (raw s2 = {fmt(float(sa[1]))}); "
          f"O's odds of 0: {fmt(odds_a)}")
    print(f"    line odds (squared Schmidt weights) after: {fmt(lines[0])} {fmt(lines[1])}")
    print("    the cut across the box wall carries nothing before the first link and lights up after it:")
    print("    decided inside, unreceived until the observer's first link")


def stage_d():
    print("\nSTAGE D - the re-signing control (declared, not computed)")
    print("    The folklore branch (every witness re-draws from the whole table) has no gate form: N independent draws")
    print("    from one table need N fresh preparations, and a measurement by one witness leaves the next witness a")
    print("    copy, never a re-draw. Room 3 of the bench plays that branch by counting instead.")


def main():
    print("The crowd and the chain, in gates (Quest for Entropy #19, Evidence Adds Up to a Fact)")
    print(f"# env: qiskit {qiskit.__version__}, python {sys.version.split()[0]}, numpy {np.__version__}")
    print("look gate: CRY(2*phi), control X, target W (overlap cos phi); particle P: amplitudes sqrt(3/4), "
          "sqrt(1/4) e^(i pi/3); V0 = " + fmt(V0))
    cal = fringe(wiring("star", 1, PHI60), {1})
    print(f"CALIBRATION  one look at P, phi = 60, witness traced out: V = {fmt(cal)}   V0 cos 60 = "
          f"{fmt(V0 * math.cos(PHI60))}   |dev| {sci(abs(cal - V0 * math.cos(PHI60)))}")
    worst = max(stage_a(), stage_t(), stage_n(), stage_b())
    stage_c()
    stage_d()
    print(f"\nEVERY ROW AGAINST ITS CLOSED FORM: max|dev| {sci(worst)}   {'PASS' if worst <= TOL else 'FAIL'}")
    return 0 if worst <= TOL else 1


if __name__ == "__main__":
    sys.exit(main())
