import pygame
from constants import *

class Checker:
    def __init__(self, row, col, player, game):
        self.row = row
        self.col = col
        self.x = col * cell_size + board_offset + cell_size // 2 - game.white_checker_img.get_width() // 2
        self.y = row * cell_size + board_offset_y + cell_size // 2 - game.white_checker_img.get_height() // 2
        self.selected = False
        self.player = player
        self.game = game

        self.animating = False
        self.animation_path = []
        self.current_path_index = 0
        self.animation_progress = 0
        self.start_x = self.x
        self.start_y = self.y
        self.target_x = self.x
        self.target_y = self.y

    def get_path(self, start_row, start_col, end_row, end_col):
        path = [(start_row, start_col)]
        visited = set()
        found_path = []

        def find_jump_path(x, y, target_x, target_y, current_path):
            nonlocal found_path

            if found_path:
                return

            if (x, y) == (target_x, target_y):
                found_path = current_path.copy()
                return

            visited.add((x, y))

            for dx, dy in [(0, -2), (-2, 0), (0, 2), (2, 0)]:
                new_x = x + dx
                new_y = y + dy

                if (0 <= new_x < board_size and 0 <= new_y < board_size and
                        (new_x, new_y) not in visited):

                    middle_x = x + dx // 2
                    middle_y = y + dy // 2

                    if (self.game.board.board[middle_x][middle_y] is not None and
                            self.game.board.board[new_x][new_y] is None):

                        current_path.append((new_x, new_y))
                        find_jump_path(new_x, new_y, target_x, target_y, current_path)
                        if not found_path:
                            current_path.pop()

            visited.remove((x, y))

        if abs(start_row - end_row) + abs(start_col - end_col) == 1:
            path.append((end_row, end_col))
            return path

        find_jump_path(start_row, start_col, end_row, end_col, path)
        return found_path if found_path else path

    def can_jump(self, start_row, start_col, end_row, end_col):
        if self.game.board.board[end_row][end_col] is not None:
            return False

        if not (start_row == end_row or start_col == end_col):
            return False

        if start_row == end_row:
            mid_col = (start_col + end_col) // 2
            return (abs(start_col - end_col) == 2 and
                    self.game.board.board[start_row][mid_col] is not None)
        else:
            mid_row = (start_row + end_row) // 2
            return (abs(start_row - end_row) == 2 and
                    self.game.board.board[mid_row][start_col] is not None)

    def get_possible_jumps(self, row, col, visited=None):
        if visited is None:
            visited = set()

        possible_moves = set()

        def test_jump(x, y, target_x, target_y, visited_positions):
            if (x, y) not in visited_positions:
                visited_positions.add((x, y))

            if (x, y) != (row, col):
                possible_moves.add((x, y))

            for dx, dy in [(0, -2), (-2, 0), (0, 2), (2, 0)]:
                new_x = x + dx
                new_y = y + dy

                if 0 <= new_x < board_size and 0 <= new_y < board_size:
                    middle_x = x + dx // 2
                    middle_y = y + dy // 2

                    if (self.game.board.board[middle_x][middle_y] is not None and
                            self.game.board.board[new_x][new_y] is None and
                            (new_x, new_y) not in visited_positions):
                        test_jump(new_x, new_y, target_x, target_y, visited_positions)

        test_jump(row, col, None, None, visited)

        return possible_moves

    def get_possible_moves(self, row, col):
        moves = set()

        for d_row, d_col in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            new_row = row + d_row
            new_col = col + d_col

            if (0 <= new_row < board_size and
                    0 <= new_col < board_size and
                    self.game.board.board[new_row][new_col] is None):
                moves.add((new_row, new_col))

        jumps = self.get_possible_jumps(row, col)
        moves.update(jumps)

        return moves

    def start_animation(self, path):
        self.animating = True
        self.animation_path = path
        self.current_path_index = 0
        self.animation_progress = 0
        self.start_x = self.x
        self.start_y = self.y
        if path:
            next_row, next_col = path[0]
            self.target_x = next_col * cell_size + board_offset + cell_size // 2 - self.game.white_checker_img.get_width() // 2
            self.target_y = next_row * cell_size + board_offset_y + cell_size // 2 - self.game.white_checker_img.get_height() // 2

    def update_animation(self):
        if self.animating:
            self.animation_progress += 0.1
            if self.animation_progress >= 1:
                self.x = self.target_x
                self.y = self.target_y
                self.current_path_index += 1

                if self.current_path_index < len(self.animation_path):
                    self.animation_progress = 0
                    self.start_x = self.x
                    self.start_y = self.y
                    next_row, next_col = self.animation_path[self.current_path_index]
                    self.target_x = next_col * cell_size + board_offset + cell_size // 2 - self.game.white_checker_img.get_width() // 2
                    self.target_y = next_row * cell_size + board_offset_y + cell_size // 2 - self.game.white_checker_img.get_height() // 2
                else:
                    self.animating = False
                    self.game.animating = False
                    if self.animation_path:
                        final_row, final_col = self.animation_path[-1]
                        self.row = final_row
                        self.col = final_col
            else:
                t = self.animation_progress
                t = t * t * (3 - 2 * t)
                self.x = self.start_x + (self.target_x - self.start_x) * t
                self.y = self.start_y + (self.target_y - self.start_y) * t

    def draw(self):
        self.update_animation()
        if self.player == 1:
            self.game.screen.blit(self.game.white_checker_img, (self.x, self.y))
        else:
            self.game.screen.blit(self.game.black_checker_img, (self.x, self.y))
        if self.selected:
            pygame.draw.rect(self.game.screen, (74, 75, 77),
                             (self.col * cell_size + board_offset,
                              self.row * cell_size + board_offset_y,
                              cell_size, cell_size), 2)

    def move(self, row, col):
        self.row = row
        self.col = col
        self.x = col * cell_size + board_offset + cell_size // 2 - self.game.white_checker_img.get_width() // 2
        self.y = row * cell_size + board_offset_y + cell_size // 2 - self.game.white_checker_img.get_height() // 2

