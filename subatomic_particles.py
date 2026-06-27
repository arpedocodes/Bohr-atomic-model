import numpy as np
import pygame

ORBIT_COLOR = (90, 70, 110)
ORBIT_ACTIVE_COLOR = (200, 60, 60)
NUCLEUS_COLOR = (255, 230, 0)
ELECTRON_COLOR = (0, 255, 255)
ELECTRON_GLOW_COLOR = (0, 255, 255)

# How many quantum levels the simulation supports. This is a *display*
# ceiling, not a physical one - real hydrogen has infinitely many bound
# levels, but we only have so many pixels.
MAX_N = 6

# On-screen radius range that every orbit is squeezed into. This is the fix
# for the original bug: radius used to be a literal 60*n**2 px, so n=3 (540px)
# blew straight through an 800x600 window. Instead we keep the *physically
# correct* r ∝ n² relationship between orbits, but rescale the whole curve
# so that even n=MAX_N fits comfortably inside the window.
MIN_RADIUS_PX = 45
MAX_RADIUS_PX = 250


def orbit_radius(n, min_radius=MIN_RADIUS_PX, max_radius=MAX_RADIUS_PX, max_n=MAX_N):
    """
    Map a quantum number n -> an on-screen pixel radius.

    r(n) ∝ n² is preserved (so the *spacing* between orbits still looks
    physically correct - the gap between n=2 and n=3 is bigger than between
    n=1 and n=2, just like the real r_n = n² * a0 relationship), but the
    whole curve is linearly rescaled into [min_radius, max_radius] so the
    outermost orbit always stays on screen no matter the window size.
    """
    n = max(1, min(n, max_n))
    if max_n == 1:
        return min_radius
    return min_radius + (max_radius - min_radius) * (n ** 2 - 1) / (max_n ** 2 - 1)


class Electron:
    def __init__(self, n=1, angular_speed=2.2, initial_angle=0.0, max_n=MAX_N):
        self.max_n = max_n
        self.base_angular_speed = angular_speed
        self.n = n
        self.radius = orbit_radius(n, max_n=max_n)
        self.angle = initial_angle
        self.angular_speed = self._speed_for(n)

    def _speed_for(self, n):
        # Stylized "slows down the higher it gets" - not exact physics
        # (real orbital period grows like n^3), but it reads nicely on
        # screen and conveys that higher orbits are "lazier".
        return self.base_angular_speed / (n ** 1.5)

    def set_level(self, n):
        """Jump straight to level n (used for both excitation and de-excitation)."""
        n = max(1, min(n, self.max_n))
        self.n = n
        self.radius = orbit_radius(n, max_n=self.max_n)
        self.angular_speed = self._speed_for(n)

    def update(self, dt):
        self.angle += self.angular_speed * dt

    def position(self, center):
        cx, cy = center
        x = cx + self.radius * np.cos(self.angle)
        y = cy + self.radius * np.sin(self.angle)
        return int(x), int(y)

    def draw(self, surface, center):
        pos = self.position(center)
        # soft glow
        glow = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*ELECTRON_GLOW_COLOR, 60), (20, 20), 16)
        surface.blit(glow, (pos[0] - 20, pos[1] - 20))
        pygame.draw.circle(surface, ELECTRON_COLOR, pos, 8)


class Nucleus:
    def __init__(self, radius=14):
        self.radius = radius

    def draw(self, surface, center):
        pygame.draw.circle(surface, NUCLEUS_COLOR, center, self.radius)
        pygame.draw.circle(surface, (255, 255, 255), center, self.radius, 1)


class Orbit:
    def __init__(self, n=1, width=2, max_n=MAX_N):
        self.max_n = max_n
        self.n = n
        self.width = width
        self.radius = orbit_radius(n, max_n=max_n)

    def set_level(self, n):
        n = max(1, min(n, self.max_n))
        self.n = n
        self.radius = orbit_radius(n, max_n=self.max_n)

    def draw(self, surface, center, active=True):
        color = ORBIT_ACTIVE_COLOR if active else ORBIT_COLOR
        pygame.draw.circle(surface, color, center, int(self.radius), self.width)