import pygame

BG = (28, 28, 42)
PANEL = (38, 38, 58)
BORDER = (110, 110, 150)
BORDER_ACTIVE = (120, 200, 255)
TEXT = (235, 235, 245)
MUTED = (160, 160, 180)


class InputBox:
    """A minimal text-entry box for typing a custom wavelength (nm)."""

    def __init__(self, rect, font, prompt="Wavelength (nm): "):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.prompt = prompt
        self.text = ""
        self.active = False

    def handle_event(self, event):
        """Returns the submitted text (as a string) on Enter, else None."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                submitted, self.text = self.text, ""
                return submitted
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode and (event.unicode.isdigit() or event.unicode == "."):
                if len(self.text) < 10:
                    self.text += event.unicode
        return None

    def draw(self, surface):
        color = BORDER_ACTIVE if self.active else BORDER
        pygame.draw.rect(surface, PANEL, self.rect, border_radius=6)
        pygame.draw.rect(surface, color, self.rect, 2, border_radius=6)
        shown = self.prompt + self.text + ("|" if self.active else "")
        text_surface = self.font.render(shown, True, TEXT)
        surface.blit(text_surface, (self.rect.x + 8, self.rect.y + 8))


class Button:
    """A small clickable rectangle. `value` is returned on click."""

    def __init__(self, rect, label, value):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.value = value
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return self.value
        return None

    def draw(self, surface, font):
        color = (90, 90, 150) if self.hovered else PANEL
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, BORDER, self.rect, 1, border_radius=6)
        text_surface = font.render(self.label, True, TEXT)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


def draw_text_block(surface, font, lines, pos, color=TEXT, line_height=20):
    x, y = pos
    for line in lines:
        surface.blit(font.render(line, True, color), (x, y))
        y += line_height