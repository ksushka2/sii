import pygame
from constants import *

class LoginScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font_header = pygame.font.SysFont('Arial', 30)
        self.font_entry = pygame.font.SysFont('Arial', 24)
        self.font_label = pygame.font.SysFont('Arial', 22)

        self.username = ""
        self.password = ""
        self.active_input = None
        self.show_register_popup = False
        self.is_registration = False
        self.game_started = False
        self.error_message = ""
        self.error_timer = 0

        self.username_rect = pygame.Rect(window_size_w // 2 - 100, 230, 200, 30)
        self.password_rect = pygame.Rect(window_size_w // 2 - 100, 330, 200, 30)
        self.login_btn = pygame.Rect(window_size_w // 2 - 50, 410, 100, 40)

        self.popup_rect = pygame.Rect(window_size_w // 2 - 200, window_size_h // 2 - 100, 400, 200)
        self.yes_btn = pygame.Rect(window_size_w // 2 - 100, window_size_h // 2 + 20, 80, 40)
        self.no_btn = pygame.Rect(window_size_w // 2 + 20, window_size_h // 2 + 20, 80, 40)

    def caesar_cipher(self, text, shift=6):
        result = ""
        for char in text:
            if 'А' <= char <= 'Я' or 'а' <= char <= 'я':
                ascii_offset = ord('а') if char.islower() else ord('А')
                shifted = (ord(char) - ascii_offset + shift) % 32 + ascii_offset
                result += chr(shifted)
            elif 'A' <= char <= 'Z' or 'a' <= char <= 'z':
                ascii_offset = ord('a') if char.islower() else ord('A')
                shifted = (ord(char) - ascii_offset + shift) % 26 + ascii_offset
                result += chr(shifted)
            else:
                result += char
        return result

    def caesar_decipher(self, text, shift=6):
        return self.caesar_cipher(text, -shift)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not self.show_register_popup:
                if self.username_rect.collidepoint(event.pos):
                    self.active_input = "username"
                elif self.password_rect.collidepoint(event.pos):
                    self.active_input = "password"
                elif self.login_btn.collidepoint(event.pos):
                    if self.is_registration:
                        self.register_user()
                    else:
                        self.login()
                else:
                    self.active_input = None
            elif self.show_register_popup:
                if self.yes_btn.collidepoint(event.pos):
                    self.is_registration = True
                elif self.no_btn.collidepoint(event.pos):
                    self.show_register_popup = False
                    self.username = ""
                    self.password = ""

        elif event.type == pygame.KEYDOWN and self.active_input and not self.show_register_popup:
            if event.key == pygame.K_BACKSPACE:
                if self.active_input == "username":
                    self.username = self.username[:-1]
                else:
                    self.password = self.password[:-1]
            elif event.key == pygame.K_RETURN:
                if self.is_registration:
                    self.register_user()
                else:
                    self.login()
            else:
                if self.active_input == "username":
                    self.username += event.unicode
                else:
                    self.password += event.unicode

    def login(self):
        if len(self.password) < 3:
            self.error_message = "Пароль должен содержать минимум 3 символа"
            self.error_timer = 1500
            return False

        try:
            with open('users.txt', 'r', encoding='utf-8') as file:
                for line in file:
                    encrypted_line = line.strip()
                    decrypted_line = self.caesar_decipher(encrypted_line)
                    stored_username, stored_password = decrypted_line.split(':')
                    if stored_username.strip() == self.username and stored_password.strip() == self.password:
                        self.game_started = True
                        return True
            self.show_register_popup = True
            return False
        except FileNotFoundError:
            with open('users.txt', 'w', encoding='utf-8') as file:
                pass
            self.show_register_popup = True
            return False

    def register_user(self):
        if len(self.password) < 3:
            self.error_message = "Пароль должен содержать минимум 3 символа"
            self.error_timer = 1500
            return False

        if self.username and self.password:
            user_data = f"{self.username}:{self.password}"
            encrypted_data = self.caesar_cipher(user_data)
            with open('users.txt', 'a', encoding='utf-8') as file:
                file.write(encrypted_data + '\n')
            return True
        return False

    def draw(self):
        if self.game_started:
            return

        header_text = "Регистрация" if self.is_registration else "Авторизация"
        header = self.font_header.render(header_text, True, black)
        header_rect = header.get_rect(center=(window_size_w // 2, 160))
        self.screen.blit(header, header_rect)

        username_label = self.font_label.render("Имя пользователя", True, black)
        self.screen.blit(username_label, (window_size_w // 2 - 100, 200))

        pygame.draw.rect(self.screen, gray if self.active_input == "username" else black,
                         self.username_rect, 2)
        username_text = self.font_entry.render(self.username, True, black)
        self.screen.blit(username_text, (self.username_rect.x + 5, self.username_rect.y + 5))

        password_label = self.font_label.render("Пароль", True, black)
        self.screen.blit(password_label, (window_size_w // 2 - 100, 300))

        pygame.draw.rect(self.screen, gray if self.active_input == "password" else black,
                         self.password_rect, 2)
        hidden_password = "*" * len(self.password)
        password_text = self.font_entry.render(hidden_password, True, black)
        self.screen.blit(password_text, (self.password_rect.x + 5, self.password_rect.y + 5))

        pygame.draw.rect(self.screen, gray, self.login_btn)
        button_text = "Сохранить" if self.is_registration else "Войти"
        login_text = self.font_label.render(button_text, True, black)
        login_text_rect = login_text.get_rect(center=self.login_btn.center)
        self.screen.blit(login_text, login_text_rect)

        if self.error_message and self.error_timer > 0:
            error_surface = self.font_label.render(self.error_message, True, (77, 19, 19))
            error_rect = error_surface.get_rect(center=(window_size_w // 2, 390))
            self.screen.blit(error_surface, error_rect)
            self.error_timer -= 1

        if self.show_register_popup:
            overlay = pygame.Surface((window_size_w, window_size_h))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(128)
            self.screen.blit(overlay, (0, 0))

            pygame.draw.rect(self.screen, white, self.popup_rect)
            pygame.draw.rect(self.screen, black, self.popup_rect, 2)

            popup_header = self.font_header.render("Зарегистрироваться", True, black)
            popup_header_rect = popup_header.get_rect(center=(window_size_w // 2, window_size_h // 2 - 70))
            self.screen.blit(popup_header, popup_header_rect)

            popup_text = self.font_label.render("Имя пользователя и пароль не найдены", True, black)
            popup_text2 = self.font_label.render("зарегистрироваться?", True, black)
            popup_text_rect = popup_text.get_rect(center=(window_size_w // 2, window_size_h // 2 - 20))
            popup_text_rect2 = popup_text2.get_rect(center=(window_size_w // 2, window_size_h // 2))
            self.screen.blit(popup_text, popup_text_rect)
            self.screen.blit(popup_text2, popup_text_rect2)

            pygame.draw.rect(self.screen, gray, self.yes_btn)
            pygame.draw.rect(self.screen, gray, self.no_btn)

            yes_text = self.font_label.render("Да", True, black)
            no_text = self.font_label.render("Нет", True, black)

            yes_text_rect = yes_text.get_rect(center=self.yes_btn.center)
            no_text_rect = no_text.get_rect(center=self.no_btn.center)

            self.screen.blit(yes_text, yes_text_rect)
            self.screen.blit(no_text, no_text_rect)