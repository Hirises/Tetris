import pygame
import sys
import random
from enum import Enum

class AppState(Enum):
    Menu = 0
    Run = 1
class GameState(Enum):
    GameOver = -1
    Pause = 0
    Drop = 1
    WaitNewBlock = 2
    Animating = 3
class MenuState(Enum):
    Main = 0
    Setting = 1
    Help = 2
    KeySetting = 3
    ScoreBoard = 4
class CellState(Enum):
    Empty = 0
    Occupied = 1

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
KEY_RIGHT = pygame.K_d
KEY_LEFT = pygame.K_a
KEY_TURN_RIGHT = pygame.K_w
KEY_TURN_LEFT = pygame.K_s
KEY_FAST_DROP = pygame.K_SPACE
KEY_PAUSE = pygame.K_q
ALL_CHECKING_KEYS = [KEY_RIGHT, KEY_LEFT, KEY_TURN_RIGHT, KEY_TURN_LEFT, KEY_FAST_DROP, KEY_PAUSE]
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
menuState = MenuState.Main
score = 0
curBlock = None
pressedKey = {}
lastX = 0
lastState = GameState.WaitNewBlock
listener = None

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

def displayTextRect(string, x, y, dx, dy = 40, size = 40, font = "arial",
                    color = (0, 0, 0), backgroundColor = (255, 255, 255)):
    pygame.draw.rect(screen, backgroundColor, (x - dx / 2, y - dy / 2, dx, dy))
    font = pygame.font.SysFont(font, size)
    text = font.render(string, True, color)
    rect = text.get_rect()
    rect.center = (x, y)
    screen.blit(text, rect)
    
def isCollideIn(pos, x, y, dx, dy):
    posX = pos[0]
    posY = pos[1]
    leftX = x - dx / 2
    rightX = x + dx / 2
    upY = y + dy / 2
    downY = y - dy / 2
    
    return posX >= leftX and posX <= rightX and posY >= downY and posY <= upY
    
def displayInterectibleTextRect(pos, string, x, y, dx, dy = 40, size = 40, gain = 1.1, font = "arial",
                                color = (0, 0, 0), backgroundColor = (255, 255, 255),
                                newColor = (0, 0, 0), newBackgroundColor = (200, 200, 200)):
    
    if isCollideIn(pos, x, y, dx, dy):
        displayTextRect(string, x, y, int(dx * gain), int(dy * gain), int(size * gain), font, newColor, newBackgroundColor)
    else:
        displayTextRect(string, x, y, dx, dy, size, font, color, backgroundColor)

def setLeftMoveKey(keyCode):
    global KEY_LEFT
    global listener
    listener = None
    KEY_LEFT = keyCode
def setRightMoveKey(keyCode):
    global KEY_RIGHT
    global listener
    listener = None
    KEY_RIGHT = keyCode
def setLeftTurnKey(keyCode):
    global KEY_TURN_LEFT
    global listener
    listener = None
    KEY_TURN_LEFT = keyCode
def setRightTurnKey(keyCode):
    global KEY_TURN_RIGHT
    global listener
    listener = None
    KEY_TURN_RIGHT = keyCode
def setDropFastKey(keyCode):
    global KEY_FAST_DROP
    global listener
    listener = None
    KEY_FAST_DROP = keyCode
def setPauseKey(keyCode):
    global KEY_PAUSE
    global listener
    listener = None
    KEY_PAUSE = keyCode

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
        
        if self.x + len(self.curState) > HORIZONTAL_CELL_COUNT:
            self.x = HORIZONTAL_CELL_COUNT - len(self.curState)
            
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
            self.y -= 1
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
        if locX + len(state) > HORIZONTAL_CELL_COUNT:
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
        global appState
        
        self.gameReset()
        gameState = GameState.WaitNewBlock
        appState = AppState.Run
    
    def gameReset(self):
        global score
        global cells
        global curBlock
        global gameState
        global lastX
        
        lastX = 0
        gameState = gameState.WaitNewBlock
        self.tick = 0
        curBlock = None
        score = 0
        cells.clear()
        for x in range(0, HORIZONTAL_CELL_COUNT):
            tmp = []
            for y in range(0, VERTICAL_CELL_COUNT):
                tmp.append(Cell())
            cells.append(tmp)
    
    def gameEnd(self):
        global gameState
        
        gameState = GameState.GameOver
    
    def keyUp(self, keyCode):
        global TICK_PER_CELL
        
        if keyCode == KEY_FAST_DROP:
            TICK_PER_CELL = DEFAULT_TICK_PER_CELL
    
    def keyPressed(self, keyCode):
        if not appState is AppState.Run:
            return
        
        if keyCode == KEY_LEFT:
            if not curBlock is None:
                curBlock.move(-1, 0)
        if keyCode == KEY_RIGHT:
            if not curBlock is None:
                curBlock.move(1, 0)
    
    def keyDown(self, keyCode):
        global TICK_PER_CELL
        global gameState
        global lastState
        
        if keyCode == KEY_FAST_DROP:
            TICK_PER_CELL = ACCELERATED_TICK_PRE_CELL
        
        if not appState is AppState.Run:
            return
        
        if keyCode == KEY_LEFT:
            if not curBlock is None:
                curBlock.move(-1, 0)
        if keyCode == KEY_RIGHT:
            if not curBlock is None:
                curBlock.move(1, 0)
            
        if keyCode == KEY_TURN_LEFT:
            if not curBlock is None:
                curBlock.turnLeft()
        if keyCode == KEY_TURN_RIGHT:
            if not curBlock is None:
                curBlock.turnRight()
        if keyCode == KEY_PAUSE:
            if not gameState is GameState.GameOver:
                if gameState is GameState.Pause:
                    gameState = lastState
                else:
                    lastState = gameState
                    gameState = GameState.Pause
    
    def update(self):
        if appState is AppState.Run:
            self.tick += 1
            
            if curBlock is None and gameState is GameState.WaitNewBlock:
                self.spawnNewBlock()
            
            if self.tick % TICK_PER_CELL == 0 and gameState is GameState.Drop:
                curBlock.fall()
    
    def spawnNewBlock(self):
        global curBlock
        global gameState
        
        curBlock = Block(ALL_BLOCK_STATES[random.randint(0, len(ALL_BLOCK_STATES) - 1)],
                         color = ALL_BLOCK_COLORS[random.randint(0, len(ALL_BLOCK_COLORS) - 1)],
                         dirZ = randomBit(), dirX = randomBit(), dirY = randomBit(), x = lastX)
        gameState = GameState.Drop
     
    def mouseUp(self):
        global appState
        global menuState
        global gameState
        global listener
        
        pos = pygame.mouse.get_pos()
        
        if appState is AppState.Menu:
            if menuState is MenuState.Main:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 150, 200, 40):
                    self.gameReset()
                    self.gameStart()
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 100, 200, 40):
                    menuState = MenuState.Setting
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    pygame.quit()
                    sys.exit()
            elif menuState is MenuState.Setting:
                if isCollideIn(pos, SCREEN_WIDTH / 2, 170, 200, 40):
                    menuState = MenuState.KeySetting
                elif isCollideIn(pos, SCREEN_WIDTH / 2, 220, 200, 40):
                    menuState = MenuState.ScoreBoard
                elif isCollideIn(pos, SCREEN_WIDTH / 2, 270, 200, 40):
                    menuState = MenuState.Help
                elif isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    menuState = MenuState.Main
            elif menuState is MenuState.KeySetting:
                if isCollideIn(pos, SCREEN_WIDTH / 2 - 50, 130, 80, 30):
                    listener = lambda keyCode : setLeftMoveKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 - 50, 180, 80, 30):
                    listener = lambda keyCode : setRightMoveKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 - 50, 230, 80, 30):
                    listener = lambda keyCode : setLeftTurnKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 - 50, 280, 80, 30):
                    listener = lambda keyCode : setRightTurnKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 + 250, 130, 80, 30):
                    listener = lambda keyCode : setDropFastKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 + 250, 180, 80, 30):
                    listener = lambda keyCode : setPauseKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    menuState = MenuState.Setting
            elif menuState == MenuState.Help:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    menuState = MenuState.Setting
            elif menuState == MenuState.ScoreBoard:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    menuState = MenuState.Setting
        elif appState is AppState.Run:
            if gameState is GameState.GameOver:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 120, 200, 40):
                    self.gameReset()
                    self.gameStart()
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 70, 200, 40):
                    menuState = MenuState.Main
                    appState = AppState.Menu
            elif gameState is GameState.Pause:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 155, 200, 40):
                    gameState = lastState
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 105, 200, 40):
                    self.gameReset()
                    self.gameStart()
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 55, 200, 40):
                    menuState = MenuState.Main
                    appState = AppState.Menu
     
    def drawUI(self):
        pos = pygame.mouse.get_pos()
        if appState is AppState.Menu:
            if menuState is MenuState.Main:
                displayText("Tetris", SCREEN_WIDTH / 2, 100, size = 60, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "New Game", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 150, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Settings", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 100, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.KeySetting:
                displayText("Key Setting", SCREEN_WIDTH / 2, 50, size = 40, color = (255, 255, 255), font = "hancommalangmalang")
                displayText("Move Left", SCREEN_WIDTH / 2 - 200, 130, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, pygame.key.name(KEY_LEFT).upper(), SCREEN_WIDTH / 2 - 50, 130, 80, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayText("Move Right", SCREEN_WIDTH / 2 - 200, 180, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, pygame.key.name(KEY_RIGHT).upper(), SCREEN_WIDTH / 2 - 50, 180, 80, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayText("Turn Left", SCREEN_WIDTH / 2 - 200, 230, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, pygame.key.name(KEY_TURN_LEFT).upper(), SCREEN_WIDTH / 2 - 50, 230, 80, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayText("Turn Right", SCREEN_WIDTH / 2 - 200, 280, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, pygame.key.name(KEY_TURN_RIGHT).upper(), SCREEN_WIDTH / 2 - 50, 280, 80, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayText("Drop Fast", SCREEN_WIDTH / 2 + 100, 130, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, pygame.key.name(KEY_FAST_DROP).upper(), SCREEN_WIDTH / 2 + 250, 130, 80, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayText("Pause", SCREEN_WIDTH / 2 + 100, 180, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, pygame.key.name(KEY_PAUSE).upper(), SCREEN_WIDTH / 2 + 250, 180, 80, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.Setting:
                displayText("Settings", SCREEN_WIDTH / 2, 60, size = 40, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Key Setting", SCREEN_WIDTH / 2, 170, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Score Board", SCREEN_WIDTH / 2, 220, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Help", SCREEN_WIDTH / 2, 270, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.ScoreBoard:
                displayInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.Help:
                displayText("Help", SCREEN_WIDTH / 2, 60, size = 40, color = (255, 255, 255), font = "hancommalangmalang")
                displayText("move block to fill line", SCREEN_WIDTH / 2, 120, size = 30, color = (255, 255, 255), font = "hancommalangmalang")
                displayText("try not to fill screen", SCREEN_WIDTH / 2, 150, size = 30, color = (255, 255, 255), font = "hancommalangmalang")
                displayText("you can play both sole", SCREEN_WIDTH / 2, 200, size = 30, color = (255, 255, 255), font = "hancommalangmalang")
                displayText("and even with your friend!", SCREEN_WIDTH / 2, 230, size = 30, color = (255, 255, 255), font = "hancommalangmalang")
                displayText("please enjoy this game", SCREEN_WIDTH / 2, 280, size = 30, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
        elif appState is AppState.Run:
            if gameState is GameState.GameOver:
                displayText("Game Over", SCREEN_WIDTH / 2, 100, size = 60, color = (255, 255, 255), font = "hancommalangmalang")
                displayText("score " + str(score), SCREEN_WIDTH / 2, 170, size = 30, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Restart", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 120, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Back to Menu", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 70, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif gameState is GameState.Pause:
                displayText("Paused", SCREEN_WIDTH / 2, 100, size = 60, color = (255, 255, 255), font = "hancommalangmalang")
                displayText("score " + str(score), SCREEN_WIDTH / 2, 170, size = 30, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Continue", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 155, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Restart", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 105, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Back to Menu", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 55, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            else:
                displayText(str(score), 500, 50, color = (255, 255, 255), font = "hancommalangmalang")
        
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

#메인루프
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONUP:
            manager.mouseUp()
        if not listener is None:
            if event.type == pygame.KEYDOWN:
                if event.key in ALL_CHECKING_KEYS:
                    continue
                listener(event.key)
                ALL_CHECKING_KEYS = [KEY_RIGHT, KEY_LEFT, KEY_TURN_RIGHT, KEY_TURN_LEFT, KEY_FAST_DROP, KEY_PAUSE]
    
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