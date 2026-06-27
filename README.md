# Bohr Atom Simulation

An interactive simulation of a hydrogen atom built with **pygame**, based on the
Bohr model. Fire photons of any wavelength at the electron and watch real
quantum behaviour play out: only the *right* energy gets absorbed, the
electron jumps to a higher orbit, and then cascades back down — releasing
photons whose wavelengths are calculated live from the actual Bohr energy
formula.

## Demo

https://github.com/user-attachments/assets/47a3c942-607d-4945-b604-6dfeca4b10f9

---

## What it does

- Renders a hydrogen atom: nucleus, electron, and its current orbit.
- Lets you **fire a photon of any wavelength** at the atom via an on-screen
  input box, or pick from real spectral-line presets (Lyman-α, Balmer-α,
  an ionizing UV photon, etc).
- Checks the photon's energy (`E = hc/λ`) against the actual energy gaps
  between Bohr levels. Only a matching energy gets absorbed — everything
  else passes straight through, same as a real atom.
- On absorption, the electron jumps to the corresponding level and orbit.
- After a short delay, the electron **cascades back down** one level at a
  time, emitting a new photon at each step with a wavelength computed from
  `λ = hc / ΔE`, coloured to match its actual position in the visible
  spectrum (UV/IR photons render as a neutral marker since they're not
  visible light).
- A **"Hold level"** toggle lets you pause the cascade indefinitely so you
  can fire a second photon at an already-excited electron (e.g. excite to
  n=2 with Lyman-α, hold, then fire Balmer-α to push it to n=3).
  
## Installation

```bash
git clone https://github.com/arpedocodes/Bohr-atomic-model.git
cd Bohr-atomic-model
pip install pygame numpy
```

## Usage

```bash
python main.py
```

- Type a wavelength in nanometers into the input box and press **Enter**
  (or click **Fire**).
- Or click one of the preset buttons for a known hydrogen line.
- Click **Hold level** to freeze the electron at its current level so you
  can experiment with stacking transitions; click **Release** to let it
  resume cascading down.

## The physics

| Quantity | Formula |
|---|---|
| Energy of level *n* | `E_n = -13.6 / n²` eV |
| Photon energy from wavelength | `E = hc / λ = 1239.84 / λ(nm)` eV |
| Transition energy (absorption/emission) | `ΔE = 13.6 × (1/n_low² − 1/n_high²)` eV |
| Binding energy at level *n* (ionization threshold) | `13.6 / n²` eV |

A photon is absorbed only if its energy matches one of these discrete gaps
within a small tolerance. If its energy exceeds the binding energy of the
current level, the electron is ionized (knocked free) instead of just
excited.

## Project structure

| File | Purpose |
|---|---|
| `main.py` | Simulation loop, UI panel, event handling |
| `subatomic_particles.py` | `Electron`, `Nucleus`, `Orbit` classes, with window-safe orbit scaling |
| `energyrelease.py` | Pure physics — energy/wavelength conversions, transition matching, wavelength→RGB |
| `waves.py` | The travelling sine-wave visual representing a photon |
| `ui.py` | Reusable `InputBox` and `Button` widgets |
| `distance.py` | Small geometry helper |

## Known limitations / roadmap

- Only one incoming photon is processed per frame; rapid-fire photons queue
  visually but are evaluated one at a time.
- Photons currently only fire from the left edge.
- No persistent "emission spectrum" view yet — would be a nice addition:
  a strip along the bottom that lights up at each wavelength a photon was
  emitted at, building a spectrum over time.

## License

Add your preferred license here (e.g. MIT) — see [choosealicense.com](https://choosealicense.com/) if unsure.
