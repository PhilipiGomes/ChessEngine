import chess
import os
import pandas as pd
from EnginePuzzles import get_best_move
import csv
import math
import matplotlib.pyplot as plt  # Importando matplotlib para gráficos

# Função para carregar os puzzles de um arquivo CSV
def load_puzzles_from_csv(csv_filename):
    df = pd.read_csv(csv_filename)
    return df

# Função para filtrar puzzles por tema
def filter_puzzles_by_theme(df, theme):
    return df[df['Themes'].str.contains(theme, case=False, na=False)]

# Função para filtrar puzzles por rating
def filter_puzzles_by_rating(df, min_rating, max_rating):
    return df[(df['Rating'] >= min_rating) & (df['Rating'] <= max_rating)]

# Função para pegar um puzzle aleatório e os movimentos corretos
def get_random_fen_and_moves(df):
    random_row = df.sample(n=1)
    return random_row['PuzzleId'].values[0], random_row['FEN'].values[0], random_row['Moves'].values[0], random_row['Themes'].values[0], random_row['GameUrl'].values[0], random_row['Rating'].values[0]

# Função para calcular a nova classificação (rating) usando o sistema Elo
def update_rating(current_rating, puzzle_rating, correct):
    k = 32
    s = 400 / math.log(10)
    prob = 1 / (1 + (math.e) ** ((current_rating - puzzle_rating) / s))
    if correct:
        print(f'Aumentou rating em {k * prob}')
        return current_rating + k * prob
    else:
        print(f'Diminuiu rating em {k * (1 - prob)}')
        return current_rating - k * (1 - prob)

# Função principal para resolver os puzzles
def puzzle(board, depth, num_puzzles, theme=None, rang=500):
    # Carregar os puzzles do arquivo CSV
    csv_filename = 'lichess_db_puzzle.csv'  # Atualize o caminho do arquivo, se necessário
    df_puzzles = load_puzzles_from_csv(csv_filename)
    
    # Filtrar puzzles pelo tema, se fornecido
    if theme:
        df_puzzles = filter_puzzles_by_theme(df_puzzles, theme)
    
    # Inicializar o rating do bot
    rating = 1500
    min_rating = rating - rang
    max_rating = rating + rang

    # Listas para armazenar as variações de rating
    ratings_history = [rating]

    # Arquivo para salvar os dados dos puzzles
    with open(f"PuzzlesResults/puzzle_results_{depth}{"_" if theme is None else f"_{theme}_"}{rang}_{num_puzzles}.csv", mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['PuzzleId', 'FEN', 'Moves', 'Rating', 'Themes', 'GameUrl', 'BotMoves', 'CorrectMoves', 'Result'])

        for puzzle_index in range(num_puzzles):
            # Recalcular min_rating e max_rating a cada puzzle
            min_rating = rating - rang
            max_rating = rating + rang

            df_puzzles = filter_puzzles_by_rating(df_puzzles, min_rating, max_rating)


            if len(df_puzzles) == 0:
                break

            # Obter um puzzle aleatório
            puzzle_id, fen, moves, themes, game_url, puzzle_rating = get_random_fen_and_moves(df_puzzles)
            move_list = moves.split()
            board.set_fen(fen)

            # Verificar se a posição FEN é válida
            if not board.is_valid():
                print(f"Posição FEN inválida para o puzzle {puzzle_id}.")
                continue

            os.system('cls')

            print(f'Number of puzzles filtered: {len(df_puzzles)}')
            print(f"Puzzle {puzzle_index + 1}: {puzzle_id}")
            print(f"Puzzle rating: {puzzle_rating}")
            print(f"Bot rating: {rating}")
            print(f'Puzzle FEN: {fen} \n')

            bot_moves = []
            correct_moves = []
            puzzle_solved = True

            for i, move in enumerate(move_list):
                if i % 2 == 0:
                    try:
                        move_san = board.san(board.parse_uci(move))
                        board.push_san(move_san)
                        bot_moves.append(move_san)
                        correct_moves.append(move_san)
                        print(f"Puzzle move: {move_san}")
                    except ValueError:
                        print(f"Movimento inválido: {move}")
                        puzzle_solved = False
                        break
                else:  # Movimentos de índice ímpar (do bot)
                    # Movimentos do bot
                    bot_move = get_best_move(board, depth)

                    if bot_move is None:
                        print("Erro: o bot não encontrou um movimento válido.")
                        puzzle_solved = False
                        correct_moves.append(expected_move_san)
                        break
                    
                    bot_move_san = board.san(bot_move)

                    expected_move_san = board.san(board.parse_uci(move))

                    print(f'Bot move: {bot_move_san}, expected move: {expected_move_san}')

                    if bot_move_san != expected_move_san:
                        print("Bot falhou!")
                        puzzle_solved = False
                        bot_moves.append(bot_move_san)
                        correct_moves.append(expected_move_san)
                        break
                    else:
                        print("Bot Acertou!")
                        board.push(bot_move)
                        bot_moves.append(bot_move_san)
                    
                    correct_moves.append(expected_move_san)

            rating = update_rating(rating, puzzle_rating, puzzle_solved)

            # Armazenar o rating no histórico
            ratings_history.append(rating)

            writer.writerow([puzzle_id, fen, moves, round(rating, 3), themes, game_url, " ".join(bot_moves), " ".join(correct_moves), "Acerto" if puzzle_solved else "Erro"])
        writer.writerow([])
        writer.writerow([f"Final Rating: {round(rating, 3)}"])

    os.system('cls')
    print(f"Rating final do bot: {rating:.2f}")

    # Gerar o gráfico com a variação do rating
    plt.plot(ratings_history, marker='o', linestyle='-', color='b')
    plt.title("Variação do Rating durante a resolução dos puzzles")
    plt.xlabel("Número do Puzzle")
    plt.ylabel("Rating")
    plt.grid(True)
    plt.show()

board = chess.Board()

# Testando a função com tema e faixa de rating
puzzle(board, 4, num_puzzles=200, theme=None, rang=500)
