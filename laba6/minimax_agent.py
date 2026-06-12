from constants import board_size
from halma_logic import WEIGHT_POLE, apply_move, check_winner, get_all_moves, grid_from_checkers


class MinimaxAgent:
    def __init__(self, player=1, depth=3):
        # player: 1 белые, -1 чёрные; depth: глубина дерева поиска
        self.player = player
        self.depth = depth
        self.opponent = -player

    def choose_move(self, grid):#лучший ход (sr,sc,er,ec)
        if self.player == -1:
            #чёрные максимизируют оценку
            score, move = self.minimaX(grid, self.depth, float('-inf'), float('inf'), True)
        else:
            #белые минимизируют оценку
            score, move = self.minimaX(grid, self.depth, float('-inf'), float('inf'), False)
        return move

    def choose_move_from_board(self, board): #ход
        return self.choose_move(grid_from_checkers(board))

    def evaluatE(self, grid): #оценка
        score = 0.0
        for row in range(board_size):
            for col in range(board_size):
                cell = grid[row][col]
                if cell == -1:
                    score += WEIGHT_POLE[row][col]
                elif cell == 1:
                    score -= WEIGHT_POLE[7 - row][7 - col]
        return score

    def minimaX(self, grid, depth, alpha, beta, maximizing_player): #рекурсивный minimax
        winner = check_winner(grid)  #проверка победителя
        if winner == -1:
            return float('inf'), None  #чёрные выиграли!
        if winner == 1:
            return float('-inf'), None  #белые выиграли(

        if maximizing_player:
            for move in get_all_moves(grid, -1):
                new_grid = apply_move(grid, move)
                if check_winner(new_grid) == -1:
                    return float('inf'), move

        if depth == 0:
            return self.evaluatE(grid), None

        if maximizing_player: #ищем максимум
            max_eval = float('-inf')
            best_move = None
            moves = get_all_moves(grid, -1)
            if not moves:
                return self.evaluatE(grid), None
            for move in moves:
                new_grid = apply_move(grid, move)  # сделать ход
                eval_score, _ = self.minimaX(new_grid, depth - 1, alpha, beta, False)  #ход белых
                if eval_score > max_eval or best_move is None:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)  #обновить alpha
                if beta <= alpha:
                    break  #отсечение ветки
            return max_eval, best_move

        #ищем минимум(
        min_eval = float('inf')
        best_move = None
        moves = get_all_moves(grid, 1)
        if not moves:
            return self.evaluatE(grid), None
        for move in moves:
            new_grid = apply_move(grid, move)
            eval_score, _ = self.minimaX(new_grid, depth - 1, alpha, beta, True)  #чёрные
            if eval_score < min_eval or best_move is None:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move #оценка, лучший ход на этом уровне
