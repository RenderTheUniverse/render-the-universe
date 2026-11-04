"""An electron in a box: solving the time-dependent Schrödinger equation with Crank–Nicolson.
Units: hbar = m = 1, box width L = 1.  Walls: psi = 0 at x = 0 and x = 1.
Run: python3 sim.py   ->  writes sim_data.npz (the data the video was drawn from)"""
import numpy as np
from scipy.linalg import solve_banded, eigh_tridiagonal

# ---------------------------------------------------------------- the core (shown in the video)
N  = 4000                       # chop the box into 4000 pieces
dx = 1 / (N + 1)
x  = np.arange(1, N + 1) * dx   # the walls (x=0, x=1) are left out: psi is zero there

def crank_nicolson(dt):
    # H psi = -1/2 d²psi/dx²  ->  a tridiagonal matrix ("how sharply the wave curves")
    main = np.full(N, 1 / dx**2, complex); off = np.full(N, -0.5 / dx**2, complex)
    A = np.array([ 0.5j*dt*off,  1 + 0.5j*dt*main,  0.5j*dt*off])   # (1 + i dt/2 H)
    def step(psi):                                                 # one tick of the clock
        rhs = (1 - 0.5j*dt*main) * psi
        rhs[1:]  -= 0.5j*dt*off[1:]  * psi[:-1]
        rhs[:-1] -= 0.5j*dt*off[:-1] * psi[1:]
        return solve_banded((1, 1), A, rhs)                        # (1 + i dt/2 H) psi_new = (1 - i dt/2 H) psi
    return step

def bump(x0, width, k0=0.0):
    psi = np.exp(-(x - x0)**2 / (4 * width**2)) * np.exp(1j * k0 * x)
    return psi / np.sqrt(np.sum(abs(psi)**2) * dx)
# ----------------------------------------------------------------------------------------------

def down(a, f=4): return a.reshape(-1, f).mean(1)          # 4000 -> 1000 points for drawing

def experiment1():
    """Fast bump moving right: bouncing, interference, quantum carpet, revival."""
    dt, k0 = 4e-6, 20 * np.pi
    step, psi = crank_nicolson(dt), bump(0.25, 0.05, k0)
    psi0 = psi.copy()
    T_rev = 4 / np.pi                                      # exact revival time of the ideal box
    n_steps = int(1.03 * T_rev / dt); every = 25           # save every 25 steps = 1e-4 time units
    dens, wave, times, overlap = [], [], [], []
    for n in range(n_steps + 1):
        if n % every == 0:
            t = n * dt
            dens.append(down(abs(psi)**2).astype(np.float32)); times.append(t)
            if t <= 0.25: wave.append(down(psi).astype(np.complex64))
            overlap.append(abs(np.sum(np.conj(psi0) * psi) * dx)**2)
        psi = step(psi)
        if n % 50000 == 0: print(f'  exp1 step {n}/{n_steps}  norm={np.sum(abs(psi)**2)*dx:.9f}', flush=True)
    overlap = np.array(overlap); i_rev = int(np.argmax(np.where(np.array(times) > 0.9 * T_rev, overlap, 0)))
    print(f'  revival at t={times[i_rev]:.5f} (ideal {T_rev:.5f}), overlap with start = {overlap[i_rev]:.4f}')
    return dict(e1_dens=np.array(dens), e1_wave=np.array(wave), e1_t=np.array(times),
                e1_overlap=overlap, e1_irev=i_rev)

def experiment2():
    """Bump at rest near a wall + virtual microphone -> Fourier transform -> energy spikes."""
    dt = 1e-5
    step, psi = crank_nicolson(dt), bump(0.3, 0.05)
    probe = int(0.37 / dx)
    t_run, rec_every, save_every = 4.0, 10, 100
    sig, dens, wave = [], [], []
    for n in range(int(t_run / dt)):
        if n % rec_every == 0: sig.append(psi[probe])
        if n % save_every == 0 and n * dt <= 2.0:
            dens.append(down(abs(psi)**2).astype(np.float32)); wave.append(down(psi).astype(np.complex64))
        psi = step(psi)
        if n % 100000 == 0: print(f'  exp2 step {n}', flush=True)
    sig = np.array(sig); ts = rec_every * dt
    win = np.hanning(len(sig))
    spec = np.abs(np.fft.fft(sig * win))
    omega = -2 * np.pi * np.fft.fftfreq(len(sig), ts)      # psi ~ exp(-i E t): energy = -frequency
    keep = (omega > 0) & (omega < 700); order = np.argsort(omega[keep])
    E1 = np.pi**2 / 2
    return dict(e2_dens=np.array(dens), e2_wave=np.array(wave), e2_sig=sig.astype(np.complex64), e2_sig_dt=ts,
                e2_omega=omega[keep][order] / E1, e2_spec=spec[keep][order] / spec[keep].max(), e2_probe=0.37)

def eigenstates(k=8):
    """The shapes that belong to each step (stationary states)."""
    E, V = eigh_tridiagonal(np.full(N, 1 / dx**2), np.full(N - 1, -0.5 / dx**2), select='i', select_range=(0, k - 1))
    V = V / np.sqrt(dx); V *= np.sign(V[N // 10])           # normalise, make each start upward
    return dict(eig_E=E / E[0], eig_V=np.array([down(v) for v in V.T]).astype(np.float32))

def real_units():
    import scipy.constants as c
    L = 1e-9
    E1 = c.h**2 / (8 * c.m_e * L**2) / c.e
    print(f'  real box 1 nm: E1 = {E1:.3f} eV, E2-E1 = {3*E1:.3f} eV; L = 0.5 nm: E1 = {4*E1:.3f} eV')
    return dict(E1_eV_1nm=E1)

if __name__ == '__main__':
    out = {}
    print('eigenstates'); out.update(eigenstates()); print('  E_n/E_1 =', np.round(out['eig_E'], 4))
    out.update(real_units())
    print('experiment 2'); out.update(experiment2())
    pk = out['e2_omega'][(out['e2_spec'] > 0.05) & (np.r_[0, np.diff(np.sign(np.diff(out['e2_spec']))), 0] < 0)]
    print('  spectrum peaks (units of E1):', np.round(pk, 2))
    print('experiment 1'); out.update(experiment1())
    np.savez_compressed('sim_data.npz', x=down(x), **out)
    print('saved sim_data.npz')
