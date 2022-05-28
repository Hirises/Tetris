import re
import pygame
import sys
import random
from enum import Enum

import socket

#State Enum 정의
class AppState(Enum):
    Menu = 0
    Run = 1
class GameState(Enum):
    GameOver = -1
    Paused = 0
    Drop = 1
    WaitNewBlock = 2
    Animating = 3
class MenuState(Enum):
    Main = 0
    Setting = 1
    Help = 2
    KeySetting = 3
    NewWorkSetting = 4
    GameMode = 5
class CellState(Enum):
    Empty = 0
    Occupied = 1
class AnimationType(Enum):
    LineClear = 1
class Animation:
    def __init__(self, type, var):
        global gameState
        global preAnimaionState

        self.type = type
        self.tick = 0
        self.var = var

        if not gameState is GameState.Animating:
            preAnimaionState = gameState
            gameState = GameState.Animating

    def update(self):
        self.tick += 1
        if self.type == AnimationType.LineClear:
            if self.tick == 1:
                for x in range(0, HORIZONTAL_CELL_COUNT):
                    for y in self.var:
                        cells[x][y].changeState(CellState.Occupied, (255, 255, 255))
            elif (self.tick - 3) >= HORIZONTAL_CELL_COUNT:
                for x in range(0, HORIZONTAL_CELL_COUNT):
                    for y in self.var:
                        cells[x][y].changeState(CellState.Empty, (255, 0, 0))
                for locY in sorted(self.var):
                    for y in range(locY, 1, -1):
                        for x in range(0, HORIZONTAL_CELL_COUNT):
                            cells[x][y].changeState(cells[x][y - 1].state, cells[x][y - 1].color)
                animations.remove(self)
            elif self.tick >= 3:
                for y in self.var:
                    cells[self.tick - 3][y].changeState(CellState.Empty, (255, 255, 255))

#화면 설정
SCREEN_WIDTH = 600
SCREEN_HEIGTH = 400
TPS = 30
SCREEN_COLOR = (40, 20, 80)
GAME_SCREEN_COLOR = (150, 150, 150)
GAME_SCREEN_OFFSET = (200, 0)

#셀 설정
HORIZONTAL_CELL_COUNT = 10
VERTICAL_CELL_COUNT = 20
CELL_SIZE = 20
CELL_OFFSET = 1
EMPTY_CELL_COLOR = (0, 0, 0)

#블럭 설정
DEFAULT_TICK_PER_CELL = 10
ACCELERATED_TICK_PRE_CELL = 2
TICK_PER_CELL = DEFAULT_TICK_PER_CELL
SCORE_PER_LINE = 100
COMBO_SCORE = 50
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
FAKE_BLOCK_COLOR = (255, 255, 255)

#키 설정
KEY_INPUT_DELAY = 7
KEY_INPUT_REPEAT = 3
KEY_RIGHT = pygame.K_d
KEY_LEFT = pygame.K_a
KEY_TURN_RIGHT = pygame.K_w
KEY_TURN_LEFT = pygame.K_s
KEY_FAST_DROP = pygame.K_SPACE
KEY_PAUSE = pygame.K_q
ALL_CHECKING_KEYS = [KEY_RIGHT, KEY_LEFT, KEY_TURN_RIGHT, KEY_TURN_LEFT, KEY_FAST_DROP, KEY_PAUSE]

#초기화
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGTH))
clock = pygame.time.Clock()

#글로벌 변수
appState = AppState.Menu
menuState = MenuState.Main
pressedKey = {}
highScore = 0
manager = None
listener = None
port = 15500

#인게임 변수
gameState = GameState.WaitNewBlock
prePauseState = GameState.WaitNewBlock
preAnimaionState = GameState.WaitNewBlock
cells = []
score = 0
combo = 0
curBlock = None
fakeBlock = None
lastX = 0
animations = []

#선정의 메소드

def randomBit():
    if random.randint(0, 1) == 0:
        return 1
    else:
        return -1

#역순 입력 지원하는 range 메소드
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
        
#화면에 글자 출력
def displayText(string, x, y, size = 40, font = "arial", color = (0, 0, 0)):
    font = pygame.font.SysFont(font, size)
    text = font.render(string, True, color)
    rect = text.get_rect()
    rect.center = (x, y)
    screen.blit(text, rect)

#화면에 글자 + 사각형 배경 출력
def displayTextRect(string, x, y, dx, dy = 40, size = 40, font = "arial",
                    color = (0, 0, 0), backgroundColor = (255, 255, 255)):
    pygame.draw.rect(screen, backgroundColor, (x - dx / 2, y - dy / 2, dx, dy))
    font = pygame.font.SysFont(font, size)
    text = font.render(string, True, color)
    rect = text.get_rect()
    rect.center = (x, y)
    screen.blit(text, rect)
    
#마우스에 반응하는 글자 + 사각형 배경 출력
def displayInterectibleTextRect(pos, string, x, y, dx, dy = 40, size = 40, gain = 1.1, font = "arial",
                                color = (0, 0, 0), backgroundColor = (255, 255, 255),
                                newColor = (0, 0, 0), newBackgroundColor = (200, 200, 200)):
    
    if isCollideIn(pos, x, y, dx, dy):
        displayTextRect(string, x, y, int(dx * gain), int(dy * gain), int(size * gain), font, newColor, newBackgroundColor)
    else:
        displayTextRect(string, x, y, dx, dy, size, font, color, backgroundColor)

class TextField:
    def __init__(self, x, y, dx, dy, content = "", placeHolder = "", color = (0, 0, 0), backgroundColor = (255, 255, 255), size = 40, font = "arial"):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.content = content
        self.placeHolder = placeHolder
        self.color = color
        self.backgroundColor = backgroundColor
        self.size = size
        self.font = font
        self.focused = False
    
    def draw(self):
        if self.focused:
            displayTextRect(self.content + "|", x, y, self.dx, self.dy, self.size, self.font, self.color, self.backgroundColor)
        else:
            if self.content == "":
                displayTextRect(self.placeHolder, x, y, self.dx, self.dy, self.size, self.font, self.color, self.backgroundColor)
            else:
                displayTextRect(self.content, x, y, self.dx, self.dy, self.size, self.font, self.color, self.backgroundColor)

    def mouseDown(self, pos):
        if isCollideIn(pos, self.x, self.y, self.dx, self.dy):
            self.focused = True
        else:
            self.focused = False

    def keyDown(self, keyCode):
        if not self.focused:
            return

        if keyCode == pygame.K_ENTER:
            self.focused = False
        elif keyCode == pygame.K_BACKSPACE:
            if len(self.content) > 0:
                self.content = self.content[-1:]
        elif re.match("[0-9]|[a-z]|[A-Z]|\[[0-9]\]", pygame.key.name(keyCode)):
            self.content = self.content + str(pygame.key.name(keyCode))

#마우스 위치 검출
def isCollideIn(pos, x, y, dx, dy):
    posX = pos[0]
    posY = pos[1]
    leftX = x - dx / 2
    rightX = x + dx / 2
    upY = y + dy / 2
    downY = y - dy / 2
    
    return posX >= leftX and posX <= rightX and posY >= downY and posY <= upY

#람다 대용 키 입력 리스너
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

def getMyIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

#블럭 객체
class Block:
    def __init__(self, originState, x = 0, 
                 dirZ = 1, dirX = 1, dirY = 1, color = (255, 0, 0)):
        global fakeBlock

        self.originState = originState
        self.x = x
        self.y = 0
        self.dirX = dirX
        self.dirY = dirY
        self.dirZ = dirZ
        self.curState = self.getState(self.dirZ, self.dirX, self.dirY)
        self.color = color
        self.y -= len(self.curState[0]) - 1

        #화면 오른쪽으로 넘어가는 것 방지
        if self.x + len(self.curState) > HORIZONTAL_CELL_COUNT:
            self.x = HORIZONTAL_CELL_COUNT - len(self.curState)
            
        #게임 종료 감지
        if self.isColideWith(self.curState, self.x, self.y):
            manager.gameEnd()
            return

        #떨어질 위치 미리보기 생성
        fakeBlock = FakeBlock(self.curState, self.x, self.y, self.color)
        
    #회전 이후의 블럭 상태
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
        global fakeBlock

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
        fakeBlock = FakeBlock(self.curState, self.x, self.y, self.color)
        
    def turnLeft(self):
        global fakeBlock

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
        fakeBlock = FakeBlock(self.curState, self.x, self.y, self.color)
    
    def fall(self):
        if self.isColideWith(self.curState, self.x, self.y + 1):
            self.landing()
            
        self.y += 1
    
    def move(self, dx, dy):
        global fakeBlock

        if self.isColideWith(self.curState, self.x + dx, self.y + dy):
            return
        
        self.x += dx
        self.y += dy
        fakeBlock = FakeBlock(self.curState, self.x, self.y, self.color)
        
    def landing(self):
        global curBlock
        global gameState
        global lastX
        global score
        global fakeBlock
        global combo
        
        #블럭 배치
        for x in range(0, len(self.curState)):
            for y in range(0, len(self.curState[0])):
                if y + self.y < 0:
                    continue
                
                if self.curState[x][y] is CellState.Occupied:
                    cells[x + self.x][y + self.y].changeState(CellState.Occupied, self.color)
        
        #게임 종료 감지
        if self.y - len(self.curState[0]) + 1 < 0:
            self.y -= 1
            manager.gameEnd()
            return
        
        #다음 블럭 요청
        lastX = self.x
        gameState = GameState.WaitNewBlock
        curBlock = None
        fakeBlock = None

        #라인 클리어 감지
        lines = []
        for y in range(self.y + len(self.curState[0]) - 1, self.y - 1, - 1):
            if self.lineCheck(y):
                lines.append(y)
                score += SCORE_PER_LINE + COMBO_SCORE * combo
                combo += 1
        if len(lines) > 0:
            animations.append(Animation(AnimationType.LineClear, lines))
        else:
            combo = 0
            
    #라인 클리어 감지
    def lineCheck(self, y):
        for x in range(0, HORIZONTAL_CELL_COUNT):
            if cells[x][y].state is CellState.Empty:
                return False

        return True
        
    #충돌 감지
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

#떨어질 위치 표시용 가짜 블럭
class FakeBlock:
    def __init__(self, state, x, y, color):
        self.state = state
        self.x = x
        self.y = y
        self.color = color

        #바닥에 닿을 때까지 이동
        while not self.isColideWith(self.y + 1):
            self.y += 1

    #충돌감지 (Block 클래스와 동일)
    def isColideWith(self, locY):
        for x in range(0, len(self.state)):
            for y in range(0, len(self.state[0])):
                if self.x + x >= HORIZONTAL_CELL_COUNT:
                    return True
                if locY + y >= VERTICAL_CELL_COUNT:
                    return True
                if locY + y < 0:
                    continue
                
                if (self.state[x][y] is CellState.Occupied 
                    and cells[x + self.x][y + locY].state is CellState.Occupied):
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
        global combo
        
        lastX = 0
        gameState = gameState.WaitNewBlock
        self.tick = 0
        curBlock = None
        score = 0
        combo = 0
        cells.clear()
        for x in range(0, HORIZONTAL_CELL_COUNT):
            tmp = []
            for y in range(0, VERTICAL_CELL_COUNT):
                tmp.append(Cell())
            cells.append(tmp)
    
    def gameEnd(self):
        global gameState
        global highScore
        
        gameState = GameState.GameOver
        if score > highScore:
            highScore = score
    
    def keyUp(self, keyCode):
        global TICK_PER_CELL
        
        if keyCode == KEY_FAST_DROP:
            TICK_PER_CELL = DEFAULT_TICK_PER_CELL
    
    def keyPressed(self, keyCode):
        if not appState is AppState.Run or gameState is GameState.GameOver or gameState is GameState.Paused:
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
        global prePauseState
        
        if keyCode == KEY_FAST_DROP:
            TICK_PER_CELL = ACCELERATED_TICK_PRE_CELL
        
        if not appState is AppState.Run or gameState is GameState.GameOver:
            return
        
        if keyCode == KEY_PAUSE:
            if not gameState is GameState.GameOver:
                if gameState is GameState.Paused:
                    #다시 누르면 Pause 해제
                    gameState = prePauseState
                else:
                    prePauseState = gameState
                    gameState = GameState.Paused

        if  gameState is GameState.Paused:
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
    
    def update(self):
        global gameState

        if appState is AppState.Run:
            self.tick += 1
            
            if gameState is GameState.WaitNewBlock:
                if curBlock is None:
                    self.spawnNewBlock()
            elif gameState is GameState.Drop:
                if self.tick % TICK_PER_CELL == 0:
                    curBlock.fall()
            elif gameState is GameState.Animating:
                if len(animations) == 0:
                    #애니매이션 완료시 다시 시작
                    gameState = preAnimaionState
                for animation in animations:
                    animation.update()
    
    #다음 블럭 생성
    def spawnNewBlock(self):
        global curBlock
        global gameState
        
        curBlock = Block(ALL_BLOCK_STATES[random.randint(0, len(ALL_BLOCK_STATES) - 1)],
                         color = ALL_BLOCK_COLORS[random.randint(0, len(ALL_BLOCK_COLORS) - 1)],
                         dirZ = randomBit(), dirX = randomBit(), dirY = randomBit(), x = lastX)
        gameState = GameState.Drop

    #마우스 클릭시 
    def mouseUp(self):
        global appState
        global menuState
        global gameState
        global listener
        
        pos = pygame.mouse.get_pos()
        
        if appState is AppState.Menu:
            if menuState is MenuState.Main:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 150, 200, 40):
                    #메인 메뉴 - New Game
                    menuState = MenuState.GameMode
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 100, 200, 40):
                    #메인 메뉴 - Settings
                    menuState = MenuState.Setting
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    #메인 메뉴 - Quit
                    pygame.quit()
                    sys.exit()
            elif menuState is MenuState.GameMode:
                if isCollideIn(pos, SCREEN_WIDTH / 4 + 10, SCREEN_HEIGTH - 230, SCREEN_WIDTH / 2 - 50, SCREEN_HEIGTH - 140):
                    self.gameReset()
                    self.gameStart()
                elif isCollideIn(pos, SCREEN_WIDTH / 4 - 10, SCREEN_HEIGTH - 230, SCREEN_WIDTH / 2 - 50, SCREEN_HEIGTH - 140):
                    pass
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    menuState = MenuState.Main
            elif menuState is MenuState.Setting:
                if isCollideIn(pos, SCREEN_WIDTH / 2, 170, 200, 40):
                    #세팅 - Key Setting
                    menuState = MenuState.KeySetting
                elif isCollideIn(pos, SCREEN_WIDTH / 2, 220, 200, 40):
                    #세팅 - NewWork
                    menuState = MenuState.NewWorkSetting
                elif isCollideIn(pos, SCREEN_WIDTH / 2, 270, 200, 40):
                    #세팅 - Help
                    menuState = MenuState.Help
                elif isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    #세팅 - Quit
                    menuState = MenuState.Main
            elif menuState is MenuState.KeySetting:
                if isCollideIn(pos, SCREEN_WIDTH / 2 - 70, 130, 100, 30):
                    #키 세팅 - Left Move
                    listener = lambda keyCode : setLeftMoveKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 - 70, 180, 100, 30):
                    #키 세팅 - Right Move
                    listener = lambda keyCode : setRightMoveKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 - 70, 230, 100, 30):
                    #키 세팅 - Left Turn
                    listener = lambda keyCode : setLeftTurnKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 - 70, 280, 100, 30):
                    #키 세팅 - Right Turn
                    listener = lambda keyCode : setRightTurnKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 + 230, 130, 100, 30):
                    #키 세팅 - Fast Drop
                    listener = lambda keyCode : setDropFastKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 + 230, 180, 100, 30):
                    #키 세팅 - Pause Game
                    listener = lambda keyCode : setPauseKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    #키 세팅 - Quit
                    menuState = MenuState.Setting
            elif menuState == MenuState.Help:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    #도움말 - Quit
                    menuState = MenuState.Setting
            elif menuState == MenuState.NewWorkSetting:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    #네트워크 설정 - Quit
                    menuState = MenuState.Setting
        elif appState is AppState.Run:
            if gameState is GameState.GameOver:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 120, 200, 40):
                    #게임 오버 - Restart
                    self.gameReset()
                    self.gameStart()
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 70, 200, 40):
                    #게임 오버 - Back To Menu
                    menuState = MenuState.Main
                    appState = AppState.Menu
            elif gameState is GameState.Paused:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 155, 200, 40):
                    #정지 메뉴 - Continue
                    gameState = prePauseState
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 105, 200, 40):
                    #정지 메뉴 - Restart
                    self.gameEnd()
                    self.gameReset()
                    self.gameStart()
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 55, 200, 40):
                    #정지 메뉴 - Back To Menu
                    self.gameEnd()
                    menuState = MenuState.Main
                    appState = AppState.Menu
     
    def drawUI(self):
        pos = pygame.mouse.get_pos()
        if appState is AppState.Menu:
            if menuState is MenuState.Main:
                #메인 메뉴
                displayText("Tetris", SCREEN_WIDTH / 2, 100, size = 60, color = (255, 255, 255), font = "hancommalangmalang")
                displayText("highScore " + str(highScore), SCREEN_WIDTH / 2, 150, size = 25, color = (255, 255, 255), font = "hancommalangmalang")

                displayInterectibleTextRect(pos, "New Game", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 150, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Settings", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 100, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.GameMode:
                displayInterectibleTextRect(pos, "Sole", SCREEN_WIDTH / 4 + 10, SCREEN_HEIGTH - 230, SCREEN_WIDTH / 2 - 50, SCREEN_HEIGTH - 140, size = 80, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Duel", 3 * SCREEN_WIDTH / 4 - 10, SCREEN_HEIGTH - 230, SCREEN_WIDTH / 2 - 50, SCREEN_HEIGTH - 140, size = 80, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            
                displayInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.KeySetting:
                #키 설정
                displayText("Key Setting", SCREEN_WIDTH / 2, 50, size = 40, color = (255, 255, 255), font = "hancommalangmalang")


                displayText("Move Left", SCREEN_WIDTH / 2 - 200, 130, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, pygame.key.name(KEY_LEFT).upper(), SCREEN_WIDTH / 2 - 70, 130, 100, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                
                displayText("Move Right", SCREEN_WIDTH / 2 - 200, 180, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, pygame.key.name(KEY_RIGHT).upper(), SCREEN_WIDTH / 2 - 70, 180, 100, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                
                displayText("Turn Left", SCREEN_WIDTH / 2 - 200, 230, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, pygame.key.name(KEY_TURN_LEFT).upper(), SCREEN_WIDTH / 2 - 70, 230, 100, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                
                displayText("Turn Right", SCREEN_WIDTH / 2 - 200, 280, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, pygame.key.name(KEY_TURN_RIGHT).upper(), SCREEN_WIDTH / 2 - 70, 280, 100, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                
                displayText("Drop Fast", SCREEN_WIDTH / 2 + 100, 130, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, pygame.key.name(KEY_FAST_DROP).upper(), SCREEN_WIDTH / 2 + 230, 130, 100, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                
                displayText("Pause Game", SCREEN_WIDTH / 2 + 100, 180, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, pygame.key.name(KEY_PAUSE).upper(), SCREEN_WIDTH / 2 + 230, 180, 100, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                

                displayInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.Setting:
                #설정
                displayText("Settings", SCREEN_WIDTH / 2, 60, size = 40, color = (255, 255, 255), font = "hancommalangmalang")
                
                displayInterectibleTextRect(pos, "Key Setting", SCREEN_WIDTH / 2, 170, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "NetWork", SCREEN_WIDTH / 2, 220, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Help", SCREEN_WIDTH / 2, 270, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                
                displayInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.NewWorkSetting:
                #네트워크 설정
                displayText("Network Settings", SCREEN_WIDTH / 2, 60, size = 40, color = (255, 255, 255), font = "hancommalangmalang")

                displayText("Port", SCREEN_WIDTH / 2, 170, size = 40, color = (255, 255, 255), font = "hancommalangmalang")

                displayInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.Help:
                #도움말
                displayText("Help", SCREEN_WIDTH / 2, 60, size = 40, color = (255, 255, 255), font = "hancommalangmalang")
                
                displayText("move block to fill line", SCREEN_WIDTH / 2, 120, size = 30, color = (200, 200, 200), font = "hancommalangmalang")
                displayText("try not to fill screen", SCREEN_WIDTH / 2, 150, size = 30, color = (200, 200, 200), font = "hancommalangmalang")
                displayText("you can play both sole", SCREEN_WIDTH / 2, 200, size = 30, color = (200, 200, 200), font = "hancommalangmalang")
                displayText("and even with your friend!", SCREEN_WIDTH / 2, 230, size = 30, color = (200, 200, 200), font = "hancommalangmalang")
                displayText("please enjoy this game", SCREEN_WIDTH / 2, 280, size = 30, color = (200, 200, 200), font = "hancommalangmalang")
                
                displayInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
        elif appState is AppState.Run:
            if gameState is GameState.GameOver:
                #게임 오버
                displayTextRect("Game Over", SCREEN_WIDTH / 2, 100, dx = SCREEN_WIDTH, dy = 70, size = 60, color = (255, 255, 255), font = "hancommalangmalang", backgroundColor = (20, 20, 20))
                
                displayTextRect("score " + str(score), SCREEN_WIDTH / 2, 170, dy = 40, dx = 200, size = 30, color = (255, 255, 255), font = "hancommalangmalang", backgroundColor = (20, 20, 20))
                
                displayInterectibleTextRect(pos, "Restart", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 120, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Back to Menu", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 70, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif gameState is GameState.Paused:
                #정지 메뉴
                displayTextRect("Paused", SCREEN_WIDTH / 2, 100, dx = SCREEN_WIDTH, dy = 70, size = 60, color = (255, 255, 255), font = "hancommalangmalang", backgroundColor = (20, 20, 20))
                
                displayTextRect("score " + str(score), SCREEN_WIDTH / 2, 170, dy = 40, dx = 200, size = 30, color = (255, 255, 255), font = "hancommalangmalang", backgroundColor = (20, 20, 20))
                
                displayInterectibleTextRect(pos, "Continue", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 155, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Restart", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 105, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                displayInterectibleTextRect(pos, "Back to Menu", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 55, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            else:
                displayText(str(score), 500, 50, color = (255, 255, 255), font = "hancommalangmalang")
        
    def drawScreen(self):
        if appState is AppState.Run:
            #배경
            pygame.draw.rect(screen, GAME_SCREEN_COLOR, 
                             (GAME_SCREEN_OFFSET[0], GAME_SCREEN_OFFSET[1], 
                              CELL_SIZE * HORIZONTAL_CELL_COUNT, 
                              CELL_SIZE * VERTICAL_CELL_COUNT))
            
            #셀 그리기
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
                                         (CELL_SIZE * x + GAME_SCREEN_OFFSET[0], 
                                          CELL_SIZE * y + GAME_SCREEN_OFFSET[1], 
                                          CELL_SIZE - offsetX, CELL_SIZE - offsetY))
                    else:
                        pygame.draw.rect(screen, cells[x][y].color, 
                                         (CELL_SIZE * x + GAME_SCREEN_OFFSET[0],
                                          CELL_SIZE * y + GAME_SCREEN_OFFSET[1], 
                                          CELL_SIZE - offsetX, CELL_SIZE - offsetY))
            
            #페이크 블럭 그리기
            if not fakeBlock is None:
                state = fakeBlock.state
                for x in range(fakeBlock.x, fakeBlock.x + len(state)):
                    for y in range(fakeBlock.y, fakeBlock.y + len(state[0])):
                        if y < 0:
                            continue
                        
                        offsetX = CELL_OFFSET
                        offsetY = CELL_OFFSET
                        if x - 1 == HORIZONTAL_CELL_COUNT:
                            offsetX = 0
                        if y - 1 == VERTICAL_CELL_COUNT:
                            offsetY = 0
                        
                        if state[x - fakeBlock.x][y - fakeBlock.y] is CellState.Occupied:
                            pygame.draw.rect(screen, FAKE_BLOCK_COLOR, 
                                             (CELL_SIZE * x + GAME_SCREEN_OFFSET[0], 
                                              CELL_SIZE * y + GAME_SCREEN_OFFSET[1], 
                                              CELL_SIZE - offsetX, CELL_SIZE - offsetY))
            
            #블럭 그리기
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
                                             (CELL_SIZE * x + GAME_SCREEN_OFFSET[0], 
                                              CELL_SIZE * y + GAME_SCREEN_OFFSET[1], 
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

        #입력 처리
        if event.type == pygame.MOUSEBUTTONUP:
            manager.mouseUp()
        if not listener is None:
            if event.type == pygame.KEYDOWN:
                if event.key in ALL_CHECKING_KEYS:
                    continue
                listener(event.key)
                ALL_CHECKING_KEYS = [KEY_RIGHT, KEY_LEFT, KEY_TURN_RIGHT, KEY_TURN_LEFT, KEY_FAST_DROP, KEY_PAUSE]
    
    #키 입력 처리
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
    
    #메인 로직 처리
    manager.update()
    
    #화면 업데이트
    screen.fill(SCREEN_COLOR)
    manager.drawScreen()
    manager.drawUI()
    pygame.display.update()

    clock.tick(TPS)