import pygame
import pytmx

# --- Constants ---
SCREEN_WIDTH = 480 
SCREEN_HEIGHT = 320
FPS = 60

# --- Pygame Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tiled Map with Collision Debug")
clock = pygame.time.Clock()
screen.fill((50, 50, 50))  # Gray instead of (0, 0, 0)

# --- Player Class ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((32, 32))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)

    def update(self, collision_objects):
        keys = pygame.key.get_pressed()
        self.velocity.x = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        self.velocity.y = keys[pygame.K_DOWN] - keys[pygame.K_UP]
        self.velocity *= 5

        # Move X
        self.pos.x += self.velocity.x
        self.rect.x = int(self.pos.x)
        self.check_collision(collision_objects, 'horizontal')

        # Move Y
        self.pos.y += self.velocity.y
        self.rect.y = int(self.pos.y)
        self.check_collision(collision_objects, 'vertical')

    def check_collision(self, collision_objects, direction):
        for obj in collision_objects:
            if self.rect.colliderect(obj):
                print(f"[COLLISION] With rect: {obj} on {direction} axis")

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
                    elif self.velocity.y < 0:
                        self.rect.top = obj.bottom
                    self.pos.y = self.rect.y
                    self.velocity.y = 0

# --- Game Class ---
class Game:
    def __init__(self, map_file):
        self.tmxdata = pytmx.load_pygame(map_file, pixelalpha=True)
        self.map_width = self.tmxdata.width * self.tmxdata.tilewidth
        self.map_height = self.tmxdata.height * self.tmxdata.tileheight
        self.collision_objects = []
        self.load_collision_objects()
        self.start_time = pygame.time.get_ticks()

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

    def get_spawn_point(self, name="player"):
        spawn_layer = self.tmxdata.get_layer_by_name("spawn")
        
        for obj in spawn_layer:
            x = obj.x
            y = obj.y - obj.height  # Tiled origin is bottom-left
            print(f"[SPAWN] Using spawn point at ({x}, {y})")
            return (x, y)
        return (0, 0)


    def render(self, surface, camera):
        current_time = pygame.time.get_ticks()

        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if gid == 0:
                        continue

                    tile = self.tmxdata.get_tile_image_by_gid(gid)
                    tile_props = self.tmxdata.get_tile_properties_by_gid(gid)

                    if tile_props and "frames" in tile_props:
                        anim = tile_props["frames"]
                        total_duration = sum(frame[1] for frame in anim)
                        current = current_time % total_duration

                    surface.blit(tile, (
                        x * self.tmxdata.tilewidth - camera.x,
                        y * self.tmxdata.tileheight - camera.y))

        for rect in self.collision_objects:
            debug_rect = pygame.Rect(rect.x - camera.x, rect.y - camera.y, rect.width, rect.height)
            pygame.draw.rect(surface, (0, 255, 0), debug_rect, 2)


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

def main():
    game = Game("1-1.tmx")
    spawn_x, spawn_y = game.get_spawn_point()
    print("Spawn:", spawn_x, spawn_y)

    player = Player(spawn_x, spawn_y)
    player_sprite = pygame.sprite.GroupSingle(player)
    camera = Camera(game.map_width, game.map_height)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        player.update(game.collision_objects)

        camera.camera = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

        screen.fill((50, 50, 50))
        game.render(screen, camera.camera)

        screen.blit(player.image, (player.rect.x, player.rect.y))

        pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(spawn_x, spawn_y, 32, 32), 2)

        pygame.display.flip()
        clock.tick(FPS)



if __name__ == "__main__":
    main()
