#агент sarsa
#sarsa_update
import json
import os
import random  #epsilon-жадная политика, случайные ходы при обучении
from halma_logic import apply_move, check_winner, encode_state, evaluate_position, get_all_moves, grid_from_checkers, new_game_grid


class SarsaAgent: #класс RL-агента табличная Q(s,a)
    def __init__(self, player=-1, alpha=0.3, gamma=0.95, epsilon=0.15, lookahead_opponent=None):
        #alpha скорость обучения; gamma дисконт; epsilon исследование
        # lookahead_opponent — опционально MinimaxAgent для просмотра ответа белых в игре
        self.player = player
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.q = {}  #Q-таблица - {str(state): {str(action): value}}
        self.lookahead_opponent = lookahead_opponent

    def get_q(self, state, action): #чтение Q(s,a)
        state_key = str(state) #ключ состояния
        action_key = str(action) #ключ действия
        if state_key not in self.q:
            return 0.0
        return self.q[state_key].get(action_key, 0.0)

    def set_q(self, state, action, value): #запись Q(s,a)
        state_key = str(state)
        action_key = str(action)
        if state_key not in self.q:
            self.q[state_key] = {}  #создаем словарь действий для состояния
        self.q[state_key][action_key] = value #меняем состояние

    def Eval_delta(self, grid, move): #насколько ход лучше
        before = evaluate_position(grid)
        after = evaluate_position(apply_move(grid, move))
        return after - before

    def choose_action(self, grid, rng, explore=None): #выбор хода
        moves = get_all_moves(grid, self.player)
        if not moves:
            return None

        state = encode_state(grid, self.player) # s для Q-таблицы
        if explore is None:
            use_epsilon = self.epsilon > 0  #при обучении — смотреть epsilon
        else:
            use_epsilon = explore  #в игре False
        if use_epsilon and rng.random() < self.epsilon:
            return rng.choice(moves) #исследование - случайный ход

        best = moves[0]  #жадный выборперебор всех ходов
        best_val = self.Score_move(grid, state, best)
        for move in moves[1:]:
            val = self.Score_move(grid, state, move)
            if val > best_val:
                best_val = val
                best = move
        return best  #ход с максимальной оценкой

    def Score_move(self, grid, state, move): #итоговая оценка хода при игре
        score = self.get_q(state, move) + 2.0 * self.Eval_delta(grid, move)
        if self.lookahead_opponent is None:
            return score
        #сарса ход, ответ минимакса, оценка позиции
        g1 = apply_move(grid, move)
        opp = self.lookahead_opponent.choose_move(g1)
        if opp is not None:
            g1 = apply_move(g1, opp)
        return score + evaluate_position(g1) * 0.3

    def sarsa_update(self, state, action, reward, next_state, next_action): #!!обновление Q(s,a)
        q_sa = self.get_q(state, action)  # текущее Q(s,a)
        if next_state is None or next_action is None:
            target = reward  #Q=0
        else:
            target = reward + self.gamma * self.get_q(next_state, next_action) #r + γ Q(s',a')
        self.set_q(state, action, q_sa + self.alpha * (target - q_sa)) #Q += α(target - Q)

    def train_episode(self, minimax_opponent, rng, max_plies=200): #1 обучающая партия
        grid = new_game_grid()
        state = encode_state(grid, self.player)  #начальное s
        action = self.choose_action(grid, rng, explore=True)  #первое a (с epsilon)
        if action is None:
            return 0

        for _ in range(max_plies):  #цикл шагов
            eval_before = evaluate_position(grid)
            grid = apply_move(grid, action)  #чёрныt
            reward = evaluate_position(grid) - eval_before  #награда за ход

            winner = check_winner(grid)
            if winner == self.player:
                reward += 200.0
                self.sarsa_update(state, action, reward, None, None) #конец — без s',a'
                return winner
            if winner == -self.player:
                reward -= 200.0
                self.sarsa_update(state, action, reward, None, None)
                return winner

            opp = minimax_opponent.choose_move(grid)  #белыe
            if opp is None:
                self.sarsa_update(state, action, reward, None, None)
                return check_winner(grid)

            eval_before = evaluate_position(grid)
            grid = apply_move(grid, opp)  #применяем ход белых
            reward += evaluate_position(grid) - eval_before  #- ход соперника

            winner = check_winner(grid)
            if winner != 0:
                if winner == self.player:
                    reward += 200.0
                else:
                    reward -= 200.0
                self.sarsa_update(state, action, reward, None, None)
                return winner

            next_state = encode_state(grid, self.player) #s' после хода обоих
            next_action = self.choose_action(grid, rng, explore=True) #a' — следующий ход сарса
            self.sarsa_update(state, action, reward, next_state, next_action) #обновление сарса

            if next_action is None:
                return check_winner(grid)
            state = next_state
            action = next_action

        return 0  #ничья

    def select_move_for_board(self, board, rng): #ход в pygame
        return self.choose_action(grid_from_checkers(board), rng, explore=False)

    def save(self, path):
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as file:
            json.dump({
                'player': self.player,
                'alpha': self.alpha,
                'gamma': self.gamma,
                'epsilon': self.epsilon,
                'q': self.q,
            }, file)

    def load(self, path): #загрузить модель
        if not os.path.exists(path):
            return False
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        self.player = data.get('player', -1)
        self.alpha = data.get('alpha', self.alpha)
        self.gamma = data.get('gamma', self.gamma)
        self.epsilon = data.get('epsilon', self.epsilon)
        self.q = data.get('q', {})
        return True

    def merge_q_table(self, other_q): #дообновить второй Q-таблицей
        added = 0
        for state_key, actions in other_q.items():
            if state_key not in self.q:
                self.q[state_key] = dict(actions)
                added += len(actions)
                continue
            for action_key, value in actions.items():
                if action_key not in self.q[state_key]:
                    added += 1
                self.q[state_key][action_key] = value
        return added #число новых пар

    def learn_from_played_game(self, moves, winner, alpha=None): #дообучение после партии с человеком
        if not moves:
            return {'updates': 0, 'new_states': 0, 'new_pairs': 0}

        old_alpha = self.alpha
        if alpha is not None:
            self.alpha = alpha  #маленький шаг

        states_before = set(self.q.keys())
        pairs_before = 0
        for actions in self.q.values():
            pairs_before += len(actions)

        grid = new_game_grid()
        updates = 0
        i = 0

        while i < len(moves):
            if moves[i][0] != 'black':
                i += 1
                continue

            state = encode_state(grid, self.player)
            action = moves[i][1]
            eval_before = evaluate_position(grid)
            grid = apply_move(grid, action)
            reward = evaluate_position(grid) - eval_before

            w = check_winner(grid)
            if w != 0:
                if w == self.player:
                    reward += 200.0
                else:
                    reward -= 200.0
                self.sarsa_update(state, action, reward, None, None)
                updates += 1
                break

            if i + 1 < len(moves) and moves[i + 1][0] == 'white':
                eval_before = evaluate_position(grid)
                grid = apply_move(grid, moves[i + 1][1])
                reward += evaluate_position(grid) - eval_before
                w = check_winner(grid)
                if w != 0:
                    if w == self.player:
                        reward += 200.0
                    else:
                        reward -= 200.0
                    self.sarsa_update(state, action, reward, None, None)
                    updates += 1
                    break

                next_state = encode_state(grid, self.player)
                next_action = None
                if i + 2 < len(moves) and moves[i + 2][0] == 'black':
                    next_action = moves[i + 2][1]
                self.sarsa_update(state, action, reward, next_state, next_action)
                updates += 1
                i += 2
            else:
                self.sarsa_update(state, action, reward, None, None)
                updates += 1
                i += 1
            continue

        self.alpha = old_alpha

        states_after = set(self.q.keys())
        pairs_after = 0
        for actions in self.q.values():
            pairs_after += len(actions)

        return {
            'updates': updates,
            'new_states': len(states_after - states_before),
            'new_pairs': pairs_after - pairs_before,
            'total_states': len(states_after),
            'total_pairs': pairs_after,
            'winner': winner,
        }

    def load_merge(self, path): #загрузить Q
        if not os.path.exists(path):
            return 0
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return self.merge_q_table(data.get('q', {}))
