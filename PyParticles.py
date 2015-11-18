import math, random
import time
import colorsys

PARTICLE_ELASTICITY = 1 # .9
MASS_OF_AIR = 0 # .02

def addVectors((angle1, length1), (angle2, length2)):
    """ Returns the sum of two vectors """
    
    x  = math.sin(angle1) * length1 + math.sin(angle2) * length2
    y  = math.cos(angle1) * length1 + math.cos(angle2) * length2
    
    angle  = 0.5 * math.pi - math.atan2(y, x)
    length = math.hypot(x, y)

    return (angle, length)

# I broke this for opposite destruct. If you wish to reinstate it, 
#  look at the original code, URL is in the header.
def combine(p1, p2):
    if math.hypot(p1.x - p2.x, p1.y - p2.y) < p1.size + p2.size:
        total_mass = p1.mass + p2.mass
        p1.x = (p1.x*p1.mass + p2.x*p2.mass)/total_mass
        p1.y = (p1.y*p1.mass + p2.y*p2.mass)/total_mass
        (p1.angle, p1.speed) = addVectors((p1.angle, p1.speed*p1.mass/total_mass), (p2.angle, p2.speed*p2.mass/total_mass))
        p1.speed *= (p1.elasticity*p2.elasticity)
        p1.mass += p2.mass
        p1.collide_with = p2

def opposite_destruct(p1, p2):
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    
    dist = math.hypot(dx, dy)
    if dist < p1.size + p2.size:
        if p1.species == -p2.species:
            p1.destroy = True
            p2.destroy = True

def collide(p1, p2):
    """ Tests whether two particles overlap
        If they do, make them bounce, i.e. update their angle, speed and position """
    
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    
    dist = math.hypot(dx, dy)
    if dist < p1.size + p2.size:
        angle = math.atan2(dy, dx) + 0.5 * math.pi
        total_mass = p1.mass + p2.mass

        (p1.angle, p1.speed) = addVectors((p1.angle, p1.speed*(p1.mass-p2.mass)/total_mass), (angle, 2*p2.speed*p2.mass/total_mass))
        (p2.angle, p2.speed) = addVectors((p2.angle, p2.speed*(p2.mass-p1.mass)/total_mass), (angle+math.pi, 2*p1.speed*p1.mass/total_mass))
        elasticity = p1.elasticity * p2.elasticity
        p1.speed *= elasticity
        p2.speed *= elasticity

        overlap = 0.5*(p1.size + p2.size - dist+1)
        p1.x += math.sin(angle)*overlap
        p1.y -= math.cos(angle)*overlap
        p2.x -= math.sin(angle)*overlap
        p2.y += math.cos(angle)*overlap

class Particle:
    """ A circular object with a velocity, size and mass """
    
    def __init__(self, (x, y), size, mass=1):
        self.x = x
        self.y = y
        self.size = size
        self.colour = (0, 0, 255)
        self.thickness = 0
        self.speed = 0
        self.angle = 0
        self.mass = mass
        self.drag = 1
        self.elasticity = PARTICLE_ELASTICITY
        self.destroy = False #Mark this particle for destruction next round
        self.type = 0
        self.species = -1

    def move(self):
        """ Update position based on speed, angle """

        self.x += math.sin(self.angle) * self.speed
        self.y -= math.cos(self.angle) * self.speed

    def experienceDrag(self):
        self.speed *= self.drag

    def mouseMove(self, (x, y)):
        """ Change angle and speed to move towards a given point """
        
        dx = x - self.x
        dy = y - self.y
        self.angle = 0.5*math.pi + math.atan2(dy, dx)
        self.speed = math.hypot(dx, dy) * 0.1
        
    def accelerate(self, vector):
        """ Change angle and speed by a given vector """
        (self.angle, self.speed) = addVectors((self.angle, self.speed), vector)
        
    def attract(self, other):
        """" Change velocity based on gravatational attraction between two particle"""
        
        dx = (self.x - other.x)
        dy = (self.y - other.y)
        dist  = math.hypot(dx, dy)
        
        if dist < self.size + self.size:
            return True

        theta = math.atan2(dy, dx)
        force = 0.2 * self.mass * other.mass / dist**2
        self.accelerate((theta- 0.5 * math.pi, force/self.mass))
        other.accelerate((theta+ 0.5 * math.pi, force/other.mass))

    def get_particle_color(self,num_species):
        #mult = 360/num_species
        mult = 1.0/num_species
        h = .5 + mult*self.species
        print "----------"
        print "num_species: %f"%(num_species)
        print "mult: %f"%(mult)
        print "H! %f"%(h)
        unscaled = colorsys.hsv_to_rgb(h, .5, .5)

        return (unscaled[0]*255,unscaled[1]*255,unscaled[2]*255)
        #return (species*mult,100,species*mult)

class Environment:
    """ Defines the boundary of a simulation and its properties """
    
    def __init__(self, (width, height)):
        self.width = width
        self.height = height
        self.particles = []
        
        self.colour = (255,255,255)
        self.mass_of_air = MASS_OF_AIR
        self.elasticity = 0.75
        self.acceleration = (0,0)
        
        self.particle_functions1 = []
        self.particle_functions2 = []
        self.function_dict = {
        'move': (1, lambda p: p.move()),
        'drag': (1, lambda p: p.experienceDrag()),
        'bounce': (1, lambda p: self.bounce(p)),
        'accelerate': (1, lambda p: p.accelerate(self.acceleration)),
        'react': (2, lambda p1, p2: self.react(p1,p2)),
        'collide': (2, lambda p1, p2: collide(p1, p2)),
        'combine': (2, lambda p1, p2: combine(p1, p2)),
        'attract': (2, lambda p1, p2: p1.attract(p2)),
        'opposite_destruct': (2, lambda p1, p2: opposite_destruct(p1, p2))}

        self.reaction_rules = {}
        self.species_count = None
        
    def addFunctions(self, function_list):
        for func in function_list:
            (n, f) = self.function_dict.get(func, (-1, None))
            if n == 1:
                self.particle_functions1.append(f)
            elif n == 2:
                self.particle_functions2.append(f)
            else:
                print "No such function: %s" % f

    def addNewFunction(self, key, tupe):
        self.function_dict[key] = tupe

    def addParticles(self, n=1, **kargs):
        """ Add n particles with properties given by keyword arguments """
        
        for i in range(n):
            size = kargs.get('size', random.randint(10, 20))
            mass = kargs.get('mass', random.randint(100, 10000))
            x = kargs.get('x', random.uniform(size, self.width-size))
            y = kargs.get('y', random.uniform(size, self.width-size))

            particle = Particle((x, y), size, mass)
            particle.speed = kargs.get('speed', random.random())
            particle.angle = kargs.get('angle', random.uniform(0, math.pi*2))
            particle.colour = kargs.get('colour', (0, 0, 255))
            particle.drag = (particle.mass/(particle.mass + self.mass_of_air)) ** particle.size

            self.particles.append(particle)

    def update(self):
        """  Moves particles and tests for collisions with the walls and each other """
        
        for i, particle in enumerate(self.particles):
            for f in self.particle_functions1:
                f(particle)
            for particle2 in self.particles[i+1:]:
                for f in self.particle_functions2:
                    f(particle, particle2)

    def bounce(self, particle):
        """ Tests whether a particle has hit the boundary of the environment """
        
        if particle.x > self.width - particle.size:
            particle.x = 2*(self.width - particle.size) - particle.x
            particle.angle = - particle.angle
            particle.speed *= self.elasticity

        elif particle.x < particle.size:
            particle.x = 2*particle.size - particle.x
            particle.angle = - particle.angle
            particle.speed *= self.elasticity

        if particle.y > self.height - particle.size:
            particle.y = 2*(self.height - particle.size) - particle.y
            particle.angle = math.pi - particle.angle
            particle.speed *= self.elasticity

        elif particle.y < particle.size:
            particle.y = 2*particle.size - particle.y
            particle.angle = math.pi - particle.angle
            particle.speed *= self.elasticity

    def react(self, p1, p2):
        if math.hypot(p1.x - p2.x, p1.y - p2.y) < p1.size + p2.size:
            a = b = None
            if (p1.species,p2.species) in self.reaction_rules:
                a = p1.species
                b = p2.species
            if (p2.species,p1.species) in self.reaction_rules:
                a = p2.species
                b = p1.species

            if a and b:
                #print "react!"
                #P1 becomes our combined molecule. For most purposes he is a new molecule.
                p1.species = self.reaction_rules[(a,b)]
                p1.colour = p1.get_particle_color(self.species_count)

                #Update mass, color, etc.
                total_mass = p1.mass + p2.mass
                p1.x = (p1.x*p1.mass + p2.x*p2.mass)/total_mass
                p1.y = (p1.y*p1.mass + p2.y*p2.mass)/total_mass
                (p1.angle, p1.speed) = addVectors((p1.angle, p1.speed*p1.mass/total_mass), (p2.angle, p2.speed*p2.mass/total_mass))
                p1.speed *= (p1.elasticity*p2.elasticity)
                p1.mass += p2.mass

                #Mark p2 for destruction
                p2.destroy = True
                
            

    def findParticle(self, (x, y)):
        """ Returns any particle that occupies position x, y """
        
        for particle in self.particles:
            if math.hypot(particle.x - x, particle.y - y) <= particle.size:
                return particle
        return None

    def shrink(self, xamt, yamt):
        """ Shrinks the universe, and moves particles into shrunken version"""
        if xamt <= self.width and yamt <= self.height:
            newx = self.width - xamt
            newy = self.height - yamt
            for i in range(newx, self.width):
                for j in range(newy, self.height):
                    p = self.findParticle((i,j))
                    if p:
                        p.x = newx / 2
                        p.y = newy / 2
                        #if p.y - yamt > 0: p.y = p.y - yamt

            self.width = self.width - xamt
            self.height = self.height - yamt
        else:
            print "invalid shrink amount %d %d! Silent return."%(xamt, xamt)
            print "%d %d"%(self.width, self.height)
            return



# class Genus(object):
#     """Specifies interactions between species, and their specifics"""



