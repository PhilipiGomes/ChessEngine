import chess
import os
import importlib.util
import csv
import random
from EngineForPuzzles import get_best_move

# Função para carregar os puzzles de arquivos Python na pasta 'puzzles'
def load_puzzles_from_dict(folder_path='puzzles'):
    puzzles_dict = {}

    # Listar todos os arquivos .py na pasta de puzzles
    for filename in os.listdir(folder_path):
        if filename.endswith(".py"):
            # Gerar o caminho completo do arquivo
            file_path = os.path.join(folder_path, filename)
            
            # Carregar o arquivo Python dinamicamente
            spec = importlib.util.spec_from_file_location(filename, file_path)
            puzzles_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(puzzles_module)
            
            # A variável "puzzles_dict" deve estar dentro de cada arquivo
            puzzles_dict.update(puzzles_module.puzzles_dict)

    return puzzles_dict

# Função para filtrar puzzles por tema
def filter_puzzles_by_theme(puzzles_dict, theme):
    return {k: v for k, v in puzzles_dict.items() if theme.lower() in v['Themes'].lower()}

# Função para filtrar puzzles por rating
def filter_puzzles_by_rating(puzzles_dict, min_rating, max_rating):
    return {k: v for k, v in puzzles_dict.items() if v['Rating'] is not None and min_rating <= v['Rating'] <= max_rating}

# Função para pegar um puzzle aleatório e os movimentos corretos
def get_random_fen_and_moves(puzzles_dict):
    random_puzzle_id = random.choice(list(puzzles_dict.keys()))
    puzzle = puzzles_dict[random_puzzle_id]
    return puzzle['PuzzleId'], puzzle['FEN'], puzzle['Moves'], puzzle['Themes'], puzzle['GameUrl'], puzzle['Rating']

# Função para calcular a nova classificação (rating) usando o sistema Elo
def update_rating(current_rating, puzzle_rating, correct):
    K = 32
    expected_score = 1 / (1 + 10 ** ((current_rating - puzzle_rating) / 400))
    if correct:
        return current_rating + K * (1 - expected_score)
    else:
        return current_rating + K * (0 - expected_score)

# Função principal para resolver os puzzles
def puzzle(board, depth, num_puzzles, theme=None, rang=500):
    # Carregar os puzzles do arquivo de dicionário
    puzzles_dict = load_puzzles_from_dict()

    # Filtrar puzzles pelo tema, se fornecido
    if theme:
        puzzles_dict = filter_puzzles_by_theme(puzzles_dict, theme)

    # Inicializar o rating do bot
    rating = 1500
    max_rating = rating + rang
    min_rating = rating - rang

    # Arquivo para salvar os dados dos puzzles
    with open(f"puzzle_results_depth_{depth}_theme_{theme}_rating_{min_rating}_{max_rating}.csv", mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['PuzzleId', 'FEN', 'Moves', 'Rating', 'Themes', 'GameUrl', 'BotMoves', 'CorrectMoves', 'Result'])

        for puzzle_index in range(num_puzzles):
            max_rating = rating + rang
            min_rating = rating - rang

            # Filtrar puzzles pelo rating
            puzzles_dict = filter_puzzles_by_rating(puzzles_dict, min_rating, max_rating)

            if len(puzzles_dict) == 0:
                break

            # Obter um puzzle aleatório
            puzzle_id, fen, moves, themes, game_url, puzzle_rating = get_random_fen_and_moves(puzzles_dict)
            move_list = moves.split()
            board.set_fen(fen)

            os.system('cls' if os.name == 'nt' else 'clear')  # Limpar a tela no Windows ou sistemas Unix

            print(f"Puzzle {puzzle_index + 1}: {puzzle_id}")

            bot_moves = []
            correct_moves = []
            puzzle_solved = True

            for i, move in enumerate(move_list):
                if i % 2 == 0:  # Movimentos de índice par (do adversário)
                    # Executar movimento do adversário
                    try:
                        move_san = board.san(board.parse_uci(move))
                        board.push_san(move_san)
                        bot_moves.append(move_san)
                        correct_moves.append(move_san)  # Adicionar movimento do adversário na lista de movimentos corretos
                    except ValueError:
                        print(f"Movimento inválido: {move}")
                        puzzle_solved = False
                        break
                else:  # Movimentos de índice ímpar (do bot)
                    # Movimentos do bot
                    bot_move = get_best_move(board, depth)
                    bot_move_san = board.san(bot_move)
                    bot_moves.append(bot_move_san)

                    # O movimento correto a ser comparado é o de índice ímpar
                    expected_move_san = board.san(board.parse_uci(move))  # Esse é o movimento correto

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

            # Atualizar o rating usando o rating do puzzle
            rating = update_rating(rating, puzzle_rating, puzzle_solved)

            # Gravar os resultados no arquivo CSV
            writer.writerow([puzzle_id, fen, moves, round(rating, 3), themes, game_url, " ".join(bot_moves), " ".join(correct_moves), "Acerto" if puzzle_solved else "Erro"])

    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"Rating final do bot: {rating:.2f}")

# Configuração do tabuleiro e execução dos puzzles
board = chess.Board()

# Iniciar resolução de puzzles com tema e rating escolhidos
puzzle(board, 3, num_puzzles=50, theme=None, rang=500)
