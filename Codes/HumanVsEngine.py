import os
import random
import time

import chess
from ChessEngine import ChessEngine as ce

board = chess.Board()


def save_game(moves, white, black):
    if board.is_checkmate():
        if board.turn == chess.BLACK:
            result = "1-0"
        else:
            result = "0-1"
    else:
        result = "1/2-1/2"

    pgn_header = (
        f'[Event "Engine vs Human Game"]\n'
        f'[Site "Local"]\n'
        f"[Date \"{time.strftime('%Y.%m.%d')}\"]\n"
        f'[Round "1"]\n'
        f'[White "{white}"]\n'
        f'[Black "{black}"]\n'
        f'[WhiteElo "1500"]\n'
        f'[BlackElo "1500"]\n'
        f'[Result "{result}"]\n\n'
    )
    filename = f"Codes/Games/game_{time.strftime('%Y_%m_%d')}_HumanvsEngine.pgn"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as file:
        file.write(pgn_header)

        move_text = ""
        for i in range(0, len(moves), 2):
            move_text += f"{i // 2 + 1}. {moves[i]}"
            if i + 1 < len(moves):
                move_text += f" {moves[i + 1]}"
            move_text += " "

        move_text += result

        file.write(move_text.strip())

    print(f"Game saved to {filename}")


# Function to test Engine vs Human
def engine_play(depth):
    sequence = []
    
    engine = ce(board, depth, None, "Engine")
    
    white = random.choice([engine.name, "Human"])
    black = engine.name if white == "Human" else "Human"

    engine.color = chess.WHITE if white == engine.name else chess.BLACK
    
    print()

    while not board.is_game_over():
        if engine.color == board.turn:
            print("Engine's turn.")
            best_move = engine.get_best_move(sequence)
            if best_move is None:
                print("Engine has no legal moves. Game over.")
                break
            move_san = board.san(best_move)
            print(f"Engine move: {move_san}")
            sequence.append(move_san)
            board.push(best_move)
        else:
            move_san = input("Enter your move (in SAN format, e.g., e4): ")
            try:
                move = chess.Board.parse_san(board, move_san)
                if move in board.legal_moves:
                    board.push_san(move_san)
                    sequence.append(move_san)
                else:
                    print("Invalid move. Try again.")
            except ValueError:
                print("Invalid move format. Try again.")

    if board.is_checkmate():
        print("Checkmate!")
    else:
        print("Draw!")
    save_game(sequence, white, black)


engine_play(4)
