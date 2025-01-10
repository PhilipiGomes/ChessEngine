from Engine import *
import chess
import random
import time


board = chess.Board()

def save_game(moves, white, black):
    filename = f"game_{time.strftime('%d-%m-%Y_%H:%M:%S')}.pgn"

    if board.is_checkmate():
        if board.turn == chess.BLACK:
            result = "1-0"
        else:
            result = "0-1"
    else:
        result = "1/2-1/2"

    pgn_header = (
        f"[Event \"AI vs Human Game\"]\n"
        f"[Site \"Local\"]\n"
        f"[Date \"{time.strftime('%Y.%m.%d')}\"]\n"
        f"[Round \"1\"]\n"
        f"[White \"{white}\"]\n"
        f"[Black \"{black}\"]\n"
        f"[Result \"{result}\"]\n\n"
    )

    with open(filename, 'w') as file:
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

# Function to test AI vs Human
def ai_play(depth):
    sequence = []

    white = random.choice([f"AI (Depth {depth})", "Human"])
    black = f"AI (Depth {depth})" if white == "Human" else "Human"

    print()

    while not board.is_game_over():
        if (board.turn == chess.WHITE and white == f"AI (Depth {depth})") or (board.turn == chess.BLACK and black == f"AI (Depth {depth})"):
            print(f"AI's turn. Current board:\n{board}")
            best_move = get_best_move(board, depth, sequence)  # Adjust depth as needed
            print(f"AI move: {best_move}")
            sequence.append(board.san(best_move))
            board.push(best_move)

        else:
            print(f"Your turn. Current board:\n{board}")
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
    elif board.is_stalemate() or board.is_fivefold_repetition() or board.is_insufficient_material() or board.is_seventyfive_moves():
        print("Draw!")
    save_game(sequence, white, black)




# Start AI vs Human game
ai_play(2)