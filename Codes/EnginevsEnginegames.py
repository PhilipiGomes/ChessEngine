import os
import random
import time
from typing import Tuple

import chess
from ChessEngine import ChessEngine

board = chess.Board()


# Função para salvar o jogo
def save_game(moves, white, black, n_game, board):
    filename = f"Games/n_games/depth3 vs depth1/game_{n_game}_{white}_{black}.pgn"

    if board.is_checkmate():
        if board.turn == chess.BLACK:
            result = "1-0"
        else:
            result = "0-1"
    elif (
        board.is_stalemate()
        or board.is_insufficient_material()
        or board.is_seventyfive_moves()
        or board.is_variant_draw()
    ):
        result = "1/2-1/2"
    else:
        result = "1/2-1/2"

    pgn_header = (
        f'[Event "Engine vs Engine Game"]\n'
        f'[Site "Local"]\n'
        f"[Date \"{time.strftime('%Y.%m.%d')}\"]\n"
        f'[Round "1"]\n'
        f'[White "{white}"]\n'
        f'[Black "{black}"]\n'
        f'[WhiteElo "1500"]\n'
        f'[BlackElo "1500"]\n'
        f'[Result "{result}"]\n\n'
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

    print(f"Game saved to {filename}")


# Função para testar o jogo entre duas IAs
def engine_vs_engine(
    engine1: ChessEngine, engine2: ChessEngine
) -> Tuple[str, ChessEngine, ChessEngine]:
    sequence = []

    engine1.color = random.choice([chess.WHITE, chess.BLACK])
    engine2.color = chess.WHITE if engine1.color == chess.BLACK else chess.BLACK

    print(
        f"White: {engine1.name} (Depth {engine1.depth}), Black: {engine2.name} (Depth {engine2.depth})",
        end="\n\n",
    )

    while not board.is_game_over():
        if engine1.color == board.turn:
            best_move = engine1.get_best_move(sequence)
        elif engine2.color == board.turn:
            best_move = engine2.get_best_move(sequence)
        san_move = board.san(best_move)
        if board.turn == chess.WHITE:
            tamanho_str = len(san_move)
            if board.fullmove_number >= 10:
                if tamanho_str < 4:
                    if tamanho_str == 2:
                        fim = "  "
                    else:
                        fim = " "
                else:
                    fim = ""
            else:
                if tamanho_str < 5:
                    if tamanho_str == 2:
                        fim = "   "
                    elif tamanho_str == 3:
                        fim = "  "
                    else:
                        fim = " "
                else:
                    fim = ""
            print(f"{board.fullmove_number}. {san_move}", end=fim)
            print("\t", end="")
        else:
            print(f"{san_move}")
        sequence.append(san_move)
        board.push(best_move)
    if board.turn != chess.WHITE:
        print()
    print()

    save_game(
        sequence,
        f"{engine1.name} (Depth {engine1.depth})",
        f"{engine2.name} (Depth {engine2.depth})",
    )

    return board.result(), engine1, engine2


def n_games(depth1, depth2, number_games=10):
    wins = 0
    draws = 0
    losses = 0

    engine1 = ChessEngine(board, depth1, None, "Engine 1")
    engine2 = ChessEngine(board, depth2, None, "Engine 2")

    for _ in range(1, number_games + 1):
        board.reset()
        result, engine_1, engine_2 = engine_vs_engine(engine1, engine2)

        if (result == "1-0" and engine1.name == engine_1.name) or (
            result == "0-1" and engine1.name == engine_1.name
        ):
            wins += 1
        elif (result == "1-0" and engine2.name == engine_2.name) or (
            result == "0-1" and engine2.name == engine_2.name
        ):
            losses += 1
        else:
            draws += 1

    print("\nTabela de Resultados:")
    print(
        f"{engine1.name} (Depth {engine1.depth}) vs {engine2.name} (Depth {engine2.depth})"
    )
    print(f"Wins: {wins} | Draws: {draws} | Losses: {losses}")


n_games(3, 1, 1000)
