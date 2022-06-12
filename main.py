#--- Import 영역 ------------------------------------------------------------------------------------------------------------------------------------------------

import re
import threading
import pygame
import sys
import random
import socket
from enum import Enum


# --- 상수 영역 ------------------------------------------------------------------------------------------------------------------------------------------------

GAME_VERSION = 1

#실행 플레그
FLAG_PRINT_DEBUG_LOG = True     #디버깅 메세지 출력
FLAG_RANDOM_IGNORE_PACKET = False   #의도적으로 패킷 손실시키기
FLAG_PACKET_IGNORE_RATE = 3     #패킷 손실률

#화면 설정
SCREEN_RESOLUTION = 1         #화면 해상도
PRE_SCREEN_RESOLUTION = 1
RESET_DELAY_SEC = 10                #해상도 설정 초기화 대기 시간(초)
SCREEN_RESOLUTIONS = [
                        1,      #600 X 400
                        1.5,    #900 X 600
                        2,      #1200 X 800
                        3       #1800 X 1200
                     ]      
SCREEN_WIDTH = 600
SCREEN_HEIGTH = 400
TPS = 30
SCREEN_COLOR = (40, 20, 80)
GAME_SCREEN_COLOR = (150, 150, 150)
GAME_SCREEN_OFFSET_MID = (200, 0)
GAME_SCREEN_OFFSET_LEFT = (0, 0)
GAME_SCREEN_OFFSET_RIGHT = (300, 0)

#게임 설정
class AppState(Enum):   #앱 상태
    Menu = 0
    Game = 1
class GameState(Enum):  #게임 상태
    GameOver = -1
    Paused = 0
    Drop = 1
    WaitNewBlock = 2
    Animating = 3
class MenuState(Enum):  #메뉴 위치
    Main = 0
    GameMode = 1
    CreateRoom = 2
    EnterRoom = 3
    Options = 4
    KeySetting = 5
    Settings = 6
    Help = 7
class GameType(Enum):   #게임 환경
    Local = 0
    Network = 1
class GameMode(Enum):   #게임 모드
    Classic = 0
    Fusion = 1

#셀 설정
HORIZONTAL_CELL_COUNT = 10
VERTICAL_CELL_COUNT = 20
CELL_SIZE = 20
CELL_OFFSET = 1
EMPTY_CELL_COLOR = (0, 0, 0)
class CellState(Enum):
    Empty = 0
    Occupied = 1
class CellEffect(Enum):
    Default = 0
    Confusion = 1
    Blindness = 2
    SpeedUp = 3
CELL_EFFECT_RATE = [97, 1, 1, 1]    #CellEffect Enum 순서와 같다

#블럭 설정
DEFAULT_TICK_PER_CELL = 10      #블럭이 1칸 떨어지는데 걸리는 틱 수
ACCELERATED_TICK_PRE_CELL = 2
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
class AnimationType(Enum):
    LineClear = 1

#키 설정
KEY_INPUT_DELAY_TICK = 7
KEY_INPUT_REPEAT_TICK = 3
KEY_RIGHT = pygame.K_d
KEY_LEFT = pygame.K_a
KEY_TURN_RIGHT = pygame.K_w
KEY_TURN_LEFT = pygame.K_s
KEY_FAST_DROP = pygame.K_SPACE
KEY_PAUSE = pygame.K_q
ALL_CHECKING_KEYS = [KEY_RIGHT, KEY_LEFT, KEY_TURN_RIGHT, KEY_TURN_LEFT, KEY_FAST_DROP, KEY_PAUSE]

#네트워크 설정
class NetworkState(Enum):
    Disconnected = -1
    Connecting = 1
    Connected = 2
DEFAULT_PORT = 14500
class PacketInOut(Enum):
    In = 0
    Out = 1
class PacketType(Enum):
    Invalid = -1       #오류
    AccessRequire = 0  #맨 처음 접속 요청
    AccessAccept = 1   #접속 허가
    AccessDeny = 2     #접속 거부
    SynchronizeGameSetting = 3     #게임 설정 동기화
    Synchronized = 4   #동기화 완료
    BlockMove = 5      #블럭 이동
    BlockLanding = 6   #블럭 고정
    ChangeTickPerCell = 7          #블럭 떨어지는 속도 변경
    ApplyEffect = 8    #효과 적용
    SynchronizeGameOver = 9        #게임 오버
    SynchronizeRestart = 10         #다시 시작
    SynchronizeCancelRestart = 11  #다시 시작 취소
    Disconnect = 12    #접속 해제
PACKET_IDENTIFIERS = {}   #패킷 식별자
PACKET_IDENTIFIERS[PacketType.Invalid] = "INVL"
PACKET_IDENTIFIERS[PacketType.AccessRequire] = "ACRQ"
PACKET_IDENTIFIERS[PacketType.AccessAccept] = "ACOK"
PACKET_IDENTIFIERS[PacketType.AccessDeny] = "ACNO"
PACKET_IDENTIFIERS[PacketType.SynchronizeGameSetting] = "SYGS"
PACKET_IDENTIFIERS[PacketType.Synchronized] = "SYFH"
PACKET_IDENTIFIERS[PacketType.BlockMove] = "BKMV"
PACKET_IDENTIFIERS[PacketType.BlockLanding] = "BKLD"
PACKET_IDENTIFIERS[PacketType.ChangeTickPerCell] = "CTPC"
PACKET_IDENTIFIERS[PacketType.ApplyEffect] = "APFX"
PACKET_IDENTIFIERS[PacketType.SynchronizeGameOver] = "GAEN"
PACKET_IDENTIFIERS[PacketType.SynchronizeRestart] = "REST"
PACKET_IDENTIFIERS[PacketType.SynchronizeCancelRestart] = "CNRT"
PACKET_IDENTIFIERS[PacketType.Disconnect] = "QUIT"

# --- 변수 영역 ------------------------------------------------------------------------------------------------------------------------------------------------

#pygame 변수
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGTH))
clock = pygame.time.Clock()

#글로벌 변수
appState = AppState.Menu
menuState = MenuState.Main
gameType = GameType.Local
gameMode = GameMode.Classic
pressedKey = {}             #현재 눌려져 있는 키 (커스텀 키 입력 구현 용도)
highScore = 0
localManager = None
remoteManager = None
keyInputListener = None     #키 커스텀 용도
displayObjects = {}         #텍스트 필드 등 UI 오브젝트
displaySettingResetTick = -1      #해상도 설정 리셋 틱

#인게임 변수 (클래스로 묶어서 관리)
class IngameValue():
    def __init__(self):
        self.isRemote = False   #Remote인지 여부
        self.manager = None
        self.GAME_SCREEN_OFFSET = GAME_SCREEN_OFFSET_MID    #게임 스크린 위치 Offset
        self.TICK_PER_CELL = DEFAULT_TICK_PER_CELL
        self.gameState = GameState.WaitNewBlock
        self.prePauseState = GameState.WaitNewBlock     #Pause 이전 상태 (복구 용도)
        self.preAnimaionState = GameState.WaitNewBlock  #Animaion 이전 상태 (복구 용도)
        self.cells = []
        self.cellLock = threading.Lock()
        self.blockID = 0
        self.curBlock = None
        self.fakeBlock = None
        self.lastX = 0  #마지막으로 블럭이 착지했던 X 좌표값 (블럭 위치가 계속해서 이어지도록 하기 위함)
        self.score = 0
        self.combo = 0
        self.animations = []    #현재 재생중인 애니매이션
        self.RANDOM_SEED = 0    #랜덤 시드
        self.random = random.Random()

    #gameState 변경
    def changeState(self, state):
        if gameType is GameType.Network and self.gameState is GameState.Paused:
            #멈춤 상태면 prePauseState에 반영 (게임 모드가 Network인 경우에만)
            self.prePauseState = state
        else:
            self.gameState = state
localGameValue = IngameValue()
localGameValue.isRemote = False

#네트워킹 변수
netSocket = None     #소켓
address = None      #주소

networkState = NetworkState.Disconnected    #현재 네드워크 상태
networkThread = None        #네트워킹 담당 쓰레드
packetPool = None          #패킷 풀
returnedPackets = None     #반환된 패킷
packetPoolLock = threading.Lock()   #패킷 풀 락
remoteGameValue = IngameValue()
remoteGameValue.GAME_SCREEN_OFFSET = GAME_SCREEN_OFFSET_RIGHT
remoteGameValue.isRemote = True
localRestart = False    #재시작 동의 여부
remoteRestart = False
class SynchronizeState(Enum):   #동기화 진행 상태
    WaitBoth = 0        #송수신 대기 중
    WaitReceived = 1    #패킷 수신 대기 중
    WaitSend = 2        #수신 완료 패킷 대기 중 (송신 완료 대기 중)
    Synchronized = 3    #동기화 완료
synchronizedGameSetting = SynchronizeState.Synchronized #게임 설정 동기화 여부
synchronizedGameOver = SynchronizeState.Synchronized    #게임 오버 동기화 여부
synchronizedRestart = SynchronizeState.Synchronized     #재시작 동의 상태 동기화 여부


#--- 선정의 멤버 영역 ------------------------------------------------------------------------------------------------------------------------------------------------
        
#--- 디스플레이 멤버

#화면 해상도 적용
def applyScreenResolution():
    global screen

    screen = pygame.display.set_mode((resize(SCREEN_WIDTH), resize(SCREEN_HEIGTH)))

#해상도 반영 (상수)
def resize(value):
    return int(value * SCREEN_RESOLUTION)

#해상도 반영 (튜플)
def resizeAll(*value):
    return tuple(int(SCREEN_RESOLUTION * element) for element in value)

#마우스 위치 검출
def isCollideIn(pos, x, y, dx, dy):
    posX = pos[0]
    posY = pos[1]
    leftX = resize(x - dx / 2)
    rightX = resize(x + dx / 2)
    upY = resize(y + dy / 2)
    downY = resize(y - dy / 2)
    
    return posX >= leftX and posX <= rightX and posY >= downY and posY <= upY

#화면에 글자 출력
def drawText(string, x, y, size = 40, font = "arial", color = (0, 0, 0)): 
    font = pygame.font.SysFont(font, resize(size))
    text = font.render(string, True, color)
    rect = text.get_rect()
    rect.center = resizeAll(x, y)
    screen.blit(text, rect)

#화면에 글자 + 사각형 배경 출력
def drawTextRect(string, x, y, dx, dy = 40, size = 40, font = "arial", color = (0, 0, 0), backgroundColor = (255, 255, 255)): 
    pygame.draw.rect(screen, backgroundColor, resizeAll(x - dx / 2, y - dy / 2, dx, dy))
    font = pygame.font.SysFont(font, resize(size))
    text = font.render(string, True, color)
    rect = text.get_rect()
    rect.center = resizeAll(x, y)
    screen.blit(text, rect)
    
#마우스에 반응하는 글자 + 사각형 배경 출력
def drawInterectibleTextRect(pos, string, x, y, dx, dy = 40, size = 40, gain = 1.1, font = "arial",
                                color = (0, 0, 0), backgroundColor = (255, 255, 255),
                                newColor = (0, 0, 0), newBackgroundColor = (200, 200, 200), ignoreAlert = False):            
    
    if "alert" in displayObjects and displayObjects["alert"].enable and not ignoreAlert:
        drawTextRect(string, x, y, dx, dy, size, font, color, backgroundColor)
        return

    if isCollideIn(pos, x, y, dx, dy):
        drawTextRect(string, x, y, int(dx * gain), int(dy * gain), int(size * gain), font, newColor, newBackgroundColor)
    else:
        drawTextRect(string, x, y, dx, dy, size, font, color, backgroundColor)

#텍스트를 입력받을 수 있는 필드 (숫자만 가능)
class TextField:    
    def __init__(self, x, y, dx, dy, enableFunction, content = "", placeHolder = "",
                 color = (0, 0, 0), backgroundColor = (255, 255, 255), size = 40, font = "arial", maxLength = 5,
                 maxValue = 999, minValue = 0, useMinMax = False):
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
        self.enableFunction = enableFunction
        self.maxLength = maxLength
        self.maxValue = maxValue
        self.minValue = minValue
        self.useMinMax = useMinMax
    
    #화면에 출력
    def draw(self):
        if self.enableFunction():
            if self.focused:
                drawTextRect(self.content + "|", self.x, self.y, self.dx, self.dy, self.size, self.font, self.color, self.backgroundColor)
            else:
                if self.content == "":
                    drawTextRect(self.placeHolder, self.x, self.y, self.dx, self.dy, self.size, self.font, self.color, self.backgroundColor)
                else:
                    drawTextRect(self.content, self.x, self.y, self.dx, self.dy, self.size, self.font, self.color, self.backgroundColor)

    #클릭 검사
    def mouseDown(self, pos):
        if self.enableFunction():
            if self.focused == False and isCollideIn(pos, self.x, self.y, self.dx, self.dy):
                self.focused = True
            elif self.focused == True:
                self.focused = False
                if self.useMinMax:
                    if int(self.content) > self.maxValue:
                        self.content = str(self.maxValue)
                    elif int(self.content) < self.minValue:
                        self.content = str(self.minValue)

    #키 입력 처리
    def keyDown(self, keyCode):
        if self.enableFunction():
            if not self.focused:
                return

            if keyCode == pygame.K_KP_ENTER or keyCode == pygame.K_RETURN:
                self.focused = False
            elif keyCode == pygame.K_BACKSPACE:
                if len(self.content) > 0:
                    self.content = self.content[:len(self.content) - 1]
            elif re.match("[0-9]", pygame.key.name(keyCode)) and len(self.content) < self.maxLength:
                self.content = self.content + str(pygame.key.name(keyCode))

    #현재 내용 반환
    def getContent(self):
        if self.content == "":
            return self.placeHolder
        else:
            return self.content

#알림창
class AlertContainer:    
    def __init__(self, content = [""], backgroundColor = (200, 200, 200), fontColor = (0, 0, 0), font = "arial", size =30,
                 buttonFont = "arial", buttonFontSize = 30, buttonColor = (255, 255, 255), buttonbackgroundColor = (50, 50, 50),
                 buttonHighlightColor = (255, 255, 255), buttonHighlightBackgroundColor = (100, 100, 100), closeFunction = None):
        self.enable = True
        self.content = content
        self.backgroundColor = backgroundColor
        self.color = fontColor
        self.font = font
        self.size = size
        self.buttonFont = buttonFont
        self.buttonFontSize = buttonFontSize
        self.buttonColor = buttonColor
        self.buttonBackgroundColor = buttonbackgroundColor
        self.buttonHighlightColor = buttonHighlightColor
        self.buttonHighlightBackgroundColor = buttonHighlightBackgroundColor
        self.closeFunction = closeFunction
    
    #화면에 출력
    def draw(self):
        if not self.enable:
            return

        pygame.draw.rect(screen, self.backgroundColor, resizeAll(100, 75, 400, 250))
        index = 1
        for string in self.content:
            drawText(string, 300, 75 + self.size * index, self.size, self.font, self.color)
            index += 1
        drawInterectibleTextRect(pygame.mouse.get_pos(), "close", 300, 325 - (self.buttonFontSize + 5) / 2 - 5, 100, (self.buttonFontSize + 5),
                                 size = self.buttonFontSize, font = self.buttonFont, color = self.buttonColor, backgroundColor = self.buttonBackgroundColor,
                                 newColor = self.buttonHighlightColor, newBackgroundColor = self.buttonHighlightBackgroundColor, ignoreAlert = True)

    #클릭 검사
    def mouseDown(self, pos):
        if not self.enable:
            return

        if isCollideIn(pos, 300, 325 - (self.buttonFontSize + 5) / 2 - 10, 100, (self.buttonFontSize + 5)):
            self.enable = False
            if not self.closeFunction is None:
                self.closeFunction()

    #키 입력 처리
    def keyDown(self, keyCode):
        return

#--- 유틸 멤버

#디버그 로그 출력
def debugLog(*message): 
    if FLAG_PRINT_DEBUG_LOG:
        print(*message)

#에러 디버깅 로그 출력
def errorLog(type, message, *content):
    additionalContent = ""
    for index in range(0, len(content)):
        if index % 2 == 0:
            continue
        additionalContent += str(content[index - 1]) + ": " + str(content[index]) + ", "
    if len(additionalContent) > 0:
        additionalContent = additionalContent[0:-2]
    debugLog("[" + type + "] " + message + "   " + additionalContent)

#알림 창 출력
def alertLog(*content, closeFunction = None):
    displayObjects["alert"] = AlertContainer(list(content), font = "hancommalangmalang", buttonFont = "hancommalangmalang", size = 40, buttonFontSize = 25, closeFunction = closeFunction)

#랜덤으로 -1 또는 1을 반환 (블럭 회전값 랜덤 적용시 사용)
def randomBit(ran):    
    if ran.randint(0, 1) == 0:
        return 1
    else:
        return -1

#역순 입력 지원하는 range() 메소드
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

#--- 람다 대용 멤버

#키 커스텀 기능 지원 용도
def setLeftMoveKey(keyCode):
    global KEY_LEFT
    global keyInputListener
    keyInputListener = None
    KEY_LEFT = keyCode
def setRightMoveKey(keyCode):
    global KEY_RIGHT
    global keyInputListener
    keyInputListener = None
    KEY_RIGHT = keyCode
def setLeftTurnKey(keyCode):
    global KEY_TURN_LEFT
    global keyInputListener
    keyInputListener = None
    KEY_TURN_LEFT = keyCode
def setRightTurnKey(keyCode):
    global KEY_TURN_RIGHT
    global keyInputListener
    keyInputListener = None
    KEY_TURN_RIGHT = keyCode
def setDropFastKey(keyCode):
    global KEY_FAST_DROP
    global keyInputListener
    keyInputListener = None
    KEY_FAST_DROP = keyCode
def setPauseKey(keyCode):
    global KEY_PAUSE
    global keyInputListener
    keyInputListener = None
    KEY_PAUSE = keyCode

#텍스트 필드 디스플레이 조건 지원 용도
def whenNetworkSetting():
    return menuState is MenuState.Settings and networkThread is None
def whenIpInputing():
    return menuState is MenuState.EnterRoom and networkState is NetworkState.Disconnected

#해상도 초기화 지원용도
def setResetDelayTick():
    global displaySettingResetTick
    global PRE_SCREEN_RESOLUTION
    displaySettingResetTick = -1
    PRE_SCREEN_RESOLUTION = SCREEN_RESOLUTION

#--- 네트워킹 멤버

#내 IP 가져오기 (추후 사용 예정)
def getMyIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

#네트워킹용 패킷 모듈
class Packet():
    def __init__(self, _input, _data, _type = PacketType.Invalid):
        if _input is PacketInOut.In:    #받은 정보를 패킷으로 변환
            initial = PACKET_IDENTIFIERS[PacketType.Invalid]
            realData = ""

            if not isinstance(_data, str):
                self.valid = False
                errorLog("exception 101", "패킷 데이터가 String이 아닙니다", "data", _data)
                return
            if len(_data) < 4:
                self.valid = False
                errorLog("exception 102", "패킷 데이터가 너무 짧습니다", "data", _data)
                return

            initial = _data[0:4]
            if len(_data) > 4:
                realData = _data[4:]

            #식별자 찾기
            self.type = PacketType.Invalid
            for type in PACKET_IDENTIFIERS:
                if PACKET_IDENTIFIERS[type] == initial:
                    self.type = type
                    break
            if self.type is PacketType.Invalid:
                self.valid = False
                errorLog("exception 103", "일치하는 패킷 식별자가 없습니다", "initial", initial, "full data", _data)
                return
            
            #패킷 해석
            decodedData = {}
            splitedData = []
            if "&" in realData:
                splitedData = realData.split("&")
            else:
                splitedData = [realData]
            if len(realData) > 0:
                for atomicData in splitedData:
                    splitedAtomicData = atomicData.split("?")
                    if len(splitedAtomicData) != 2:
                        errorLog("exception 104", "유효하지 않은 패킷 구조입니다", "target data", splitedAtomicData, "full data", _data)
                        continue
                    decodedData[splitedAtomicData[0]] = splitedAtomicData[1]

            self.data = decodedData
            self.valid = True
        elif _input is PacketInOut.Out:     #내보낼 정보를 패킷으로 변환
            if not isinstance(_data, dict):
                errorLog("exception 111", "패킷 데이터가 Dictionary가 아닙니다", "data", _data)
                self.valid = False
                return
            self.type = _type
            self.data = _data
            self.valid = True
        else:       #이상한 값을 입력했을 때
            errorLog("exception 121", "올바르지 않은 패킷 타입입니다", "input", _input)
            self.valid = False

    #타입 체크까지 다 해서 값 반환
    def getIntValues(self, *keys):
        output = []
        result = True

        for key in keys:
            if not self.valid:
                errorLog("exception 131", "유효하지 않은 패킷입니다")
                output.append(0)
                result = False
                continue
            if self.data[key] is None:
                errorLog("exception 132", "대상 값이 존재하지 않습니다", "key", key, "data", self.data)
                output.append(0)
                result = False
                continue
            if not isinstance(self.data[key], str):
                errorLog("exception 133", "대상 값이 String이 아닙니다", "key", key, "value", self.data[key], "full data", self.data)
                output.append(0)
                result = False
                continue
            
            try:
                output.append(int(self.data[key]))
            except Exception as e:
                errorLog("exception 134", "대상 값이 Int가 아닙니다", "key", key, "value", self.data[key], "full data", self.data)
                debugLog(type(e), e)
                output.append(0)
                result = False
        output.append(result)
        return tuple(output)

    #이 패킷의 정보를 인코딩하여 반환
    def getPackedData(self):
        if not self.valid:
            errorLog("exception 141", "유효하지 않은 패킷입니다")
            return PACKET_IDENTIFIERS[PacketType.Invalid]

        encodedData = ""
        for key in self.data:
            encodedData += str(key) + "?" + str(self.data[key]) + "&"
        if len(encodedData) > 0:
            encodedData = encodedData[:-1]
        rawData = PACKET_IDENTIFIERS[self.type] + encodedData

        return rawData.encode()

    #패킷 전송
    def sendTo(self, _address = None):
        global netSocket

        #패킷 복구 확인용 패킷 씹기
        if FLAG_RANDOM_IGNORE_PACKET and random.randint(0, FLAG_PACKET_IGNORE_RATE - 1) == 0:
            debugLog(">//", self.type, self.data)
            return

        if netSocket is None:
            errorLog("exception 151", "소켓이 존재하지 않습니다", "type", self.type, "data", self.data)
            return
        if not self.valid:
            errorLog("exception 152", "유효하지 않은 패킷입니다")
            return

        if _address is None:
            if address is None:
                errorLog("exception 153", "주소값이 존재하지 않습니다", "type", self.type, "data", self.data)
                return

            _address = address

        try:
            netSocket.sendto(self.getPackedData(), _address)
            debugLog(">>>", self.type, self.data)
        except Exception as e:
            errorLog("exception 154", "패킷 전송에 실패하였습니다", "socket", netSocket, "type", self.type, "data", self.data)
            debugLog(type(e), e)
            return

#방 생성
def createRoom():
    global netSocket
    global networkState
    global address

    if not netSocket is None or not address is None:
        closeRoom()

    netSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)     #UCP 사용
    networkState = NetworkState.Disconnected
    address = None

    debugLog("socket is opend")

#방 제거
def closeRoom(deep = 1, useAlert = True, stay = False):
    global netSocket
    global networkState
    global address
    global networkThread
    global packetPool
    global returnedPackets
    global appState
    global menuState

    #스텍 오버플로우 방지용도
    if deep > 5:
        errorLog("exception 211", "Stack Over Flow")
        return

    if gameType is GameType.Network:
        if not localGameValue.gameState is GameState.GameOver and appState == AppState.Game:
            localManager.gameEnd(True)
        if not stay:
            appState = AppState.Menu
            menuState = MenuState.GameMode

    if not netSocket is None and not address is None and networkState is NetworkState.Connected:
        #QUIT 패킷 전송
        packet = Packet(PacketInOut.Out, {}, PacketType.Disconnect)
        packet.sendTo()

    if netSocket is None:
        errorLog("exception 212", "소켓이 존재하지 않습니다")
        networkState = NetworkState.Disconnected
        return

    try:
        netSocket.close()
    except Exception as e:
        errorLog("exception 213", "소켓 닫기에 실패하였습니다", "socket", netSocket)
        debugLog(type(e), e)
        if not netSocket is None:
            #제대로 안 닫혔으면 닫힐 때까지 계속 실행
            closeRoom(deep + 1)
        return
    try:
        packetPoolLock.acquire()
        packetPool = None
        returnedPackets = None
    finally:
        packetPoolLock.release()
    networkState = NetworkState.Disconnected
    address = None
    netSocket = None
    networkThread = None
    debugLog("socket is closed")
    if useAlert:
        alertLog("Connection is Closed")

#접속 대기
def waitEnter():
    global netSocket
    global networkState
    global address
    global packetPool
    global returnedPackets
    global gameType

    if netSocket is None:
        createRoom()

    try:
        #소켓 바인딩
        netSocket.bind(("127.0.0.1", int(displayObjects["port"].getContent())))
    except Exception as e:
        if displayObjects["port"] is None:
            errorLog("exception 221", "소켓 바인딩에 실패하였습니다", "socket", netSocket, "port", "Text File is None")
        else:
            errorLog("exception 221", "소켓 바인딩에 실패하였습니다", "socket", netSocket, "port", displayObjects["port"].getContent())
        debugLog(type(e), e)
        closeRoom(useAlert = False)
        alertLog("Error 101", "Fail to bind socket", "Try for other port")
        return
    
    debugLog("socket is binded at port " + displayObjects["port"].getContent())

    try:
        (rawData, _address) = netSocket.recvfrom(1024)
        data = rawData.decode()
    except Exception as e:
        errorLog("exception 222", "클라이언트로부터 패킷 수신에 실패하엿습니다", "socket", netSocket)
        debugLog(type(e), e)
        closeRoom(useAlert = False, stay = True)
        if networkState is NetworkState.Disconnected:
            return
        waitEnter()
        return

    networkState = NetworkState.Connecting
    packet = Packet(PacketInOut.In, data)
    if not packet.valid or not packet.type is PacketType.AccessRequire:
        #이상한 패킷을 받았으면 취소
        if packet.valid:
            errorLog("exception 223", "올바르지 않은 패킷입니다", "type", packet.type)
        else:
            errorLog("exception 223", "올바르지 않은 패킷입니다", "type", "Packet is Invaild")
        closeRoom(useAlert = False, stay = True)
        waitEnter()
        return
    (version, result) = packet.getIntValues("ver")
    if not result or version != GAME_VERSION:
        #게임 버전이 일치하지 않으면 취소
        if result:
            errorLog("exception 224", "게임 버전이 일치하지 않습니다", "local version", GAME_VERSION, "remote version", version)
        else:
            errorLog("exception 225", "패킷 데이터가 올바르지 않습니다", "data", packet.data)
        packet = Packet(PacketInOut.Out, {}, PacketType.AccessDeny)
        packet.sendTo(_address)
        closeRoom(useAlert = False, stay = True)
        waitEnter()
        return

    #접속 수락 패킷 전송
    packet = Packet(PacketInOut.Out, {}, PacketType.AccessAccept)
    packet.sendTo(_address)

    address = _address
    networkState = NetworkState.Connected
    debugLog("successfully connected with client from " + address[0] + ":" + str(address[1]))
    try:
        packetPoolLock.acquire()
        packetPool = []
        returnedPackets = []
    finally:
        packetPoolLock.release()
    gameType = GameType.Network

    t = threading.Thread(target=runPacketListener, daemon=True)
    t.start()
    localManager.gameStart()
    remoteManager.gameStart()

#방 접속
def enterRoom(_ip, _port):
    global netSocket
    global networkState
    global address
    global packetPool
    global returnedPackets
    global gameType

    if netSocket is None:
        createRoom()
    networkState = NetworkState.Connecting

    #접속 요청 패킷 전송
    packet = Packet(PacketInOut.Out, {"ver" : GAME_VERSION}, PacketType.AccessRequire)
    packet.sendTo((_ip, _port))

    debugLog("send packet to server. wait respond")

    data = None
    try:
        #서버측 응답 대기
        (rawData, _address) = netSocket.recvfrom(1024)
        data = rawData.decode()
    except Exception as e:
        errorLog("exception 231", "서버로부터 패킷 수신에 실패하였습니다", "socket", netSocket)
        debugLog(type(e), e)
        closeRoom(useAlert = False, stay = True)
        return

    packet = Packet(PacketInOut.In, data)
    if not packet.valid or not packet.type is PacketType.AccessAccept:
        #접속 수락 패킷이 아니면 취소
        if packet.valid:
            errorLog("exception 232", "올바르지 않은 패킷입니다", "type", packet.type)
        else:
            errorLog("exception 233", "올바르지 않은 패킷입니다", "type", "Packet is Invaild")
        closeRoom(useAlert = False, stay = True)
        if packet.valid and packet.type == PacketType.AccessDeny:
            alertLog("Error 103", "Incorrect game version", "please check game version")
        return

    address = _address
    networkState = NetworkState.Connected
    debugLog("successfully connected with server from " + address[0] + ":" + str(address[1]))
    try:
        packetPoolLock.acquire()
        packetPool = []
        returnedPackets = []
    finally:
        packetPoolLock.release()
    gameType = GameType.Network

    t = threading.Thread(target=runPacketListener, daemon=True)
    t.start()
    localManager.gameStart()
    remoteManager.gameStart()

#무한 반복 패킷 수신 처리기
def runPacketListener():
    debugLog("start listening packet")
    while(True):
        #접속 종료 처리
        if netSocket is None:
            errorLog("exception 241", "소켓이 존재하지 않습니다")
            closeRoom()
            return

        try:
            #패킷 대기
            (rawData, _address) = netSocket.recvfrom(1024)
            data = rawData.decode()
        except ConnectionResetError as e:
            #접속 종료 처리
            errorLog("exception 242", "접속이 종료되었습니다")
            debugLog(type(e), e)
            closeRoom()
            return
        except Exception as e:
            #접속 종료 처리
            if netSocket is None:
                errorLog("exception 243", "소켓이 존재하지 않습니다")
                debugLog(type(e), e)
                closeRoom()
                return
            errorLog("exception 244", "패킷 수신 중 오류가 발생하였습니다")
            debugLog(type(e), e)
            continue
        packet = Packet(PacketInOut.In, data)
        if not packet.valid or packet.type is PacketType.Invalid:
            #이상한 패킷이면 취소
            if packet.valid:
                errorLog("exception 245", "올바르지 않은 패킷입니다", "type", packet.type)
            else:
                errorLog("exception 246", "올바르지 않은 패킷입니다", "type", "Packet is Invaild")
            continue
        
        #큐에 추가
        try:
            packetPoolLock.acquire()
            if packetPool is None:
                return
            debugLog("<<<", packet.type, packet.data)
            packetPool.append(packet)
        finally:
            packetPoolLock.release()

#다음 패킷 가져오기, lock 필수
def getNextPacket():
    if packetPool is None:
        errorLog("exception 251", "패킷 풀이 존재하지 않습니다")
        return None

    if len(packetPool) <= 0:
        return None
    packet = packetPool[0]
    packetPool.remove(packet)

    return packet


#반환된 패킷 넘기기, lock 필수
def passOverReturedPackets():
    if packetPool is None or returnedPackets is None:
        errorLog("exception 252", "패킷 풀이 존재하지 않습니다")
        return

    for packet in returnedPackets:
        packetPool.append(packet)
    returnedPackets.clear()

#패킷 반환, lock 필수
def postponePacket(packet):
    if returnedPackets is None:
        errorLog("exception 253", "패킷 풀이 존재하지 않습니다")
        return

    returnedPackets.append(packet)

#다음 패킷 존재 여부, lock 필수
def hasNextPacket():
    if packetPool is None:
        errorLog("exception 254", "패킷 풀이 존재하지 않습니다")
        return False

    isEmpty = len(packetPool) == 0

    return not isEmpty


#--- 메인 클래스 영역 ------------------------------------------------------------------------------------------------------------------------------------------------

#셀 하나하나의 상태
class Cell:
    def __init__(self, state = CellState.Empty, color = (255, 0, 0), effect = CellEffect.Default):
        self.state = state
        self.color = color
        self.effect = effect
        
    def changeState(self, state, color):
        self.state = state
        self.color = color

#블럭 객체
class Block:
    def __init__(self, originState, gamevalue, id, x = 0, 
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
        self.gamevalue = gamevalue
        self.id = id

        #화면 오른쪽으로 넘어가는 것 방지
        if self.x + len(self.curState) > HORIZONTAL_CELL_COUNT:
            self.x = HORIZONTAL_CELL_COUNT - len(self.curState)
            
        #게임 종료 감지
        if self.isColideWith(self.curState, self.x, self.y):
            if self.gamevalue.isRemote:
                self.gamevalue.curBlock = None
            else:
                localManager.gameEnd(False)
            return

        #떨어질 위치 미리보기 생성
        self.gamevalue.fakeBlock = FakeBlock(self.curState, self.x, self.y, self.color, self.gamevalue)

    #1칸 떨어지기
    def fall(self):
        if self.isColideWith(self.curState, self.x, self.y + 1):
            #충돌시 고정
            self.landing()
            
        self.y += 1
    
    #이동
    def move(self, dx, dy):
        if self.isColideWith(self.curState, self.x + dx, self.y + dy):
            return
        
        self.x += dx
        self.y += dy

        #반영
        self.applyFakeBlock()
        if gameType is GameType.Network and not self.gamevalue.isRemote:
            self.synchronizePosition()

    #좌측 회전
    def turnLeft(self):
        dirZ = self.dirZ
        dirX = self.dirX
        dirY = self.dirY
        y = self.y
        x = self.x
        
        #미리 돌려보기
        dirZ *= -1
        if dirX == dirY:
            dirX *= -1
        else:
            dirY *= -1
        state = self.getState(dirZ, dirX, dirY)
        y -=  len(state[0]) - len(self.curState[0])
            
        #오른쪽 벽에서는 미끄러지듯 회전
        isCollide = True
        for i in range(0, len(state)):
            if self.isColideWith(state, x, y):
                x -= 1
                continue
            isCollide = False
            break

        #충돌하면 취소
        if isCollide:
            return
            
        #결과 적용
        self.curState = self.getState(dirZ, dirX, dirY)
        self.dirZ = dirZ
        self.dirX = dirX
        self.dirY = dirY
        self.y = y
        self.x = x

        #반영
        self.applyFakeBlock()
        if gameType is GameType.Network and not self.gamevalue.isRemote:
            self.synchronizePosition()

    #우측 회전
    def turnRight(self):
        dirZ = self.dirZ
        dirX = self.dirX
        dirY = self.dirY
        y = self.y
        x = self.x
        
        #미리 돌려보기
        dirZ *= -1
        if dirX == dirY:
            dirY *= -1
        else:
            dirX *= -1
        state = self.getState(dirZ, dirX, dirY)
        y -=  len(state[0]) - len(self.curState[0])

        #오른쪽 벽에서는 미끄러지듯 회전
        isCollide = True
        for i in range(0, len(state)):
            if self.isColideWith(state, x, y):
                x -= 1
                continue
            isCollide = False
            break

        #충돌하면 취소
        if isCollide:
            return
        
        #결과 적용
        self.curState = self.getState(dirZ, dirX, dirY)
        self.dirZ = dirZ
        self.dirX = dirX
        self.dirY = dirY
        self.y = y
        self.x = x

        #반영
        self.applyFakeBlock()
        if gameType is GameType.Network and not self.gamevalue.isRemote:
            self.synchronizePosition()

    #블럭 고정
    def landing(self):
        try:
            self.gamevalue.cellLock.acquire()
            for x in range(0, len(self.curState)):
                for y in range(0, len(self.curState[0])):
                    if y + self.y < 0:
                        continue
                    
                    if self.curState[x][y] is CellState.Occupied:
                        if x + self.x < 0 or x + self.x >= HORIZONTAL_CELL_COUNT or y + self.y < 0 or y + self.y > VERTICAL_CELL_COUNT:
                            continue
                        self.gamevalue.cells[x + self.x][y + self.y].changeState(CellState.Occupied, self.color)
        finally:
            self.gamevalue.cellLock.release()
        
        #게임 종료 감지
        if not self.gamevalue.isRemote and self.y - len(self.curState[0]) + 1 < 0:
            self.y -= 1
            localManager.gameEnd(False)
            return
        
        #다음 블럭 요청
        self.gamevalue.lastX = self.x
        self.gamevalue.changeState(GameState.WaitNewBlock)
        self.gamevalue.curBlock = None
        self.gamevalue.fakeBlock = None

        #라인 클리어 처리
        lines = []
        try:
            self.gamevalue.cellLock.acquire()
            for y in range(self.y + len(self.curState[0]) - 1, self.y - 1, - 1):
                if self.lineCheck(y):
                    lines.append(y)
                    self.gamevalue.score += SCORE_PER_LINE + COMBO_SCORE * self.gamevalue.combo
                    self.gamevalue.combo += 1
        finally:
            self.gamevalue.cellLock.release()

        #콤보 점수 처리
        if len(lines) > 0:
            self.gamevalue.animations.append(Animation(AnimationType.LineClear, lines, self.gamevalue))
        else:
            self.gamevalue.combo = 0
        
        if gameType is GameType.Network and not self.gamevalue.isRemote:
            self.synchronizeCells()

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
                    and self.gamevalue.cells[x + locX][y + locY].state is CellState.Occupied):
                    return True
        return False

    #블럭 상태 계산
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
    
    #라인 클리어 확인
    def lineCheck(self, y):
        for x in range(0, HORIZONTAL_CELL_COUNT):
            if self.gamevalue.cells[x][y].state is CellState.Empty:
                return False

        return True

    #페이크 블럭 반영
    def applyFakeBlock(self):
        self.gamevalue.fakeBlock = FakeBlock(self.curState, self.x, self.y, self.color, self.gamevalue)

    #위치 동기화
    def synchronizePosition(self):
        if gameType is GameType.Network and not self.gamevalue.isRemote:
            packet = Packet(PacketInOut.Out, {"tick": self.gamevalue.manager.tick, "id": self.id, "x": self.x, "y": self.y, "dirX": self.dirX, "dirY": self.dirY, "dirZ": self.dirZ}, PacketType.BlockMove)
            packet.sendTo()

    #셀 배치 동기화        
    def synchronizeCells(self):
        if gameType is GameType.Network and not self.gamevalue.isRemote:
            encodedCells = ""
            for x in range(0, HORIZONTAL_CELL_COUNT):
                for y in range(0, VERTICAL_CELL_COUNT):
                    if self.gamevalue.cells[x][y].state == CellState.Occupied:
                        encodedCells += str(ALL_BLOCK_COLORS.index(self.gamevalue.cells[x][y].color) + 1)
                    else:
                        encodedCells += "0"
            packet = Packet(PacketInOut.Out, {"tick": self.gamevalue.manager.tick, "cells": "1" + str(encodedCells), "score": self.gamevalue.score, "combo": self.gamevalue.combo}, PacketType.BlockLanding)
            packet.sendTo()

#떨어질 위치 표시용 가짜 블럭
class FakeBlock:
    def __init__(self, state, x, y, color, gamevalue):
        self.state = state
        self.x = x
        self.y = y
        self.color = color
        self.gamevalue = gamevalue

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
                    and self.gamevalue.cells[x + self.x][y + locY].state is CellState.Occupied):
                    return True
        return False

#애니메이션
class Animation:
    def __init__(self, type, var, gamevalue):
        self.type = type
        self.tick = 0
        self.var = var
        self.gamevalue = gamevalue

        #게임 상태 변경
        if not self.gamevalue.gameState is GameState.Animating:
            self.gamevalue.preAnimaionState = self.gamevalue.gameState
            self.gamevalue.changeState(GameState.Animating)

    #애니메이션 처리
    def update(self):
        self.tick += 1

        #라인 클리어 애니메이션
        if self.type == AnimationType.LineClear:
            try:
                self.gamevalue.cellLock.acquire()
                if self.tick == 1:
                    #라인 흰색으로 칠하기
                    for x in range(0, HORIZONTAL_CELL_COUNT):
                        for y in self.var:
                            self.gamevalue.cells[x][y].changeState(
                                CellState.Occupied, (255, 255, 255))
                elif (self.tick - 3) >= HORIZONTAL_CELL_COUNT:
                    #라인 내리기
                    for x in range(0, HORIZONTAL_CELL_COUNT):
                        for y in self.var:
                            self.gamevalue.cells[x][y].changeState(CellState.Empty, (255, 0, 0))
                    for locY in sorted(self.var):
                        for y in range(locY, 1, -1):
                            for x in range(0, HORIZONTAL_CELL_COUNT):
                                self.gamevalue.cells[x][y].changeState(
                                    self.gamevalue.cells[x][y - 1].state, self.gamevalue.cells[x][y - 1].color)
                    self.gamevalue.animations.remove(self)
                elif self.tick >= 3:
                    #라인 차례로 지우기
                    for y in self.var:
                        self.gamevalue.cells[self.tick - 3][y].changeState(CellState.Empty, (255, 255, 255))
            finally:
                self.gamevalue.cellLock.release()

#게임 메니저
class GameManager:
    def __init__(self, gamevalue):
        self.tick = 0
        self.gamevalue = gamevalue

    #--- 게임 제어 영역 ------------------------------

    #게임 시작
    def gameStart(self):
        global appState
        global synchronizedGameSetting

        self.gameReset()
        self.gamevalue.changeState(GameState.WaitNewBlock)
        if not self.gamevalue.isRemote:
            appState = AppState.Game

        #반영
        if gameType is GameType.Network:
            synchronizedGameSetting = SynchronizeState.WaitBoth
    
    #게임 리셋
    def gameReset(self):
        global synchronizedGameOver
        global synchronizedGameSetting
        global synchronizedRestart
        global localRestart
        global remoteRestart

        self.gamevalue.lastX = 0
        self.gamevalue.changeState(GameState.WaitNewBlock)
        self.tick = 0
        self.gamevalue.curBlock = None
        self.gamevalue.score = 0
        self.gamevalue.combo = 0
        try:    #셀 클리어
            self.gamevalue.cellLock.acquire()
            self.gamevalue.cells.clear()
            for x in range(0, HORIZONTAL_CELL_COUNT):
                tmp = []
                for y in range(0, VERTICAL_CELL_COUNT):
                    tmp.append(Cell())
                self.gamevalue.cells.append(tmp)
        finally:
            self.gamevalue.cellLock.release()
        self.gamevalue.blockID = 0
        self.gamevalue.RANDOM_SEED = self.gamevalue.random.randrange(0, sys.maxsize)
        self.gamevalue.random.seed(self.gamevalue.RANDOM_SEED)
        localRestart = False
        remoteRestart = False
        if self.gamevalue.isRemote: #동기화 상태 초기화
            synchronizedGameSetting =  SynchronizeState.Synchronized
            synchronizedGameOver =  SynchronizeState.Synchronized
            synchronizedRestart =  SynchronizeState.Synchronized
        if gameType is GameType.Local:  #화면 Offset 설정
            self.gamevalue.GAME_SCREEN_OFFSET = GAME_SCREEN_OFFSET_MID
        elif gameType is GameType.Network:
            if self.gamevalue.isRemote:
                self.gamevalue.GAME_SCREEN_OFFSET = GAME_SCREEN_OFFSET_RIGHT
            else:
                self.gamevalue.GAME_SCREEN_OFFSET = GAME_SCREEN_OFFSET_LEFT
    
    #게임 종료
    def gameEnd(self, force = False):
        global highScore
        global synchronizedGameOver

        #반영
        if not force and gameType is GameType.Network and not synchronizedGameOver is SynchronizeState.WaitSend:
            packet = Packet(PacketInOut.Out, {"tick": self.tick}, PacketType.SynchronizeGameOver)
            packet.sendTo()
            synchronizedGameOver = SynchronizeState.WaitSend
            return

        #초기화
        localGameValue.gameState = GameState.GameOver
        localGameValue.curBlock = None
        localGameValue.fakeBlock = None
        remoteGameValue.gameState = GameState.GameOver
        remoteGameValue.curBlock = None
        remoteGameValue.fakeBlock = None
        if not self.gamevalue.isRemote:
            if self.gamevalue.score > highScore:
                highScore = self.gamevalue.score
    
    #--- 메인 로직 영역 ------------------------------

    #틱당 1회 실행되는 메인 로직 함수
    def update(self):
        global displaySettingResetTick
        global PRE_SCREEN_RESOLUTION
        global SCREEN_RESOLUTION

        #해상도 초기화
        if displaySettingResetTick > 0:
            displaySettingResetTick -= 1
            alertLog("Display setting will be", "reseted after " + str(displaySettingResetTick // TPS + 1) + " seconds", "close this alert to remain", closeFunction = setResetDelayTick)
        elif displaySettingResetTick == 0:
            displaySettingResetTick = -1
            SCREEN_RESOLUTION = PRE_SCREEN_RESOLUTION
            applyScreenResolution()
            displayObjects["alert"].enable = False

        if appState is AppState.Game:
            #동기화 실행
            if self.gamevalue.isRemote and gameType is GameType.Network and synchronizedGameOver is SynchronizeState.WaitSend:
                #게임 오버 동기화
                packet = Packet(PacketInOut.Out, {"tick": self.tick}, PacketType.SynchronizeGameOver)
                packet.sendTo()
            if self.gamevalue.isRemote and gameType is GameType.Network and synchronizedRestart is SynchronizeState.WaitSend:
                #재시작 동기화
                if localRestart:
                    packet = Packet(PacketInOut.Out, {}, PacketType.SynchronizeRestart)
                else:
                    packet = Packet(PacketInOut.Out, {}, PacketType.SynchronizeCancelRestart)
                packet.sendTo()
            if self.gamevalue.isRemote and gameType is GameType.Network and (synchronizedGameSetting is SynchronizeState.WaitSend or synchronizedGameSetting is SynchronizeState.WaitBoth):
                #게임 설정 동기화
                packet = Packet(PacketInOut.Out, {"seed": localGameValue.RANDOM_SEED, "speed": localGameValue.TICK_PER_CELL}, PacketType.SynchronizeGameSetting)
                packet.sendTo(address)
            if synchronizedGameSetting is not SynchronizeState.Synchronized:
                #게임 오버 동기화 될 때까지 대기
                return
            if self.tick % TPS == 0 and gameType is GameType.Network and not self.gamevalue.isRemote and not localGameValue.gameState is GameState.GameOver:
                #블럭 낙하 속도 동기화
                self.synchronizedFallingSpeed()

            self.tick += 1
            
            #Network 게임모드에서는 Pause 상태여도 게임이 계속 진행됨
            state = self.gamevalue.gameState
            if gameType is GameType.Network and self.gamevalue.gameState is GameState.Paused:
                state = self.gamevalue.prePauseState

            #GameState별 처리
            if state is GameState.WaitNewBlock:
                #다음 블럭 생성
                if self.gamevalue.curBlock is None:
                    self.spawnNewBlock()
            elif state is GameState.Drop:
                #블럭 드랍
                if self.tick % self.gamevalue.TICK_PER_CELL == 0:
                    self.gamevalue.curBlock.fall()
            elif state is GameState.Animating:
                #애니매이션 재생
                if len(self.gamevalue.animations) == 0:
                    #애니매이션 완료시 이전 상태로 복귀
                    if self.gamevalue.gameState is GameState.Paused and gameType is GameType.Network:
                        self.gamevalue.prePauseState = self.gamevalue.preAnimaionState
                    else:
                        self.gamevalue.changeState(self.gamevalue.preAnimaionState)
                for animation in self.gamevalue.animations:
                    animation.update()
    
    #패킷 처리
    def processPacket(self, packet):
        global synchronizedGameSetting
        global synchronizedGameOver
        global synchronizedRestart
        global localRestart
        global remoteRestart

        if packet.type is PacketType.Invalid:
            #오류 패킷
            pass
        elif packet.type is PacketType.SynchronizeGameSetting:
            #게임 설정 동기화
            packetOut = Packet(PacketInOut.Out, {"type": 0}, PacketType.Synchronized)
            packetOut.sendTo()

            #이미 동기화 되었다면 return
            if synchronizedGameSetting is SynchronizeState.Synchronized or synchronizedGameSetting is SynchronizeState.WaitSend:
                return

            (seed, tps, result) = packet.getIntValues("seed", "speed")

            if not result:
                return

            remoteGameValue.RANDOM_SEED = seed
            remoteGameValue.TICK_PER_CELL = tps

            #동기화 상태 변경
            if synchronizedGameSetting is SynchronizeState.WaitBoth:
                synchronizedGameSetting = SynchronizeState.WaitSend
            elif synchronizedGameSetting is SynchronizeState.WaitReceived:
                synchronizedGameSetting = SynchronizeState.Synchronized
        elif packet.type is PacketType.Synchronized:
            #동기화 완료
            (type, result) = packet.getIntValues("type")

            if not result:
                return

            #게임 설정 동기화
            if type == 0:
                if synchronizedGameSetting is SynchronizeState.WaitBoth:
                    synchronizedGameSetting = SynchronizeState.WaitReceived
                elif synchronizedGameSetting is SynchronizeState.WaitSend:
                    synchronizedGameSetting = SynchronizeState.Synchronized

            #효과 동기화
            elif type == 1:
                (id, result) = packet.getIntValues("id")

                if not result:
                    return

            #재시작 동기화
            elif type == 2:
                if synchronizedRestart is SynchronizeState.WaitSend:
                    synchronizedRestart = SynchronizeState.Synchronized
                    if localRestart == True and remoteRestart == True and localGameValue.gameState is GameState.GameOver:
                        localManager.gameStart()
                        remoteManager.gameStart()

            #게임 오버 동기화
            elif type == 3:
                if synchronizedGameOver is SynchronizeState.WaitSend:
                    synchronizedGameOver = SynchronizeState.Synchronized
                    localManager.gameEnd(True)
        elif packet.type is PacketType.SynchronizeGameOver:
            #게임 종료
            packetOut = Packet(PacketInOut.Out, {"type": 3}, PacketType.Synchronized)
            packetOut.sendTo()

            #동기화 상태 변경
            if not localGameValue.gameState is GameState.GameOver:
                localManager.gameEnd(True)
        elif packet.type is PacketType.BlockMove:
            #블럭 이동
            (remoteTick, id, x, y, dirX, dirY, dirZ, result) = packet.getIntValues("tick", "id", "x", "y", "dirX", "dirY", "dirZ")

            if not result:
                return
            if self.gamevalue.curBlock is None or self.gamevalue.curBlock.id != id:
                #블럭 ID가 일치하지 않으면 블럭 다시 생성
                self.spawnNewBlock(id)
            if self.tick < remoteTick:
                #미래의 패킷이면 보관한 후 나중에 처리
                postponePacket(packet)
                return

            self.gamevalue.curBlock.x = x
            self.gamevalue.curBlock.y = y + (self.tick  // self.gamevalue.TICK_PER_CELL - remoteTick  // self.gamevalue.TICK_PER_CELL)
            self.gamevalue.curBlock.dirX = dirX
            self.gamevalue.curBlock.dirY = dirY
            self.gamevalue.curBlock.dirZ = dirZ
            self.gamevalue.curBlock.curState = self.gamevalue.curBlock.getState(dirZ, dirX, dirY)
            self.gamevalue.curBlock.applyFakeBlock()
        elif packet.type is PacketType.BlockLanding:
            #블럭 착지
            (remoteTick, _cells, _score, _combo, result) = packet.getIntValues("tick", "cells", "score", "combo")
            if not result:
                return
            if self.tick < remoteTick:
                #미래의 패킷이면 보관한 후 나중에 처리
                postponePacket(packet)
                return

            #디코딩
            decodedCells = []
            index = 0
            strData = str(_cells)
            strData = strData[1:]
            if len(strData) < HORIZONTAL_CELL_COUNT * VERTICAL_CELL_COUNT:
                return
            for x in range(0, HORIZONTAL_CELL_COUNT):
                tmp = []
                for y in range(0, VERTICAL_CELL_COUNT):
                    if strData[index] == "0":
                        tmp.append(Cell(CellState.Empty, color = (0, 0, 0)))
                    else:
                        try:
                            color = ALL_BLOCK_COLORS[int(strData[index]) - 1]
                        except Exception as e:
                            errorLog("exception 301", "올바르지 않은 패킷 데이터입니다", "data", strData[index], "full data", packet.data)
                            debugLog(type(e), e)
                            return
                        tmp.append(Cell(CellState.Occupied, color))
                    index += 1
                decodedCells.append(tmp)

            #적용
            self.gamevalue.score = _score
            self.gamevalue.combo = _combo
            try:
                self.gamevalue.cellLock.acquire()
                self.gamevalue.cells = decodedCells
            finally:
                self.gamevalue.cellLock.release()
        elif packet.type is PacketType.ChangeTickPerCell:
            #블럭 하락 속도 동기화
            (remoteTick, speed, result) = packet.getIntValues("tick", "speed")

            if not result:
                return
            if self.tick < remoteTick:
                #미래의 패킷이면 보관한 후 나중에 처리
                postponePacket(packet)
                return

            self.gamevalue.TICK_PER_CELL = speed
        elif packet.type is PacketType.ApplyEffect:
            #효과 적용
            packetOut = Packet(PacketInOut.Out, {"type": 1, "id": 0}, PacketType.Synchronized)
            packetOut.sendTo()
            
            (remoteTick, id, result) = packet.getIntValues("tick", "id")

            if not result:
                return
            if self.tick < remoteTick:
                #미래의 패킷이면 보관한 후 나중에 처리
                postponePacket(packet)
                return

            
        elif packet.type is PacketType.SynchronizeRestart:
            #다시하기
            packetOut = Packet(PacketInOut.Out, {"type": 2}, PacketType.Synchronized)
            packetOut.sendTo()
            
            if not localGameValue.gameState is GameState.GameOver:
                return

            if localRestart == False:
                remoteRestart = True
            else:
                if localGameValue.gameState is GameState.GameOver:
                    remoteManager.gameStart()
                    localManager.gameStart()
        elif packet.type is PacketType.SynchronizeCancelRestart:
            #다시하기 취소
            packetOut = Packet(PacketInOut.Out, {"type": 2}, PacketType.Synchronized)
            packetOut.sendTo()

            if not localGameValue.gameState is GameState.GameOver:
                    return

            remoteRestart = False
        elif packet.type is PacketType.Disconnect:
            #접속 해제 패킷
            if appState == AppState.Game:
                localManager.gameEnd(True)
            closeRoom()

    #다음 블럭 생성
    def spawnNewBlock(self, id = -1):
        if id <= -1:
            id = self.gamevalue.blockID
        self.gamevalue.random.seed(self.gamevalue.RANDOM_SEED + id)
        self.gamevalue.curBlock = Block(ALL_BLOCK_STATES[self.gamevalue.random.randint(0, len(ALL_BLOCK_STATES) - 1)], self.gamevalue, self.gamevalue.blockID,
                         color = ALL_BLOCK_COLORS[self.gamevalue.random.randint(0, len(ALL_BLOCK_COLORS) - 1)],
                         dirZ = randomBit(self.gamevalue.random), dirX = randomBit(self.gamevalue.random), dirY = randomBit(self.gamevalue.random), x = self.gamevalue.lastX)
        self.gamevalue.blockID = id + 1
        self.gamevalue.changeState(GameState.Drop)
     
    #블럭 하락 속도 동기화
    def synchronizedFallingSpeed(self):
        if gameType is GameType.Network and not self.gamevalue.isRemote and not self.gamevalue.gameState is GameState.GameOver:
            packet = Packet(PacketInOut.Out, {"tick": self.tick, "speed": self.gamevalue.TICK_PER_CELL}, PacketType.ChangeTickPerCell)
            packet.sendTo()

    #--- 입력 제어 영역 ------------------------------

    #키를 눌렀을 때 1회 호출
    def keyDown(self, keyCode):
        if self.gamevalue.isRemote:
            return
        
        #빠른 드랍
        if keyCode == KEY_FAST_DROP:
            self.gamevalue.TICK_PER_CELL = ACCELERATED_TICK_PRE_CELL
            if gameType is GameType.Network and networkState.Connected and appState.Game and not self.gamevalue.isRemote and not self.gamevalue.gameState is GameState.GameOver:
                self.synchronizedFallingSpeed()
        
        if not appState is AppState.Game or self.gamevalue.gameState is GameState.GameOver:
            return
        
        #Pause 검사
        if keyCode == KEY_PAUSE:
            if not self.gamevalue.gameState is GameState.GameOver:
                if self.gamevalue.gameState is GameState.Paused:
                    #다시 누르면 Pause 해제
                    self.gamevalue.gameState = self.gamevalue.prePauseState
                else:
                    self.gamevalue.prePauseState = self.gamevalue.gameState
                    self.gamevalue.gameState = GameState.Paused

        if  self.gamevalue.gameState is GameState.Paused:
            return

        #좌우 이동
        if keyCode == KEY_LEFT:
            if not self.gamevalue.curBlock is None:
                self.gamevalue.curBlock.move(-1, 0)
        if keyCode == KEY_RIGHT:
            if not self.gamevalue.curBlock is None:
                self.gamevalue.curBlock.move(1, 0)
            
        #좌우 회전
        if keyCode == KEY_TURN_LEFT:
            if not self.gamevalue.curBlock is None:
                self.gamevalue.curBlock.turnLeft()
        if keyCode == KEY_TURN_RIGHT:
            if not self.gamevalue.curBlock is None:
                self.gamevalue.curBlock.turnRight()

    #키를 누르고 있는 동안 일정 틱마다 호출
    def keyPressed(self, keyCode):
        if not appState is AppState.Game or self.gamevalue.gameState is GameState.GameOver or self.gamevalue.gameState is GameState.Paused:
            return
        if self.gamevalue.isRemote:
            return

        #좌우 이동
        if keyCode == KEY_LEFT:
            if not self.gamevalue.curBlock is None:
                self.gamevalue.curBlock.move(-1, 0)
        if keyCode == KEY_RIGHT:
            if not self.gamevalue.curBlock is None:
                self.gamevalue.curBlock.move(1, 0)

    #키를 눌렀다가 땔 때
    def keyUp(self, keyCode):
        if self.gamevalue.isRemote:
            return

        #빠른 드랍
        if keyCode == KEY_FAST_DROP:
            self.gamevalue.TICK_PER_CELL = DEFAULT_TICK_PER_CELL
            if gameType is GameType.Network and networkState.Connected and appState.Game and not self.gamevalue.isRemote and not self.gamevalue.gameState is GameState.GameOver:
                self.synchronizedFallingSpeed()

    #마우스 클릭시 
    def mouseUp(self):
        global appState
        global menuState
        global gameType
        global keyInputListener
        global networkThread
        global networkState
        global synchronizedRestart
        global localRestart
        global remoteRestart
        global PRE_SCREEN_RESOLUTION
        global SCREEN_RESOLUTION
        global displaySettingResetTick
        global screen
        global gameMode
        
        if self.gamevalue.isRemote:
            return
        
        pos = pygame.mouse.get_pos()

        if "alert" in displayObjects and displayObjects["alert"].enable:
            return

        if appState is AppState.Menu:
            if menuState is MenuState.Main:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 150, 200, 40):
                    #메인 메뉴 - New Game
                    menuState = MenuState.GameMode
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 100, 200, 40):
                    #메인 메뉴 - Settings
                    menuState = MenuState.Options
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    #메인 메뉴 - Quit
                    pygame.quit()
                    sys.exit()
            elif menuState is MenuState.GameMode:
                if isCollideIn(pos, SCREEN_WIDTH / 4 + 10, SCREEN_HEIGTH - 230, SCREEN_WIDTH / 2 - 50, SCREEN_HEIGTH - 140):
                    #게임 플레이 - Sole
                    gameType = GameType.Local
                    self.gameReset()
                    self.gameStart()
                elif isCollideIn(pos, 3 * SCREEN_WIDTH / 4 - 10, SCREEN_HEIGTH - 295, SCREEN_WIDTH / 2 - 50, SCREEN_HEIGTH / 2 - 75):
                    #게임 플레이 - Create Room
                    gameType = GameType.Network
                    menuState = MenuState.CreateRoom
                elif isCollideIn(pos, 3 * SCREEN_WIDTH / 4 - 10, SCREEN_HEIGTH - 165, SCREEN_WIDTH / 2 - 50, SCREEN_HEIGTH / 2 - 75):
                    #게임 플레이 - Enter Room
                    gameType = GameType.Network
                    menuState = MenuState.EnterRoom
                elif isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    #세팅 - Quit
                    menuState = MenuState.Main
            elif menuState is MenuState.Options:
                if isCollideIn(pos, SCREEN_WIDTH / 2, 170, 200, 40):
                    #세팅 - Key Setting
                    menuState = MenuState.KeySetting
                elif isCollideIn(pos, SCREEN_WIDTH / 2, 220, 200, 40):
                    #세팅 - NewWork
                    menuState = MenuState.Settings
                elif isCollideIn(pos, SCREEN_WIDTH / 2, 270, 200, 40):
                    #세팅 - Help
                    menuState = MenuState.Help
                elif isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    #세팅 - Quit
                    menuState = MenuState.Main
            elif menuState is MenuState.KeySetting:
                if isCollideIn(pos, SCREEN_WIDTH / 2 - 70, 130, 100, 30):
                    #키 세팅 - Left Move
                    keyInputListener = lambda keyCode : setLeftMoveKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 - 70, 180, 100, 30):
                    #키 세팅 - Right Move
                    keyInputListener = lambda keyCode : setRightMoveKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 - 70, 230, 100, 30):
                    #키 세팅 - Left Turn
                    keyInputListener = lambda keyCode : setLeftTurnKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 - 70, 280, 100, 30):
                    #키 세팅 - Right Turn
                    keyInputListener = lambda keyCode : setRightTurnKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 + 230, 130, 100, 30):
                    #키 세팅 - Fast Drop
                    keyInputListener = lambda keyCode : setDropFastKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 + 230, 180, 100, 30):
                    #키 세팅 - Pause Game
                    keyInputListener = lambda keyCode : setPauseKey(keyCode)
                elif isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    #키 세팅 - Quit
                    menuState = MenuState.Options
            elif menuState == MenuState.Help:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    #도움말 - Quit
                    menuState = MenuState.Options
            elif menuState == MenuState.Settings:
                if isCollideIn(pos, SCREEN_WIDTH / 2 + 125, 90, 200, 50):
                    #일반 설정 - Resolution
                    curIndex = SCREEN_RESOLUTIONS.index(PRE_SCREEN_RESOLUTION)
                    if curIndex + 1 >= len(SCREEN_RESOLUTIONS):
                        PRE_SCREEN_RESOLUTION = SCREEN_RESOLUTIONS[0]
                    else:
                        PRE_SCREEN_RESOLUTION = SCREEN_RESOLUTIONS[curIndex + 1]
                elif isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    #일반 설정 - Quit / Apply
                    if SCREEN_RESOLUTION != PRE_SCREEN_RESOLUTION:
                        #Apply
                        (SCREEN_RESOLUTION, PRE_SCREEN_RESOLUTION) = (PRE_SCREEN_RESOLUTION, SCREEN_RESOLUTION)
                        displaySettingResetTick = RESET_DELAY_SEC * TPS
                        applyScreenResolution()
                    #Quit
                    menuState = MenuState.Options
            elif menuState == MenuState.CreateRoom:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    #방 생성 - Quit
                    menuState = MenuState.GameMode
                elif isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 110, 200, 40):
                    if networkThread is None:
                        #방 생성 - Create
                        createRoom()

                        networkThread = threading.Thread(target=waitEnter, daemon=True)
                        networkThread.start()
                    else:
                        #방 생성 - Cancel
                        closeRoom(useAlert = False, stay = True)
                elif isCollideIn(pos, SCREEN_WIDTH / 2 + 125, 90, 200, 50):
                    #방 생성 - GameMode
                    if networkThread is None:
                        if gameMode is GameMode.Classic:
                            gameMode = GameMode.Fusion
                        else:
                            gameMode = GameMode.Classic
            elif menuState == MenuState.EnterRoom:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40):
                    if not networkState is NetworkState.Connected:
                        #방 입장 - Quit
                        closeRoom(useAlert = False)
                        menuState = MenuState.GameMode
                elif isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 160, 250, 55):
                    if networkState is NetworkState.Disconnected:
                        #방 입장 - Connect
                        createRoom()

                        if not networkThread is None:
                            return

                        _ip = displayObjects["ip1"].getContent()
                        _ip += "." + displayObjects["ip2"].getContent()
                        _ip += "." + displayObjects["ip3"].getContent()
                        _ip += "." + displayObjects["ip4"].getContent()
                        networkThread = threading.Thread(daemon=True, target=enterRoom, args=(_ip, int(displayObjects["ipPort"].getContent())))
                        networkThread.start()
                    elif networkState is NetworkState.Connecting:
                        #방 입장 - Cancel
                        closeRoom(useAlert = False)
        elif appState is AppState.Game:
            if localGameValue.gameState is GameState.GameOver:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 120, 200, 40):
                    if gameType is GameType.Network:
                        if localRestart == False:
                            #게임 오버 - Restart
                            localRestart = True
                            synchronizedRestart = SynchronizeState.WaitSend
                        else:
                            #게임 오버 - Restart Cancel
                            localRestart = False
                            synchronizedRestart = SynchronizeState.WaitSend
                    else:
                        #게임 오버 - Restart
                        self.gameReset()
                        self.gameStart()
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 70, 200, 40):
                    #게임 오버 - Back To Menu
                    if gameType is GameType.Network:
                        closeRoom(useAlert = False)
                    appState = AppState.Menu
                    menuState = MenuState.Main
            elif localGameValue.gameState is GameState.Paused:
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 155, 200, 40):
                    #정지 메뉴 - Continue
                    localGameValue.gameState = localGameValue.prePauseState
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 105, 200, 40):
                    if gameType is GameType.Network:
                        #정지 메뉴 - Give Up
                        self.gameEnd()
                    else:
                        #정지 메뉴 - Restart
                        self.gameEnd()
                        self.gameReset()
                        self.gameStart()
                if isCollideIn(pos, SCREEN_WIDTH / 2, SCREEN_HEIGTH - 55, 200, 40):
                    #정지 메뉴 - Back To Menu
                    if gameType is GameType.Network:
                        closeRoom(useAlert = False)
                    else:
                        self.gameEnd()
                    menuState = MenuState.Main
                    appState = AppState.Menu

    #--- UX/UI 영역--------------------------------

    def drawScreen(self):
        if appState is AppState.Game:
            #배경
            pygame.draw.rect(screen, GAME_SCREEN_COLOR, 
                             resizeAll(self.gamevalue.GAME_SCREEN_OFFSET[0], self.gamevalue.GAME_SCREEN_OFFSET[1], 
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
                            
                    if self.gamevalue.cells[x][y].state is CellState.Empty:
                        pygame.draw.rect(screen, EMPTY_CELL_COLOR, 
                                         resizeAll(CELL_SIZE * x + self.gamevalue.GAME_SCREEN_OFFSET[0], 
                                          CELL_SIZE * y + self.gamevalue.GAME_SCREEN_OFFSET[1], 
                                          CELL_SIZE - offsetX, CELL_SIZE - offsetY))
                    else:
                        pygame.draw.rect(screen, self.gamevalue.cells[x][y].color, 
                                         resizeAll(CELL_SIZE * x + self.gamevalue.GAME_SCREEN_OFFSET[0],
                                          CELL_SIZE * y + self.gamevalue.GAME_SCREEN_OFFSET[1], 
                                          CELL_SIZE - offsetX, CELL_SIZE - offsetY))
            
            #페이크 블럭 그리기
            if not self.gamevalue.fakeBlock is None:
                state = self.gamevalue.fakeBlock.state
                for x in range(self.gamevalue.fakeBlock.x, self.gamevalue.fakeBlock.x + len(state)):
                    for y in range(self.gamevalue.fakeBlock.y, self.gamevalue.fakeBlock.y + len(state[0])):
                        if y < 0:
                            continue
                        
                        offsetX = CELL_OFFSET
                        offsetY = CELL_OFFSET
                        if x - 1 == HORIZONTAL_CELL_COUNT:
                            offsetX = 0
                        if y - 1 == VERTICAL_CELL_COUNT:
                            offsetY = 0
                        
                        if state[x - self.gamevalue.fakeBlock.x][y - self.gamevalue.fakeBlock.y] is CellState.Occupied:
                            pygame.draw.rect(screen, FAKE_BLOCK_COLOR, 
                                             resizeAll(CELL_SIZE * x + self.gamevalue.GAME_SCREEN_OFFSET[0], 
                                              CELL_SIZE * y + self.gamevalue.GAME_SCREEN_OFFSET[1], 
                                              CELL_SIZE - offsetX, CELL_SIZE - offsetY))
            
            #블럭 그리기
            if not self.gamevalue.curBlock is None:
                state = self.gamevalue.curBlock.curState
                for x in range(self.gamevalue.curBlock.x, self.gamevalue.curBlock.x + len(state)):
                    for y in range(self.gamevalue.curBlock.y, self.gamevalue.curBlock.y + len(state[0])):
                        if y < 0:
                            continue
                        
                        offsetX = CELL_OFFSET
                        offsetY = CELL_OFFSET
                        if x - 1 == HORIZONTAL_CELL_COUNT:
                            offsetX = 0
                        if y - 1 == VERTICAL_CELL_COUNT:
                            offsetY = 0
                        
                        if state[x - self.gamevalue.curBlock.x][y - self.gamevalue.curBlock.y] is CellState.Occupied:
                            pygame.draw.rect(screen, self.gamevalue.curBlock.color, 
                                             resizeAll(CELL_SIZE * x + self.gamevalue.GAME_SCREEN_OFFSET[0], 
                                              CELL_SIZE * y + self.gamevalue.GAME_SCREEN_OFFSET[1], 
                                              CELL_SIZE - offsetX, CELL_SIZE - offsetY))

    #UI 출력
    def drawUI(self):
        if self.gamevalue.isRemote:
            return

        pos = pygame.mouse.get_pos()

        if appState is AppState.Menu:
            if menuState is MenuState.Main:
                #메인 메뉴
                drawText("Tetris", SCREEN_WIDTH / 2, 100, size = 60, color = (255, 255, 255), font = "hancommalangmalang")
                drawText("highScore " + str(highScore), SCREEN_WIDTH / 2, 150, size = 25, color = (255, 255, 255), font = "hancommalangmalang")

                drawInterectibleTextRect(pos, "New Game", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 150, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, "Options", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 100, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, "Exit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.GameMode:
                #게임 모드 설정
                drawInterectibleTextRect(pos, "Sole", SCREEN_WIDTH / 4 + 10, SCREEN_HEIGTH - 230, SCREEN_WIDTH / 2 - 50, SCREEN_HEIGTH - 140, size = 80, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, "Create Room", 3 * SCREEN_WIDTH / 4 - 10, SCREEN_HEIGTH - 295, SCREEN_WIDTH / 2 - 50, SCREEN_HEIGTH / 2 - 75, size = 30, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, "Enter Room", 3 * SCREEN_WIDTH / 4 - 10, SCREEN_HEIGTH - 160, SCREEN_WIDTH / 2 - 50, SCREEN_HEIGTH / 2 - 75, size = 30, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")

                drawInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.KeySetting:
                #키 설정
                drawText("Key Setting", SCREEN_WIDTH / 2, 50, size = 40, color = (255, 255, 255), font = "hancommalangmalang")


                drawText("Move Left", SCREEN_WIDTH / 2 - 200, 130, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, pygame.key.name(KEY_LEFT).upper(), SCREEN_WIDTH / 2 - 70, 130, 100, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                
                drawText("Move Right", SCREEN_WIDTH / 2 - 200, 180, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, pygame.key.name(KEY_RIGHT).upper(), SCREEN_WIDTH / 2 - 70, 180, 100, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                
                drawText("Turn Left", SCREEN_WIDTH / 2 - 200, 230, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, pygame.key.name(KEY_TURN_LEFT).upper(), SCREEN_WIDTH / 2 - 70, 230, 100, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                
                drawText("Turn Right", SCREEN_WIDTH / 2 - 200, 280, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, pygame.key.name(KEY_TURN_RIGHT).upper(), SCREEN_WIDTH / 2 - 70, 280, 100, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                
                drawText("Drop Fast", SCREEN_WIDTH / 2 + 100, 130, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, pygame.key.name(KEY_FAST_DROP).upper(), SCREEN_WIDTH / 2 + 230, 130, 100, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                
                drawText("Pause Game", SCREEN_WIDTH / 2 + 100, 180, size = 20, color = (255, 255, 255), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, pygame.key.name(KEY_PAUSE).upper(), SCREEN_WIDTH / 2 + 230, 180, 100, 30, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                

                drawInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.Options:
                #설정
                drawText("Settings", SCREEN_WIDTH / 2, 60, size = 40, color = (255, 255, 255), font = "hancommalangmalang")
                
                drawInterectibleTextRect(pos, "Key Setting", SCREEN_WIDTH / 2, 170, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, "Settings", SCREEN_WIDTH / 2, 220, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, "Help", SCREEN_WIDTH / 2, 270, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                
                drawInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.Settings:
                #일반 설정
                if networkThread is None:
                    drawText("Port", SCREEN_WIDTH / 2 - 100, 170, size = 40, color = (255, 255, 255), font = "hancommalangmalang")
                drawText("Resolution", SCREEN_WIDTH / 2 - 100, 90, size = 40, color = (255, 255, 255), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, str(int(SCREEN_WIDTH * PRE_SCREEN_RESOLUTION)) + " X " + str(int(SCREEN_HEIGTH * PRE_SCREEN_RESOLUTION)), SCREEN_WIDTH / 2 + 125, 90, 200, 50, size = 30, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")

                if PRE_SCREEN_RESOLUTION != SCREEN_RESOLUTION:
                    drawInterectibleTextRect(pos, "Apply", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                else:
                    drawInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.CreateRoom:
                #방 생성
                if networkThread is None:
                    drawText("GameMode", SCREEN_WIDTH / 2 - 100, 90, size = 40, color = (255, 255, 255), font = "hancommalangmalang")
                    drawInterectibleTextRect(pos, str(gameMode._name_), SCREEN_WIDTH / 2 + 125, 90, 200, 50, size = 30, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                else:
                    if networkState is NetworkState.Disconnected:
                        drawText("Waiting Player", SCREEN_WIDTH / 2, SCREEN_HEIGTH / 2 - 50, size = 50, color = (255, 255, 255), font = "hancommalangmalang")
                    elif networkState is NetworkState.Connecting:
                        drawText("Connecting", SCREEN_WIDTH / 2, SCREEN_HEIGTH / 2 - 50, size = 50, color = (255, 255, 255), font = "hancommalangmalang")
                    elif networkState is NetworkState.Connected:
                        drawText("Connected!", SCREEN_WIDTH / 2, SCREEN_HEIGTH / 2 - 50, size = 50, color = (255, 255, 255), font = "hancommalangmalang")

                if networkThread is None:
                    drawInterectibleTextRect(pos, "Create", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 110, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                else:
                    drawInterectibleTextRect(pos, "Cancel", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 110, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.EnterRoom:
                #방 입장
                if networkState is NetworkState.Connecting:
                    drawText("Connecting", SCREEN_WIDTH / 2, 130, size = 50, color = (255, 255, 255), font = "hancommalangmalang")
                elif networkState is NetworkState.Connected:
                    drawText("Connected!", SCREEN_WIDTH / 2, 130, size = 50, color = (255, 255, 255), font = "hancommalangmalang")

                if networkState is NetworkState.Disconnected:
                    drawInterectibleTextRect(pos, "Connect", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 160, 250, 55, size = 30, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                elif networkState is NetworkState.Connecting:
                    drawInterectibleTextRect(pos, "Cancel", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 160, 250, 55, size = 30, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")

                if not networkState is NetworkState.Connected:
                    drawInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif menuState is MenuState.Help:
                #도움말
                drawText("Help", SCREEN_WIDTH / 2, 60, size = 40, color = (255, 255, 255), font = "hancommalangmalang")
                
                drawText("move block to fill line", SCREEN_WIDTH / 2, 120, size = 30, color = (200, 200, 200), font = "hancommalangmalang")
                drawText("try not to fill screen", SCREEN_WIDTH / 2, 150, size = 30, color = (200, 200, 200), font = "hancommalangmalang")
                drawText("you can play both sole", SCREEN_WIDTH / 2, 200, size = 30, color = (200, 200, 200), font = "hancommalangmalang")
                drawText("and even with your friend!", SCREEN_WIDTH / 2, 230, size = 30, color = (200, 200, 200), font = "hancommalangmalang")
                drawText("please enjoy this game", SCREEN_WIDTH / 2, 280, size = 30, color = (200, 200, 200), font = "hancommalangmalang")
                
                drawInterectibleTextRect(pos, "Quit", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 50, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
        elif appState is AppState.Game:
            if localGameValue.gameState is GameState.GameOver:
                #게임 오버
                drawTextRect("Game Over", SCREEN_WIDTH / 2, 100, dx = SCREEN_WIDTH, dy = 70, size = 60, color = (255, 255, 255), font = "hancommalangmalang", backgroundColor = (20, 20, 20))
                
                drawTextRect("score " + str(localGameValue.score), SCREEN_WIDTH / 2, 170, dy = 40, dx = 200, size = 30, color = (255, 255, 255), font = "hancommalangmalang", backgroundColor = (20, 20, 20))
                
                if remoteRestart:
                    drawText("Restart Require!", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 157, size = 25, color = (255, 255, 255), font = "hancommalangmalang")
                elif localRestart:
                    drawText("Waiting Other Player", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 157, size = 25, color = (255, 255, 255), font = "hancommalangmalang")
                if gameType is GameType.Network and localRestart:
                    drawInterectibleTextRect(pos, "Cancel", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 120, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                else:
                    drawInterectibleTextRect(pos, "Restart", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 120, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                if gameType is GameType.Local or not localRestart:
                    drawInterectibleTextRect(pos, "Back to Menu", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 70, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            elif localGameValue.gameState is GameState.Paused:
                #정지 메뉴
                drawTextRect("Paused", SCREEN_WIDTH / 2, 100, dx = SCREEN_WIDTH, dy = 70, size = 60, color = (255, 255, 255), font = "hancommalangmalang", backgroundColor = (20, 20, 20))
                
                drawTextRect("score " + str(localGameValue.score), SCREEN_WIDTH / 2, 170, dy = 40, dx = 200, size = 30, color = (255, 255, 255), font = "hancommalangmalang", backgroundColor = (20, 20, 20))
                
                drawInterectibleTextRect(pos, "Continue", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 155, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                if gameType is GameType.Local:
                    drawInterectibleTextRect(pos, "Restart", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 105, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                else:
                    drawInterectibleTextRect(pos, "Give Up", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 105, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
                drawInterectibleTextRect(pos, "Back to Menu", SCREEN_WIDTH / 2, SCREEN_HEIGTH - 55, 200, 40, size = 20, color = (255, 255, 255), backgroundColor = (50, 50, 50), newBackgroundColor = (100, 100, 100), font = "hancommalangmalang")
            else:
                #게임 중
                if gameType is GameType.Network:
                    drawText(str(localGameValue.score), 250, 50, color = (255, 255, 255), font = "hancommalangmalang")
                    drawText(str(remoteGameValue.score), 550, 50, color = (255, 255, 255), font = "hancommalangmalang")
                else:
                    drawText(str(localGameValue.score), 500, 50, color = (255, 255, 255), font = "hancommalangmalang")
     

#--- 메인 로직 영역 ------------------------------------------------------------------------------------------------------------------------------------------------

#게임 메니저 생성
localManager = GameManager(localGameValue)
remoteManager = GameManager(remoteGameValue)
localGameValue.manager = localManager
remoteGameValue.manager = remoteManager

#UI Objects 생성
displayObjects["port"] = TextField(SCREEN_WIDTH / 2 + 125, 170, 200, 50, whenNetworkSetting, font="hancommalangmalang", color=(50, 50, 50), maxLength=5, content=str(DEFAULT_PORT),
useMinMax= True, minValue=10000, maxValue=65535)
displayObjects["ip1"] = TextField(SCREEN_WIDTH / 2 -220, 130, 80, 40, whenIpInputing, font="hancommalangmalang", color=(50, 50, 50), maxLength=3, content="127",
useMinMax= True, minValue=0, maxValue=255)
displayObjects["ip2"] = TextField(SCREEN_WIDTH / 2 - 125, 130, 80, 40, whenIpInputing, font="hancommalangmalang", color=(50, 50, 50), maxLength=3, content="0",
useMinMax= True, minValue=0, maxValue=255)
displayObjects["ip3"] = TextField(SCREEN_WIDTH / 2 - 30, 130, 80, 40, whenIpInputing, font="hancommalangmalang", color=(50, 50, 50), maxLength=3, content="0",
useMinMax= True, minValue=0, maxValue=255)
displayObjects["ip4"] = TextField(SCREEN_WIDTH / 2 + 65, 130, 80, 40, whenIpInputing, font="hancommalangmalang", color=(50, 50, 50), maxLength=3, content="1",
useMinMax= True, minValue=0, maxValue=255)
displayObjects["ipPort"] = TextField(SCREEN_WIDTH / 2 + 200, 130, 150, 40, whenIpInputing, font="hancommalangmalang", color=(50, 50, 50), maxLength=5, content=str(DEFAULT_PORT),
useMinMax= True, minValue=10000, maxValue=65535)

#메인 루프
while True:
    try:
        for event in pygame.event.get():
            #윈도우 종료 처리
            if event.type == pygame.QUIT:
                try:
                    if gameType is GameType.Network and networkState is NetworkState.Connected:
                        closeRoom(useAlert = False)
                    if appState is AppState.Run and not localManager.gameState == GameState.GameOver:
                        localManager.gameEnd()
                finally:
                    pygame.quit()
                    sys.exit()

            #입력 처리
            if event.type == pygame.MOUSEBUTTONUP:
                #마우스 클릭
                localManager.mouseUp()
                for ui in displayObjects:
                    displayObjects[ui].mouseDown(pygame.mouse.get_pos())
            if event.type == pygame.KEYDOWN:
                #키보드 입력 처리 - 1
                for ui in displayObjects:
                    displayObjects[ui].keyDown(event.key)

                if not keyInputListener is None:
                    #키 설정 처리
                    if event.key in ALL_CHECKING_KEYS:
                        continue
                    keyInputListener(event.key)
                    ALL_CHECKING_KEYS = [KEY_RIGHT, KEY_LEFT, KEY_TURN_RIGHT, KEY_TURN_LEFT, KEY_FAST_DROP, KEY_PAUSE]
        
        #키보드 입력 처리 - 2
        curPressedKey = pygame.key.get_pressed()
        for keyCode in ALL_CHECKING_KEYS:
            if not curPressedKey[keyCode] and keyCode in pressedKey:
                #키 땠을 때
                localManager.keyUp(keyCode)
                pressedKey.pop(keyCode)
            if curPressedKey[keyCode]:
                if not keyCode in pressedKey:
                    #키 눌렀을 때
                    localManager.keyDown(keyCode)
                    pressedKey[keyCode] = localManager.tick
                elif (pressedKey[keyCode] >= KEY_INPUT_DELAY_TICK 
                    and localManager.tick - pressedKey[keyCode] >= KEY_INPUT_DELAY_TICK
                    and (localManager.tick - pressedKey[keyCode] - KEY_INPUT_DELAY_TICK) % KEY_INPUT_REPEAT_TICK == 0):
                    #키 누르고 있을 때
                    localManager.keyPressed(keyCode)
        
        #패킷 처리
        if gameType is GameType.Network and networkState is NetworkState.Connected:
            packet = None
            while True:
                try:
                    packetPoolLock.acquire()
                    if not hasNextPacket():
                        break
                    packet = getNextPacket()
                finally:
                    packetPoolLock.release()
                if packet is not None:
                    remoteManager.processPacket(packet)
            try:
                packetPoolLock.acquire()
                passOverReturedPackets() #보류된 패킷 넘기기
            finally:
                packetPoolLock.release()


        #메인 로직
        if gameType is GameType.Network:
            remoteManager.update()
        localManager.update()
        
        #화면 업데이트
        screen.fill(SCREEN_COLOR)
        if gameType is GameType.Network:
            remoteManager.drawScreen()
        localManager.drawScreen()
        localManager.drawUI()
        for ui in displayObjects:
            displayObjects[ui].draw()
        pygame.display.update()

        #틱 진행
        clock.tick(TPS)
    except Exception as e:
        #전체 에러 처리기
        debugLog(type(e), e)
        if networkState is None:
            networkState = NetworkState.Disconnected
            closeRoom()
        elif networkState is NetworkState.Connected:
            closeRoom()
        if appState is None:
            localManager.gameEnd(True)
            localManager.gameReset()
            appstate = AppState.Menu
            menuState = MenuState.Main
        elif appState is AppState.Game:
            localManager.gameEnd(True)
            localManager.gameReset()
            appstate = AppState.Menu
            menuState = MenuState.Main
        else:
            appstate = AppState.Menu
            menuState = MenuState.Main
