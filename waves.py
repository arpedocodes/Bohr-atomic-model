import math

import numpy as np
import pygame


class Wave:
    """
    A travelling sine wave drawn on screen, representing a photon.

    `wavelength_nm` is the *physically meaningful* wavelength used for all
    energy calculations (E = hc/λ). The wave is also squashed into a
    sensible on-screen pixel wavelength (`draw_wavelength_px`) purely for
    drawing - otherwise a 91nm UV photon would draw as an invisible sliver
    and a 1000nm IR photon would draw as one giant hump.
    """

    def __init__(
        self,
        amplitude,
        wavelength_nm,
        frequency,
        direction_of_wave,
        color=(0, 255, 255),
        width=3,
        tilt=0,
        speed=240.0,
        center=(0, 0),
        interaction=True,
        length_px=160,
    ):
        self.amplitude = amplitude
        self.wavelength_nm = wavelength_nm
        # Squash arbitrary physical wavelengths into a visually pleasant
        # pixel wavelength (roughly 16-90px) without losing the physical
        # value used for energy calculations.
        self.draw_wavelength_px = max(16, min(90, wavelength_nm / 6))
        self.frequency = frequency
        self.color = color
        self.width = width
        self.tilt = math.radians(tilt)
        self.speed = speed
        self.distance = 0.0
        self.length_px = length_px

        self.k = 2 * np.pi / self.draw_wavelength_px
        self.omega = 2 * np.pi * frequency

        # direction_of_wave "right" -> wave travels toward +x over time.
        # direction_of_wave "left"  -> wave travels toward -x over time.
        self.direction = 1 if direction_of_wave == "right" else -1
        self.center = center
        self.interaction = interaction
        self.removed = False

    def update_distance(self, dt):
        self.distance += self.speed * dt

    def is_offscreen(self, width, margin=250):
        return self.distance > width + margin

    def _build_points(self, t):
        if self.removed:
            return []
        cx, cy = self.center
        offset = self.direction * self.distance
        pts = []
        for local_x in range(0, self.length_px, 3):
            y = self.amplitude * np.sin(self.k * local_x + self.omega * t)
            shifted_x = local_x + offset

            px = shifted_x * math.cos(self.tilt) - y * math.sin(self.tilt)
            py = shifted_x * math.sin(self.tilt) + y * math.cos(self.tilt)

            pts.append((int(px + cx), int(py + cy)))
        return pts

    def get_points(self, t):
        """Points used for collision detection - only meaningful while the
        wave can still interact with the electron."""
        if not self.interaction or self.removed:
            return []
        return self._build_points(t)

    def remove(self):
        self.removed = True

    def draw(self, surface, t):
        pts = self._build_points(t)
        if len(pts) > 1:
            pygame.draw.lines(surface, self.color, False, pts, self.width)