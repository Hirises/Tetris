import pygame
import sys
from enum import Enum

SCREEN_WIDTH = 600
SCREEN_HEIGTH = 400
HORIZONTAL_CELL_COUNT = 10
VERTICAL_CELL_COUNT = 20
CELL_SIZE = 20
CELL_OFFSET = 1
EMPTY_CELL_COLOR = (0, 0, 0)
SCREEN_COLOR = (255, 255, 255)
GAME_SCREEN_COLOR = (150, 150, 150)
SCREEN_OFFSET = (200, 0)
TPS = 30
DEFAULT_TICK_PER_CELL = 10
ACCELERATED_TICK_PRE_CELL = 3
TICK_PER_CELL = 10

class CellState(Enum):
    Empty = 0
    Occupied = 1

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGTH))
clock = pygame.time.Clock()

#블럭 상태
cells = []
    
#글로벌 변수
manager = None
curBlock = None
pressedKey = []

def getRange(start, to, step):
    if step > 0:
        if start > to:
            return range(to, start, step)
        else:
            return range(start, to, step)
    elif step == 0:
        return []
    else:
        if start < to:
            return range(to, start, step)
        else:
            return range(start, to, step)

#블럭 객체 - 왼쪽 위가 (0, 0)
class Block:
    def __init__(self, originState, x = 0, y = 0, dirX = 1, dirY = 1, color = (255, 0, 0)):
        self.originState = originState
        self.x = x
        self.y = y
        self.dirX = dirX
        self.dirY = dirY
        self.curState = self.getState(self.dirX, self.dirY)
        self.color = color
        
    def getState(self, dirX, dirY):
        state = []
        for x in getRange(0, len(self.originState), dirX):
            tmp = []
            for y in getRange(0, len(self.originState[0]), dirY):
                tmp.append(self.originState[x][y])
            state.append(tmp)
        return state
    
    def move(self, dx, dy):
        if self.isColideWith(self.curState, self.x + dx, self.y + dy):
            self.landing()
            
        self.x += dx
        self.y += dy
        
    def landing(self):
        global curBlock
        
        for x in range(0, len(self.curState)):
            for y in range(0, len(self.curState[0])):
                if self.curState[x][y] is CellState.Occupied:
                    cells[x + self.x][y + self.y].changeState(CellState.Occupied, self.color)
                
        curBlock = None
        
        
    def isColideWith(self, state, locX, locY):
        if locX < 0 or locY < 0:
            return True
        
        for x in range(0, len(state)):
            for y in range(0, len(state[0])):
                if locX + x >= HORIZONTAL_CELL_COUNT:
                    return True
                if locY + y >= VERTICAL_CELL_COUNT:
                    return True
                
                if (state[x][y] is CellState.Occupied 
                    and cells[x + locX][y + locY].state is CellState.Occupied):
                    return True
        return False

#셀 하나하나의 상태
class Cell:
    def __init__(self, state = CellState.Empty, color = (255, 0, 0)):
        self.state = state
        self.color = color
        
    def changeState(self, state, color):
        self.state = state
        self.color = color

#게임 메니저
class GameManager:
    def __init__(self):
        self.tick = 0
    
    def keyUp(self, keyCode):
        global TICK_PER_CELL
        
        if keyCode == pygame.K_SPACE:
            TICK_PER_CELL = DEFAULT_TICK_PER_CELL
    
    def keyDown(self, keyCode):
        global TICK_PER_CELL
        
        if keyCode == pygame.K_SPACE:
            TICK_PER_CELL = ACCELERATED_TICK_PRE_CELL
            
        if keyCode == pygame.K_a:
            if not curBlock is None:
                curBlock.move(-1, 0)
        if keyCode == pygame.K_d:
            if not curBlock is None:
                curBlock.move(1, 0)
    
    def update(self):
        self.tick += 1
        
        if curBlock is None:
            self.spawnNewBlock()
        
        if self.tick % TICK_PER_CELL == 0:
            curBlock.move(0, 1)
    
    def spawnNewBlock(self):
        global curBlock
        
        curBlock = Block([[CellState.Occupied, CellState.Occupied],
                          [CellState.Occupied, CellState.Occupied]])
     
    def drawScreen(self):
        pygame.draw.rect(screen, GAME_SCREEN_COLOR, 
                         (SCREEN_OFFSET[0], SCREEN_OFFSET[1], 
                          CELL_SIZE * HORIZONTAL_CELL_COUNT, 
                          CELL_SIZE * VERTICAL_CELL_COUNT))
        
        for y in range(0, VERTICAL_CELL_COUNT):
            for x in range(0, HORIZONTAL_CELL_COUNT):
                if cells[x][y].state is CellState.Empty:
                    pygame.draw.rect(screen, EMPTY_CELL_COLOR, 
                                     (CELL_SIZE * x + SCREEN_OFFSET[0], 
                                      CELL_SIZE * y + SCREEN_OFFSET[1], 
                                      CELL_SIZE - CELL_OFFSET, CELL_SIZE - CELL_OFFSET))
                else:
                    pygame.draw.rect(screen, cells[x][y].color, 
                                     (CELL_SIZE * x + SCREEN_OFFSET[0],
                                      CELL_SIZE * y + SCREEN_OFFSET[1], 
                                      CELL_SIZE - CELL_OFFSET, CELL_SIZE - CELL_OFFSET))
        if not curBlock is None:
            state = curBlock.curState
            for x in range(curBlock.x, curBlock.x + len(state)):
                for y in range(curBlock.y, curBlock.y + len(state[0])):
                    if state[x - curBlock.x][y - curBlock.y] is CellState.Occupied:
                        pygame.draw.rect(screen, curBlock.color, 
                                         (CELL_SIZE * x + SCREEN_OFFSET[0], 
                                          CELL_SIZE * y + SCREEN_OFFSET[1], 
                                          CELL_SIZE - CELL_OFFSET, CELL_SIZE - CELL_OFFSET))
     
#초기화
manager = GameManager()

for x in range(0, HORIZONTAL_CELL_COUNT):
    tmp = []
    for y in range(0, VERTICAL_CELL_COUNT):
        tmp.append(Cell())
    cells.append(tmp)

#메인루프
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    
    curPressedKey = pygame.key.get_pressed();
    for keyCode in pressedKey:
        if not keyCode in curPressedKey:
            manager.keyUp(keyCode)
            pressedKey.remove(keyCode)
    for keyCode in curPressedKey:
        if not keyCode in pressedKey:
            manager.keyDown(keyCode)
            pressedKey.append(keyCode)
    
    manager.update()
    
    screen.fill(SCREEN_COLOR)
    manager.drawScreen()
    
    pygame.display.update()
    clock.tick(TPS)