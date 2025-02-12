from Engine import get_best_move
import chess
import time
import os
import random


board = chess.Board()

def save_game(moves, white, black):
    filename = f"game_AIvsAI.pgn"

    if board.is_checkmate():
        if board.turn == chess.BLACK:
            result = "1-0"
        else:
            result = "0-1"
    else:
        result = "1/2-1/2"

    pgn_header = (
        f"[Event \"AI vs AI Game\"]\n"
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

# Function to test AI vs AI
def ai_vs_ai(depth_ai1, depth_ai2):
    os.system('cls')
    sequence = []

    depth_white = random.choice([depth_ai1, depth_ai2])
    depth_black = depth_ai2 if depth_white == depth_ai1 else depth_ai1

    while not board.is_game_over():
        if board.turn == chess.WHITE:
            best_move = get_best_move(board, depth_white, sequence)
            sequence.append(board.san(best_move))
            board.push(best_move)
        else:
            best_move = get_best_move(board, depth_black, sequence)
            sequence.append(board.san(best_move))
            board.push(best_move)
        print(board)
        print()



    if board.is_checkmate():
        print("Checkmate!")
    elif board.is_stalemate() or board.is_fivefold_repetition() or board.is_insufficient_material() or board.is_seventyfive_moves():
        print("Draw!")
    save_game(sequence, f"AI (Depth {depth_white})",f"AI (Depth {depth_black})")



# Start AI vs AI game
start = time.time()
ai_vs_ai(4, 2)
elapsed = time.time() - start
print(f'Time to finish this game: {elapsed:.3f} seconds')