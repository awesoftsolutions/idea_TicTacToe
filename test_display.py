"""Quick test of pygame display initialization."""
import pygame
import sys

pygame.init()
print(f"Pygame version: {pygame.version.ver}")
print(f"Display initialized: {pygame.display.get_init()}")
screen = pygame.display.set_mode((960, 720), pygame.NOFRAME)
print(f"Screen created: {screen is not None}")
pygame.display.set_caption("Favur Tic-Tac-Toe")
print("Caption set")
pygame.quit()
print("Pygame quit")
sys.exit(0)