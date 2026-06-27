import sys

import pygame

from distance import calculate_distance
from energyrelease import (
    ReleaseEnergy,
    photon_energy_ev,
    find_matching_transition,
    series_name,
    wavelength_to_rgb,
)
from subatomic_particles import Electron, Nucleus, Orbit, MAX_N
from ui import InputBox, Button, draw_text_block
from waves import Wave

# -------------------- CONFIG -------------------- #
WIDTH, HEIGHT = 900, 700
SIM_HEIGHT = 520          # everything below this y is the UI panel
CENTER = (WIDTH // 2, 260)
FPS = 60

BACKGROUND_COLOR = (16, 16, 26)
PANEL_COLOR = (28, 28, 42)

# A handful of real hydrogen transitions, ready to fire with one click.
PRESETS = [
    ("Lyman-a  121.5nm", 121.5),
    ("Lyman-b  102.6nm", 102.6),
    ("Balmer-a 656.3nm", 656.3),
    ("Balmer-b 486.1nm", 486.1),
    ("Ionize   91.2nm", 91.2),
    ("Off-res. 500nm", 500.0),
]


class Simulation:
    def __init__(self, center):
        self.center = center
        self.nucleus = Nucleus(radius=14)
        self.electron = Electron(n=1, angular_speed=2.4)
        self.orbit = Orbit(n=1)
        self.waves = []

        self.cascade_cooldown = 0.0
        self.cascade_interval = 3.0  # seconds an excited level sits idle before falling
        self.hold = False  # when True, pause the countdown entirely (manual control)

        self.ionized = False
        self.ionize_timer = 0.0

        self.status = "Ground state (n=1). Fire a photon - only the right energy gets absorbed!"

    def add_wave(self, wave):
        self.waves.append(wave)

    def fire_user_wave(self, wavelength_nm, direction="right"):
        if wavelength_nm <= 0:
            self.status = "Wavelength must be a positive number."
            return
        if self.ionized:
            self.status = "The electron has been ionized - wait for it to settle back down."
            return

        color = wavelength_to_rgb(wavelength_nm)
        start_x = -20 if direction == "right" else WIDTH + 20
        wave = Wave(
            amplitude=18,
            wavelength_nm=wavelength_nm,
            frequency=1.1,
            direction_of_wave=direction,
            color=color,
            center=(start_x, self.center[1]),
            tilt=0,
            interaction=True,
        )
        self.add_wave(wave)
        energy = photon_energy_ev(wavelength_nm)
        self.status = f"Fired photon: {wavelength_nm:.1f} nm  (E = {energy:.2f} eV)"

    def excite_to(self, n_target, wavelength_nm, energy_ev):
        self.electron.set_level(n_target)
        self.orbit.set_level(n_target)
        self.cascade_cooldown = self.cascade_interval
        self.status = (
            f"Absorbed! {wavelength_nm:.1f} nm ({energy_ev:.2f} eV) -> "
            f"electron jumped to n={n_target}"
        )

    def ionize(self, wavelength_nm, energy_ev):
        self.ionized = True
        self.ionize_timer = 2.0
        self.status = (
            f"{wavelength_nm:.1f} nm ({energy_ev:.2f} eV) exceeds the binding "
            f"energy - the electron is knocked free!"
        )

    def cascade_step(self):
        n_high = self.electron.n
        n_low = n_high - 1
        self.electron.set_level(n_low)
        self.orbit.set_level(n_low)

        emitted = ReleaseEnergy(n_high, n_low)
        wl = emitted.energy_to_wavelength()
        color = emitted.wavelength_to_rgb()

        wave = Wave(
            amplitude=18,
            wavelength_nm=wl,
            frequency=1.1,
            direction_of_wave="right",
            color=color,
            center=self.electron.position(self.center),
            tilt=0,
            interaction=False,  # emitted light doesn't re-trigger absorption logic
        )
        self.add_wave(wave)

        self.status = (
            f"Emitted {wl:.1f} nm (n={n_high}->{n_low}, {series_name(n_low)} series)"
        )
        self.cascade_cooldown = self.cascade_interval if n_low > 1 else 0.0

    @staticmethod
    def wave_hits_electron(points, epos, threshold=14):
        ex, ey = epos
        for px, py in points:
            if calculate_distance(px, py, ex, ey) < threshold:
                return True
        return False

    def handle_interactions(self, t):
        if self.ionized:
            return  # electron is gone - nothing to absorb a photon
        epos = self.electron.position(self.center)
        for wave in self.waves:
            if wave.removed or not wave.interaction:
                continue
            pts = wave.get_points(t)
            if pts and self.wave_hits_electron(pts, epos):
                energy = photon_energy_ev(wave.wavelength_nm)
                kind, target = find_matching_transition(self.electron.n, energy, max_n=MAX_N)
                if kind == "excite":
                    self.excite_to(target, wave.wavelength_nm, energy)
                    wave.remove()
                elif kind == "ionize":
                    self.ionize(wave.wavelength_nm, energy)
                    wave.remove()
                # else: off-resonance - the photon just keeps travelling
                break  # one absorption event per frame is enough

    def update(self, dt, t):
        if self.ionized:
            self.ionize_timer -= dt
            if self.ionize_timer <= 0:
                self.electron.set_level(1)
                self.orbit.set_level(1)
                self.ionized = False
                self.status = "A fresh electron settles back into the ground state (n=1)."
        else:
            self.electron.update(dt)
            if self.cascade_cooldown > 0 and not self.hold:
                self.cascade_cooldown -= dt
                if self.cascade_cooldown <= 0:
                    self.cascade_step()

        for wave in self.waves:
            wave.update_distance(dt)
        self.waves = [w for w in self.waves if not w.removed and not w.is_offscreen(WIDTH)]

        self.handle_interactions(t)

    def draw(self, surface, t):
        if not self.ionized:
            self.orbit.draw(surface, self.center)
        self.nucleus.draw(surface, self.center)
        for wave in self.waves:
            wave.draw(surface, t)
        if not self.ionized:
            self.electron.draw(surface, self.center)
        else:
            font = pygame.font.SysFont("consolas", 18)
            text = font.render("electron ionized - free!", True, (255, 120, 120))
            surface.blit(text, text.get_rect(center=(self.center[0], self.center[1])))


def build_ui(font, small_font):
    panel_y = SIM_HEIGHT + 14
    input_box = InputBox((20, panel_y, 260, 34), font, prompt="lambda (nm): ")
    fire_button = Button((290, panel_y, 90, 34), "Fire", "fire_custom")
    hold_button = Button((390, panel_y, 130, 34), "Hold level", "toggle_hold")

    preset_buttons = []
    bx, by = 20, panel_y + 50
    for label, wl in PRESETS:
        preset_buttons.append(Button((bx, by, 150, 30), label, wl))
        bx += 158
        if bx > WIDTH - 150:
            bx = 20
            by += 38

    return input_box, fire_button, hold_button, preset_buttons


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Bohr Atom Simulation")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("consolas", 18)
    small_font = pygame.font.SysFont("consolas", 15)

    sim = Simulation(CENTER)
    input_box, fire_button, hold_button, preset_buttons = build_ui(font, small_font)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        t = pygame.time.get_ticks() / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            submitted = input_box.handle_event(event)
            if submitted:
                try:
                    sim.fire_user_wave(float(submitted))
                except ValueError:
                    sim.status = f"'{submitted}' isn't a valid number."

            clicked = fire_button.handle_event(event)
            if clicked == "fire_custom":
                try:
                    sim.fire_user_wave(float(input_box.text or 0))
                    input_box.text = ""
                except ValueError:
                    sim.status = "Type a wavelength first, then hit Fire."

            if hold_button.handle_event(event) == "toggle_hold":
                sim.hold = not sim.hold
                sim.status = (
                    "Holding at n="
                    + str(sim.electron.n)
                    + " - fire another photon, then click Release to resume the cascade."
                    if sim.hold
                    else "Released - the cascade will continue."
                )

            for btn in preset_buttons:
                value = btn.handle_event(event)
                if value is not None:
                    sim.fire_user_wave(value)

        sim.update(dt, t)

        # ---- draw ---- #
        screen.fill(BACKGROUND_COLOR)
        pygame.draw.rect(screen, PANEL_COLOR, (0, SIM_HEIGHT, WIDTH, HEIGHT - SIM_HEIGHT))
        pygame.draw.line(screen, (70, 70, 95), (0, SIM_HEIGHT), (WIDTH, SIM_HEIGHT), 2)

        sim.draw(screen, t)

        info_lines = [
            f"Electron level: n = {sim.electron.n}" + ("  (IONIZED)" if sim.ionized else ""),
            sim.status,
        ]
        draw_text_block(screen, font, info_lines, (20, 16), line_height=24)

        input_box.draw(screen)
        fire_button.draw(screen, font)
        hold_button.label = "Release" if sim.hold else "Hold level"
        hold_button.draw(screen, font)
        for btn in preset_buttons:
            btn.draw(screen, small_font)

        hint = "Type any wavelength (nm) and hit Enter/Fire, or click a preset above."
        draw_text_block(screen, small_font, [hint], (20, HEIGHT - 26), color=(160, 160, 180))

        pygame.display.set_caption(f"Bohr Atom Simulation - n={sim.electron.n}")
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()