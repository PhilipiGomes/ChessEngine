import chess
from ChessEngine import ChessEngine
import random


def main():
    board = chess.Board(fen='8/3r4/3k4/8/8/8/3K4/8 w - - 0 1')
    sequence = []
    engine_color = random.choice([chess.BLACK])
    engine = ChessEngine(board, 2, engine_color)
    my_color_str = "White" if engine_color == chess.BLACK else "Black"
    engine_color_str = "White" if engine_color == chess.WHITE else "Black"
    print(f"Me: {my_color_str}, Engine: {engine_color_str}")
    while True:
        print(board)
        print()
        if board.turn == engine_color:
            best_move = engine.get_best_move(sequence)
            sequence.append(board.san(best_move))
            print(f"Engine move: {board.san(best_move)}")
            board.push(best_move)
        else:
            while True:
                my_move = input("Your Move (SAN format): ")
                try:
                    my_move_uci = board.parse_san(my_move)
                    break
                except ValueError:
                    print("Invalid SAN move, try again: ")
                
            sequence.append(my_move)
            board.push(my_move_uci)
        print()
        if board.is_game_over():
            break
    print(f"Game Over! Result: {board.result()}")


if __name__ == "__main__":
    main()
