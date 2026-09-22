import os
import random
import subprocess
import time

import chess
from ChessEngine import ChessEngine

board = chess.Board()


# Função para salvar o jogo
def save_game(moves, white, black, n_game, result):
    filename = f"Codes/Games/n_games/game_{n_game}_{white}_{black}.pgn"

    pgn_header = (
        f'[Event "Engine vs Engine Game"]\n'
        f'[Site "Local"]\n'
        f'[Date "{time.strftime("%Y.%m.%d")}"]\n'
        f'[Round "1"]\n'
        f'[White "{white}"]\n'
        f'[Black "{black}"]\n'
        f'[WhiteElo "1500"]\n'
        f'[BlackElo "1500"]\n'
        f'[Result "{board.result()}"]\n\n'
    )

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w") as file:
        file.write(pgn_header)

        move_text = ""
        for i in range(0, len(moves), 2):
            move_text += f"{i // 2 + 1}. {moves[i]} "
            if i + 1 < len(moves):
                move_text += f"{moves[i + 1]} "

        move_text += result
        file.write(move_text.strip())


# Função para testar o jogo entre duas IAs
def engine_vs_engine(
    engine1: ChessEngine, engine2: ChessEngine
) -> tuple[str, list[str]]:
    sequence = []

    engine1.color = random.choice([chess.WHITE, chess.BLACK])
    engine2.color = chess.WHITE if engine1.color == chess.BLACK else chess.BLACK

    if engine1.color == chess.WHITE:
        white_name = engine1.name
        black_name = engine2.name
        white_depth = engine1.depth
        black_depth = engine2.depth
    else:
        white_name = engine2.name
        black_name = engine1.name
        white_depth = engine2.depth
        black_depth = engine1.depth

    print(
        f"White: {white_name} (Depth {white_depth}), Black: {black_name} (Depth {black_depth})",
    )

    while not board.is_game_over():
        best_move = random.choice(list(board.legal_moves))
        if engine1.color == board.turn:
            best_move = engine1.get_best_move(sequence)
        elif engine2.color == board.turn:
            best_move = engine2.get_best_move(sequence)
        san_move = board.san(best_move)
        sequence.append(san_move)
        board.push(best_move)

    print(board.result(), end="\n\n")

    return board.result(), sequence


def n_games(depth1, depth2, number_games=10):
    wins = 0
    draws = 0
    losses = 0

    subprocess.run("cls", shell=True, check=False)

    engine1 = ChessEngine(board, depth1, None, "Engine 1")
    engine2 = ChessEngine(board, depth2, None, "Engine 2")

    for i in range(number_games):
        board.reset()
        print(f"Game {i + 1}:")
        result, sequence = engine_vs_engine(engine1, engine2)

        if engine1.color == chess.WHITE:
            save_game(
                sequence,
                f"{engine1.name} (Depth {engine1.depth})",
                f"{engine2.name} (Depth {engine2.depth})",
                i,
                result,
            )
        else:
            save_game(
                sequence,
                f"{engine2.name} (Depth {engine2.depth})",
                f"{engine1.name} (Depth {engine1.depth})",
                i,
                result,
            )

        if (result == "1-0" and engine1.color == chess.WHITE) or (
            result == "0-1" and engine1.color == chess.BLACK
        ):
            wins += 1
        elif (result == "1-0" and engine2.color == chess.WHITE) or (
            result == "0-1" and engine2.color == chess.BLACK
        ):
            losses += 1
        else:
            draws += 1

    subprocess.run("cls", shell=True, check=False)

    print("Tabela de Resultados:", end="\n\n")
    print(
        f"    {engine1.name} (Depth {engine1.depth})\t\t    vs\t\t     {engine2.name} (Depth {engine2.depth})"
    )
    print(f"\tWins: {wins} \t|\tDraws: {draws}\t|\tLosses: {losses}")


n_games(4, 5, 30)
