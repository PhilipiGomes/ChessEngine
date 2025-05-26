import chess
import time
import os
import random
from EngineAIvsAI import get_best_move

board = chess.Board()

# Função para calcular a probabilidade de vitória (usando fórmula de ELO)
def calculate_elo(expected, actual, k=32):
    return k * (actual - expected)

# Função para calcular a probabilidade de vitória (E)
def expected_score(rating1, rating2):
    return 1 / (1 + 10 ** ((rating2 - rating1) / 400))

# Função para atualizar o rating
def update_rating(rating1, rating2, result1, result2, k=32):
    expected1 = expected_score(rating1, rating2)
    expected2 = expected_score(rating2, rating1)
    
    new_rating1 = rating1 + calculate_elo(expected1, result1, k)
    new_rating2 = rating2 + calculate_elo(expected2, result2, k)
    
    return new_rating1, new_rating2

# Função para salvar o jogo
def save_game(moves, white, black, game_number, ratings):
    filename = f"Codes/Games/Tournament/game_{game_number}_{white}_{black}.pgn"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Obter o rating atual das IAs
    white_rating = ratings.get(white, 1500)
    black_rating = ratings.get(black, 1500)

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
        f"[Round \"{game_number}\"]\n"
        f"[White \"{white}\"]\n"
        f"[Black \"{black}\"]\n"
        f"[WhiteElo \"{round(white_rating, 3)}\"]\n"
        f"[BlackElo \"{round(black_rating, 3)}\"]\n"
        f"[Result \"{result}\"]\n\n"
    )

    with open(filename, 'w') as file:
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
def ai_vs_ai(depth_ai1, depth_ai2, results, ratings, transposition_table_ai1, transposition_table_ai2, game_number):
    os.system('cls')
    sequence = []

    depth_white = random.choice([depth_ai1, depth_ai2])
    depth_black = depth_ai2 if depth_white == depth_ai1 else depth_ai1

    print(f'Game {game_number} of {num_games}:')
    print(f'White: AI (Depth {depth_white}), Black: AI (Depth {depth_black})')
    board.reset()

    while not board.is_game_over():
        if board.turn == chess.WHITE:
            best_move = get_best_move(board, depth_white, sequence, transposition_table_ai1)
            # Callback: se não encontrar movimento válido, faz um aleatório.
            if not best_move:
                board.push(random.choice(list(board.legal_moves)))
            sequence.append(board.san(best_move))
            board.push(best_move)
        else:
            best_move = get_best_move(board, depth_black, sequence, transposition_table_ai2)
            # Callback: se não encontrar movimento válido, faz um aleatório.
            if not best_move:
                board.push(random.choice(list(board.legal_moves)))
            sequence.append(board.san(best_move))
            board.push(best_move)
    
    os.system('cls')
    result = board.result()

    print(result)
    save_game(sequence, f"AI (Depth {depth_white})", f"AI (Depth {depth_black})", game_number, ratings)

    # Atualizar as estatísticas
    if result == '1-0':  # White win
        results[f"AI (Depth {depth_white})"]['wins'] += 1
        results[f"AI (Depth {depth_black})"]['losses'] += 1
        ratings[f"AI (Depth {depth_white})"] = update_rating(ratings[f"AI (Depth {depth_white})"], ratings[f"AI (Depth {depth_black})"], 1, 0)[0]
        ratings[f"AI (Depth {depth_black})"] = update_rating(ratings[f"AI (Depth {depth_white})"], ratings[f"AI (Depth {depth_black})"], 1, 0)[1]
    elif result == '0-1':  # Black win
        results[f"AI (Depth {depth_white})"]['losses'] += 1
        results[f"AI (Depth {depth_black})"]['wins'] += 1
        ratings[f"AI (Depth {depth_white})"] = update_rating(ratings[f"AI (Depth {depth_white})"], ratings[f"AI (Depth {depth_black})"], 0, 1)[0]
        ratings[f"AI (Depth {depth_black})"] = update_rating(ratings[f"AI (Depth {depth_white})"], ratings[f"AI (Depth {depth_black})"], 0, 1)[1]
    else:  # Draw
        results[f"AI (Depth {depth_white})"]['draws'] += 1
        results[f"AI (Depth {depth_black})"]['draws'] += 1
        ratings[f"AI (Depth {depth_white})"] = update_rating(ratings[f"AI (Depth {depth_white})"], ratings[f"AI (Depth {depth_black})"], 0.5, 0.5)[0]
        ratings[f"AI (Depth {depth_black})"] = update_rating(ratings[f"AI (Depth {depth_white})"], ratings[f"AI (Depth {depth_black})"], 0.5, 0.5)[1]

# Inicializar resultados e ratings
ratings = {
    "AI (Depth 1)": 1500,
    "AI (Depth 2)": 1500,
    "AI (Depth 3)": 1500, 
    "AI (Depth 4)": 1500, 
    "AI (Depth 5)": 1500, 
    "AI (Depth 6)": 1500,
    "AI (Depth 7)": 1500,
    "AI (Depth 8)": 1500,
    "AI (Depth 9)": 1500,
    "AI (Depth 10)": 1500
    }

results = {
    "AI (Depth 1)":  {'wins': 0, 'draws': 0, 'losses': 0},
    "AI (Depth 2)":  {'wins': 0, 'draws': 0, 'losses': 0},
    "AI (Depth 3)":  {'wins': 0, 'draws': 0, 'losses': 0},
    "AI (Depth 4)":  {'wins': 0, 'draws': 0, 'losses': 0},
    "AI (Depth 5)":  {'wins': 0, 'draws': 0, 'losses': 0},
    "AI (Depth 6)":  {'wins': 0, 'draws': 0, 'losses': 0},
    "AI (Depth 7)":  {'wins': 0, 'draws': 0, 'losses': 0},
    "AI (Depth 8)":  {'wins': 0, 'draws': 0, 'losses': 0},
    "AI (Depth 9)":  {'wins': 0, 'draws': 0, 'losses': 0},
    "AI (Depth 10)": {'wins': 0, 'draws': 0, 'losses': 0},
    }

# Inicializar tabelas de transposição
transposition_tables = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}, 7: {}, 8: {}, 9:{}, 10: {}}

# Inicializar contador de jogos
game_number = 1

depths = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
n_rounds = 3
num_games = len(depths) * (len(depths) - 1) * n_rounds // 2

# Jogar as partidas entre as IAs
for depth1 in depths:
    for depth2 in depths[depths.index(depth1)+1:]:
        for _ in range(n_rounds):
            ai_vs_ai(depth1, depth2, results, ratings, transposition_tables[depth1], transposition_tables[depth2], game_number)
            game_number += 1  # Incrementa o número da partida após cada jogo

# Exibir a tabela de classificação
print("\nTabela de Classificação:")
print("   AI       | Vitórias | Empates | Derrotas | Rating")
for depth in sorted(ratings.keys(), key=lambda x: ratings[x], reverse=True):
    print(f"{depth}| {results[depth]['wins']}       | {results[depth]['draws']}     | {results[depth]['losses']}     | {ratings[depth]:.2f}")
