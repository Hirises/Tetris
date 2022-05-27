import pygame
import sys
from enum import Enum

SCREEN_WIDTH = 600
SCREEN_HEIGTH = 400
HORIZONTAL_BLOCK_COUNT = 10
VERTICAL_BLOCK_COUNT = 20

class CellState(Enum):
    Empty = 0
    Occupied = 1

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGTH))
clock = pygame.time.Clock()

#블럭 상태
cells = []
for y in range(0, VERTICAL_BLOCK_COUNT):
    tmp = []
    for x in range(0, HORIZONTAL_BLOCK_COUNT):
        tmp.append(CellState.Empty)
    cells.append(tmp)

#블럭 객체 - 왼쪽 위가 (0, 0)
class Block:
    def __init__(self, blockStates, pivot = (0, 0), x = 0, y = 0):
        self.blockStates = blockStates
        self.pivot = pivot
        self.curState = self.blockStates[0]
        self.x = x
        self.y = y
        
    def getWorldPostion(self, localPos):
        return (self.x + localPos[0] - self.pivot[0], self.y + localPos[1] - self.pivot[1])
        
    def isCollideWithDown(self, state):
        for localX in range(0, len(state)):
            for localY in range(0, len(state[localX])):
                if state[localX][localY] is CellState.Empty:
                    continue
                elif state[localX][localY] is CellState.Occupied:
                    if cells[self.x + localX - self.pivot[0]][self.y + localY - self.pivot[1] + 1] is CellState.Occupied:
                        return True
                    break
        return False
    
    def isCollideWithRight(self, state):
        pass
    
    def isCollideWithLeft(self, state):
        pass
        
    def moveRight(self):
        if self.isCollideWithRight(self.curState):
            return
        
        self.x += 1

    def moveLeft(self):
        if self.isCollideWithLeft(self.curState):
            return
        
        self.x -= 1
        
    def moveDown(self):
        if self.isCollideWithDown(self.curState):
            return
        
        self.y += 1
        
    def turnRight(self):
        pass

    def turnLeft(self):
        pass
        

while True:
    for event in pygame.event.get():
        if event[pygame.QUIT]:
            pygame.quit()
            sys.exit()
    
    screen.fill((255, 255, 255))
    
    pygame.display.update()
    clock.tick(30)