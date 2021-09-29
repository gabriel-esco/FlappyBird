import pygame
import random
import time
import math
from enum import Enum
from os import path

pygame.init()

#################----Constant Values----#################
# I/O files
HS_FILE = "highscore.txt"

# set font
font1 = pygame.font.SysFont("menlo", 50)
font2 = pygame.font.SysFont("menlo", 30)
font3 = pygame.font.SysFont("menlo", 40)
all_fonts = pygame.font.get_fonts()

# images
flaps = [
    pygame.image.load("bird1.png"),
    pygame.image.load("bird2.png"),
    pygame.image.load("bird3.png"),
]
bird_png = pygame.image.load("bird.png")
bottom_pipe_png = pygame.image.load("pipe.png")
top_pipe_png = pygame.image.load("topPipe.png")
floor_tile_img = pygame.image.load("floor.png")
sound_on = pygame.image.load("sound_on.png")
sound_on = pygame.transform.scale(sound_on, (50, 45))
sound_off = pygame.image.load("sound_off.png")
sound_off = pygame.transform.scale(sound_off, (50, 45))
background = pygame.image.load("background.png")
background = pygame.transform.scale(background, (480, 800))

# sound effects
die_sound = pygame.mixer.Sound("sfx_die.wav")
hit_sound = pygame.mixer.Sound("sfx_hit.wav")
point_sound = pygame.mixer.Sound("sfx_point.wav")
swoosh_sound = pygame.mixer.Sound("sfx_swooshing.wav")
flap_sound = pygame.mixer.Sound("sfx_wing.wav")


# set constant rgb colors
WHITE = (255, 255, 255)
RED1 = (200, 0, 0)
RED2 = (240, 93, 118)
BLUE1 = (0, 0, 255)
BLUE2 = (0, 100, 255)
GREEN1 = (50, 168, 82)
GREEN2 = (68, 227, 110)
ORANGE = (255, 165, 0)
PURPLE = (138, 43, 226)
YELLOW = (245, 197, 66)
BLACK = (0, 0, 0)
FPS = 60
TARGET_FPS = 30
BLOCK_SIZE = 20
RUN_SPEED = 9
JUMP_SPEED = 20
G_CONST = 2.3
BIRD_WIDTH = 66
BIRD_HEIGHT = math.floor((158 / 221) * BIRD_WIDTH)

# set constant directions
class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4
    VERTICAL = 5
    HORIZONTAL = 6


#################----Object Definitions----#################
class Pipe(pygame.sprite.Sprite):
    def __init__(self, game, top, x=0, y=0, w=10, h=100):
        self.groups = game.pipes
        pygame.sprite.Sprite.__init__(self, self.groups)
        # store position
        self.w, self.h = (
            bottom_pipe_png.get_rect().width,
            bottom_pipe_png.get_rect().height,
        )
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.image = self.image.convert_alpha()
        # self.rect = self.image.get_rect()
        self.rect = pygame.Rect(x, y, self.w, self.h)
        self.rect.x = x
        self.rect.y = y
        self.counted = False
        self.top = top


class Floor:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = floor_tile_img.get_rect().width
        self.h = floor_tile_img.get_rect().height
        self.rect = pygame.Rect(x, y, self.w, self.h)
        self.counted = False


class Bird(pygame.sprite.Sprite):
    def __init__(self, game, x=0, y=0):
        pygame.sprite.Sprite.__init__(self)
        # store position
        self.image = pygame.transform.scale(bird_png, (BIRD_WIDTH, BIRD_HEIGHT))
        self.rect = self.image.get_rect()

        # store position
        self.x, self.y = x, y
        self.w, self.h = self.rect.width, self.rect.height
        self.rect.x, self.rect.y = self.x, self.y
        self.y_vel = 0
        self.dead = False
        self.flapCount = 0
        self.falling = False

    def _jump(self, game):
        self.y_vel = - JUMP_SPEED 

    def _landed(self, game):
        if self.rect.y >= game.floor - self.rect.height - 10:
            self.rect.y = game.floor - self.rect.height - 10
            return True
        return False


#################----Game Definition----#################
class FlappyBird:
    def __init__(self, w=480, h=740):
        self.w, self.h = w, h
        # init display
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption("Flappy Bird")
        self.dt = 1

        # sound settings
        self.sound_on = True
        self.sound_on_rect = pygame.Rect(
            self.w * 0.85, 5, sound_on.get_rect().width, sound_on.get_rect().height
        )
        self.sound_off_rect = pygame.Rect(
            self.w * 0.85, 5, sound_off.get_rect().width, sound_off.get_rect().height
        )
        self.load_data()
        self._reset()

    def _play_step(self):
        # check for user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if (
                    event.key == pygame.K_UP or event.key == pygame.K_SPACE
                ) and not self.bird.dead:
                    self.bird._jump(self)
                    self.play_sound(flap_sound)
                    if not self.started:
                        self.pipe_spawn_time = time.time()
                        self.started = True
            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                if (
                    self.sound_on_rect.x
                    < pos[0]
                    < self.sound_on_rect.x + self.sound_on_rect.width
                    and self.sound_on_rect.y
                    <= pos[1]
                    <= self.sound_on_rect.y + self.sound_on_rect.height
                ):
                    self._toggle_sound()

        if self.started and not self.round_over:
            # gravity pulls down
            self.bird.y_vel += G_CONST * self.dt * TARGET_FPS
            self.bird.rect.y += self.bird.y_vel * self.dt * TARGET_FPS
            if (
                self.bird.rect.y >= self.floor or self.bird.rect.y <= 0
            ) and not self.bird.dead:
                self.bird.dead = True
                self.play_sound(hit_sound)
                self._flash()
                pygame.time.delay(40)
            self.round_over = self.bird._landed(self)

            # spawn pipes
            spawn_time = random.uniform(0.5, 1) * 2 + self.pipe_spawn_time
            if time.time() >= spawn_time:
                hole_location = random.uniform(0.5, 0.75)
                top_pipe = Pipe(
                    self,
                    True,
                    self.w,
                    self.floor * hole_location - top_pipe_png.get_rect().height - 200,
                )
                bottom_pipe = Pipe(self, False, self.w, self.floor * hole_location)
                self.pipe_spawn_time = time.time()

        if not self.bird.dead:
            self.bird.flapCount += 1
            # move floor
            for floor in self.floor_tiles:
                floor.rect.x -= RUN_SPEED * self.dt * TARGET_FPS
            if self.floor_tiles[0].rect.x <= 0 and self.floor_tiles[0].counted == False:
                new_floor = Floor(
                    self.floor_tiles[0].rect.x + self.floor_tiles[0].w - 20, self.floor
                )
                self.floor_tiles.append(new_floor)
                self.floor_tiles[0].counted = True
                print("new floor")
            if self.floor_tiles[0].rect.x + self.floor_tiles[0].w <= 0:
                del self.floor_tiles[0]
                print("deleted floor")
            # move pipes
            for pipe in self.pipes:
                pipe.rect.x -= RUN_SPEED * self.dt * TARGET_FPS
                if (
                    pipe.rect.x < self.bird.rect.x
                    and pipe.counted == False
                    and pipe.top == False
                ):
                    pipe.counted = True
                    self.score += 1
                    self.play_sound(point_sound)
                if pipe.rect.x < 0 - pipe.w:
                    self.pipes.remove(pipe)
                    del pipe
        pipes_hit = pygame.sprite.spritecollide(self.bird, self.pipes, False)
        if len(pipes_hit) > 0 and not self.bird.dead:
            print(pipes_hit)
            self.bird.dead = True
            self.play_sound(hit_sound)
            self._flash()

        # start playing falling sound once bird is falling after dying
        if self.bird.dead and self.bird.y_vel > 5 and not self.bird.falling:
            self.bird.falling = True
            self.play_sound(die_sound)
            

        self._update_ui()
        return self.round_over

    def _reset(self):
        self.started = False
        # initialize characters
        self.bird = Bird(self, self.w * 0.13, self.h * 0.4)
        self.pipe_spawn_time = time.time()
        self.score = 0
        # store sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.pipes = pygame.sprite.Group()
        self.floor = self.h * (345 / 400)
        self.floor_tiles = []
        floor = Floor(0, self.floor)
        self.floor_tiles.append(floor)
        self.game_over_box = pygame.Rect(
            self.w / 2 - self.w / 4, self.h, self.w / 2, self.h * 0.4
        )
        self.round_over = False

    def _toggle_sound(self):
        if self.sound_on:
            self.sound_on = False
        else:
            self.sound_on = True

    #################----Helper Functions----#################
    def load_data(self):
        # load high score
        self.dir = path.dirname(__file__)
        with open(path.join(self.dir, HS_FILE), "r") as f:
            try:
                self.highscore = int(f.read())
            except:
                self.highscore = 0

    def play_sound(self, sound):
        if self.sound_on:
            sound.play()

    def rot_center(self, image, angle, x, y):

        scaled_image = pygame.transform.scale(image, (self.bird.w, self.bird.h))
        rotated_image = pygame.transform.rotate(scaled_image, angle)
        new_rect = rotated_image.get_rect(center=image.get_rect(center=(x, y)).center)
        new_rect.x = x
        new_rect.y = y

        return rotated_image, new_rect

    #################----Menus----#################
    def game_over_menu(self):
        self._update_ui()
        if self.game_over_box.y > self.h * 0.4 - (self.h * 0.4) / 2:
            self.game_over_box.y -= 35

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_SPACE:
                    self.play_sound(swoosh_sound)
                    return True
                if event.key == pygame.K_q:
                    pygame.quit()
                    quit()
            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                if (
                    self.sound_on_rect.x
                    < pos[0]
                    < self.sound_on_rect.x + self.sound_on_rect.width
                    and self.sound_on_rect.y
                    <= pos[1]
                    <= self.sound_on_rect.y + self.sound_on_rect.height
                ):
                    self._toggle_sound()
        return False

    #################----User Interface----#################

    def _update_ui(self):
        self.display.blit(background, pygame.Rect(0, 0, self.w, self.h))

        # draw pipes
        for pipe in self.pipes:
            if pipe.top == True:
                self.display.blit(
                    top_pipe_png,
                    pygame.Rect(pipe.rect.x, pipe.rect.y, pipe.rect.w, pipe.rect.h),
                )
            else:
                self.display.blit(
                    bottom_pipe_png,
                    pygame.Rect(pipe.rect.x, pipe.rect.y, pipe.rect.w, pipe.rect.h),
                )

        # draw floor
        # pygame.draw.rect(self.display, GREEN1, (0, self.h * 0.9, self.w, self.h))
        for floor_tile in self.floor_tiles:
            self.display.blit(floor_tile_img, floor_tile.rect)

        # draw bird
        if self.bird.flapCount >= 15:
            self.bird.flapCount = 0

        if self.started:
            angle = min(max(-self.bird.y_vel * 3 + 40, -90), 20)
            rotated_img = self.rot_center(
                flaps[self.bird.flapCount // 5],
                angle,
                self.bird.rect.x,
                self.bird.rect.y,
            )
            self.display.blit(rotated_img[0], rotated_img[1])
        else:
            self.display.blit(
                pygame.transform.scale(
                    flaps[self.bird.flapCount // 5], (self.bird.w, self.bird.h)
                ),
                self.bird.rect,
            )
        if self.sound_on:
            self.display.blit(sound_on, self.sound_on_rect)
        else:
            self.display.blit(sound_off, self.sound_off_rect)

        if self.round_over:
            if self.score > self.highscore:
                self.highscore = self.score
                with open(path.join(self.dir, HS_FILE), "w") as f:
                    f.write(str(self.score))
                highscore = font2.render("New High Score!: " + str(self.highscore), True, WHITE)
            else:
                highscore = font2.render("High Score: " + str(self.highscore), True, WHITE)
            pygame.draw.rect(self.display, ORANGE, self.game_over_box, border_radius=15)
            game_over_text = font3.render("GAME OVER", True, WHITE)
            score = font2.render("Score: " + str(self.score), True, WHITE)
            self.display.blit(
                game_over_text,
                [
                    self.w / 2 - game_over_text.get_rect().width / 2,
                    self.game_over_box.y + self.game_over_box.height * 0.1,
                ],
            )
            self.display.blit(
                score,
                [
                    self.w / 2 - score.get_rect().width / 2,
                    self.game_over_box.y + self.game_over_box.height / 2,
                ],
            )
            self.display.blit(
                highscore,
                [
                    self.w / 2 - highscore.get_rect().width / 2,
                    self.game_over_box.y
                    + self.game_over_box.height / 2
                    + score.get_rect().height,
                ],
            )
        else:
            score = font1.render(str(self.score), True, WHITE)
            self.display.blit(score, [self.w / 2 - score.get_rect().width / 2, 0])
        pygame.display.flip()

    def _flash(self):
        fade = pygame.Surface((self.w, self.h))
        fade.fill(WHITE)
        for alpha in range(0, math.floor(300 * self.dt * TARGET_FPS), math.floor(35 * self.dt * TARGET_FPS)):
            fade.set_alpha(alpha)
            self.display.blit(fade, (0, 0))
            pygame.display.flip()

    def _game_over_ui(self):
        pygame.draw.rect(self.display, ORANGE, self.game_over_box, border_radius=15)
        text = font1.render("GAME OVER", True, WHITE)
        score = font2.render("Score: " + str(self.score), True, WHITE)
        self.display.blit(
            text, [self.w / 2 - text.get_rect().width / 2, self.h * 0.4]
        )
        self.display.blit(
            score, [self.w / 2 - score.get_rect().width / 2, self.h * 0.4]
        )
        pygame.display.flip()


if __name__ == "__main__":

    def play(game):
        game_over = False
        prev_time = time.time()
        while not game_over:
            clock.tick(FPS)
            now = time.time()
            game.dt = now - prev_time
            prev_time = now
            game_over = game._play_step()
            if game_over:
                game.play_sound(swoosh_sound)
                game_end(game)

    def game_end(game):
        new_game = False
        while not new_game:
            clock.tick(FPS)
            new_game = game.game_over_menu()
        if new_game:
            game._reset()
            play(game)
        else:
            pygame.quit()
            quit()

    game = FlappyBird()
    clock = pygame.time.Clock()
    play(game)
