#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Starting from Box2D.examples.simple.simple_02
"""
import pygame
from pygame.locals import (QUIT, KEYDOWN, K_ESCAPE)

import Box2D  # The main library
# Box2D.b2 maps Box2D.vec2 to vec2 (and so on)
from Box2D.b2 import (world, polygonShape, staticBody, dynamicBody, fixtureDef, vec2)


boardSize = 20
# --- constants ---
# Box2D deals with meters, but we want to display pixels,
# so define a conversion factor:
PPM = 1  # pixels per meter
TARGET_FPS = 60
TIME_STEP = 1.0 / TARGET_FPS
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480

# --- pygame setup ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
pygame.display.set_caption('Simple pygame example')
clock = pygame.time.Clock()

# --- pybox2d world setup ---
# Create the world
world = world(gravity=(0, 0), doSleep=True)

# # And a static body to hold the ground shape
# ground_body = world.CreateStaticBody(
#     position=(0, 1),
#     shapes=polygonShape(box=(50, 5)),
# )

# # Create a dynamic body
# dynamic_body = world.CreateDynamicBody(position=(10, 15), angle=15)

# # And add a box fixture onto it (with a nonzero density, so it will move)
# box = dynamic_body.CreatePolygonFixture(box=(2, 1), density=1, friction=0.3)

colors = {
    staticBody: (127, 127, 127, 255),
    dynamicBody: (255, 255, 255, 255),
}

class Board:
    """docstring for Board"""
    def __init__(self, stage, x, y, fixed):
        super(Board, self).__init__()
        pcb = fixtureDef(
            shape=polygonShape(box=(boardSize, boardSize)),
            density=2,
            friction=2
        )

        base = stage.CreateStaticBody(position=(x,y), angle=0)

        self.top = stage.CreateDynamicBody(position=(x,y), fixtures=pcb, angle=0)
        self.top.angularDamping = 8
        self.top.linearDamping = 8

        self.handle = vec2(x+(boardSize), y)

        if (fixed):
            stage.CreateRevoluteJoint(
                bodyA=base,
                bodyB=self.top,
                anchor=base.worldCenter,
                maxMotorTorque = 3.0,
                motorSpeed = 0.0,
            )
        else:
            stage.CreateDistanceJoint(
                bodyA=base,
                bodyB=self.top,
                anchorA=base.worldCenter,
                anchorB=self.top.worldCenter,
                frequencyHz = 0.05,
                dampingRatio = 0.01
            )



class Trace:
    """docstring for Trace"""
    def __init__(self, stage, boardA, endpointA, boardB, endpointB, segments):
        super(Trace, self).__init__()
        # self.arg = arg
        
        knot = fixtureDef(
            shape=polygonShape(box=(1, 1)),
            density=2,
            friction=0.6,
        )

        # Create springy chain
        prevBody = boardA
        prevBody = stage.CreateDynamicBody(
            position=endpointA,
            fixtures=knot
        )
        stage.CreateRevoluteJoint(
            bodyA=boardA,
            bodyB=prevBody,
            # anchor=(endpointA.x, endpointA.y),
            anchor=endpointA
        )

        for i in range(segments):
            x = endpointA.x + (i+1)*((endpointB.x - endpointA.x)/segments)
            y = endpointA.y + (i+1)*((endpointB.y - endpointA.y)/segments)
            body = stage.CreateDynamicBody(
                position=(x, y),
                fixtures=knot
            )
            body.linearDamping = 5
            halflength = (pygame.math.Vector2(prevBody.worldCenter.x, prevBody.worldCenter.y).distance_to((body.worldCenter.x, body.worldCenter.y)))/8
            stage.CreateDistanceJoint(
                frequencyHz=7,
                dampingRatio=1,
                bodyA=prevBody,
                bodyB=body,
                anchorA=prevBody.worldCenter,
                anchorB=body.worldCenter,
                length = halflength
            )

            prevBody = body

        stage.CreateRevoluteJoint(
            bodyA=prevBody,
            bodyB=boardB,
            # anchor=(endpointB.x, endpointB.y),
            anchor=endpointB
        )


board1 = Board(world, 30, 30, True)
board2 = Board(world, 200, 300, True)
trace1 = Trace(stage=world, boardA=board1.top, endpointA=board1.handle, boardB=board2.top, endpointB=board2.handle, segments=30)
obstacle1 = Board(world, 60, 80, False)
obstacle2 = Board(world, 180, 200, False)


# --- main game loop ---
running = True
while running:
    # Check the event queue
    for event in pygame.event.get():
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            # The user closed the window or pressed escape
            running = False

    screen.fill((200, 200, 200, 0))
    # Draw the world
    for body in (world.bodies):  # or: world.bodies
        # The body gives us the position and angle of its shapes
        for fixture in body.fixtures:
            # The fixture holds information like density and friction,
            # and also the shape.
            shape = fixture.shape

            # Naively assume that this is a polygon shape. (not good normally!)
            # We take the body's transform and multiply it with each
            # vertex, and then convert from meters to pixels with the scale
            # factor.
            vertices = [(body.transform * v) * PPM for v in shape.vertices]

            # But wait! It's upside-down! Pygame and Box2D orient their
            # axes in different ways. Box2D is just like how you learned
            # in high school, with positive x and y directions going
            # right and up. Pygame, on the other hand, increases in the
            # right and downward directions. This means we must flip
            # the y components.
            vertices = [(v[0], SCREEN_HEIGHT - v[1]) for v in vertices]

            pygame.draw.polygon(screen, colors[body.type], vertices)

        for joint in world.joints:
            p1, p2 = joint.anchorA, joint.anchorB
            p1Flipped = vec2(p1.x, SCREEN_HEIGHT - p1.y)
            p2Flipped = vec2(p2.x, SCREEN_HEIGHT - p2.y)
            pygame.draw.line(screen, (255,0,255,255), p1Flipped, p2Flipped)
    # Make Box2D simulate the physics of our world for one step.
    # Instruct the world to perform a single step of simulation. It is
    # generally best to keep the time step and iterations fixed.
    # See the manual (Section "Simulating the World") for further discussion
    # on these parameters and their implications.
    world.Step(TIME_STEP, 10, 10)

    # Flip the screen and try to keep at the target FPS
    pygame.display.flip()
    clock.tick(TARGET_FPS)

pygame.quit()
print('Done!')
