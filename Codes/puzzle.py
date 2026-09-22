import csv
import os

import chess
import pandas as pd
from ChessEngine import ChessEngine as ce


# Função para carregar os puzzles de um arquivo CSV
def load_puzzles_from_csv(csv_filename: str, theme: str | None = None):
    df = pd.read_csv(csv_filename)
    if theme:
        df = filter_puzzles_by_theme(df, theme)
    return df


# Função para filtrar puzzles por tema
def filter_puzzles_by_theme(df, theme: str):
    return df[df["Themes"].str.contains(theme, case=False, na=False)]


# Função para filtrar puzzles por rating
def filter_puzzles_by_rating(df, min_rating: float, max_rating: float):
    return df[(df["Rating"] >= min_rating) & (df["Rating"] <= max_rating)]


# Função para pegar um puzzle aleatório e os movimentos corretos
def get_random_fen_and_moves(df) -> tuple:
    random_row = df.sample(n=1)
    return (
        random_row["PuzzleId"].values[0],
        random_row["FEN"].values[0],
        random_row["Moves"].values[0],
        random_row["Themes"].values[0],
        random_row["GameUrl"].values[0],
        random_row["Rating"].values[0],
    )


# Função principal para resolver os puzzles
def puzzle(
    board: chess.Board, depth: int, theme: str | None = None, rang: int | None = None
):
    # Carregar os puzzles do arquivo CSV
    csv_filename = r".\Codes\Data\lichess_db_puzzle.csv"  # Atualize o caminho do arquivo, se necessário
    print("Loading puzzles...")
    df_puzzles = load_puzzles_from_csv(csv_filename, theme)

    # Inicializar o rating do bot
    rating = 1500
    if rang is None:
        rang = 0
    max_rating = rating + rang
    min_rating = rating - rang

    # Arquivo para salvar os dados dos puzzles
    os.makedirs(r".\Codes\PuzzlesResults", exist_ok=True)
    with open(
        rf".\Codes\PuzzlesResults\puzzle_results_{depth}_{theme}_{rang}.csv",
        mode="w",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "PuzzleId",
                "FEN",
                "Moves",
                "Rating",
                "Themes",
                "GameUrl",
                "BotMoves",
                "CorrectMoves",
                "Result",
            ]
        )

        # Filtrar puzzles pelo rating
        print(f"Filtering puzzles by rating: {min_rating} - {max_rating}")
        df_puzzles = filter_puzzles_by_rating(df_puzzles, min_rating, max_rating)

        # Obter um puzzle aleatório
        puzzle_id, fen, moves, themes, game_url, _ = get_random_fen_and_moves(
            df_puzzles
        )
        move_list = moves.split()
        board.set_fen(fen)

        print(f"Puzzle ID: {puzzle_id}")
        print(f"Puzzle FEN: {fen}")

        bot_moves = []
        correct_moves = []
        puzzle_solved = True
        engine = ce(board, depth, not board.turn)
        # Itera sobre os movimentos do puzzle
        for i, move in enumerate(move_list):
            if i % 2 == 0:  # Movimentos de índice par (do adversário)
                # Executar movimento do adversário
                try:
                    move_san = board.san(board.parse_uci(move))
                    board.push_san(move_san)
                    bot_moves.append(move_san)
                    correct_moves.append(
                        move_san
                    )  # Adicionar movimento do adversário na lista de movimentos corretos
                    print(move_san)
                except ValueError:
                    print(f"Movimento inválido: {move}")
                    puzzle_solved = False
                    break
            else:  # Movimentos de índice ímpar (do bot)
                bot_move = engine.get_best_move([])
                bot_move_san = board.san(bot_move)
                bot_moves.append(bot_move_san)

                # O movimento correto a ser comparado é o de índice ímpar
                expected_move_san = board.san(
                    board.parse_uci(move)
                )  # Esse é o movimento correto

                print(f"Bot move: {bot_move_san}, expected move: {expected_move_san}")

                if bot_move_san != expected_move_san:
                    print("Bot falhou!")
                    puzzle_solved = False
                    correct_moves.append(expected_move_san)
                    break
                else:
                    print("Bot Acertou!")
                    board.push(bot_move)

                # Adicionar movimento correto do bot até este ponto
                correct_moves.append(expected_move_san)

        # Gravar os resultados no arquivo CSV
        writer.writerow(
            [
                puzzle_id,
                fen,
                moves,
                rating,
                themes,
                game_url,
                " ".join(bot_moves),
                " ".join(correct_moves),
                "Acerto" if puzzle_solved else "Erro",
            ]
        )


# Configuração do tabuleiro e execução dos puzzles
board = chess.Board()

# Iniciar resolução de puzzles com tema e range de rating escolhidos
puzzle(board, 4, rang=150)
