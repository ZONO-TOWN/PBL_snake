// Copyright [2021] <Copyright Eita Aoki (Thunder) >
#include<string>
#include<vector>
#include<sstream>
#include<utility>
#include<random>
#include<assert.h>
#include<math.h>
#include<chrono>
#include <algorithm>
#include <tuple>
#include <deque>
#include <optional>
#include<iostream>
#include<functional>

std::random_device rnd;
std::mt19937 mt(rnd());

using Action = int;
// 移動方向の定義
constexpr const Action UP = 0;
constexpr const Action DOWN = 1;
constexpr const Action LEFT = 2;
constexpr const Action RIGHT = 3;

using Actions = std::vector<int>;
using ScoreType = int64_t;
constexpr const ScoreType INF = 1000000000LL;

// 盤面サイズ
constexpr const int H = 10; // 高さ
constexpr const int W = 10; // 幅

// ヘビの体を表す座標
using Point = std::pair<int, int>;
// ヘビの体のリスト（キューまたはデック）
using Snake = std::deque<Point>;

// 時間を管理するクラス
class TimeKeeper {
private:
	std::chrono::high_resolution_clock::time_point start_time_;
	int64_t time_threshold_;

public:

	// 時間制限をミリ秒単位で指定してインスタンスをつくる。
	TimeKeeper(const int64_t& time_threshold)
		:start_time_(std::chrono::high_resolution_clock::now()),
		time_threshold_(time_threshold)
	{

	}

	// インスタンス生成した時から指定した時間制限を超過したか判定する。
	bool isTimeOver() const {
		auto diff = std::chrono::high_resolution_clock::now() - this->start_time_;
		return std::chrono::duration_cast<std::chrono::milliseconds>(diff).count() >= time_threshold_;
	}

};

// ヘビゲームのDuelモード
class SnakeDuelState {
private:
    // ヘビの体 (0: 現プレイヤー, 1: 敵プレイヤー)
    std::vector<Snake> snakes_; 
    // 餌の位置 (存在しない場合はnullopt)
    std::optional<Point> food_pos_; 
    // どちらのプレイヤーのターンか (0: 先手/現プレイヤー, 1: 後手/敵プレイヤー)
    int turn_; 

    // 新しい餌の位置をランダムに設定
    void setFoodPosition() {
        std::vector<Point> empty_cells;
        for (int y = 0; y < H; ++y) {
            for (int x = 0; x < W; ++x) {
                Point p = {x, y};
                // 既にヘビの体があるマスは除外
                bool is_snake = false;
                for(const auto& body_part : snakes_[0]) if (body_part == p) is_snake = true;
                for(const auto& body_part : snakes_[1]) if (body_part == p) is_snake = true;
                
                if (!is_snake) {
                    empty_cells.push_back(p);
                }
            }
        }

        if (!empty_cells.empty()) {
            this->food_pos_ = empty_cells[mt() % empty_cells.size()];
        } else {
            this->food_pos_ = std::nullopt; // 盤面が埋まった
        }
    }

    // 次の移動先座標を計算
    Point nextHead(const Snake& snake, const Action action) const {
        Point head = snake.front();
        switch (action) {
            case UP: head.second--; break;
            case DOWN: head.second++; break;
            case LEFT: head.first--; break;
            case RIGHT: head.first++; break;
        }
        return head;
    }

    // 衝突判定
    bool isCollision(const Point& head, const Snake& my_snake, const Snake& enemy_snake) const {
        // 1. 壁の衝突
        if (head.first < 0 || head.first >= W || head.second < 0 || head.second >= H)
            return true;

        // 2. 自分の体との衝突 (頭の次以降)
        if (my_snake.size() > 1) {
            for (auto it = std::next(my_snake.begin()); it != my_snake.end(); ++it) {
                if (*it == head) return true;
            }
        }
        
        // 3. 相手の体との衝突
        for (const auto& body_part : enemy_snake) {
            if (body_part == head) return true;
        }

        return false;
    }

public:
    // 初期化
    SnakeDuelState() : turn_(0), snakes_(2) {
        // P0 (現プレイヤー) は左上からスタート
        snakes_[0].push_back({W/4, H/4});
        // P1 (敵プレイヤー) は右下からスタート
        snakes_[1].push_back({W*3/4, H*3/4});
        setFoodPosition();
    }
    
    // [どのゲームでも実装する] : 現在のプレイヤー視点の盤面評価
    ScoreType getScore() const {
        if (this->isLose()) return -INF; 
        if (this->isDraw()) return 0;
        // 自分の長さ - 相手の長さ
        return snakes_[0].size() - snakes_[1].size();
    }

    // [どのゲームでも実装する] : 現在のプレイヤーが負けたか判定
    bool isLose() const {
        // ヘビの体が1つもない状態を負けとします
        return snakes_[0].empty();
    }
    
    // [どのゲームでも実装する] : 引き分けになったか判定
    bool isDraw() const {
        // 盤面が全てヘビで埋まり、餌がない
        if (food_pos_ == std::nullopt) {
            return true;
        }
        // お互いが合法手を持たない（両方同時に衝突/身動きが取れない）
        if (legalActions().empty() && getEnemyLegalActions().empty()) {
             return true;
        }
        return false;
    }

    // [どのゲームでも実装する] : ゲームが終了したか判定
    bool isDone() const {
        return snakes_[0].empty() || snakes_[1].empty() || isDraw();
    }
    
    // 敵プレイヤーの合法手を取得（主に isDraw 判定用）
    Actions getEnemyLegalActions() const {
        Actions actions;
        const auto& my_snake = snakes_[1];
        const auto& enemy_snake = snakes_[0];
        
        Actions all_moves = {UP, DOWN, LEFT, RIGHT};
        for (const auto action : all_moves) {
            Point next = nextHead(my_snake, action);
            if (!isCollision(next, my_snake, enemy_snake)) {
                actions.emplace_back(action);
            }
        }
        return actions;
    }
    
    // [どのゲームでも実装する] : 現在のプレイヤーが可能な行動を全て取得
    Actions legalActions() const {
        Actions actions;
        const auto& my_snake = snakes_[0];
        const auto& enemy_snake = snakes_[1];
        
        Actions all_moves = {UP, DOWN, LEFT, RIGHT};
        for (const auto action : all_moves) {
            Point next = nextHead(my_snake, action);
            if (!isCollision(next, my_snake, enemy_snake)) {
                actions.emplace_back(action);
            }
        }
        return actions;
    }

    // [どのゲームでも実装する] : 指定したactionでゲームを1ターン進め、次のプレイヤー視点の盤面にする
    void advance(const Action action) {
        Snake& my_snake = snakes_[0];
        Snake& enemy_snake = snakes_[1];
        
        Point next = nextHead(my_snake, action);
        
        // **注意: MCTS/MiniMaxは legalActions から行動を選ぶため、通常この advance は衝突しない行動で呼ばれます**
        // ただし、プレイアウト（ランダム行動）では、advance の前に legalActions のチェックが必要です。
        
        // 衝突判定（MCTSでは不要だがロジックとしては重要）
        if (isCollision(next, my_snake, enemy_snake)) {
            // 衝突した場合、自分のヘビを消滅させる（負け）
            my_snake.clear();
        } else {
            // 衝突しない場合: 移動
            my_snake.push_front(next);
            
            // 餌の取得判定
            if (food_pos_.has_value() && next == food_pos_.value()) {
                // 餌を取った場合、しっぽは消えない（ヘビが伸びる）
                setFoodPosition();
            } else {
                // 餌を取らなかった場合、しっぽを消す（ヘビの長さ維持）
                my_snake.pop_back();
            }
        }
        
        // プレイヤー交代
        std::swap(snakes_[0], snakes_[1]);
        turn_ = (turn_ + 1) % 2;
    }

    // [実装しなくてもよいが実装すると便利] : 現在のプレイヤーの勝率計算のためのスコアを計算する
    double getFirstPlayerScoreForWinRate() const {
        if (snakes_[1].empty()) return 1.0; // P1(先手)が勝った
        if (snakes_[0].empty()) return 0.0; // P2(後手)が勝った
        if (isDraw()) return 0.5;
        return 0.5; // 決着がついていない
    }

    // [実装しなくてもよいが実装すると便利] : 現在のゲーム状況を文字列にする
    std::string toString() const {
        std::stringstream ss;
        ss << "Turn: P" << turn_ << ", Current Snake Length: " << snakes_[0].size() << ", Enemy Snake Length: " << snakes_[1].size() << std::endl;
        
        std::vector<std::vector<char>> board(H, std::vector<char>(W, '.'));

        // 餌
        if (food_pos_.has_value()) {
            board[food_pos_->second][food_pos_->first] = '*';
        }
        
        // 敵のヘビ ( 'o' )
        for (const auto& p : snakes_[1]) {
            board[p.second][p.first] = 'o';
        }
        // 現プレイヤーのヘビ ( 'x' )
        for (const auto& p : snakes_[0]) {
            board[p.second][p.first] = 'x';
        }

        // 頭の強調
        if (!snakes_[0].empty()) board[snakes_[0].front().second][snakes_[0].front().first] = 'X';
        if (!snakes_[1].empty()) board[snakes_[1].front().second][snakes_[1].front().first] = 'O';

        for (int y = 0; y < H; ++y) {
            for (int x = 0; x < W; ++x) {
                ss << board[y][x];
            }
            ss << std::endl;
        }
        return ss.str();
    }
};

using State = SnakeDuelState;

// ランダムに行動を決定する
Action randomAction(const State& state) {
	auto legal_actions = state.legalActions();
    if (legal_actions.empty()) return -1; // 合法手がない場合は無効な値を返す
	return legal_actions[mt() % (legal_actions.size())];
}


namespace montecarlo {
	// 配列の最大値のインデックスを返す
	int argMax(const std::vector<double>& x) {
		return std::distance(x.begin(), std::max_element(x.begin(), x.end()));
	}
	// ランダムプレイアウトをして勝敗スコアを計算する
	double playout(State* state) { 
		if (state->isDone()) {
            // isLose() は現在のプレイヤー（次に動くプレイヤー）が負けているか判定
			if (state->isLose()) return 0.0; // 現プレイヤーが負け (前のプレイヤーの勝利)
			if (state->isDraw()) return 0.5; // 引き分け
            // 現プレイヤーが負けておらず、ゲームが終了している場合（=敵ヘビが空）
            return 1.0; // 現プレイヤーの勝利
		}

		auto legal_actions = state->legalActions();
		if (legal_actions.empty()) {
            // 合法手がない場合はその場で負けと見なす
			return 0.0;
		}

		state->advance(randomAction(*state));
        // 相手の視点でのスコアを 1.0 から引く
		return 1. - playout(state);
	}
	
	// プレイアウト回数を指定して原始モンテカルロ法で行動を決定する
	Action primitiveMontecarloAction(const State& state, int playout_number) {
		auto legal_actions = state.legalActions();
        if (legal_actions.empty()) return -1;
        
		double best_value = -INF;
		int best_i = -1;
		for (int i = 0; i < legal_actions.size(); i++) {
			double value = 0;
			for (int j = 0; j < playout_number; j++) {
				State next_state = state;
				next_state.advance(legal_actions[i]);
				value += 1. - playout(&next_state);
			}
			if (value > best_value) {
				best_i = i;
				best_value = value;
			}
		}
		return legal_actions[best_i];

	}
	// 制限時間(ms)を指定して原始モンテカルロ法で行動を決定する
	Action primitiveMontecarloActionWithTimeThreshold(const State& state, const int64_t time_threshold) {
		auto legal_actions = state.legalActions();
        if (legal_actions.empty()) return -1;

		auto time_keeper = TimeKeeper(time_threshold);
		auto values = std::vector<double>(legal_actions.size());
        auto counts = std::vector<int>(legal_actions.size(), 0);

        // 時間が許す限りプレイアウトを続ける
		while (true) {
			for (int i = 0; i < legal_actions.size(); i++) {
				State next_state = state;
				next_state.advance(legal_actions[i]);
				values[i] += 1. - playout(&next_state);
                counts[i]++;
			}
			if (time_keeper.isTimeOver()) {
				break;
			}
		}

        // プレイアウトが1回も行われなかった場合の防御
        if (std::all_of(counts.begin(), counts.end(), [](int c){ return c == 0; })) {
            return legal_actions[0];
        }

		return legal_actions[argMax(values)];
	}

	constexpr const double C = 1.; //UCB1の計算に使う定数
	constexpr const int EXPAND_THRESHOLD = 10; // ノードを展開する閾値

	// MCTSの計算に使うノード
	class Node {
	private:
		State state_;
		double w_; // 勝利点 (Win)
	public:
		std::vector<Node>child_nodes;
		double n_; // 試行回数 (Count)

		// ノードの評価を行う (選択->展開->シミュレーション->バックプロパゲーション)
		double evaluate() {
			if (this->state_.isDone()) {
                // 勝敗が決まっている場合
				double value = this->state_.isLose() ? 0 : (this->state_.isDraw() ? 0.5 : 1.0);
				this->w_ += value;
				++this->n_;
				return value;
			}
			if (this->child_nodes.empty()) {
                // 展開されていないノード（シミュレーション）
				State state_copy = this->state_;
				double value = playout(&state_copy);
				this->w_ += value;
				++this->n_;

				if (this->n_ == EXPAND_THRESHOLD)
					this->expand();

				return value;
			}
			else {
                // 展開されているノード（選択）
				double value = 1. - this->nextChiledNode().evaluate();
				this->w_ += value;
				++this->n_;
				return value;
			}
		}

		// ノードを展開する
		void expand() {
			auto legal_actions = this->state_.legalActions();
			this->child_nodes.clear();
			for (const auto action : legal_actions) {
				this->child_nodes.emplace_back(this->state_);
				this->child_nodes.back().state_.advance(action);
			}
		}

		// UCB1に基づいてどのノードを評価するか選択する
		Node& nextChiledNode() {
			for (auto& child_node : this->child_nodes) {
				if (child_node.n_ == 0)
					return child_node; // 未試行のノードを優先
			}
			double t = 0;
			for (const auto& child_node : this->child_nodes) {
				t += child_node.n_;
			}
			double best_value = -INF;
			int best_i = -1;
			for (int i = 0; i < this->child_nodes.size(); i++) {
				const auto& child_node = this->child_nodes[i];
				
                // UCB1 = (1 - 相手視点の勝率) + C * sqrt(2 * log(親の試行回数) / 自分の試行回数)
				double ucb1_value = (1. - child_node.w_ / child_node.n_) + (double)C * std::sqrt(2. * std::log(t) / child_node.n_);
				if (ucb1_value > best_value) {
					best_i = i;
					best_value = ucb1_value;
				}
			}
			return this->child_nodes[best_i];
		}

		Node(const State& state) :state_(state), w_(0), n_(0) {}

	};

	// プレイアウト数を指定してMCTSで行動を決定する
	Action mctsAction(const State& state, const int playout_number) {
		Node root_node = Node(state);
		root_node.expand();
        if (root_node.child_nodes.empty()) return -1;

		for (int i = 0; i < playout_number; i++) {
			root_node.evaluate();
		}
		auto legal_actions = state.legalActions();

		int best_n = -1;
		int best_i = -1;
		assert(legal_actions.size() == root_node.child_nodes.size());
		for (int i = 0; i < legal_actions.size(); i++) {
			int n = root_node.child_nodes[i].n_;
			if (n > best_n) {
				best_i = i;
				best_n = n;
			}
		}
		return legal_actions[best_i];
	}

	// 制限時間(ms)を指定してMCTSで行動を決定する
	Action mctsActionWithTimeThreshold(const State& state, const int64_t time_threshold) {
		Node root_node = Node(state);
		root_node.expand();
        auto legal_actions = state.legalActions();
        if (root_node.child_nodes.empty()) return -1; // 合法手がない
        
		auto time_keeper = TimeKeeper(time_threshold);
		for (int cnt = 0;; cnt++) {
			if (time_keeper.isTimeOver()) {
				break;
			}
			root_node.evaluate();
		}
        
        // 1回も探索が行われなかった場合は最初の合法手を返す
        int best_i_default = 0;
        if (root_node.n_ == 0) {
            return legal_actions[best_i_default];
        }

		int best_n = -1;
		int best_i = -1;
		assert(legal_actions.size() == root_node.child_nodes.size());
		for (int i = 0; i < legal_actions.size(); i++) {
			int n = root_node.child_nodes[i].n_;
			if (n > best_n) {
				best_i = i;
				best_n = n;
			}
		}
		return legal_actions[best_i];
	}
}
using montecarlo::primitiveMontecarloAction;
using montecarlo::mctsAction;
using montecarlo::mctsActionWithTimeThreshold;
using montecarlo::primitiveMontecarloActionWithTimeThreshold;


using AIFunction = std::function<Action(const State&)>;
using StringAIPair = std::pair<std::string, AIFunction>;

// ゲームを1回プレイしてゲーム状況を表示する
void playGame(const std::vector<StringAIPair>& ais) {
	using std::cout; using std::endl;
	auto state = State();
    if (state.legalActions().empty()) {
        cout << "ゲーム開始直後に合法手がありません。" << endl;
        return;
    }
    
	while (!state.isDone()) {
		// 1p
		{
			cout << "1p " << ais[0].first << "------------------------------------" << endl;
			Action action = ais[0].second(state);
			cout << "action " << action << endl;
            if (action < 0) {
                cout << "1p: 合法手がないため負け（または引き分け）" << endl;
                break;
            }
			state.advance(action);
			cout << state.toString() << endl;
			if (state.isDone())break;
		}
		// 2p
		{
			cout << "2p " << ais[1].first << "------------------------------------" << endl;
			Action action = ais[1].second(state);
			cout << "action " << action << endl;
            if (action < 0) {
                cout << "2p: 合法手がないため負け（または引き分け）" << endl;
                break;
            }
			state.advance(action);
			cout << state.toString() << endl;
			if (state.isDone())break;
		}
	}
    cout << "--- Game Ended ---" << endl;
    if (state.getFirstPlayerScoreForWinRate() == 1.0) {
        cout << "Winner: 1p (" << ais[0].first << ")" << endl;
    } else if (state.getFirstPlayerScoreForWinRate() == 0.0) {
        cout << "Winner: 2p (" << ais[1].first << ")" << endl;
    } else {
        cout << "Result: Draw" << endl;
    }
}

// ゲームをgame_number×2(先手後手を交代)回プレイしてaisの0番目のAIの勝率を表示する。
void testFirstPlayerWinRate(const std::vector<StringAIPair>& ais, const int game_number) {
	using std::cout; using std::endl;

	double first_player_win_rate = 0;
	for (int i = 0; i < game_number; i++) {
		for (int j = 0; j < 2; j++) {//先手後手平等に行う
			auto state = State();
			auto& first_ai = ais[j];
			auto& second_ai = ais[(j + 1) % 2];
            
            bool game_aborted = false;
			while (true) {
                
                // P1の行動
                Action action1 = first_ai.second(state);
                if (action1 < 0) {game_aborted = true; break;}
                state.advance(action1);
                if (state.isDone())break;

                // P2の行動
                Action action2 = second_ai.second(state);
                if (action2 < 0) {game_aborted = true; break;}
                state.advance(action2);
                if (state.isDone())break;
			}
            
            if (game_aborted) {
                 cout << "Warning: Game aborted due to no legal action." << endl;
                 continue;
            }

			double win_rate_point = state.getFirstPlayerScoreForWinRate();
			// P1(ais[j])が先手でなかった場合、勝率を反転してais[0]視点に戻す
			if (j == 1)win_rate_point = 1.0 - win_rate_point;
			
			first_player_win_rate += win_rate_point;


		}
		cout << "i " << i << " w " << first_player_win_rate / ((i + 1) * 2) << endl;

	}
	first_player_win_rate /= (double)(game_number * 2);
	cout << "Winning rate of " << ais[0].first << " to " << ais[1].first << ":\t" << first_player_win_rate << endl;
}
int main() {
	using std::cout; using std::endl;

	std::vector<StringAIPair> ais = {
		// モンテカルロ木探索 (MCTS): 1000回プレイアウト
		StringAIPair("mctsAction",[](const State& state) {return mctsAction(state, 1000); }),
		// 原始モンテカルロ法: 1000回プレイアウト
		StringAIPair("primitiveMontecarloAction",[](const State& state) {return primitiveMontecarloAction(state,1000); }),
		// MCTS: 制限時間 10ms
		// StringAIPair("mctsActionWithTimeThreshold",[](const State& state) {return mctsActionWithTimeThreshold(state, 10); }),
		// 原始モンテカルロ法: 制限時間 10ms
		// StringAIPair("primitiveMontecarloActionWithTimeThreshold",[](const State& state) {return primitiveMontecarloActionWithTimeThreshold(state, 10); }),
	};
	
	cout << "--- Single Game Play ---" << endl;
	playGame(ais);
	
    // cout << "\n--- Win Rate Test (10 games) ---" << endl;
	// testFirstPlayerWinRate(ais,10);
	return 0;
}