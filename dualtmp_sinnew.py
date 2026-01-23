import random
import typing
from collections import deque
import math
import time
import copy
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
start_time = 0 #ターン開始時の時間

direction = {"up": 0, "right": 1, "down": 2, "left": 3} #方向は数字で管理

finishNode_n = 20  #DUCTについて，子を生成する閾値

fieldHeight = 11
fieldWidth = 11

createNodeCnt = 0 #Debug用，作られたノードの数を監視，計算量の目安に
playoutCnt = 0

nowMyLength = 0
nowEnemyLength = 0
# ---------------------------
# DUCT
# ---------------------------

"""
DUCTの計算に使うノード
"""
class Node:
    def __init__(self, _parent : "Node", myDirection :int, enemyDirection :int, game_state):
        global createNodeCnt
        self.children = None     #4x4タプル: children[自分の方向][相手の方向]
        self.parent = _parent
        self.w_my = 0               #my 合計ウェイト(float)
        self.w_enemy = 0            #enemy 合計ウェイト(float)
        self.n = 0               #試行回数
        self.myDirection = myDirection        #自分の方向
        self.enemyDirection = enemyDirection  #相手の方向

        self.myBody, self.enemyBody, self.foodPos = self.node_ExpectBody(game_state)

        createNodeCnt += 1

    def node_ExpectBody(self, game_state):
        if self.parent is not None:
            myBody = copy.copy(self.parent.myBody)
            enemyBody = copy.copy(self.parent.enemyBody)
            foodPos = copy.copy(self.parent.foodPos)
            
            directions = ((1, 0), (0, 1), (-1, 0), (0, -1))
            myHead = tuple(a + b for a, b in zip(directions[self.myDirection], myBody[0]))
            enemyHead = tuple(a + b for a, b in zip(directions[self.enemyDirection], enemyBody[0]))

            myBody.insert(0, myHead)
            enemyBody.insert(0, enemyHead)
            
            if myBody[0] in foodPos:
                foodPos.remove(myBody[0])
            else:
                myBody.pop(-1)
            if enemyBody[0] in foodPos:
                foodPos.remove(enemyBody[0])
            else:
                enemyBody.pop(-1)
            
            return myBody, enemyBody, foodPos
        else:
            return get_myBody(game_state), get_enemyBody(game_state), get_foodlist(game_state)

    """
    子ノードについて、自分の方向に関してnが一番多いmyDirectionを返す
    担当者:大西
    total_n: 一つのmy_directionに対するnの合計(敵の4方向の動きに対するnの和)
    max_direction: nの最大値を持つmy_direction
    max_total_n: nの最大値
    返り値: max_direction
    """
    def getMax_n_ChildDirection(self):
        total_n = 0
        max_direction = -1
        max_total_n = -1
        for i in range(4):
            total_n = 0
            for j in range(4):
                if self.children[i][j] is not None:
                    total_n += self.children[i][j].n
            if total_n > max_total_n:
                max_total_n = total_n
                max_direction = i
        return max_direction

    """
    このノードのn(試行回数)をインクリメント
    このノードのwにgetWを加算
    さらにこのノードの親,さらにその親,さらに...にも，この処理を行う．
    このノードのnがfinishNode_nと同じになったなら，子を生成
    """
    def backup(self, myGetW: float, enemyGetW: float, game_state: typing.Dict):
        curr = self
        while curr is not None:
            curr.n += 1
            curr.w_my += myGetW
            curr.w_enemy += enemyGetW
            if curr.parent is None:
                break
            curr = curr.parent
        if self.n == finishNode_n:
            self.expand(game_state)
    
    """
    子ノードを生成し，コンポジションとして持つ
    """
    def expand(self, game_state: typing.Dict):
        tempList = [[None for _ in range(4)] for _ in range(4)]

        for i in direction.values():
            for j in direction.values():
                myDirectionCheck, enemyDirectionCheck, isCrash= directionCheck_notBoard(self.myBody, self.enemyBody, i, j)
                #print("----")
                """
                if isCrash:
                    #print("crash")
                    if (len(self.myBody) > len(self.enemyBody)):
                        enemyDirectionCheck = False
                    elif (len(self.myBody) < len(self.enemyBody)):
                        myDirectionCheck = False
                    else:
                        myDirectionCheck = False
                        enemyDirectionCheck = False
                """
                if myDirectionCheck and enemyDirectionCheck:
                    tempList[i][j] = Node(self, i, j, None)
                    #print("CreateNode")
                if myDirectionCheck:
                    print(f"myBody:{self.myBody}")
                    print(f"enemyBody:{self.enemyBody}")
                    print(f"mydir:{i}, enemydir:{j}")
                
        self.children = tuple(tempList)

    """
    今まで進んできた方向のリストを返す
    have_thisNodeDirection:現在のノードの移動をリストに含めるか
    """
    def getDirectionList(self, have_thisNodeDirection: bool):
        myDirectionList = []
        enemyDirectionList = []

        curr = self
        if not have_thisNodeDirection:
            curr = self.parent
        while (curr is not None and curr.parent is not None):
            myDirectionList.insert(0, curr.myDirection)
            enemyDirectionList.insert(0, curr.enemyDirection)
            if curr.parent is None:
                break
            curr = curr.parent
        
        return myDirectionList, enemyDirectionList

    """
    子ノードのuct1計算を計算し，ucb1が最大になる移動方向の組（ノード）を返す．
    自分，敵それぞれ各方向に関してucb1を計算(参考:https://www.terry-u16.net/entry/decoupled-uct#f-d7234ffa)
    つまり4+4個分のucb1を導出し，一番大きい組み合わせの子ノードを返す
    """
    def maxUcb1Node(self) -> "Node":
        """ 自分の最善手を計算 """
        best_my_direction = -1
        max_my_ucb = -1.0
        
        # 自分の4方向（上下左右）についてループ
        for my_d in range(4):
            sum_my_w = 0 
            sum_n = 0          # 自分の合計試行回数
            has_child = False
            
            # 自分がその方向に進んだ場合に、相手の4方向（上下左右）についてループ
            for enemy_d in range(4):
                child = self.children[my_d][enemy_d]
                if child is not None:
                    has_child = True
                    sum_my_w += child.w_my
                    sum_n += child.n
            
            if has_child:
                # 自分視点のUCB1
                score = self.ucb1(sum_my_w, sum_n)
                if score > max_my_ucb:
                    max_my_ucb = score
                    best_my_direction = my_d

        """ 相手の最善手を計算 """
        best_enemy_direction = -1
        max_enemy_ucb = -1.0

        # 相手の4方向（上下左右）についてループ
        for enemy_d in range(4):
            sum_enemy_w = 0
            sum_n = 0
            has_child = False
            
            # 相手がその方向に進んだ場合に、自分の4方向（上下左右）についてループ
            for my_d in range(4):
                child = self.children[my_d][enemy_d]
                if child is not None:
                    has_child = True
                    sum_enemy_w += child.w_enemy
                    sum_n += child.n
            
            if has_child:
                # 相手視点のUCB1
                score = self.ucb1(sum_enemy_w, sum_n)
                if score > max_enemy_ucb:
                    max_enemy_ucb = score
                    best_enemy_direction = enemy_d

        # 双方の最善手を満たすノードを返す
        if best_my_direction != -1 and best_enemy_direction != -1:
            return self.children[best_my_direction][best_enemy_direction]
        else:
            return None

    """
    ucb1を計算
    """
    def ucb1(self, w :float, n :float) -> float:
        if n == 0:
            return float('inf')         # 探索を促すためにinfiniteを返す
        
        c = 1.414       # 探索定数（仮）
        exploration_term = c * math.sqrt(math.log(self.n) / n)
        return (w / n) + exploration_term

    """
    子ノードのucb1を比較し，選択すべきノードを決定
    そのノードに子がいるなら->子に対してevaluate
    そのノードに子がいないなら->プレイアウト(?),backup関数
    """
    def evaluate(self, game_state: typing.Dict):
        # 子ノードが存在しない場合
        if self.children is None:
            getW_my, getW_enemy = self.calculateWeight(game_state)
            self.backup(getW_my, getW_enemy, game_state)
            return

        # 子ノードが存在する場合
        nextNode = self.maxUcb1Node()
        
        if nextNode is not None:
            nextNode.evaluate(game_state)
        else:
            # 次世代に子ノードが存在しない場合
            self.backup(0, 0, game_state)

    """
    重みを計算（計算式は要検討）(0から1)
    """
    def calculateWeight(self, game_state: typing.Dict) -> float:
        global playoutCnt
        playoutCnt += 1

        if self.myBody[0] == self.enemyBody[0]:
            if (len(self.myBody) > len(self.enemyBody)):
                return 1, 0
            elif (len(self.myBody) < len(self.enemyBody)):
                return 0, 1
            else:
                return 0, 0
        #simulation
        #mydirList, enemydirList = self.simulate_old(game_state, 10, mydirList, enemydirList)
        myBody, enemyBody, myGetFood, enemyGetFood, isCrash = self.simulate(game_state, 5)

        myExpectLength = len(self.myBody) + myGetFood
        enemyExpectLenght = len(self.enemyBody) + enemyGetFood
        #頭が衝突するとき0or1を返す．
        #勝敗は現在のHPで比較しているため，精度は低い
        if isCrash:
            if myExpectLength > enemyExpectLenght:
                return 1, 0
            elif myExpectLength < enemyExpectLenght:
                return 0, 1
            else:
                return 0, 0
        
        #衝突しないとき
        myWeight = 0.5
        enemyWeight = 0.5

        #体の長さを評価
        incMyLength = myExpectLength - nowMyLength
        incEnemyLength = enemyExpectLenght - nowEnemyLength
        incDif = max(0, min((incMyLength - incEnemyLength) * 0.1, 0.2))
        myWeight += incDif
        enemyWeight -= incDif

        #生存範囲で評価
        """
        crashPoint, myPoint, enemyPoint = deepCalculateSurvivalArea(myBody, enemyBody)
        sumPoint = crashPoint + myPoint + enemyPoint

        if myExpectLength > enemyExpectLenght:
            myPoint += crashPoint
        elif myExpectLength < enemyExpectLenght:
            enemyPoint += crashPoint

        if myPoint > enemyPoint:
            myWeight += myPoint/sumPoint * 0.3
            enemyWeight -= myPoint/sumPoint * 0.3
        elif myPoint < enemyPoint:
            enemyWeight += enemyPoint/sumPoint * 0.3
            myWeight -= enemyPoint/sumPoint * 0.3
        """

        return myWeight, enemyWeight

    """
    nターン後までシミュレート
    返り値
    myBody:シミュレーション後のmyBody
    enemyBody
    myFood:シミュレーション後どれだけ餌をとれたか
    enemyFood
    isCrash
    """
    def simulate(self, game_state: typing.Dict, turn: int):
        if turn == 0:
            return self.myBody, self.enemyBody, 0, 0, False
        myBody = copy.copy(self.myBody)
        enemyBody = copy.copy(self.enemyBody)
        myFood = 0
        enemyFood = 0

        foodPos = copy.copy(self.foodPos)
  
        directions = ((1, 0), (0, 1), (-1, 0), (0, -1))

        for i in range(0, turn):
            mydirOk = []
            enemydirOk = []

            for dir in direction.values():
                myOk, temp, isCrash = directionCheck_notBoard(myBody, enemyBody, dir, -1)
                temp, enemyOk, isCrash = directionCheck_notBoard(myBody, enemyBody, -1, dir)
                if myOk:    
                    mydirOk.append(dir)
                if enemyOk:
                    enemydirOk.append(dir)
            if (len(mydirOk) == 0 or len(enemydirOk) == 0):
                return myBody, enemyBody, myFood, enemyFood, False
            random_mydir = mydirOk[random.randrange(0, len(mydirOk))]
            random_enemydir = enemydirOk[random.randrange(0, len(enemydirOk))]

            myHead = tuple(a + b for a, b in zip(directions[random_mydir], myBody[0]))
            enemyHead = tuple(a + b for a, b in zip(directions[random_enemydir], enemyBody[0]))
            
            myBody.insert(0, myHead)
            enemyBody.insert(0, enemyHead)
            
            if myBody[0] in foodPos:
                foodPos.remove(myBody[0])
                myFood += 1
            else:
                myBody.pop(-1)
            if enemyBody[0] in foodPos:
                foodPos.remove(enemyBody[0])
                enemyFood += 1
            else:
                enemyBody.pop(-1)

            if myBody[0] == enemyBody[0]:
                return myBody, enemyBody, myFood, enemyFood, True

        return myBody, enemyBody, myFood, enemyFood, False

"""
DUCTする
"""
def startDUCT(game_state: typing.Dict):
    global nowMyLength, nowEnemyLength
    nowMyLength = len(get_myBody(game_state))
    nowEnemyLength = len(get_enemyBody(game_state))

    """根を生成"""
    root = Node(None, -1, -1, game_state)
    print("expand_start")
    root.expand(game_state)
    print("expand_end")
    """時間いっぱい探索を行う．"""
    evaluate_cnt = 0
    while(time.time() - start_time < 0.4):
        root.evaluate(game_state)
        evaluate_cnt += 1
    
    print(evaluate_cnt)

    """最終的にどの方向に行くかを決める"""
    return root.getMax_n_ChildDirection()

# ---------------------------
# Utility
# ---------------------------

"""
生存範囲の数え上げ（高精度）
nターン後に到達できる座標について，nターン以内に相手がその座標に到達できないセルの数え上げ．
複数方向あるときは最大値をとる
"""
def deepCalculateSurvivalArea(myBody, enemyBody):
    #BFS用のボードを作る
    #myBoard,enemyBoardそれぞれは，それぞれのマスに行くために何ターン必要かを表している．到達不可のセルは負の値をとる
    #要改善
    board_forBFS = [[0 for _ in range(fieldWidth)] for _ in range(fieldHeight)]
    myBoard = [[0 for _ in range(fieldWidth)] for _ in range(fieldHeight)]
    enemyBoard = [[0 for _ in range(fieldWidth)] for _ in range(fieldHeight)]
    for i in range(fieldHeight):
        for j in range(fieldWidth):
            if (i, j) in myBody or (i, j) in enemyBody:
                board_forBFS[i][j] = -2
                myBoard[i][j] = -2
                enemyBoard[i][j] = -2
            else:
                board_forBFS[i][j] = -1
                myBoard[i][j] = -1
                enemyBoard[i][j] = -1

    #BFS
    directions = [(1, 0), (-1, 0), (0, -1), (0, 1)]
    sy, sx = myBody[0]
    que = deque()
    que.append((sy, sx))
    while que:
        y, x = que.popleft()
        for dy, dx in directions:
            ny, nx = y + dy, x + dx
            if not (0 <= ny < fieldHeight and 0 <= nx < fieldWidth):
                continue
            # 通行可能か（-1 は空き）
            if myBoard[ny][nx] != -1:
                continue
            myBoard[ny][nx] = myBoard[y][x] + 1
            que.append((ny, nx))

    sy, sx = enemyBody[0]
    que = deque()
    que.append((sy, sx))
    while que:
        y, x = que.popleft()
        for dy, dx in directions:
            ny, nx = y + dy, x + dx
            if not (0 <= ny < fieldHeight and 0 <= nx < fieldWidth):
                continue
            # 通行可能か（-1 は空き）
            if enemyBoard[ny][nx] != -1:
                continue
            enemyBoard[ny][nx] = enemyBoard[y][x] + 1
            que.append((ny, nx))


    #nターン以内に相手がその座標に到達できないセルの数え上げ
    clashPoint = 0
    myPoint = 0
    enemyPoint = 0
    for i in range(fieldHeight):
        for j in range(fieldWidth):
            if(myBoard[i][j] == enemyBoard[i][j]):
                clashPoint += 1
            elif(myBoard[i][j] < enemyBoard[i][j]):
                myPoint += 1
            else:
                enemyPoint += 1
    return clashPoint, myPoint, enemyPoint
    
"""
進行方向に進めるか判定
ボードなし版
返り値
(自分の方向について，相手の方向について，衝突する)
"""
def directionCheck_notBoard(myBody, enemyBody, mydir: int, enemydir: int):
    myDirectionOk = True
    enemyDirectionOk = True
    isCrash = False

    myHead = myBody[0]
    enemyHead = enemyBody[0]

    directions = ((1, 0), (0, 1), (-1, 0), (0, -1))
    if 0 <= mydir:
        next_myHead = tuple(a + b for a, b in zip(directions[mydir], myHead))
    else:
        next_myHead = myHead
    if 0 <= enemydir:
        next_enemyHead = tuple(a + b for a, b in zip(directions[enemydir], enemyHead))
    else:
        next_enemyHead = enemyHead

    if not (0 <= next_myHead[0] < fieldHeight and 0 <= next_myHead[1] < fieldWidth):
        myDirectionOk = False
    if not (0 <= next_enemyHead[0] < fieldHeight and 0 <= next_enemyHead[1] < fieldWidth):
        enemyDirectionOk = False
    if ((next_myHead in myBody) or (next_myHead in enemyBody)):
        myDirectionOk = False
    if ((next_enemyHead in myBody) or (next_enemyHead in enemyBody)):
        enemyDirectionOk = False

    if (next_myHead == next_enemyHead):
        isCrash = True

    return myDirectionOk, enemyDirectionOk, isCrash


"""
数字を入力すると対応する方向を出力．
"""
def direction_numberToString(number : int):
    direction_map = {0: "up", 1: "right", 2: "down", 3: "left"}
    return direction_map.get(number, "unknown")

def get_myBody(game_state: typing.Dict):
    return [(b["y"], b["x"]) for b in game_state['you']['body']]

def get_enemyBody(game_state: typing.Dict):
    if len(game_state["board"]["snakes"]) == 1:
        return [(0,0)]
    return [(b["y"], b["x"]) for b in game_state["board"]["snakes"][1]["body"]]

def get_foodlist(game_state: typing.Dict):
    return [(f["y"], f["x"]) for f in game_state["board"]["food"]]

# ---------------------------
# Battle Snake
# ---------------------------

def start(game_state: typing.Dict):
    print("GAME START")

def end(game_state: typing.Dict):
    print("GAME OVER\n")

def move(game_state: typing.Dict) -> typing.Dict:
    global start_time, createNodeCnt, playoutCnt
    createNodeCnt = 0
    playoutCnt = 0
    start_time = time.time()

    next_direction = startDUCT(game_state)

    next_move_direction = direction_numberToString(next_direction)

    print(f"MOVE {game_state['turn']}: {next_move_direction} ")
    print(f"CreateNode: {createNodeCnt}")
    print(f"PlayOut: {playoutCnt}")
    print("")
    return {"move": next_move_direction}

if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
