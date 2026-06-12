cell_size = 68
board_size = 8
window_size_w = 1100
window_size_h = 700
board_offset = window_size_w - (cell_size * board_size) - 50
board_offset_y = 50
fps = 60

white = (227, 214, 200)
black = (0, 0, 0)
gray = (130, 163, 194)

Icon = "assets/new_icon.png"
Music = "assets/music_fon.mp3"
Desc = "assets/desk.jpg"
White_check = "assets/white.png"
Black_check = "assets/black.png"

SARSA_MODEL_PATH = "artifacts/halma_sarsa.json"
USE_SARSA_BOT = True
SARSA_EPSILON_PLAY = 0.0
MINIMAX_DEPTH = 3

SARSA_PEOPLE_LEARN = True
SARSA_PEOPLE_ALPHA = 0.05
SARSA_PEOPLE_SEPARATE_FILE = False
SARSA_PEOPLE_MODEL_PATH = "artifacts/halma_sarsa_human.json"
