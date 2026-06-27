"""
Bohr-model physics helpers.

Everything here is plain physics with no pygame dependency, which makes it
easy to test on its own:

    E_n            = -13.6 / n^2                       eV   (energy of level n)
    DeltaE(n1->n2) = 13.6 * (1/n1^2 - 1/n2^2)           eV   (n2 > n1, energy ABSORBED)
    E_photon       = 1239.84193 / lambda(nm)            eV   (E = hc/lambda, hc in eV*nm)
    lambda(nm)     = 1239.84193 / E_photon              nm
"""

RYDBERG_EV = 13.6
HC_EV_NM = 1239.84193  # h*c expressed in eV * nm, handy because we work in nm/eV


def transition_energy_ev(n_low, n_high):
    """Energy gap between two bound levels (n_high > n_low), in eV.

    This is the energy a photon must carry to drive n_low -> n_high, and
    the energy a photon carries away when the electron falls n_high -> n_low.
    """
    return RYDBERG_EV * (1.0 / n_low ** 2 - 1.0 / n_high ** 2)


def binding_energy_ev(n):
    """Energy needed to rip the electron out of level n entirely (ionize)."""
    return RYDBERG_EV / n ** 2


def photon_energy_ev(wavelength_nm):
    """E = hc/lambda. wavelength_nm must be > 0."""
    if wavelength_nm is None or wavelength_nm <= 0:
        return 0.0
    return HC_EV_NM / wavelength_nm


def energy_to_wavelength_nm(energy_ev):
    """Inverse of photon_energy_ev. Returns None if energy is non-positive."""
    if energy_ev is None or energy_ev <= 0:
        return None
    return HC_EV_NM / energy_ev


def find_matching_transition(n_current, energy_ev, max_n=6, tolerance_ev=0.08):
    """
    Decide what an incoming photon of `energy_ev` does to an electron
    currently sitting at level `n_current`.

    Real hydrogen atoms only absorb a photon if its energy matches one of
    the *discrete* energy gaps between levels (or exceeds the binding
    energy, in which case the electron is knocked free / ionized). Anything
    else simply passes straight through - this is the whole point of
    quantized energy levels, so the simulation enforces it exactly.

    Returns a tuple:
        ("excite", n_target)  - photon absorbed, electron jumps to n_target
        ("ionize", None)      - photon energy >= binding energy, electron freed
        (None, None)          - off-resonance, the wave should pass through
    """
    binding = binding_energy_ev(n_current)

    best_n, best_diff = None, None
    for n_target in range(n_current + 1, max_n + 1):
        gap = transition_energy_ev(n_current, n_target)
        diff = abs(gap - energy_ev)
        if best_diff is None or diff < best_diff:
            best_diff, best_n = diff, n_target

    if best_n is not None and best_diff <= tolerance_ev:
        return ("excite", best_n)

    # Either there's no level left to climb to inside max_n, or the photon
    # simply carries more energy than it takes to free the electron.
    if energy_ev >= binding - tolerance_ev:
        return ("ionize", None)

    return (None, None)


def series_name(n_low):
    """Common name for the spectral series an emitted photon belongs to."""
    names = {
        1: "Lyman (UV)",
        2: "Balmer (visible)",
        3: "Paschen (IR)",
        4: "Brackett (IR)",
        5: "Pfund (IR)",
    }
    return names.get(n_low, "-")


def wavelength_to_rgb(wavelength_nm, gamma=0.8):
    """
    Approximate a visible wavelength (380-750nm) as an RGB colour.
    Wavelengths outside the visible range are rendered as a dim grey so
    UV/IR photons are still visible on screen without implying a colour
    they don't actually have.

    Based on the classic approximation by Dan Bruton
    (http://www.physics.sfasu.edu/astro/color/spectra.html).
    """
    if wavelength_nm is None:
        return (255, 255, 255)

    wl = float(wavelength_nm)

    if wl < 380 or wl > 750:
        return (90, 90, 100)  # invisible to the eye -> neutral grey marker

    if wl <= 440:
        attenuation = 0.3 + 0.7 * (wl - 380) / (440 - 380)
        r = ((-(wl - 440) / (440 - 380)) * attenuation) ** gamma
        g = 0.0
        b = (1.0 * attenuation) ** gamma
    elif wl <= 490:
        r = 0.0
        g = ((wl - 440) / (490 - 440)) ** gamma
        b = 1.0
    elif wl <= 510:
        r = 0.0
        g = 1.0
        b = (-(wl - 510) / (510 - 490)) ** gamma
    elif wl <= 580:
        r = ((wl - 510) / (580 - 510)) ** gamma
        g = 1.0
        b = 0.0
    elif wl <= 645:
        r = 1.0
        g = (-(wl - 645) / (645 - 580)) ** gamma
        b = 0.0
    else:
        attenuation = 0.3 + 0.7 * (750 - wl) / (750 - 645)
        r = (1.0 * attenuation) ** gamma
        g = 0.0
        b = 0.0

    return (int(r * 255), int(g * 255), int(b * 255))


class ReleaseEnergy:
    """
    Small wrapper (same idea as the original class) for computing the
    photon released when the electron falls from n_high to n_low.
    """

    def __init__(self, n_high, n_low):
        self.n_high = n_high
        self.n_low = n_low
        self.energy = transition_energy_ev(n_low, n_high)  # eV released

    def energy_to_wavelength(self):
        return energy_to_wavelength_nm(self.energy)

    def wavelength_to_rgb(self, gamma=0.8):
        return wavelength_to_rgb(self.energy_to_wavelength(), gamma)


if __name__ == "__main__":
    # quick sanity check
    for n1, n2 in [(1, 2), (1, 3), (2, 3), (2, 4)]:
        e = transition_energy_ev(n1, n2)
        wl = energy_to_wavelength_nm(e)
        print(f"n={n1}->{n2}: {e:.3f} eV, {wl:.1f} nm, {series_name(n1)}")