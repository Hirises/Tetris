import pygame
import sys
import random
from enum import Enum

class CellState(Enum):
    Empty = 0
    Occupied = 1
class AppState(Enum):
    Menu = 0
    Run = 1
class GameState(Enum):
    Pause = 0
    Drop = 1
    WaitNewBlock = 2
    Animating = 3

SCREEN_WIDTH = 600
SCREEN_HEIGTH = 400
HORIZONTAL_CELL_COUNT = 10
VERTICAL_CELL_COUNT = 20
CELL_SIZE = 20
CELL_OFFSET = 1
EMPTY_CELL_COLOR = (0, 0, 0)
SCREEN_COLOR = (40, 20, 80)
GAME_SCREEN_COLOR = (150, 150, 150)
SCREEN_OFFSET = (200, 0)
TPS = 30
DEFAULT_TICK_PER_CELL = 10
ACCELERATED_TICK_PRE_CELL = 2
TICK_PER_CELL = DEFAULT_TICK_PER_CELL
KEY_INPUT_DELAY = 7
KEY_INPUT_REPEAT = 3
ALL_CHECKING_KEYS = [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_SPACE]
ALL_BLOCK_STATES = [
    [[CellState.Occupied, CellState.Occupied],
     [CellState.Occupied, CellState.Occupied]],
    
    [[CellState.Occupied],
     [CellState.Occupied],
     [CellState.Occupied],
     [CellState.Occupied]],
    
    [[CellState.Occupied, CellState.Empty],
     [CellState.Occupied, CellState.Empty],
     [CellState.Occupied, CellState.Occupied]],
    
    [[CellState.Occupied, CellState.Empty],
     [CellState.Occupied, CellState.Occupied],
     [CellState.Occupied, CellState.Empty]],
    
    [[CellState.Occupied, CellState.Empty],
     [CellState.Occupied, CellState.Occupied],
     [CellState.Empty, CellState.Occupied]]
    ]
ALL_BLOCK_COLORS = [(0, 255, 0), (0, 0, 255), (255, 0, 0), (255, 255, 0), (255, 0, 255)]

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGTH))
clock = pygame.time.Clock()

#블럭 상태
cells = []
    
#글로벌 변수
manager = None

#게임 변수
gameState = GameState.WaitNewBlock
appState = AppState.Menu
score = 0
curBlock = None
pressedKey = {}
lastX = 0

def randomBit():
    if random.randint(0, 1) == 0:
        return 1
    else:
        return -1

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
            return range(to - 1, start - 1, step)
        else:
            return range(start, to, step)
        
def displayText(string, x, y, size = 40, font = "arial", color = (0, 0, 0)):
    font = pygame.font.SysFont(font, size)
    text = font.render(string, True, color)
    rect = text.get_rect()
    rect.center = (x, y)
    screen.blit(text, rect)

def displayTextRect(string, x, y, dx, dy = 40, size = 40, font = "arial", color = (0, 0, 0), backgroundColor = (255, 255, 255)):
    pygame.draw.rect(screen, backgroundColor, 
                     (x - dx / 2, y - dy / 2, dx, dy))
    font = pygame.font.SysFont(font, size)
    text = font.render(string, True, color)
    rect = text.get_rect()
    rect.center = (x, y)
    screen.blit(text, rect)

#블럭 객체 - 왼쪽 위가 (0, 0)
class Block:
    def __init__(self, originState, x = 0, 
                 dirZ = 1, dirX = 1, dirY = 1, color = (255, 0, 0)):
        self.originState = originState
        self.x = x
        self.y = 0
        self.dirX = dirX
        self.dirY = dirY
        self.dirZ = dirZ
        self.curState = self.getState(self.dirZ, self.dirX, self.dirY)
        self.color = color
    
        self.y -= len(self.curState[0]) - 1
        if self.x + len(self.curState) - 1 >= HORIZONTAL_CELL_COUNT:
            self.x -= self.x + len(self.curState) - HORIZONTAL_CELL_COUNT - 1
            
        if self.isColideWith(self.curState, self.x, self.y):
            manager.gameEnd()
        
    def getState(self, dirZ, dirX, dirY):
        state = []
        if dirZ == 1:
            for x in getRange(0, len(self.originState), dirX):
                tmp = []
                for y in getRange(0, len(self.originState[0]), dirY):
                    tmp.append(self.originState[x][y])
                state.append(tmp)
        else:
            for x in getRange(0, len(self.originState[0]), dirX):
                tmp = []
                for y in getRange(0, len(self.originState), dirY):
                    tmp.append(self.originState[y][x])
                state.append(tmp)
        return state
    
    def turnRight(self):
        dirZ = self.dirZ
        dirX = self.dirX
        dirY = self.dirY
        y = self.y
        
        dirZ *= -1
        if dirX == dirY:
            dirY *= -1
        else:
            dirX *= -1
        state = self.getState(dirZ, dirX, dirY)
        y -=  len(state[0]) - len(self.curState[0])
            
        if self.isColideWith(state, self.x, y):
            return
        
        self.curState = self.getState(dirZ, dirX, dirY)
        self.dirZ = dirZ
        self.dirX = dirX
        self.dirY = dirY
        self.y = y
        
    def turnLeft(self):
        dirZ = self.dirZ
        dirX = self.dirX
        dirY = self.dirY
        y = self.y
        
        dirZ *= -1
        if dirX == dirY:
            dirX *= -1
        else:
            dirY *= -1
        state = self.getState(dirZ, dirX, dirY)
        y -=  len(state[0]) - len(self.curState[0])
            
        if self.isColideWith(state, self.x, self.y):
            return
            
        self.curState = self.getState(dirZ, dirX, dirY)
        self.dirZ = dirZ
        self.dirX = dirX
        self.dirY = dirY
        self.y = y
    
    def fall(self):
        if self.isColideWith(self.curState, self.x, self.y + 1):
            self.landing()
            
        self.y += 1
    
    def move(self, dx, dy):
        if self.isColideWith(self.curState, self.x + dx, self.y + dy):
            return
            
        self.x += dx
        self.y += dy
        
    def landing(self):
        global curBlock
        global gameState
        global lastX
        
        for x in range(0, len(self.curState)):
            for y in range(0, len(self.curState[0])):
                if y + self.y < 0:
                    continue
                
                if self.curState[x][y] is CellState.Occupied:
                    cells[x + self.x][y + self.y].changeState(CellState.Occupied, self.color)
        
        if self.y - len(self.curState[0]) + 1 < 0:
            manager.gameEnd()
            return
        
        for y in range(self.y, self.y + len(self.curState[0])):
            self.lineCheck(y)
            
        lastX = self.x
        gameState = GameState.WaitNewBlock
        curBlock = None
            
    def lineCheck(self, y):
        global score
        
        for x in range(0, HORIZONTAL_CELL_COUNT):
            if cells[x][y].state is CellState.Empty:
                return
        
        for x in range(0, HORIZONTAL_CELL_COUNT):
            cells[x][y].changeState(CellState.Empty, (255, 0, 0))
        for y in range(y, 1, -1):
            for x in range(0, HORIZONTAL_CELL_COUNT):
                cells[x][y].changeState(cells[x][y - 1].state, cells[x][y - 1].color)
        score += 100
        
    def isColideWith(self, state, locX, locY):
        if locX < 0:
            return True
        
        for x in range(0, len(state)):
            for y in range(0, len(state[0])):
                if locX + x >= HORIZONTAL_CELL_COUNT:
                    return True
                if locY + y >= VERTICAL_CELL_COUNT:
                    return True
                if locY + y < 0:
                    continue
                
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
    
    def gameStart(self):
        global gameState
        
        self.gameReset()
        gameState.WaitNewBlock
    
    def gameReset(self):
        global score
        global cells
        global curBlock
        global gameState
        
        gameState.WaitNewBlock
        self.tick = 0
        curBlock = None
        score = 0
        for x in range(0, HORIZONTAL_CELL_COUNT):
            tmp = []
            for y in range(0, VERTICAL_CELL_COUNT):
                tmp.append(Cell())
            cells.append(tmp)
    
    def gameEnd(self):
        global gameState
        
        gameState = GameState.Pause
    
    def keyUp(self, keyCode):
        global TICK_PER_CELL
        
        if keyCode == pygame.K_SPACE:
            TICK_PER_CELL = DEFAULT_TICK_PER_CELL
    
    def keyPressed(self, keyCode):
        if not appState is AppState.Run:
            return
        
        if keyCode == pygame.K_a:
            if not curBlock is None:
                curBlock.move(-1, 0)
        if keyCode == pygame.K_d:
            if not curBlock is None:
                curBlock.move(1, 0)
    
    def keyDown(self, keyCode):
        global TICK_PER_CELL
        
        if keyCode == pygame.K_SPACE:
            TICK_PER_CELL = ACCELERATED_TICK_PRE_CELL
        
        if not appState is AppState.Run:
            return
        
        if keyCode == pygame.K_a:
            if not curBlock is None:
                curBlock.move(-1, 0)
        if keyCode == pygame.K_d:
            if not curBlock is None:
                curBlock.move(1, 0)
            
        if keyCode == pygame.K_w:
            if not curBlock is None:
                curBlock.turnLeft()
        if keyCode == pygame.K_s:
            if not curBlock is None:
                curBlock.turnRight()
    
    def update(self):
        if appState is AppState.Run:
            self.tick += 1
            
            if curBlock is None and gameState is GameState.WaitNewBlock:
                self.spawnNewBlock()
            
            if self.tick % TICK_PER_CELL == 0:
                curBlock.fall()
    
    def spawnNewBlock(self):
        global curBlock
        global gameState
        
        curBlock = Block(ALL_BLOCK_STATES[random.randint(0, len(ALL_BLOCK_STATES) - 1)],
                         color = ALL_BLOCK_COLORS[random.randint(0, len(ALL_BLOCK_COLORS) - 1)],
                         dirZ = randomBit(), dirX = randomBit(), dirY = randomBit(), x = lastX)
        gameState = GameState.Drop
     
    def drawUI(self):
        if appState is AppState.Menu:
            displayText("Tetris", SCREEN_WIDTH / 2, 100, size = 50, color = (255, 255, 255))
            displayTextRect("New Game", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 150, 200, 40, size = 30, color = (255, 255, 255), backgroundColor = (50, 50, 50))
            displayTextRect("Help", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 100, 200, 40, size = 30, color = (255, 255, 255), backgroundColor = (50, 50, 50))
            displayTextRect("Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 30, color = (255, 255, 255), backgroundColor = (50, 50, 50))
        elif appState is AppState.Run:
            displayText(str(score), 500, 50)
        
    def drawScreen(self):
        if appState is AppState.Run:
            pygame.draw.rect(screen, GAME_SCREEN_COLOR, 
                             (SCREEN_OFFSET[0], SCREEN_OFFSET[1], 
                              CELL_SIZE * HORIZONTAL_CELL_COUNT, 
                              CELL_SIZE * VERTICAL_CELL_COUNT))
            
            for y in range(0, VERTICAL_CELL_COUNT):
                for x in range(0, HORIZONTAL_CELL_COUNT):
                    offsetX = CELL_OFFSET
                    offsetY = CELL_OFFSET
                    if x + 1 >= HORIZONTAL_CELL_COUNT:
                        offsetX = 0
                    if y + 1 >= VERTICAL_CELL_COUNT:
                        offsetY = 0
                            
                    if cells[x][y].state is CellState.Empty:
                        pygame.draw.rect(screen, EMPTY_CELL_COLOR, 
                                         (CELL_SIZE * x + SCREEN_OFFSET[0], 
                                          CELL_SIZE * y + SCREEN_OFFSET[1], 
                                          CELL_SIZE - offsetX, CELL_SIZE - offsetY))
                    else:
                        pygame.draw.rect(screen, cells[x][y].color, 
                                         (CELL_SIZE * x + SCREEN_OFFSET[0],
                                          CELL_SIZE * y + SCREEN_OFFSET[1], 
                                          CELL_SIZE - offsetX, CELL_SIZE - offsetY))
            if not curBlock is None:
                state = curBlock.curState
                for x in range(curBlock.x, curBlock.x + len(state)):
                    for y in range(curBlock.y, curBlock.y + len(state[0])):
                        if y < 0:
                            continue
                        
                        offsetX = CELL_OFFSET
                        offsetY = CELL_OFFSET
                        if x - 1 == HORIZONTAL_CELL_COUNT:
                            offsetX = 0
                        if y - 1 == VERTICAL_CELL_COUNT:
                            offsetY = 0
                        
                        if state[x - curBlock.x][y - curBlock.y] is CellState.Occupied:
                            pygame.draw.rect(screen, curBlock.color, 
                                             (CELL_SIZE * x + SCREEN_OFFSET[0], 
                                              CELL_SIZE * y + SCREEN_OFFSET[1], 
                                              CELL_SIZE - offsetX, CELL_SIZE - offsetY))
     
#초기화
manager = GameManager()

for x in range(0, HORIZONTAL_CELL_COUNT):
    tmp = []
    for y in range(0, VERTICAL_CELL_COUNT):
        tmp.append(Cell())
    cells.append(tmp)

print(pygame.font.get_fonts())

#메인루프
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    
    curPressedKey = pygame.key.get_pressed()
    for keyCode in ALL_CHECKING_KEYS:
        if not curPressedKey[keyCode] and keyCode in pressedKey:
            manager.keyUp(keyCode)
            pressedKey.pop(keyCode)
        if curPressedKey[keyCode]:
            if not keyCode in pressedKey:
                manager.keyDown(keyCode)
                pressedKey[keyCode] = manager.tick
            elif (pressedKey[keyCode] >= KEY_INPUT_DELAY 
                  and manager.tick - pressedKey[keyCode] >= KEY_INPUT_DELAY
                  and (manager.tick - pressedKey[keyCode] - KEY_INPUT_DELAY) % KEY_INPUT_REPEAT == 0):
                manager.keyPressed(keyCode)
    
    manager.update()
    
    screen.fill(SCREEN_COLOR)
    manager.drawScreen()
    manager.drawUI()
    
    pygame.display.update()
    clock.tick(TPS)