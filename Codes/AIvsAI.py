import os
import random
import time

import chess
from ChessEngine import ChessEngine

board = chess.Board()


# Função para salvar o jogo
def save_game(moves, white, black):
    filename = f"Codes/Games/game_{time.strftime('%Y_%m_%d')}_{white}_{black}.pgn"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    if board.is_checkmate():
        if board.turn == chess.BLACK:
            result = "1-0"
        else:
            result = "0-1"
    else:
        result = "1/2-1/2"

    pgn_header = (
        f'[Event "AI vs AI Game"]\n'
        f'[Site "Local"]\n'
        f"[Date \"{time.strftime('%Y.%m.%d')}\"]\n"
        f'[Round "1"]\n'
        f'[White "{white}"]\n'
        f'[Black "{black}"]\n'
        f'[WhiteElo "1500"]\n'
        f'[BlackElo "1500"]\n'
        f'[Result "{result}"]\n\n'
    )

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


# Função para testar o jogo entre duas IAs
def ai_vs_ai(depth_ai1, depth_ai2):
    # trunk-ignore(bandit/B605)
    # trunk-ignore(bandit/B607)
    os.system("cls")
    sequence = []

    # trunk-ignore(bandit/B311)
    depth_white = random.choice([depth_ai1, depth_ai2])
    depth_black = depth_ai2 if depth_white == depth_ai1 else depth_ai1

    engine1 = ChessEngine(board, depth_white, chess.WHITE)
    engine2 = ChessEngine(board, depth_black, chess.BLACK)

    print(f"White: AI (Depth {depth_white}), Black: AI (Depth {depth_black})")

    while not board.is_game_over():
        if board.turn == chess.WHITE:
            best_move, best_score = engine1.get_best_move(sequence)
            if not best_move:
                # trunk-ignore(bandit/B311)
                best_move = random.choice(list(board.legal_moves))
        else:
            best_move, best_score = engine2.get_best_move(sequence)
            if not best_move:
                # trunk-ignore(bandit/B311)
                best_move = random.choice(list(board.legal_moves))
        san_move = board.san(best_move)
        print(san_move, best_score)
        sequence.append(san_move)
        board.push(best_move)

    print(f"White: AI (Depth {depth_white}), Black: AI (Depth {depth_black})")

    if board.is_checkmate():
        print("Checkmate!", "White Won!" if board.turn == chess.BLACK else "Black Won!")
    elif (
        board.is_stalemate()
        or board.is_fivefold_repetition()
        or board.is_insufficient_material()
        or board.is_seventyfive_moves()
    ):
        print("Draw!")

    save_game(sequence, f"AI (Depth {depth_white})", f"AI (Depth {depth_black})")


board = chess.Board(fen="3r4/8/3k4/8/8/8/3K4/8 w - - 0 1")

# Iniciar o jogo AI vs AI
start = time.time()
ai_vs_ai(4, 4)
elapsed = time.time() - start
print(f"Time to finish this game: {elapsed:.3f} seconds")
