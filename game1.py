#одна партия сарса против минимакс
import os
import random

from constants import SARSA_MODEL_PATH, board_size
from halma_logic import apply_move, check_winner, new_game_grid
from minimax_agent import MinimaxAgent
from sarsa_agent import SarsaAgent

def grid_to_lines(grid):
    lines = ['   ' + ' '.join(str(c) for c in range(board_size))]  # номера столбцов
    for row in range(board_size):
        cells = []
        for col in range(board_size):
            v = grid[row][col]
            if v == 1:
                cells.append('W')
            elif v == -1:
                cells.append('B')
            else:
                cells.append('.')
        lines.append(f'{row}  ' + ' '.join(cells))
    return lines


def print_final_board(grid, move_count, winner):
    # Печать итога: число ходов, победитель, финальная доска
    print()
    print('itog state: sarsa (B) \ minimax (W)')
    print('Count move B+W:', move_count)
    if winner == -1:
        print('Winner sarsa')
    elif winner == 1:
        print('Winner minimax')
    else:
        print('Winner is None')
    print('Final grid:')
    for line in grid_to_lines(grid):
        print(line)

def play_one_game(model_path=SARSA_MODEL_PATH, minimax_depth=3, lookahead_depth=2, max_plies=200):#выход winner (1, -1, 0)
    rng = random.Random(42)
    sarsa = SarsaAgent(player=-1,epsilon=0.0,  # детерминированная игра
    lookahead_opponent=MinimaxAgent(player=1, depth=lookahead_depth))
    if not os.path.isabs(model_path):
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), model_path)

    if not sarsa.load(model_path):
        print('Model is none:', model_path)
        return 0

    white = MinimaxAgent(player=1, depth=minimax_depth)

    grid = new_game_grid()
    move_count = 0  # счётчик полуходов

    while move_count < max_plies * 2:  # лимит в полуходах
        black_move = sarsa.choose_action(grid, rng, explore=False)
        if black_move is None:
            break
        grid = apply_move(grid, black_move)
        move_count += 1
        winner = check_winner(grid)
        if winner != 0:
            print_final_board(grid, move_count, winner)
            return winner

        white_move = white.choose_move(grid)
        if white_move is None:
            break
        grid = apply_move(grid, white_move)
        move_count += 1
        winner = check_winner(grid)
        if winner != 0:
            print_final_board(grid, move_count, winner)
            return winner

    winner = check_winner(grid)
    print_final_board(grid, move_count, winner)
    return winner


if __name__ == '__main__':
    play_one_game()
