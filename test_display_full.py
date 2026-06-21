"""Test pygame display with full game config."""
import pygame
import sys

pygame.init()
print(f"Pygame version: {pygame.version.ver}")
screen = pygame.display.set_mode((960, 720))
print(f"Screen created: {screen is not None}")
pygame.display.set_caption("Favur Tic-Tac-Toe")
print("Caption set")
pygame.display.flip()
print("Display flipped")
import time
time.sleep(2)
pygame.quit()
print("Done")
sys.exit(0)