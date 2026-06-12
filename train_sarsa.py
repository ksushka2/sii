#обучение сарса против минимакса
import os
import random #epsilon в train_episode
import time

from constants import SARSA_MODEL_PATH
from halma_logic import apply_move, check_winner, new_game_grid
from minimax_agent import MinimaxAgent
from sarsa_agent import SarsaAgent

def play_game(agent, opponent, rng, max_plies=200): #1 тестовая партия без обучения
    grid = new_game_grid()
    for _ in range(max_plies):
        move = agent.choose_action(grid, rng, explore=False)  #сарса без случайности
        if move is None:
            return 0
        grid = apply_move(grid, move)
        w = check_winner(grid)
        if w != 0:
            return w
        opp = opponent.choose_move(grid)
        if opp is None:
            return check_winner(grid)
        grid = apply_move(grid, opp)
        w = check_winner(grid)
        if w != 0:
            return w
    return 0  #ничья

def evaluate(agent, opponent, games, rng): #серия тестовых партий
    wins = 0
    losses = 0
    draws = 0
    old_eps = agent.epsilon #запомнить epsilon
    agent.epsilon = 0.0 #на тесте — только жадные ходы
    for _ in range(games):
        w = play_game(agent, opponent, rng)
        if w == agent.player:
            wins += 1
        elif w == -agent.player:
            losses += 1
        else:
            draws += 1
    agent.epsilon = old_eps #вернуть epsilon
    n = max(games, 1)
    return {
        'wins': wins,
        'losses': losses,
        'draws': draws,
        'win_rate': 100.0 * wins / n,
    }


def train(episodes=1200, eval_every=400, eval_games=5, train_depth=2, eval_depth=3, save_path=None): #главный цикл обучения
    if save_path is None:
        save_path = SARSA_MODEL_PATH
    if not os.path.isabs(save_path):
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), save_path)

    rng = random.Random(42)
    agent = SarsaAgent(player=-1, alpha=0.3, gamma=0.95, epsilon=0.2)  #чёрные сарса
    train_opp = MinimaxAgent(player=1, depth=train_depth)  #белые при обучении d=2
    eval_opp = MinimaxAgent(player=1, depth=eval_depth)  #белые при проверке d=3

    best_wins = -1 #лучший результат на тесте
    t0 = time.time()

    for ep in range(1, episodes + 1):
        agent.train_episode(train_opp, rng) #один эпизод сарса — вызывается sarsa_update

        if ep % 100 == 0:
            agent.epsilon = max(0.05, agent.epsilon * 0.99) #уменьшить исследование

        if ep % eval_every == 0 or ep == episodes:
            stats = evaluate(agent, eval_opp, eval_games, rng) #тест без обучения
            elapsed = time.time() - t0
            print(f'[{elapsed / 60:.1f} min] ep {ep}/{episodes} Q={len(agent.q)} win {stats["wins"]}/{eval_games} not win {stats["losses"]} (0) {stats["draws"]} win-rate {stats["win_rate"]:.0f}%')
            if stats['wins'] > best_wins:
                best_wins = stats['wins']
                agent.save(save_path) #сохранить лучшую модель

    agent.epsilon = 0.0
    agent.save(save_path) #финальное сохранение
    print('end. Model:', save_path)


if __name__ == '__main__':
    train()