#!/usr/bin/env python3
"""Stage 1 (pre-registered, E61): ion-photon state tomography from the raw Innsbruck data
(Zenodo 7031042, Calibrations/Node A/Local_ion_photon_entanglement, scans 1650.02-1703.02).
Pure numpy (no scipy available on the analysis VM).  BLIND: never reads Analysis_fidelity_and_matrices.png.

Usage: python3 reconstruct_ion_photon.py [--thr 36] [--tmin 0] [--tmax inf] [--nboot 500] [--seed 20261007] [--tag ""]
Writes (when --tag is empty): stage1_counts.csv, stage1_result.json next to this script.
"""
import numpy as np, pandas as pd, os, json, argparse, hashlib, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data', 'Data', 'Calibrations', 'Node A', 'Local_ion_photon_entanglement')

# ---------------- basis map (transcribed from Measurement_basis_and_scan_number.PNG; ion flags cross-checked
# against Parameters.txt X/Y booleans at run time) -----------------------------------------------------------
# (scan, photon label "first/second", HWP deg, QWP deg, ion basis)
BASIS = [
    ('1650.02', 'H/V', 0.0, 0.0, 'X'), ('1651', 'H/V', 0.0, 0.0, 'Z'), ('1652', 'H/V', 0.0, 0.0, 'Y'),
    ('1652.02', 'D/A', 22.5, 0.0, 'Y'), ('1653', 'D/A', 22.5, 0.0, 'Z'), ('1653.02', 'D/A', 22.5, 0.0, 'X'),
    ('1654', 'V/H', 45.0, 0.0, 'X'), ('1655', 'V/H', 45.0, 0.0, 'Z'), ('1655.02', 'V/H', 45.0, 0.0, 'Y'),
    ('1656', 'R/L', 0.0, 45.0, 'Y'), ('1657.02', 'R/L', 0.0, 45.0, 'Z'), ('1658', 'R/L', 0.0, 45.0, 'X'),
    ('1659', 'A/D', -22.5, 0.0, 'X'), ('1700', 'A/D', -22.5, 0.0, 'Z'), ('1701', 'A/D', -22.5, 0.0, 'Y'),
    ('1702.02', 'L/R', 0.0, -45.0, 'Y'), ('1703', 'L/R', 0.0, -45.0, 'Z'), ('1703.02', 'L/R', 0.0, -45.0, 'X'),
]

# ---------------- conventions ------------------------------------------------------------------------------
I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], complex); SY = np.array([[0, -1j], [1j, 0]]); SZ = np.diag([1., -1.]).astype(complex)
PAULI = {'I': I2, 'X': SX, 'Y': SY, 'Z': SZ}
s2 = 1 / np.sqrt(2)
# photon: H=|0>, V=|1>, D=(H+V)/rt2, A=(H-V)/rt2, R=(H+iV)/rt2, L=(H-iV)/rt2  (sigma_x,y,z +1 eigenstates = D,R,H)
PH = {'H': np.array([1, 0], complex), 'V': np.array([0, 1], complex),
      'D': np.array([s2, s2], complex), 'A': np.array([s2, -s2], complex),
      'R': np.array([s2, 1j * s2], complex), 'L': np.array([s2, -1j * s2], complex)}
PH_AXIS = {'H': ('Z', +1), 'V': ('Z', -1), 'D': ('X', +1), 'A': ('X', -1), 'R': ('Y', +1), 'L': ('Y', -1)}
# ion: |0> := bright (S1/2 at readout), |1> := dark.  Setting 'B' in {X,Y,Z}: bright <-> +1 eigenstate of sigma_B
def ion_proj(basis, bright):
    w, v = np.linalg.eigh(PAULI[basis]); vec = v[:, 1] if bright else v[:, 0]   # eigh: ascending -> [-1,+1]
    return np.outer(vec, vec.conj())

def proj(v): return np.outer(v, v.conj())

# ---------------- decoding ---------------------------------------------------------------------------------
def load_scan(scan, thr, tmin, tmax):
    d = np.loadtxt(os.path.join(DATA, scan, scan + '.dat'), skiprows=1, delimiter='\t')
    hdr = open(os.path.join(DATA, scan, scan + '.dat')).readline().rstrip('\n').split('\t')
    assert len(hdr) == 608 and hdr[8] == 'PMTcounts(0)' and hdr[207] == 'PMTcounts(199)' and hdr[408] == 'probs(0)', scan
    assert d.shape == (11, 608), (scan, d.shape)
    pmt = d[:, 8:208]
    assert np.all(pmt.sum(1) == d[:, 7]), 'PMTcounts(sum) check failed ' + scan
    t = pd.read_csv(os.path.join(DATA, scan, 'Photons_time.dat'), sep=r'\s+')
    assert list(t.columns) == ['Scan_point', 'Loop', 'APD1', 'APD2', 'APD3', 'APD4']
    assert t.Scan_point.min() == 1 and t.Scan_point.max() == 2000 and t.Scan_point.nunique() == 2000
    assert (t[['APD1', 'APD2']].values == 0).all()
    ncyc = 2000
    det = np.full(ncyc, -1)      # -1 = not used, 3 or 4 = heralding detector
    reason = np.array(['no_click'] * ncyc, dtype=object)
    tclick = np.full(ncyc, np.nan)
    for sp, g in t.groupby('Scan_point', sort=False):
        i = sp - 1
        lastL = g.Loop.max(); last = g[g.Loop == lastL]
        c3 = last.APD3.values[last.APD3.values > 0]; c4 = last.APD4.values[last.APD4.values > 0]
        if len(c3) == 0 and len(c4) == 0:
            reason[i] = 'no_click_20' if lastL == 20 else 'early_end_no_click'; continue
        if len(c3) > 0 and len(c4) > 0:
            reason[i] = 'double_click'; continue
        tt = (c3 if len(c3) else c4).min()
        tclick[i] = tt
        if not (tmin <= tt < tmax):
            reason[i] = 'outside_window'; continue
        det[i] = 3 if len(c3) else 4; reason[i] = 'heralded'
    # alignment: Photons_time block b (Scan_point 200b+1..200b+200) <-> .dat row b+1 (row 0 has no time tags)
    sp = np.arange(ncyc); b = sp // 200; j = sp % 200
    counts = pmt[b + 1, j]
    bright = counts > thr
    # block-level consistency vs APDscounts(3),(4)
    blk3 = np.array([((t[(t.Scan_point - 1) // 200 == k].APD3) > 0).sum() for k in range(10)])
    blk4 = np.array([((t[(t.Scan_point - 1) // 200 == k].APD4) > 0).sum() for k in range(10)])
    mism = int(np.abs(blk3 - d[1:, 5]).sum() + np.abs(blk4 - d[1:, 6]).sum())
    return dict(det=det, bright=bright, reason=reason, tclick=tclick, pmt=counts, apd_block_abs_mismatch=mism,
                apd_block_total_tags=int(blk3.sum() + blk4.sum()), apd_dat_total=int(d[1:, 5].sum() + d[1:, 6].sum()),
                row0_unused_pmt=200)

def check_flags(scan, ion):
    txt = open(os.path.join(DATA, scan, 'Parameters.txt')).read()
    fx = 'X : True' in txt; fy = 'Y : True' in txt
    exp = {'X': (True, False), 'Y': (False, True), 'Z': (False, False)}[ion]
    assert (fx, fy) == exp, (scan, ion, fx, fy)
    assert 'mapping : True' in txt and 'Cycles: 200' in txt

def scan_counts(rec):
    h = rec['det'] > 0
    out = {}
    for dd in (3, 4):
        for br in (True, False):
            out[(dd, br)] = int(np.sum(h & (rec['det'] == dd) & (rec['bright'] == br)))
    return out

# ---------------- tomography -------------------------------------------------------------------------------
def photon_state_on(apd, label, mapping):
    first, second = label.split('/')
    if mapping == 'M1':   # APD3 sees the first-named state
        return first if apd == 3 else second
    return second if apd == 3 else first   # M2

def compensated_settings(cnts, mapping):
    """Pool the two detector orientations of each (ion basis, photon axis) setting by polarisation label.
    Returns dict (ionB, phB) -> 2x2 array N[ion_sign_idx(0:+,1:-), ph_sign_idx]"""
    S = {}
    for (scan, label, hwp, qwp, ion) in BASIS:
        c = cnts[scan]
        for apd in (3, 4):
            st = photon_state_on(apd, label, mapping); ax, sg = PH_AXIS[st]
            key = (ion, ax); S.setdefault(key, np.zeros((2, 2)))
            for br in (True, False):
                S[key][0 if br else 1, 0 if sg > 0 else 1] += c[(apd, br)]
    return S

def linear_inversion(S):
    T = {}
    marg_i = {b: [] for b in 'XYZ'}; marg_p = {b: [] for b in 'XYZ'}
    sgn = np.array([1, -1])
    for (ib, pb), N in S.items():
        f = N / N.sum()
        T[(ib, pb)] = float(sgn @ f @ sgn)
        marg_i[ib].append(float(sgn @ f.sum(1))); marg_p[pb].append(float(f.sum(0) @ sgn))
    rho = np.kron(I2, I2) / 4
    for a in 'XYZ':
        rho = rho + np.mean(marg_i[a]) * np.kron(PAULI[a], I2) / 4 + np.mean(marg_p[a]) * np.kron(I2, PAULI[a]) / 4
        for b in 'XYZ':
            rho = rho + T[(a, b)] * np.kron(PAULI[a], PAULI[b]) / 4
    return rho

def povm_from_S(S):
    E = []; n = []
    for (ib, pb), N in S.items():
        for si, sgi in enumerate((+1, -1)):
            Pi = ion_proj(ib, sgi > 0)
            for sp, sgp in enumerate((+1, -1)):
                vp = [k for k, v in PH_AXIS.items() if v == (pb, sgp)][0]
                E.append(np.kron(Pi, proj(PH[vp]))); n.append(N[si, sp])
    return np.array(E), np.array(n, float)

def mle_rhor(E, n, iters=4000, rho0=None, tol=1e-12):
    rho = np.eye(4, dtype=complex) / 4 if rho0 is None else rho0.copy()
    N = n.sum(); prevL = -np.inf
    Ef = E.reshape(len(E), 16); EfT = np.ascontiguousarray(E.transpose(0, 2, 1).reshape(len(E), 16))
    for it in range(iters):
        p = np.real(EfT @ rho.reshape(16)); p = np.clip(p, 1e-15, None)
        R = ((n / p) @ Ef).reshape(4, 4) / N
        rho = R @ rho @ R; rho = (rho + rho.conj().T) / 2; rho /= np.trace(rho).real
        if it % 50 == 0:
            L = float(np.sum(n * np.log(p)));
            if abs(L - prevL) < tol * max(1, abs(L)): break
            prevL = L
    p = np.clip(np.real(np.einsum('ij,kji->k', rho, E)), 1e-300, None)
    return rho, float(np.sum(n[n > 0] * np.log(p[n > 0])))

def mle_with_efficiency(cnts, mapping, iters=20000, eps=0.3):
    """Full 18-scan conditional-multinomial ML with a free relative detector efficiency r = eta4/eta3 (nuisance)."""
    E3 = []; E4 = []; n3 = []; n4 = []; F3 = []; F4 = []
    for (scan, label, hwp, qwp, ion) in BASIS:
        c = cnts[scan]
        v3 = PH[photon_state_on(3, label, mapping)]; v4 = PH[photon_state_on(4, label, mapping)]
        F3.append(np.kron(I2, proj(v3))); F4.append(np.kron(I2, proj(v4)))
        for br in (True, False):
            E3.append(np.kron(ion_proj(ion, br), proj(v3))); n3.append(c[(3, br)])
            E4.append(np.kron(ion_proj(ion, br), proj(v4))); n4.append(c[(4, br)])
    E3, E4, F3, F4 = map(np.array, (E3, E4, F3, F4)); n3 = np.array(n3, float); n4 = np.array(n4, float)
    Ns = (n3.reshape(-1, 2).sum(1) + n4.reshape(-1, 2).sum(1)); N = Ns.sum()
    tr = lambda rho, A: np.real(np.einsum('ij,kji->k', rho, A))
    rho = np.eye(4, dtype=complex) / 4; r = 1.0
    def logL(rho, r):
        return float(np.sum(n3 * np.log(tr(rho, E3))) + np.sum(n4 * np.log(r * tr(rho, E4)))
                     - np.sum(Ns * np.log(tr(rho, F3) + r * tr(rho, F4))))
    prev = -np.inf
    for it in range(iters):
        t3 = tr(rho, F3); t4 = tr(rho, F4); q = t3 + r * t4
        H = (np.einsum('k,kij->ij', n3 / tr(rho, E3), E3) + np.einsum('k,kij->ij', n4 / tr(rho, E4), E4)
             - np.einsum('k,kij->ij', Ns / q, F3 + r * F4))
        G = np.eye(4) + eps * H / N
        rho = G @ rho @ G.conj().T; rho = (rho + rho.conj().T) / 2; rho /= np.trace(rho).real
        # r update: solve n4tot/r = sum Ns t4/(t3 + r t4) by bisection in log r
        t3 = tr(rho, F3); t4 = tr(rho, F4); n4t = n4.sum()
        lo, hi = -3.0, 3.0
        for _ in range(60):
            m = (lo + hi) / 2; rr = np.exp(m)
            g = n4t / rr - np.sum(Ns * t4 / (t3 + rr * t4))
            lo, hi = (m, hi) if g > 0 else (lo, m)
        r = np.exp((lo + hi) / 2)
        if it % 200 == 0:
            L = logL(rho, r)
            if abs(L - prev) < 1e-10 * abs(L): break
            prev = L
    return rho, float(r), logL(rho, r)

# ---------------- figures of merit -------------------------------------------------------------------------
BELL = {'Phi+': np.array([1, 0, 0, 1]) * s2, 'Phi-': np.array([1, 0, 0, -1]) * s2,
        'Psi+': np.array([0, 1, 1, 0]) * s2, 'Psi-': np.array([0, 1, -1, 0]) * s2}   # basis |ion,photon>: 0H,0V,1H,1V

def figures(rho):
    out = {k: float(np.real(v.conj() @ rho @ v)) for k, v in BELL.items()}
    out['F_Phi_family_max_over_phase'] = float(np.real(rho[0, 0] + rho[3, 3]) / 2 + abs(rho[0, 3]))
    out['Phi_family_best_phase_rad'] = float(np.angle(rho[3, 0]))   # |0H> + e^{i phi}|1V>
    out['F_Psi_family_max_over_phase'] = float(np.real(rho[1, 1] + rho[2, 2]) / 2 + abs(rho[1, 2]))
    out['Psi_family_best_phase_rad'] = float(np.angle(rho[2, 1]))   # |0V> + e^{i phi}|1H>
    T = np.array([[np.real(np.trace(rho @ np.kron(PAULI[a], PAULI[b]))) for b in 'XYZ'] for a in 'XYZ'])
    s = np.linalg.svd(T, compute_uv=False)
    out['F_max_entangled_any_local_unitary'] = float((1 + s[0] + s[1] - np.sign(np.linalg.det(T)) * s[2]) / 4)
    out['detT'] = float(np.linalg.det(T)); out['T'] = T.round(5).tolist()
    ev = np.linalg.eigvalsh(rho); out['eigenvalues'] = ev.round(6).tolist()
    out['purity'] = float(np.real(np.trace(rho @ rho)))
    return out

def F_phase_family_best(rho):
    return max(float(np.real(rho[0, 0] + rho[3, 3]) / 2 + abs(rho[0, 3])), float(np.real(rho[1, 1] + rho[2, 2]) / 2 + abs(rho[1, 2])))

# ---------------- main -------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--thr', type=float, default=36.0)        # bright iff PMT counts > thr
    ap.add_argument('--tmin', type=float, default=0.0)
    ap.add_argument('--tmax', type=float, default=np.inf)
    ap.add_argument('--nboot', type=int, default=500)
    ap.add_argument('--seed', type=int, default=20261007)
    ap.add_argument('--tag', default='')
    a = ap.parse_args()
    recs = {}; cnts = {}; rows = []
    for (scan, label, hwp, qwp, ion) in BASIS:
        check_flags(scan, ion)
        rec = load_scan(scan, a.thr, a.tmin, a.tmax); recs[scan] = rec
        c = scan_counts(rec); cnts[scan] = c
        rr = pd.Series(rec['reason']).value_counts().to_dict()
        rows.append(dict(scan=scan, photon_basis=label, HWP_deg=hwp, QWP_deg=qwp, ion_basis=ion, cycles_with_tags=2000,
                         heralded=int((rec['det'] > 0).sum()),
                         APD3_bright=c[(3, True)], APD3_dark=c[(3, False)], APD4_bright=c[(4, True)], APD4_dark=c[(4, False)],
                         excl_no_click_20=rr.get('no_click_20', 0), excl_early_end_no_click=rr.get('early_end_no_click', 0),
                         excl_double_click=rr.get('double_click', 0), excl_outside_window=rr.get('outside_window', 0),
                         block_APDscounts_abs_mismatch=rec['apd_block_abs_mismatch'],
                         tags_total=rec['apd_block_total_tags'], dat_APDscounts_total=rec['apd_dat_total']))
    df = pd.DataFrame(rows)
    res = dict(settings=dict(thr=a.thr, tmin=a.tmin, tmax=None if np.isinf(a.tmax) else a.tmax, nboot=a.nboot, seed=a.seed),
               ordering='ion (x) photon; basis |ion,photon> = |0H>,|0V>,|1H>,|1V>; ion |0> = bright; photon H=|0>',
               total_heralded=int(df.heralded.sum()), mappings={})
    rng = np.random.default_rng(a.seed)
    boot_idx = {s: [rng.integers(0, 2000, 2000) for _ in range(a.nboot)] for s, *_ in BASIS}
    for mp in ('M1', 'M2'):
        S = compensated_settings(cnts, mp)
        rho_li = linear_inversion(S)
        E, n = povm_from_S(S)
        rho_ml, L = mle_rhor(E, n)
        rho_eff, r_eff, L_eff = mle_with_efficiency(cnts, mp)
        R = dict(logL_compensated_ML=L, linear_inversion=figures(rho_li), ml_compensated=figures(rho_ml),
                 ml_18scan_free_efficiency=dict(figures(rho_eff), eta4_over_eta3=r_eff, logL=L_eff),
                 rho_LI_real=np.real(rho_li).round(5).tolist(), rho_LI_imag=np.imag(rho_li).round(5).tolist(),
                 rho_ML_real=np.real(rho_ml).round(5).tolist(), rho_ML_imag=np.imag(rho_ml).round(5).tolist(),
                 rho_MLeff_real=np.real(rho_eff).round(5).tolist(), rho_MLeff_imag=np.imag(rho_eff).round(5).tolist())
        if a.nboot > 0:
            keys = ['Phi+', 'Phi-', 'Psi+', 'Psi-', 'F_max_entangled_any_local_unitary', 'F_Phi_family_max_over_phase', 'F_Psi_family_max_over_phase']
            B = {'LI': {k: [] for k in keys}, 'ML': {k: [] for k in keys}}; rli = []; rml = []
            for bi in range(a.nboot):
                cb = {}
                for (scan, *_ ) in BASIS:
                    rec = recs[scan]; ix = boot_idx[scan][bi]
                    cb[scan] = scan_counts(dict(det=rec['det'][ix], bright=rec['bright'][ix]))
                Sb = compensated_settings(cb, mp)
                rl = linear_inversion(Sb); Eb, nb = povm_from_S(Sb); rm, _ = mle_rhor(Eb, nb, iters=1500, rho0=rho_ml)
                rli.append(rl); rml.append(rm)
                for nm, rr_ in (('LI', rl), ('ML', rm)):
                    f = figures(rr_)
                    for k in keys: B[nm][k].append(f[k])
            R['bootstrap_SE'] = {nm: {k: float(np.std(v, ddof=1)) for k, v in B[nm].items()} for nm in B}
            R['bootstrap_mean'] = {nm: {k: float(np.mean(v)) for k, v in B[nm].items()} for nm in B}
            R['bootstrap_SE_rho_ML_real'] = np.std(np.real(rml), axis=0, ddof=1).round(5).tolist()
            R['bootstrap_SE_rho_ML_imag'] = np.std(np.imag(rml), axis=0, ddof=1).round(5).tolist()
            R['bootstrap_SE_rho_LI_real'] = np.std(np.real(rli), axis=0, ddof=1).round(5).tolist()
            R['bootstrap_SE_rho_LI_imag'] = np.std(np.imag(rli), axis=0, ddof=1).round(5).tolist()
        res['mappings'][mp] = R
    res['script_sha256'] = hashlib.sha256(open(os.path.abspath(__file__), 'rb').read()).hexdigest()
    suffix = ('_' + a.tag) if a.tag else ''
    df.to_csv(os.path.join(HERE, f'stage1_counts{suffix}.csv'), index=False)
    json.dump(res, open(os.path.join(HERE, f'stage1_result{suffix}.json'), 'w'), indent=1)
    # concise summary
    print('total heralded', res['total_heralded'])
    for mp, R in res['mappings'].items():
        print(mp, 'logL_ML=%.2f' % R['logL_compensated_ML'], 'LI minEig=%.4f' % min(R['linear_inversion']['eigenvalues']),
              'detT_LI=%.3f' % R['linear_inversion']['detT'])
        for nm, key in (('LI', 'linear_inversion'), ('ML', 'ml_compensated')):
            f = R[key]; se = R.get('bootstrap_SE', {}).get(nm, {})
            print('  %s Fmax_any=%.4f(%.4f) Fphi*=%.4f Fpsi*=%.4f Phi+=%.4f Phi-=%.4f Psi+=%.4f Psi-=%.4f' % (
                nm, f['F_max_entangled_any_local_unitary'], se.get('F_max_entangled_any_local_unitary', np.nan),
                f['F_Phi_family_max_over_phase'], f['F_Psi_family_max_over_phase'], f['Phi+'], f['Phi-'], f['Psi+'], f['Psi-']))
        fe = R['ml_18scan_free_efficiency']
        print('  MLeff Fmax_any=%.4f r=%.4f logL=%.2f' % (fe['F_max_entangled_any_local_unitary'], fe['eta4_over_eta3'], fe['logL']))

if __name__ == '__main__':
    main()
