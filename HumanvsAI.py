from Engine import *
import chess


# Function to test AI vs Human
def ai_vs_human():
    board = chess.Board()
    sequence = []

    while not board.is_game_over():
        if board.turn == chess.WHITE:
            print(f"AI's turn. Current board:\n{board}")
            best_move = get_best_move(board, 2, sequence)  # Adjust depth as needed
            print(f"AI move: {best_move}")
            if type(best_move) == str:
                board.push_san(best_move)
                sequence.append(best_move)
            else:
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
    elif board.is_stalemate():
        print("Stalemate!")
    else:
        print("Game over.")


# Start AI vs Human game
ai_vs_human()
