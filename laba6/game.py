import os
import random
import sys

import pygame

from board import Board
from constants import *
from login_screen import LoginScreen
from sarsa_agent import SarsaAgent
from minimax_agent import MinimaxAgent

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((window_size_w, window_size_h))
        pygame.display.set_caption("Халма")

        icon = pygame.image.load(Icon)
        pygame.display.set_icon(icon)

        pygame.mixer.music.load(Music)
        pygame.mixer.music.set_volume(0.01)
        pygame.mixer.music.play(-1)
        self.clock = pygame.time.Clock()

        self.rng = random.Random()
        self.sarsa_model_loaded = False
        white_minimax = MinimaxAgent(player=1, depth=3)
        self.sarsa_agent = SarsaAgent(player=-1,epsilon=SARSA_EPSILON_PLAY,lookahead_opponent=white_minimax)
        if USE_SARSA_BOT:
            print("Playing Sarsa")
            path = SARSA_MODEL_PATH
            if not os.path.isabs(path):
                path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
            self.sarsa_model_loaded = self.sarsa_agent.load(path)
            if not self.sarsa_model_loaded:
                print(f"SARSA: model is None ({path}).")
            elif SARSA_PEOPLE_LEARN and SARSA_PEOPLE_SEPARATE_FILE:
                online_path = SARSA_PEOPLE_MODEL_PATH
                if not os.path.isabs(online_path):
                    online_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), online_path)
                added = self.sarsa_agent.load_merge(online_path)
                if added:
                    print(f"SARSA:{online_path} (+{added} par Q)")
        else:
            print("Playing Minimax")

        self.desk_img = pygame.image.load(Desc)
        self.white_checker_img = pygame.image.load(White_check)
        self.black_checker_img = pygame.image.load(Black_check)

        self.font = pygame.font.Font(None, 36)
        self.board = Board(self)
        self.selected_checker = None
        self.possible_moves = set()
        self.current_player = 1
        self.error_message = ""
        self.error_timer = 0
        self.is_computer_player = True
        self.animating = False
        self.animation_progress = 0
        self.show_exit_confirmation = False
        self.show_winner_popup = False
        self.winner = 0
        self.login_screen = LoginScreen(self.screen)
        self.logged_in = False

        self.RULES_TEXT = """
                                                  Правила игры Халма:


   У каждого игрока по 9 шашек: белые внизу слева, черные вверху справа.

   Игроки ходят по очереди. Возможные ходы:
   - На одну клетку вправо, влево, вниз, вверх.
   - Прыгать через шашки на пустую клетку.

   За ход можно сделать несколько прыжков, как через свои, так и через
   шашки противника.

   Побеждает тот, кто первый переместит свои шашки в угол противника.

   Совет: используйте шашки как мостики для прыжков!

"""

        self.moves_history = []
        self.moves_font = pygame.font.SysFont('Arial', 22)
        self.col_to_letter = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H'}
        self.row_to_number = {0: '8', 1: '7', 2: '6', 3: '5', 4: '4', 5: '3', 6: '2', 7: '1'}

        self.moves_scroll_y = 0
        self.sarsa_played_moves: list[tuple[str, tuple[int, int, int, int]]] = []
        self.sarsa_online_applied = False
        self.max_visible_moves = 15
        self.scroll_speed = 25
        self.moves_area_height = 550

    def add_move_to_history(self, start_pos, end_pos, player):
        start_notation = f"{self.col_to_letter[start_pos[1]]}{self.row_to_number[start_pos[0]]}"
        end_notation = f"{self.col_to_letter[end_pos[1]]}{self.row_to_number[end_pos[0]]}"
        move_text = f"{start_notation} → {end_notation}"
        self.moves_history.append((move_text, player))

    def handle_scroll(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            content_height = len(self.moves_history) * 35

            if content_height > self.moves_area_height:
                scroll_bar_rect = pygame.Rect(380, 60, 10, self.moves_area_height)

                if scroll_bar_rect.collidepoint(event.pos):
                    relative_y = event.pos[1] - 60
                    scroll_ratio = relative_y / self.moves_area_height
                    self.moves_scroll_y = min(content_height - self.moves_area_height,
                                              max(0, int(content_height * scroll_ratio)))
                else:
                    if event.button == 4:
                        self.moves_scroll_y = max(0, self.moves_scroll_y - self.scroll_speed)
                    elif event.button == 5:
                        max_scroll = content_height - self.moves_area_height
                        self.moves_scroll_y = min(max_scroll, self.moves_scroll_y + self.scroll_speed)

    def draw_moves_history(self):
        white_header = self.font.render("Ходы белых", True, black)
        black_header = self.font.render("Ходы черных", True, black)
        self.screen.blit(white_header, (20, 20))
        self.screen.blit(black_header, (200, 20))

        total_height = max(self.moves_area_height, len(self.moves_history) * 35)
        moves_surface = pygame.Surface((350, total_height))
        moves_surface.fill(white)

        white_y = 0
        black_y = 0

        for move_text, player in self.moves_history:
            text = self.moves_font.render(move_text, True, black)
            if player == 1:
                moves_surface.blit(text, (0, white_y))
                white_y += 35
            else:
                moves_surface.blit(text, (180, black_y))
                black_y += 35

        content_height = max(white_y, black_y)

        if content_height > self.moves_area_height:
            self.moves_scroll_y = min(content_height - self.moves_area_height,
                                      max(0, self.moves_scroll_y))

        visible_rect = pygame.Rect(0, self.moves_scroll_y, 350, self.moves_area_height)
        self.screen.blit(moves_surface, (20, 60), visible_rect)

        if content_height > self.moves_area_height:
            scroll_height = max(30, self.moves_area_height * self.moves_area_height / content_height)
            scroll_pos = (self.moves_scroll_y * (self.moves_area_height - scroll_height) /
                          (content_height - self.moves_area_height))

            pygame.draw.rect(self.screen, (200, 200, 200),
                             (380, 60, 10, self.moves_area_height))

            pygame.draw.rect(self.screen, (150, 150, 150),
                             (380, 60 + scroll_pos, 10, scroll_height))

    def show_winner_dialog(self):
        overlay = pygame.Surface((window_size_w, window_size_h))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))

        dialog_width = 400
        dialog_height = 200
        dialog_x = (window_size_w - dialog_width) // 2
        dialog_y = (window_size_h - dialog_height) // 2

        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, white, dialog_rect)
        pygame.draw.rect(self.screen, black, dialog_rect, 2)

        winner_text = "Победили белые!" if self.winner == 1 else "Победили черные!"
        text = self.font.render(winner_text, True, black)
        text_rect = text.get_rect(center=(window_size_w // 2, dialog_y + 60))
        self.screen.blit(text, text_rect)

        ok_button = pygame.Rect(dialog_x + (dialog_width - 100) // 2, dialog_y + dialog_height - 60, 100, 40)
        pygame.draw.rect(self.screen, gray, ok_button)
        ok_text = self.font.render("OK", True, black)
        ok_rect = ok_text.get_rect(center=ok_button.center)
        self.screen.blit(ok_text, ok_rect)

        return ok_button

    def wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0

        for word in words:
            word_surface = font.render(word + ' ', True, black)
            word_width = word_surface.get_width()

            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width

        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def show_rules(self):
        rules_running = True
        padding = 50
        line_spacing = 40
        max_width = window_size_w - (padding * 2)

        while rules_running:
            self.screen.fill(white)

            y = padding
            for line in self.RULES_TEXT.split('\n'):
                if line.strip():
                    if line.strip()[0].isdigit():
                        text_surface = self.font.render(line, True, black)
                        self.screen.blit(text_surface, (padding, y))
                        y += line_spacing
                    else:
                        wrapped_lines = self.wrap_text(line, self.font, max_width)
                        for wrapped_line in wrapped_lines:
                            text_surface = self.font.render(wrapped_line, True, black)
                            self.screen.blit(text_surface, (padding, y))
                            y += line_spacing

            back_button = pygame.Rect(window_size_w // 2 - 50, window_size_h - 100, 100, 40)
            pygame.draw.rect(self.screen, gray, back_button)
            back_text = self.font.render("Назад", True, black)
            back_text_rect = back_text.get_rect(center=back_button.center)
            self.screen.blit(back_text, back_text_rect)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_button.collidepoint(event.pos):
                        rules_running = False

    def show_menu(self):
        menu_running = True
        while menu_running:
            self.screen.fill(white)

            start_button = pygame.Rect(window_size_w // 2 - 100, window_size_h // 2 - 50, 200, 40)
            rules_button = pygame.Rect(window_size_w // 2 - 100, window_size_h // 2 + 10, 200, 40)

            pygame.draw.rect(self.screen, gray, start_button)
            pygame.draw.rect(self.screen, gray, rules_button)

            start_text = self.font.render("Начать игру", True, black)
            rules_text = self.font.render("Правила игры", True, black)

            start_text_rect = start_text.get_rect(center=start_button.center)
            rules_text_rect = rules_text.get_rect(center=rules_button.center)

            self.screen.blit(start_text, start_text_rect)
            self.screen.blit(rules_text, rules_text_rect)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.mixer.music.stop()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if start_button.collidepoint(event.pos):
                        menu_running = False
                        while not self.logged_in:
                            self.screen.fill(white)
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    pygame.mixer.music.stop()
                                    pygame.quit()
                                    sys.exit()
                                self.login_screen.handle_event(event)
                                if event.type == pygame.MOUSEBUTTONDOWN and self.login_screen.login_btn.collidepoint(
                                        event.pos):
                                    if self.login_screen.login():
                                        self.logged_in = True

                            self.login_screen.draw()
                            pygame.display.flip()

                        return self.show_opponent_selection()
                    if rules_button.collidepoint(event.pos):
                        self.show_rules()

    def reset_game_state(self):
        self.board.reset_board()
        self.selected_checker = None
        self.possible_moves = set()
        self.current_player = 1
        self.error_message = ""
        self.error_timer = 0
        self.animating = False
        self.animation_progress = 0
        self.show_winner_popup = False
        self.winner = 0
        self.moves_history = []
        self.moves_scroll_y = 0
        self.sarsa_played_moves = []
        self.sarsa_online_applied = False

    def show_opponent_selection(self):
        self.is_computer_player = True
        self.reset_game_state()
        return True

    def show_exit_dialog(self):
        overlay = pygame.Surface((window_size_w, window_size_h))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))

        dialog_width = 300
        dialog_height = 150
        dialog_x = (window_size_w - dialog_width) // 2
        dialog_y = (window_size_h - dialog_height) // 2

        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, white, dialog_rect)
        pygame.draw.rect(self.screen, black, dialog_rect, 2)

        text = self.font.render("Хотите закрыть игру?", True, black)
        text_rect = text.get_rect(center=(window_size_w // 2, dialog_y + 60))
        self.screen.blit(text, text_rect)

        yes_button = pygame.Rect(dialog_x + 50, dialog_y + 100, 80, 30)
        no_button = pygame.Rect(dialog_x + 170, dialog_y + 100, 80, 30)

        pygame.draw.rect(self.screen, gray, yes_button)
        pygame.draw.rect(self.screen, gray, no_button)

        yes_text = self.font.render("Да", True, black)
        no_text = self.font.render("Нет", True, black)

        yes_rect = yes_text.get_rect(center=yes_button.center)
        no_rect = no_text.get_rect(center=no_button.center)

        self.screen.blit(yes_text, yes_rect)
        self.screen.blit(no_text, no_rect)

        return yes_button, no_button

    def main_game(self):
        exit_button = pygame.Rect(20, window_size_h - 40, 40, 30)

        while True:
            self.clock.tick(fps)

            winner = self.board.check_winner()
            if winner != 0:
                self.winner = winner
                self.show_winner_popup = True

            if self.show_winner_popup:
                ok_button = self.show_winner_dialog()
                pygame.display.flip()

                waiting_for_ok = True
                while waiting_for_ok:
                    for event in pygame.event.get():
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            if ok_button.collidepoint(event.pos):
                                self.finish_sarsa_online_learning()
                                self.reset_game_state()
                                self.show_exit_confirmation = False
                                return
                        elif event.type == pygame.QUIT:
                            pygame.mixer.music.stop()
                            pygame.quit()
                            sys.exit()

            if self.current_player == -1 and self.is_computer_player and not self.animating:
                moved = False
                if USE_SARSA_BOT and self.sarsa_model_loaded:
                    moved = self.board.make_sarsa_move(self.sarsa_agent, self.rng)
                else:
                    moved = self.board.make_computer_move()
                if moved:
                    self.current_player = 1
                    last_move = self.board.last_move
                    if last_move:
                        self.add_move_to_history(last_move[0], last_move[1], -1)
                        sr, sc = last_move[0]
                        er, ec = last_move[1]
                        self.sarsa_played_moves.append(("black", (sr, sc, er, ec)))
                    self.error_message = ""

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.mixer.music.stop()
                    pygame.quit()
                    sys.exit()

                self.handle_scroll(event)

                if event.type == pygame.MOUSEBUTTONDOWN and not self.animating:
                    mouse_pos = event.pos

                    if exit_button.collidepoint(mouse_pos):
                        self.show_exit_confirmation = True
                    elif self.show_exit_confirmation:
                        yes_button, no_button = self.show_exit_dialog()
                        if yes_button.collidepoint(mouse_pos):
                            self.reset_game_state()
                            self.show_exit_confirmation = False
                            return
                        elif no_button.collidepoint(mouse_pos):
                            self.show_exit_confirmation = False
                    else:
                        if self.current_player == 1 or not self.is_computer_player:
                            col = (mouse_pos[0] - board_offset) // cell_size
                            row = (mouse_pos[1] - board_offset_y) // cell_size

                            if 0 <= row < board_size and 0 <= col < board_size:
                                self.handle_click(row, col)

            self.screen.fill(white)
            self.board.draw(self.possible_moves)
            self.draw_moves_history()
            self.draw_interface(exit_button)
            if self.show_exit_confirmation:
                self.show_exit_dialog()
            pygame.display.flip()

    def handle_click(self, row, col):
        if self.selected_checker:
            can_move = False

            if (self.board.board[row][col] is None and
                    ((abs(self.selected_checker.row - row) == 1 and self.selected_checker.col == col) or
                     (abs(self.selected_checker.col - col) == 1 and self.selected_checker.row == row))):
                can_move = True
            elif (row, col) in self.possible_moves:
                can_move = True

            if can_move:
                start_pos = (self.selected_checker.row, self.selected_checker.col)

                path = self.selected_checker.get_path(self.selected_checker.row, self.selected_checker.col, row, col)
                self.selected_checker.start_animation(path)
                self.animating = True

                self.board.board[self.selected_checker.row][self.selected_checker.col] = None
                self.board.board[row][col] = self.selected_checker

                self.add_move_to_history(start_pos, (row, col), self.current_player)

                if (
                    SARSA_PEOPLE_LEARN
                    and USE_SARSA_BOT
                    and self.sarsa_model_loaded
                    and self.current_player == 1
                ):
                    self.sarsa_played_moves.append(
                        ("white", (start_pos[0], start_pos[1], row, col))
                    )

                self.current_player = -self.current_player
                self.error_message = ""
            else:
                self.error_message = "Такой ход сейчас не доступен!"
                self.error_timer = 300

            self.selected_checker.selected = False
            self.selected_checker = None
            self.possible_moves = set()
        elif self.board.board[row][col] and self.board.board[row][col].player == self.current_player:
            self.selected_checker = self.board.board[row][col]
            self.selected_checker.selected = True
            self.possible_moves = self.selected_checker.get_possible_moves(row, col)

    def finish_sarsa_online_learning(self) -> None:
        if (
            not SARSA_PEOPLE_LEARN
            or not USE_SARSA_BOT
            or not self.sarsa_model_loaded
            or self.sarsa_online_applied
            or not self.sarsa_played_moves
        ):
            return

        self.sarsa_online_applied = True
        stats = self.sarsa_agent.learn_from_played_game(
            self.sarsa_played_moves,
            self.winner,
            alpha=SARSA_PEOPLE_ALPHA,
        )

        if SARSA_PEOPLE_SEPARATE_FILE:
            save_path = SARSA_PEOPLE_MODEL_PATH
        else:
            save_path = SARSA_MODEL_PATH
        if not os.path.isabs(save_path):
            save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), save_path)

        self.sarsa_agent.save(save_path)
        w = stats.get("winner", 0)
        if w == -1:
            who = "SARSA"
        elif w == 1:
            who = "belye"
        else:
            who = "nichya"
        print(f"all states={stats['total_states']}, winner={who}", flush=True)

    def draw_interface(self, exit_button):
        pygame.draw.rect(self.screen, gray, exit_button)
        exit_text = self.font.render("<=", True, black)
        exit_text_rect = exit_text.get_rect(center=exit_button.center)
        self.screen.blit(exit_text, exit_text_rect)

        player_text = f"Ходят: {'белые' if self.current_player == 1 else 'черные'}"
        text_surface = self.font.render(player_text, True, black)
        text_rect = text_surface.get_rect(center=(window_size_w - 320, window_size_h - 30))
        self.screen.blit(text_surface, text_rect)

        if self.error_message and self.error_timer > 0:
            error_surface = self.font.render(self.error_message, True, (77, 19, 19))
            error_rect = error_surface.get_rect(center=(window_size_w - 320, window_size_h - 60))
            self.screen.blit(error_surface, error_rect)
            self.error_timer -= 1
