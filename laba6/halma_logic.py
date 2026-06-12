#логика Халмы без pygame
from constants import board_size

#таблица весов клеток
WEIGHT_POLE = [
    [7, 6, 5, 4, 3, 2, 1, 0],
    [8, 7, 6, 5, 4, 3, 2, 1],
    [9, 8, 7, 6, 5, 4, 3, 2],
    [10, 9, 8, 7, 6, 5, 4, 3],
    [11, 10, 9, 8, 7, 6, 5, 4],
    [14, 14, 14, 9, 8, 7, 6, 5],
    [14, 14, 14, 10, 9, 8, 7, 6],
    [14, 14, 14, 11, 10, 9, 8, 7],
]

#Старт
INITIAL_GRID = [
    [0, 0, 0, 0, 0, -1, -1, -1],
    [0, 0, 0, 0, 0, -1, -1, -1],
    [0, 0, 0, 0, 0, -1, -1, -1],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 0, 0, 0],
]


def copy_grid(grid):
    #копия, чтобы ходы не портили исходник
    return [row[:] for row in grid]


def new_game_grid():
    #доска в начальной расстановке
    return copy_grid(INITIAL_GRID)


def check_winner(grid):
    white_win = True  #белые заняли свой угол
    for row in range(3):
        for col in range(5, 8):
            if grid[row][col] != 1:  #если нет белой фишки
                white_win = False
                break
        if not white_win:
            break
    if white_win:
        return 1

    black_win = True  #чёрные заняли свой угол
    for row in range(5, 8):
        for col in range(3):
            if grid[row][col] != -1:
                black_win = False
                break
        if not black_win:
            break
    if black_win:
        return -1
    return 0  #победителя нет


def evaluate_position(grid):
    #позиции с точки зрения чёрных
    score = 0.0
    for row in range(board_size):
        for col in range(board_size):
            cell = grid[row][col]  # -1, 0 или 1
            if cell == -1:
                score += WEIGHT_POLE[row][col]  #чем ближе к цели, тем больше плюс
            elif cell == 1:
                score -= WEIGHT_POLE[7 - row][7 - col]  #белые минусуют счет чёрным
    return score  #есои счет>0 - хорошо для чёрных


def get_jumpsl(grid, row, col, visited=None):
    #клетки, куда можно допрыгнуть цепочкой
    if visited is None:
        visited = set()  #посещённые клетки в цепочке прыжков
    possible = set()  #конечные клетки прыжков

    def test_jump(x, y, visited_positions):
        if (x, y) not in visited_positions:
            visited_positions.add((x, y))  #пометить клетку
        if (x, y) != (row, col):  #не стартовая
            possible.add((x, y))
        for dx, dy in ((0, -2), (-2, 0), (0, 2), (2, 0)):
            nx, ny = x + dx, y + dy  #клетка приземления
            if 0 <= nx < board_size and 0 <= ny < board_size:
                mx, my = x + dx // 2, y + dy // 2  #через которую прыгаем
                if grid[mx][my] != 0 and grid[nx][ny] == 0 and (nx, ny) not in visited_positions:
                    test_jump(nx, ny, visited_positions)  #продолжаем цепочку

    test_jump(row, col, visited.copy())  #запуск с шашки
    return possible  #множество конечных клеток


def get_possible_moves(grid, row, col):
    moves = set()
    for d_row, d_col in ((0, 1), (0, -1), (1, 0), (-1, 0)):  # 4 соседних клетки
        nr, nc = row + d_row, col + d_col
        if 0 <= nr < board_size and 0 <= nc < board_size and grid[nr][nc] == 0:
            moves.add((nr, nc))  # простой шаг на пустую
    moves.update(get_jumpsl(grid, row, col))  # добавить все прыжки
    return moves


def get_all_moves(grid, player):
    moves = []
    for row in range(board_size):
        for col in range(board_size):
            if grid[row][col] != player:  #не наша шашка
                continue
            for end_row, end_col in get_possible_moves(grid, row, col):
                if player == -1 and row >= 5 and col <= 2:
                    if end_row >= 5 and end_col <= 2:
                        moves.append((row, col, end_row, end_col))
                else:
                    moves.append((row, col, end_row, end_col))
    return moves #список (sr,sc,er,ec)


def apply_move(grid, move):
    #применение хода на доске
    sr, sc, er, ec = move
    new_grid = copy_grid(grid)
    new_grid[er][ec] = new_grid[sr][sc]  #ход
    new_grid[sr][sc] = 0
    return new_grid #обновленная доска


def encode_state(grid, player):#состояние s для Q-таблицы
    score = evaluate_position(grid)  #позиция
    my_goal = 0
    opp_goal = 0
    for row in range(board_size):
        for col in range(board_size):
            if grid[row][col] == player:
                if player == -1 and row >= 5 and col <= 2:
                    my_goal += 1
                elif player == 1 and row <= 2 and col >= 5:
                    my_goal += 1
            elif grid[row][col] == -player:
                if -player == -1 and row >= 5 and col <= 2:
                    opp_goal += 1
                elif -player == 1 and row <= 2 and col >= 5:
                    opp_goal += 1
    return (int(score // 4), my_goal, opp_goal)  # сжатый ключ состояния


def grid_from_checkers(board):
    #ход
    grid = [[0] * board_size for _ in range(board_size)]
    for row in range(board_size):
        for col in range(board_size):
            checker = board[row][col]
            if checker is not None:
                grid[row][col] = checker.player  # 1 или -1
    return grid #-1, 0, 1
