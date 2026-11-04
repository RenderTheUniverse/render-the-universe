# Render the Universe: simulation code

The code behind the [Render the Universe](https://www.youtube.com/@RenderTheUniverse) YouTube channel.
Every Short and simulation video on the channel is computed and drawn in Python: no stock footage, no AI video.
If you saw something on the channel and wondered "is that real?", the answer is in here.

## What's inside

### Shorts (`shorts/`)

| Script | Short | The physics / maths |
|---|---|---|
| `pendulums.py` + `pendulum_sim.py` | 1,000 pendulums, each 0.000001° apart | 1,000 double pendulums, RK4 integration. Shows chaos: tiny differences grow until the motion is unpredictable. |
| `galton.py` | 10,000 balls and a bell curve | Galton board: every bounce is a fair coin flip; the bins fill up to the binomial ≈ normal curve (central limit theorem). |
| `brach.py` + `brach_phys.py` | Brachistochrone race | Frictionless sliding with energy conservation, v = √(2gh). The cycloid beats the straight line and a deeper "dive" curve. |

Shared pieces:
- `rtu.py`: the channel look (background, text, bloom, 1080×1920 @ 30 fps), font lookup, and the ffmpeg writer.
- `smooth.py` / `smooth_all.sh`: the opening and loop used on the channel: a zoomed "best moment first" cold open with a hook, crossfaded into the real start, and a crossfade from the end back into the opening so the Short loops seamlessly.
- `coldopen.py` / `colds.sh`: the older 1-second cold open.

### Long videos (`videos/`)

| Folder | Video | Method |
|---|---|---|
| `02_electron_in_a_box/sim.py` | I Trapped an Electron in a Box (in Code) | 1D time-dependent Schrödinger equation, Crank–Nicolson; energy levels read off by "listening" to the wave (FFT). |

These produce the simulation data. The video renderers depend on narration and illustrations, so they are not included.

## Setup

1. Python 3.10 or newer, and **ffmpeg** on your PATH (macOS: `brew install ffmpeg`).
2. pycairo needs the cairo library (macOS: `brew install cairo pkg-config`; Ubuntu: `sudo apt install libcairo2-dev pkg-config`).
3. `pip install -r requirements.txt`
4. Fonts: see [`fonts/README.md`](fonts/README.md) (all free to download).

## Usage

Run from inside `shorts/`:

```bash
cd shorts
python3 galton.py stills 5 12 20   # quick preview frames at 5 s, 12 s and 20 s (JPEG)
python3 galton.py render           # full video -> galton.mp4 (silent)
```

The same pattern works for `brach.py`.
To get the version posted on the channel (cold open + seamless loop): `python3 smooth.py galton 22.4 1.30 540 1300 "Pure randomness" "built this shape." sm_galton` (all settings are in `smooth_all.sh`).
`pendulums.py` takes `stills T…` or `render` the same way.
`pendulums.py` simulates first and caches the result (`traj.npy`).

Long-video simulations:

```bash
cd videos/02_electron_in_a_box && python3 sim.py          # ~3 min, writes sim_data.npz (~90 MB)
```

## License

Code: MIT (see `LICENSE`). Feel free to learn from it, remix it and make your own videos. A link back to the channel is appreciated.
Fonts and the Noto emoji keep their own open licenses.
