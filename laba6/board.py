from constants import *
from checker import Checker
from minimax_agent import MinimaxAgent
import pygame

class Board:
    def __init__(self, game):
        #доска
        self.game = game
        self.reset_board()
        self.weight_pole = [
            [7, 6, 5, 4, 3, 2, 1, 0],
            [8, 7, 6, 5, 4, 3, 2, 1],
            [9, 8, 7, 6, 5, 4, 3, 2],
            [10, 9, 8, 7, 6, 5, 4, 3],
            [11, 10, 9, 8, 7, 6, 5, 4],
            [14, 14, 14, 9, 8, 7, 6, 5],
            [14, 14, 14, 10, 9, 8, 7, 6],
            [14, 14, 14, 11, 10, 9, 8, 7]
        ]
        self.minimax_agent = MinimaxAgent(player=-1, depth=MINIMAX_DEPTH)

    def reset_board(self):
        self.board = [[None for _ in range(board_size)] for _ in range(board_size)]
        self.init_board()
        self.last_move = None

    def init_board(self):
        initial_position = [
            [0, 0, 0, 0, 0, -1, -1, -1],
            [0, 0, 0, 0, 0, -1, -1, -1],
            [0, 0, 0, 0, 0, -1, -1, -1],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 0, 0, 0, 0, 0],
            [1, 1, 1, 0, 0, 0, 0, 0],
            [1, 1, 1, 0, 0, 0, 0, 0]
        ]

        for row in range(board_size):
            for col in range(board_size):
                if initial_position[row][col] != 0:
                    self.board[row][col] = Checker(row, col, initial_position[row][col], self.game)

    def check_winner(self):
        white_win = True
        for row in range(3):
            for col in range(5, 8):
                if not self.board[row][col] or self.board[row][col].player != 1:
                    white_win = False
                    break
            if not white_win:
                break

        black_win = True
        for row in range(5, 8):
            for col in range(3):
                if not self.board[row][col] or self.board[row][col].player != -1:
                    black_win = False
                    break
            if not black_win:
                break

        if white_win:
            return 1
        elif black_win:
            return -1
        return 0

    def draw(self, possible_moves):
        self.game.screen.fill(white)
        desk_rect = self.game.desk_img.get_rect()
        desk_rect.left = board_offset - 27
        desk_rect.top = board_offset_y - 27
        self.game.screen.blit(self.game.desk_img, desk_rect)

        for row in range(board_size):
            for col in range(board_size):
                pygame.draw.rect(self.game.screen, (197, 201, 209),
                                 (col * cell_size + board_offset,
                                  row * cell_size + board_offset_y,
                                  cell_size, cell_size), 2)
                if (row, col) in possible_moves:
                    pygame.draw.rect(self.game.screen, (6, 21, 51),
                                     (col * cell_size + board_offset,
                                      row * cell_size + board_offset_y,
                                      cell_size, cell_size), 2)

        for row in range(board_size):
            for col in range(board_size):
                if self.board[row][col]:
                    self.board[row][col].draw()

    def apply_move(self, start_row, start_col, end_row, end_col):
        checker = self.board[start_row][start_col]
        if checker is None:
            return False
        path = checker.get_path(start_row, start_col, end_row, end_col)
        if not path:
            return False
        checker.start_animation(path)
        self.game.animating = True
        self.board[start_row][start_col] = None
        self.board[end_row][end_col] = checker
        checker.move(end_row, end_col)
        self.last_move = ((start_row, start_col), (end_row, end_col))
        return True

    def make_sarsa_move(self, sarsa_agent, rng):
        if self.game.animating:
            return False
        move = sarsa_agent.select_move_for_board(self.board, rng)
        if move is None:
            return False
        sr, sc, er, ec = move
        return self.apply_move(sr, sc, er, ec)

    def make_computer_move(self):
        if self.game.animating:
            return False
        move = self.minimax_agent.choose_move_from_board(self.board)
        if move is None:
            return False
        sr, sc, er, ec = move
        return self.apply_move(sr, sc, er, ec)

