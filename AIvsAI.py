from Engine import *
import chess


# Function to test AI vs AI
def ai_vs_ai():
    board = chess.Board()
    sequence = []

    while not board.is_game_over():
        if board.turn == chess.WHITE:
            best_move = get_best_move(board, 2, sequence)  # Adjust depth as needed
            print(f"AI 1 move: {best_move}")
            if type(best_move) == str:
                board.push_san(best_move)
                sequence.append(best_move)
            else:
                sequence.append(board.san(best_move))
                board.push(best_move)

        else:
            best_move = get_best_move(board, 2, sequence)  # Adjust depth as needed
            print(f"AI 2 move: {best_move}")
            if type(best_move) == str:
                board.push_san(best_move)
                sequence.append(best_move)
            else:
                sequence.append(board.san(best_move))
                board.push(best_move)


    if board.is_checkmate():
        print("Checkmate!")
    elif board.is_stalemate() or board.is_fivefold_repetition() or board.is_insufficient_material() or board.is_seventyfive_moves():
        print("Draw!")
    else:
        print("Game over.")
    print(sequence)


# Start AI vs AI game
ai_vs_ai()