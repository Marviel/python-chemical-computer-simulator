
#  Prelude: 
#    I got the building blocks of this particle simulator from here:  http://www.petercollingridge.co.uk/pygame-physics-simulation/
#    ...THANKS PETER!
#  
#  To Run:
#    Install Pygame and proper python for Pygame 
#    (instructions here for osX: http://stackoverflow.com/questions/13300585/trouble-installing-pygame-on-mac-osx)
#    $ /usr/local/bin/pythonw runChemSim.py

import random
import pygame
import PyParticles

class UniverseScreen:
    def __init__ (self, width, height):
        self.width = width
        self.height = height
        (self.dx, self.dy) = (0, 0)
        (self.mx, self.my) = (0, 0)
        self.magnification = 1.0
        
    def scroll(self, dx=0, dy=0):
        self.dx += dx * width / (self.magnification*10)
        self.dy += dy * height / (self.magnification*10)
        
    def zoom(self, zoom):
        self.magnification *= zoom
        self.mx = (1-self.magnification) * self.width/2
        self.my = (1-self.magnification) * self.height/2
        
    def reset(self):
        (self.dx, self.dy) = (0, 0)
        (self.mx, self.my) = (0, 0)
        self.magnification = 1.0
        
def calculateRadius(mass):
    return 0.5 * mass ** (0.5)

(width, height) = (1000, 1000)
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Chemical Computation')

universe = PyParticles.Environment((width, height))
universe.colour = (0,0,0)
universe.addFunctions(['move', 'collide', 'bounce'])
universe_screen = UniverseScreen(width, height)

#  -----------------Chemical interaction rules---------------------
#------------------------------------------------------------------
#DISCLAIMER: Right now this is just doing XOR. Sorry.

var_count = 2 #Boolean variables that this function has as input
#XOR in this case
#Expects arg to be a list of two booleans, or boolean castable things.
def f(args): 
    return bool(args[0]) != bool(args[1])

#Interactions return any particles they destroy.
def destructive_interaction(a,b):
    return [a,b]

#Get the color of a particle, given:
#  i: type of the particle
#  total_count: number of types of particle
def get_color(type, total_count):
    mult = 255/total_count
    return i*mult

# Set of Reaction Rules {(molecule_type_id,....molecule_type_id): output, ...}
R = {}
# Molecular species
M = [] #[(id,-id)]

truth_tables = [] # [[[]],...]  the list items are 2d matrices.

# 1. For each boolean variable bj:
for j in range(var_count):
    # (a) Add two molecular species, bj and Bj , to M;b
    M.append(j) #bj
    M.append(-j) #Bj
    # (b) Add one destructive reaction of the form bj + Bj → ∅ to R;
    R[(j,-j)] = lambda x,y: destructive_interaction(x,y)


# This is for the single output boolean variable.
M.append(var_count)
M.append(-var_count)

# 2. For each boolean function Fi:
#for f in F_list:  skip this... we're only doing XoR

# (a) Create the truth table of Fi with 2ni input cases (where ni is the arity of Fi);
# (b) For each input case, create a logical reaction.
truth_table = []
for i in range(2**var_count):
    binarr = list('{0:02b}'.format(i)) #The binary representation of the number, with each digit split into an array
    result = f(binarr)
    truth_table.append(binarr + [result])
    # i Lefthand side (reactants) corresponds to the input of Fi.
    # ii Righthand side (products) consists of one molecular species representing the respective boolean output of Fi.
    # //Here we create an tuple of molecules, where each molecule's species corresponds to either bi or Bi, 
    # //based on the binary digit in binarray at the same location.
    reactants = tuple([x if binarr[x] == 1 else -x for x in range(var_count)])
    R[reactants] = result

#Add first particles to universe.
for p in range(400):
    particle_mass = random.randint(1,4)
    particle_size = 10 #calculateRadius(particle_mass)
    universe.addParticles(mass=particle_mass, size=particle_size, speed=20, colour=(255,255,255))
    particle = universe.particles[p]
    particle.species = p%len(M/2)


key_to_function = {
    pygame.K_LEFT:   (lambda x: x.scroll(dx = 1)),
    pygame.K_RIGHT:  (lambda x: x.scroll(dx = -1)),
    pygame.K_DOWN:   (lambda x: x.scroll(dy = -1)),
    pygame.K_UP:     (lambda x: x.scroll(dy = 1)),
    pygame.K_EQUALS: (lambda x: x.zoom(2)),
    pygame.K_MINUS:  (lambda x: x.zoom(0.5)),
    pygame.K_r:      (lambda x: x.reset())}

clock = pygame.time.Clock()
paused = False
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key in key_to_function:
                key_to_function[event.key](universe_screen)
            elif event.key == pygame.K_SPACE:
                paused = (True, False)[paused]

    if not paused:
        universe.update()
        
    screen.fill(universe.colour)
    
    particles_to_remove = []
    for p in universe.particles:
        # if 'collide_with' in p.__dict__:
        #     particles_to_remove.append(p.collide_with)
        #     p.size = calculateRadius(p.mass)
        #     del p.__dict__['collide_with']

        x = int(universe_screen.mx + (universe_screen.dx + p.x) * universe_screen.magnification)
        y = int(universe_screen.my + (universe_screen.dy + p.y) * universe_screen.magnification)
        size = int(p.size * universe_screen.magnification)
        
        if size < 2:
            pygame.draw.rect(screen, p.colour, (x, y, 2, 2))
        else:
            pygame.draw.circle(screen, p.colour, (x, y), size, 0)
    
    for p in particles_to_remove:
        if p in universe.particles:
            universe.particles.remove(p)

    pygame.display.flip()
    clock.tick(80)