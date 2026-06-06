# Astrocrash — concise, production‑ready version
import pygame
import sys
import random
import math

# Window setup
pygame.init()
WIDTH, HEIGHT, FPS = 800, 600, 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Gameplay constants
SHIP_RADIUS, MAX_SPEED = 15, 6
THRUST, FRICTION, ROT_SPEED = 0.2, 0.98, 5
BULLET_SPEED, BULLET_LIFE = 8, 60
AST_MIN, AST_MAX = 1, 3

# Colours
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)

# Player‑controlled ship
class Ship:
    def __init__(self, pos):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2()
        self.dir = pygame.math.Vector2(0, -1)
        self.radius = SHIP_RADIUS
        self.lives = 3
        self.invincible = 0

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.dir.rotate_ip(-ROT_SPEED)
        if keys[pygame.K_RIGHT]:
            self.dir.rotate_ip(ROT_SPEED)
        if keys[pygame.K_UP]:
            self.vel += self.dir * THRUST

        self.vel *= FRICTION
        if self.vel.length() > MAX_SPEED:
            self.vel.scale_to_length(MAX_SPEED)

        self.pos += self.vel
        self.pos.x %= WIDTH
        self.pos.y %= HEIGHT

        if self.invincible:
            self.invincible -= 1

    def draw(self, surf):
        nose = self.pos + self.dir * 20
        left = self.pos + self.dir.rotate(140) * 15
        right = self.pos + self.dir.rotate(-140) * 15
        pygame.draw.polygon(surf, WHITE, [nose, left, right])


# Projectile fired by the ship
class Bullet:
    def __init__(self, pos, d, ship_vel):
        self.pos = pygame.math.Vector2(pos)
        self.vel = ship_vel + d * BULLET_SPEED
        self.life = 0
        self.radius = 3

    def update(self):
        self.pos += self.vel
        self.life += 1

    def draw(self, surf):
        pygame.draw.circle(surf, YELLOW, (int(self.pos.x), int(self.pos.y)), self.radius)


# Asteroids that can split on impact
class Asteroid:
    def __init__(self, pos, vel, stage):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.stage = stage

        if stage == 4:
            self.radius, self.color = 30, RED
        elif stage == 3:
            self.radius, self.color = 25, ORANGE
        elif stage == 2:
            self.radius, self.color = 20, GREEN
        else:
            self.radius, self.color = 15, BLUE

    def update(self):
        self.pos += self.vel
        self.pos.x %= WIDTH
        self.pos.y %= HEIGHT

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

    def split(self):
        if self.stage > 1 and self.stage != 4:
            return [Asteroid(self.pos,
                             pygame.math.Vector2(1, 0).rotate(random.uniform(0, 360)) *
                             random.uniform(AST_MIN, AST_MAX),
                             self.stage - 1) for _ in range(2)]
        if self.stage == 4:
            return [Asteroid(self.pos,
                             pygame.math.Vector2(1, 0).rotate(random.uniform(0, 360)) *
                             random.uniform(AST_MIN, AST_MAX),
                             3) for _ in range(3)]
        return []


def circle_collide(p1, r1, p2, r2):
    return p1.distance_to(p2) < r1 + r2


def elastic_collision(a, b):
    collision = b.pos - a.pos
    distance = collision.length()
    if distance == 0:
        return
    normal = collision.normalize()
    rel_vel = b.vel - a.vel
    vel_along_normal = rel_vel.dot(normal)
    if vel_along_normal > 0:
        return
    impulse = vel_along_normal
    a.vel += impulse * normal
    b.vel -= impulse * normal
    overlap = (a.radius + b.radius - distance) / 2
    a.pos -= normal * overlap
    b.pos += normal * overlap


def spawn_asteroids(level):
    asts = []
    for _ in range(3 + level):
        pos = pygame.math.Vector2(random.randrange(WIDTH), random.randrange(HEIGHT))
        while pos.distance_to((WIDTH / 2, HEIGHT / 2)) < 100:
            pos = pygame.math.Vector2(random.randrange(WIDTH), random.randrange(HEIGHT))
        angle = random.uniform(0, 360)
        speed = random.uniform(AST_MIN, AST_MAX) + 0.2 * level
        vel = pygame.math.Vector2(speed, 0).rotate(angle)
        stage = random.choice([1, 2, 3])
        asts.append(Asteroid(pos, vel, stage))
    if random.random() < 0.3:
        pos = pygame.math.Vector2(random.randrange(WIDTH), random.randrange(HEIGHT))
        angle = random.uniform(0, 360)
        speed = random.uniform(AST_MIN, AST_MAX)
        vel = pygame.math.Vector2(speed, 0).rotate(angle)
        asts.append(Asteroid(pos, vel, 4))
    return asts


def main():
    ship = Ship((WIDTH / 2, HEIGHT / 2))
    bullets, asteroids = [], spawn_asteroids(1)
    score, level, cooldown = 0, 1, 0
    font = pygame.font.Font(None, 30)
    game_over = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()

        if not game_over:
            ship.update()

            if keys[pygame.K_SPACE] and cooldown <= 0:
                bullets.append(Bullet(ship.pos + ship.dir * ship.radius, ship.dir, ship.vel))
                cooldown = 10
            else:
                cooldown = max(0, cooldown - 1)

            for b in bullets:
                b.update()
            for ast in asteroids:
                ast.update()

            bullets = [b for b in bullets if b.life < BULLET_LIFE]

            new_asts = []
            for b in bullets[:]:
                for ast in asteroids[:]:
                    if circle_collide(b.pos, b.radius, ast.pos, ast.radius):
                        score += 100 * (ast.stage if ast.stage != 4 else 5)
                        new_asts.extend(ast.split())
                        if ast in asteroids:
                            asteroids.remove(ast)
                        if b in bullets:
                            bullets.remove(b)
                        break
            asteroids.extend(new_asts)

            if ship.invincible == 0:
                for ast in asteroids:
                    if circle_collide(ship.pos, ship.radius, ast.pos, ast.radius):
                        ship.lives -= 1
                        ship.invincible = 120
                        ship.pos.update(WIDTH / 2, HEIGHT / 2)
                        ship.vel.update(0, 0)
                        asteroids.remove(ast)
                        break

            for i in range(len(asteroids)):
                for j in range(i + 1, len(asteroids)):
                    if circle_collide(asteroids[i].pos, asteroids[i].radius, asteroids[j].pos, asteroids[j].radius):
                        elastic_collision(asteroids[i], asteroids[j])

            if not asteroids:
                level += 1
                asteroids = spawn_asteroids(level)
        else:
            if keys[pygame.K_RETURN]:
                main()

        if ship.lives <= 0:
            game_over = True

        screen.fill((0, 0, 0))
        for b in bullets:
            b.draw(screen)
        for ast in asteroids:
            ast.draw(screen)
        if not game_over:
            ship.draw(screen)

        hud = font.render(f"Score: {score}   Lives: {ship.lives}   Level: {level}", True, WHITE)
        screen.blit(hud, (10, 10))

        if game_over:
            msg = font.render("GAME OVER (Press ENTER to restart)", True, RED)
            screen.blit(msg, (WIDTH / 2 - msg.get_width() / 2, HEIGHT / 2))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
