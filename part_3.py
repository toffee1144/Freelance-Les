import pygame
import pytmx

# --- Constants ---
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
FPS = 60
GRAVITY = 0.5
JUMP_FORCE = -8
TILE_SIZE = 16

# --- Pygame Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tiled Map with Gravity")
clock = pygame.time.Clock()
screen.fill((50, 50, 50))


# --- Player Class ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.can_break = False  # Used only when jumping
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)
        self.on_ground = False

    def update(self, collision_objects):
        keys = pygame.key.get_pressed()

        # Horizontal movement
        self.velocity.x = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 2.5

        # Apply gravity
        self.velocity.y += GRAVITY
        if self.velocity.y > 10:
            self.velocity.y = 10  # Limit fall speed

        if keys[pygame.K_SPACE] and self.on_ground:
            self.velocity.y = JUMP_FORCE
            self.can_break = True  # mark next upward movement for breaking
        else:
            self.can_break = False

        # Jump
        if keys[pygame.K_SPACE] and self.on_ground:
            self.velocity.y = JUMP_FORCE

        # Move X
        self.pos.x += self.velocity.x
        self.rect.x = int(self.pos.x)
        self.check_collision(collision_objects, 'horizontal')

        # Move Y
        self.pos.y += self.velocity.y
        self.rect.y = int(self.pos.y)
        self.on_ground = False
        self.check_collision(collision_objects, 'vertical')

    def check_collision(self, collision_objects, direction):
        for obj in collision_objects:
            if self.rect.colliderect(obj):
                if direction == 'horizontal':
                    if self.velocity.x > 0:
                        self.rect.right = obj.left
                    elif self.velocity.x < 0:
                        self.rect.left = obj.right
                    self.pos.x = self.rect.x
                    self.velocity.x = 0
                elif direction == 'vertical':
                    if self.velocity.y > 0:
                        self.rect.bottom = obj.top
                        self.on_ground = True
                    elif self.velocity.y < 0:
                        self.rect.top = obj.bottom
                    self.pos.y = self.rect.y
                    self.velocity.y = 0

    def try_break_blocks(self, game):
        if self.velocity.y < 0:
            # Create a small hitbox just above the player's head
            hitbox = pygame.Rect(self.rect.x, self.rect.y - 4, self.rect.width, 4)

            for tile in game.breakable_tiles:
                if hitbox.colliderect(tile["rect"]) and not tile["is_animating"]:
                    print(f"[HIT] Trigger animation at ({tile['tile_x']}, {tile['tile_y']})")
                    tile["is_animating"] = True
                    tile["animation_timer"] = 0
                    break




# --- Game Class ---
class Game:
    def __init__(self, map_file):
        self.tmxdata = pytmx.load_pygame(map_file, pixelalpha=True)
        self.map_width = self.tmxdata.width * self.tmxdata.tilewidth
        self.map_height = self.tmxdata.height * self.tmxdata.tileheight

        self.breakable_tiles = []
        self.collision_objects = []

        self.load_collision_objects()
        self.load_breakable_tiles()

    def load_collision_objects(self):
        self.collision_objects = []
        for obj in self.tmxdata.get_layer_by_name("collision"):
            x = obj.x
            y = obj.y
            width = obj.width or 0
            height = obj.height or 0
            if width == 0 or height == 0:
                continue
            self.collision_objects.append(pygame.Rect(x, y, width, height))

    def get_spawn_point(self):
        spawn_layer = self.tmxdata.get_layer_by_name("spawn")
        for obj in spawn_layer:
            x = obj.x
            y = obj.y - obj.height
            print(f"[SPAWN] Using spawn point at ({x}, {y})")
            return (x, y)
        return (0, 0)

    def render(self, surface, camera):
        current_time = pygame.time.get_ticks()
        breakable_positions = {(tile["tile_x"], tile["tile_y"]) for tile in self.breakable_tiles}

        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if gid == 0:
                        continue

                    # 🛑 Skip drawing breakable tile positions here
                    if layer.name == "breakable" and (x, y) in breakable_positions:
                        continue
                    
                    tile = self.tmxdata.get_tile_image_by_gid(gid)
                    surface.blit(tile, (
                        x * self.tmxdata.tilewidth - camera.x,
                        y * self.tmxdata.tileheight - camera.y))

        # ✅ Now draw animated breakable tiles manually
        for tile in self.breakable_tiles:
            tile_image = self.tmxdata.get_tile_image_by_gid(tile["gid"])
            if tile_image:
                surface.blit(tile_image, (
                    tile["rect"].x - camera.x,
                    tile["rect"].y - camera.y))

        # Debug: draw collision boxes
        for rect in self.collision_objects:
            debug_rect = pygame.Rect(rect.x - camera.x, rect.y - camera.y, rect.width, rect.height)
            pygame.draw.rect(surface, (0, 255, 0), debug_rect, 1)

    def load_breakable_tiles(self):
        break_layer = self.tmxdata.get_layer_by_name("breakable")
        for x, y, gid in break_layer:
            if gid != 0:
                rect = pygame.Rect(
                    x * self.tmxdata.tilewidth,
                    y * self.tmxdata.tileheight,
                    self.tmxdata.tilewidth,
                    self.tmxdata.tileheight
                )
                self.breakable_tiles.append({
                    "rect": rect,
                    "tile_x": x,
                    "tile_y": y,
                    "gid": gid,
                    "is_animating": False,
                    "offset_y": 0,
                    "start_y": rect.y,
                    "animation_timer": 0
                })
                self.collision_objects.append(rect)  # ✅ Add this line back!

    def update_breakable_tile_animations(self):
        for tile in self.breakable_tiles:
            if tile["is_animating"]:
                tile["animation_timer"] += 1
                t = tile["animation_timer"]

                # Simple bounce curve (up and back)
                if t <= 10:
                    tile["offset_y"] = -abs(8 * (1 - t / 10))  # parabola bounce: goes to -8px and returns
                else:
                    tile["offset_y"] = 0
                    tile["is_animating"] = False
                    tile["animation_timer"] = 0

                tile["rect"].y = tile["start_y"] + tile["offset_y"]

# --- Camera Class ---
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topright)

    def update(self, target):
        x = -target.rect.centerx + SCREEN_WIDTH // 2
        y = -target.rect.centery + SCREEN_HEIGHT // 2
        x = min(0, max(-(self.width - SCREEN_WIDTH), x))
        y = min(0, max(-(self.height - SCREEN_HEIGHT), y))
        self.camera = pygame.Rect(x, y, self.width, self.height)


# --- Main Game Loop ---
def main():
    game = Game("1-1.tmx")
    spawn_x, spawn_y = game.get_spawn_point()
    player = Player(spawn_x, spawn_y)
    camera = Camera(game.map_width, game.map_height)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        player.update(game.collision_objects)
        player.try_break_blocks(game)  # ✅ PASS THE WHOLE GAME
        camera.update(player)
        game.update_breakable_tile_animations() 

        screen.fill((50, 50, 50))
        game.render(screen, camera.camera)
        screen.blit(player.image, (player.rect.x - camera.camera.x, player.rect.y - camera.camera.y))
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
