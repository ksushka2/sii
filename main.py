from game import Game

def main():
    game = Game()
    while True:
        if game.show_menu():
            game.main_game()

if __name__ == "__main__":
    main()
