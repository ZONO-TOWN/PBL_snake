import random
import typing
from collections import deque

import time
import gc

# ---------------------------
# info
# ---------------------------

def info() -> typing.Dict:
    print("INFO")
    return {
        "apiversion": "1",
        "author": "",  # TODO: Your Battlesnake Username
        "color": "#4444FF",
        "head": "default",
        "tail": "default",
    }

# ---------------------------
# グローバル変数
# ---------------------------
direction = {"up": 0, "right": 1, "down": 2, "left": 3} #方向は数字で管理

finishNode_n = 10  #DUCTについて，子を生成する閾値

# ---------------------------
# DUCT
# ---------------------------

"""
DUCTの計算に使うノード
"""
class Node:
    def __init__(self, _parent : "Node", myDirection :int, enemyDirection :int):
        self.children = None     #4x4タプル: children[自分の方向][相手の方向]
        self.parent = _parent
        self.w = 0               #合計ウェイト(float)
        self.n = 0               #試行回数
        self.myDirection = myDirection        #自分の方向
        self.enemyDirection = enemyDirection  #相手の方向

    def get_n(self):
        return self.n

    def get_myDirection(self):
        return self.myDirection

    """
    子ノードについて，自分の方向に関してのnが一番多いmyDirectionを返す
    """
    def getMax_n_ChildDirection(self):
        pass

    """
    このノードのn(試行回数)をインクリメント
    このノードのwにgetWを加算
    さらにこのノードの親,さらにその親,さらに...にも，この処理を行う．
    このノードのnがfinishNode_nと同じになったなら，子を生成
    """
    def backup(self, getW: float):
        pass
    
    """
    子ノードを生成し，コンポジションとして持つ
    """
    def expand(self):
        tempList = [[] * 4] * 4
        for i in direction.values():
            myDirectionCheck = directionCheck(None, i, True)
            for j in direction.values():
                if myDirectionCheck and directionCheck(None, i, False):
                    tempList[i][j] = Node(self, i, j)
        self.children = tuple(tempList)

    """
    uct1計算
    """
    def uct1(self) -> float:
        pass

    """
    子ノードのuct1を比較し，選択すべきノードを決定
    そのノードに子がいるなら->子に対してevaluate
    そのノードに子がいないなら->プレイアウト(?),backup関数
    """
    def evaluate(self):
        if self.children:
            pass

"""
DUCTする
"""
def startDUCT():
    """根を生成"""
    root = Node(None, -1, -1)
    root.expand()

    """時間いっぱい探索を行う．"""
    while():
        root.evaluate()
    
    """最終的にどの方向に行くかを決める"""
    root.getMax_n_ChildDirection()

"""
プレイアウト
"""
def playout():
    pass

# ---------------------------
# Utility
# ---------------------------

"""
生存範囲の数え上げ
"""
def calculateSurvivalArea(isPlayer: bool) -> int:
    pass

"""
重みを計算（計算式は要検討）(0から1)
"""
def calculateWeight() -> float:
    pass

"""
数字を入力すると対応する方向を出力．
"""
def direction_numberToString(number : int) -> str:
    direction_map = {0: "up", 1: "right", 2: "down", 3: "left"}
    return direction_map.get(number, "unknown")


"""
進行方向に進めるかを判定する
checkBoard : チェックする盤面 
direction  : チェックする方向
isPlayer   : 対象が自分ならTrue，相手ならFalse
返り値はboolで
"""
def directionCheck(game_state : typing.Dict, checkBoard, direction: int, isPlayer: bool) -> bool:
    # 1. 現在地の取得(game_stateから取得したい)
    if isPlayer:
        head_y, head_x = checkBoard.my_body[0]
    else:
        head_y, head_x = checkBoard.enemy_body[0]

    # 2. 場外判定(fieldWidth等のGlobal変数を使用)
    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    if target_head["x"] == 0:
        is_move_safe["left"] = False
    if target_head["x"] == fieldWidth-1:
        is_move_safe["right"] = False
    if target_head["y"] == 0:
        is_move_safe["down"] = False
    if target_head["y"] == fieldHeight-1:
        is_move_safe["up"] = False


"""
ボード生成
"""
def createboard(game_state: typing.Dict):
    my_body = get_myBody(game_state)
    enemy_body = get_enemyBody(game_state)
    food_list = get_foodlist(game_state)
    fieldHeight = 11
    fieldWidth = 11
    field = [[0 for _ in range(fieldWidth)] for _ in range(fieldHeight)]
    for i in range(fieldHeight):
        for j in range(fieldWidth):
            if (i, j) in my_body:
                field[i][j] = 1
            elif (i, j) in enemy_body:
                field[i][j] = 2
            elif (i, j) in food_list:
                field[i][j] = 3
            else:
                field[i][j] = 0
    return field


# ---------------------------
# Battle Snake
# ---------------------------

def start(game_state: typing.Dict):
    print("GAME START")

def end(game_state: typing.Dict):
    print("GAME OVER\n")

def move(game_state: typing.Dict) -> typing.Dict:
    next_move_direction = 

    print(f"MOVE {game_state['turn']}: {next_move_direction} ")
    print("")
    return {"move": next_move_direction}

if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
