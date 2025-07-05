import pygame

# Constants
SPRITE_WIDTH = 16
SPRITE_HEIGHT = 24
IDLE_FRAME = 0
WALK_FRAMES = [0, 1, 2]  # if walk sheet has 3 frames
FPS = 10

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((300, 200))
clock = pygame.time.Clock()

# --- Load IDLE SPRITE SHEET ---
idle_sheet = pygame.image.load("toad_idle.png").convert_alpha()


# --- Load WALK SPRITE SHEET ---
walk_sheet = pygame.image.load("toad_walk.png").convert_alpha()


def get_frame(sheet, index):
    x = index * SPRITE_WIDTH # Use based on how much separator pixer (SPRITE_WIDTH + 1)
    frame = sheet.subsurface(pygame.Rect(x, 0, SPRITE_WIDTH, SPRITE_HEIGHT))
    scaled = pygame.transform.smoothscale(frame, (SPRITE_WIDTH * 2, SPRITE_HEIGHT * 2))
    return scaled

# Extract frames
idle_frame = get_frame(idle_sheet, IDLE_FRAME)
walk_frames = [get_frame(walk_sheet, i) for i in WALK_FRAMES]

# Animation state
frame_index = 0
animation_timer = 0
ANIMATION_SPEED = 150  # milliseconds
running = True
is_walking = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Check key input
    keys = pygame.key.get_pressed()
    is_walking = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN]

    screen.fill((0, 255, 0))  # Bright green background

    # Update animation
    animation_timer += clock.get_time()
    if is_walking:
        if animation_timer >= ANIMATION_SPEED:
            animation_timer = 0
            frame_index = (frame_index + 1) % len(walk_frames)
        screen.blit(walk_frames[frame_index], (100, 100))
    else:
        screen.blit(idle_frame, (100, 100))
        frame_index = 0  # Reset to first walk frame next time

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
