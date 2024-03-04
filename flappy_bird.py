import pygame
import neat
import time
import os
import random
pygame.font.init()

#THE GAME PART

# set dimensions of screen
WINDOW_WIDTH = 575
WINDOW_HEIGHT = 800
GEN = 0

bird_images = []
for i in range(1, 4):
    img = f'bird{str(i)}.png'
    # print(img)
    bird_images.append(pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', img))))
BIRD_IMAGES = bird_images
# print(BIRD_IMAGES)
PIPE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'pipe.png')))
BASE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'base.png')))
BACKGROUND_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bg.png')))

STAT_FONT = pygame.font.SysFont("comicsans", 50)

class Bird:
    IMGS = BIRD_IMAGES
    MAX_ROTATION = 25   # how much the bird looks down or up, here 25 degrees
    ROTATION_VELOCITY = 20   # how much the frames rotate
    ANIMATION_TIME = 5   # how fast or slow the animations take, e.g. how fast the bird flaps wings

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0   # how much the image is tilted, starts at 0 as bird is flat at start
        self.tick_count = 0   # represents time for frames, increments each frame
        self.velocity = 0   # speed of bird
        self.height = self.y    # height position of bird
        self.img_count = 0    # which img of bird currently in use between 1,2,3
        self.img = self.IMGS[0]   # first image

    def jump(self):
        self.velocity = -10.5  # negative as pygame screen base coordinate (0,0) starts at top left of screen
                            #    and bottom left would then be (0, +ve no.)
                            #    so trying to go up by jumping would mean going in the negative direction
                            #    which would require a negative velocity
        self.tick_count = 0  # keeps track of when last jumped
        self.height = self.y  # keeps track of position of last jump
        # after each jump self.tick_count and self.height is reset
        # this is done to emulate gravity and create the slow fall effect

    def move(self): # is called in the mainline according to fps
                    # so fps =30 would call move 30 times per second
        self.tick_count += 1  # increments in each frame

        # self.tick_count = time
        # therefore this equation is basically
        # x = v*t + 3/2 * t^2
        # here the displacement is the displacemnt of frames or the bird
        displacement = self.velocity*self.tick_count + 1.5*self.tick_count**2

        # emulating terminal velocity while falling
        # remember positive is downward movement
        if displacement >= 16:
            displacement = 16

        # negative is upward movement
        # therefore this just finetunes upward movement a little
        if displacement < 0:
            displacement -= 2

        # updating position pf bird
        self.y = self.y + displacement
        
        # handles the tilting of the bird
        if displacement < 0 or self.y < (self.height + 50):
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROTATION_VELOCITY

    def draw(self, window):
        self.img_count += 1

        # swaps between images at different animation times to create the flapping of the wings affect
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # creates the effect of nosediving when going down
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2  # this makes sure the starting bird image looks consistent
                                                    # it does this by changing the self_image count which means
                                                    # the bird image being shown by using the previous code
                                                    # will actually be self.IMGS[2]

        # rotates the bird around the center
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rectangle = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)
        window.blit(rotated_image, new_rectangle.topleft)

    # handle collision
    def get_mask(self):
        return pygame.mask.from_surface(self.img)
    
class Pipe:
    GAP = 185  # space between the pipes
    VELOCITY = 5  # speed at which the pipes are moving

    def __init__(self, x):
        self.x = x
        self.height = 0  # length

        self.top = 0   # where top pipe starts from
        self.bottom = 0   # where bottom pipe starts from
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMAGE, False, True)  # top pipe
        self.PIPE_BOTTOM = PIPE_IMAGE   # bottom pipe

        self.passed = False
        self.set_height()  # basically changes the top and bottom as well as the lengths of the pipes

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height() # this basically gets the starting position of the pipe
                                                            # understand that pipe length remains same as it is an img
                                                            # so for the pipes to have variable openings
                                                            # the pipes should start outside the window
                                                            # so the top pipe starts somewhere above the window
                                                            # which would be a negative coordinate
        # bottom pipe is actually easier as the the top part part of the pipe is where it starts
        # so it will start somewhere within the window depending on the gap
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VELOCITY # moves the pipes to the left a little

    def draw(self, window):
        window.blit(self.PIPE_TOP, (self.x, self.top))
        window.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    # using masks for pixel perfect collision handling
    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y)) # calculates distance of bird from top pipe
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y)) # calculates distance of bird from bottom pipe
        
        bototm_point = bird_mask.overlap(bottom_mask, bottom_offset) # if no collision then None
        top_point = bird_mask.overlap(top_mask, top_offset) # if no collision then None

        if top_point or bototm_point:  # if collision occurs
            return True
        
        return False
    
class Base:
    VELOCITY = 5 # must be same as pipe
    WIDTH = BASE_IMAGE.get_width()
    IMG = BASE_IMAGE

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    # basically we will keep 2 images of the base
    # one image on the screen and one image right after the first image
    # once the first image leaves the screen it will be moved immediately to the end of the second image
    # which is why we have self.x1 for the first image and self.x2 for the second image
    # understand that both images are moving at the same velocity to the left
    # so our x1/x2 pointers point to the rightmost edges of the images
    # so the image will once be moved to the end of the other image only when the entire image leaves the window
    def move(self):
        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY

        if (self.x1 + self.WIDTH)< 0:
            self.x1 = self.x2 + self.WIDTH
        
        if (self.x2 + self.WIDTH)<0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, window):
        window.blit(self.IMG, (self.x1, self.y))
        window.blit(self.IMG, (self.x2, self.y))  # this image will start completely outside the window
    
# the window where the game runs
def draw_window(window, birds, pipes, base, score, gen):
    window.blit(BACKGROUND_IMAGE, (0,0)) # blit draws the image specified on the window

    for pipe in pipes:
        pipe.draw(window)

    text = STAT_FONT.render(f"Score: {str(score)}", 1, (255,255,255))
    window.blit(text, (WINDOW_WIDTH-10-text.get_width(), 10))

    text = STAT_FONT.render(f"Generation: {str(gen)}", 1, (255,255,255))
    window.blit(text, (10, 10))

    base.draw(window)

    for bird in birds:
        
        bird.draw(window)
    pygame.display.update()

def main(genomes, config):
    global GEN
    GEN += 1
    networks = []                # all 3 of these lists correspond to each bird according to the index
    ge = []                 # for example, birds[3] will have networks[3] and genomes[3]
    birds = []

    for _, g in genomes:   # genomes is in shape (ID, OBJECT)
        bird = Bird(230, 350)
        network = neat.nn.FeedForwardNetwork.create(g, config)
        networks.append(network)
        birds.append(bird)           # each bird has same starting position
        g.fitness = 0
        ge.append(g)


    base = Base(730)
    pipes = [Pipe(700)]      # 700 is the position where the pipe starts 

    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()  # defines the framerate

    score = 0

    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            # quits the game if the x button is pressed
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        # bird movement
        pipe_index = 0
        if len(birds)>0:
            if len(pipes) > 1 and birds[0].x > (pipes[0].x + pipes[0].PIPE_TOP.get_width()):
                pipe_index = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            # activating the neural network while passing the parameters
            output = networks[x].activate((abs(bird.y - pipes[pipe_index].height), 
                                           abs(bird.y - pipes[pipe_index].bottom)))
            
            if output[0] > 0.5:        # in neat output is a list containing all output neurons
                                       # in our case even though we have 1 output neuron
                                       # it will still be in format [OBJECT]
                bird.jump()

        add_pipe = False
        remove_lst = []
        for pipe in pipes:
            for bird in birds:

                if pipe.collide(bird):
                    ge[birds.index(bird)].fitness -= 1
                    networks.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.remove(bird)

                if not pipe.passed and pipe.x < bird.x:     # checks if bird has passed pipe
                    pipe.passed = True                   
                    add_pipe = True

            if (pipe.x + pipe.PIPE_TOP.get_width()) < 0:  # if pipe is ouside screen
                remove_lst.append(pipe)                 # to be removed later
            
            pipe.move()

        if add_pipe:                   # generates a pipe immediately after passing
            score += 1
            for g in ge:              # this works as all birds that have collided have already been removed
                g.fitness += 5        # so only surviving birds get this boost to fitness
            pipes.append(Pipe(700))


        for rem in remove_lst:         # removes old pipes
            pipes.remove(rem)

        for bird in birds:

            if (bird.y + bird.img.get_height()) >= 730 or bird.y < 0:    # if bird hits floor
                networks.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.remove(bird)
                
        if score > 50:
            break

        base.move()
        draw_window(window, birds, pipes, base, score, GEN)
        

# NEAT FILE READER
def run(config_path):
    # sets the headers(inside []) as functions kinda
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    
    population = neat.Population(config)

    # prints the statistics of each generation
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    # runs upto 50 generations
    winner = population.run(main,50)

    # show final stats
    print(f'\nBest genome:\n{winner}')

# neat documentation recommended way to load up the neat_cofig file
if __name__ == "__main__":
    local_directory = os.path.dirname(__file__)
    config_path = os.path.join(local_directory, "neat_config.txt")
    run(config_path)