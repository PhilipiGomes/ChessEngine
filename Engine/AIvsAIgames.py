from EngineAIvsAI import get_best_move
import chess
import time
import os
import random

board = chess.Board()

# Função para salvar o jogo
def save_game(moves, white, black, n_game, board):
    filename = f"Games/n_games/depth3 vs depth1/game_{n_game}_{white}_{black}.pgn"

    if board.is_checkmate():
        if board.turn == chess.BLACK:
            result = "1-0"
        else:
            result = "0-1"
    elif board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_variant_draw():
        result = "1/2-1/2"
    else:
        result = "1/2-1/2"

    pgn_header = (
        f"[Event \"AI vs AI Game\"]\n"
        f"[Site \"Local\"]\n"
        f"[Date \"{time.strftime('%Y.%m.%d')}\"]\n"
        f"[Round \"1\"]\n"
        f"[White \"{white}\"]\n"
        f"[Black \"{black}\"]\n"
        f"[WhiteElo \"1500\"]\n"
        f"[BlackElo \"1500\"]\n"
        f"[Result \"{result}\"]\n\n"
    )

    os.makedirs(os.path.dirname(filename), exist_ok=True)

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
def ai_vs_ai(depth_ai1, depth_ai2, transposition_table_ai1, transposition_table_ai2, n_game):
    # Limpa a tela (compatível com Windows, e pode ser adaptado para outros sistemas)
    os.system('cls' if os.name == 'nt' else 'clear')

    sequence = []

    depth_white = random.choice([depth_ai1, depth_ai2])
    depth_black = depth_ai2 if depth_white == depth_ai1 else depth_ai1

    print(f'Game number {n_game}: White: AI (Depth {depth_white}), Black: AI (Depth {depth_black})')

    while not board.is_game_over():
        if board.turn == chess.WHITE:
            best_move = get_best_move(board, depth_white, sequence, transposition_table_ai1)
            if best_move is None:
                board.push(random.choice(list(board.legal_moves)))
            sequence.append(board.san(best_move))
            board.push(best_move)
        else:
            best_move = get_best_move(board, depth_black, sequence, transposition_table_ai2)
            if best_move is None:
                board.push(random.choice(list(board.legal_moves)))
            sequence.append(board.san(best_move))
            board.push(best_move)
    
    os.system('cls')
    print(f'White: AI (Depth {depth_white}), Black: AI (Depth {depth_black})')

    result = board.result()

    print(result)
    
    save_game(sequence, f"AI (Depth {depth_white})", f"AI (Depth {depth_black})", n_game, board)

    board.reset()

    return result, depth_white, depth_black

def n_games(depth1, depth2, number_games=10):
    transposition_table_ai1 = {}
    transposition_table_ai2 = {}

    wins = 0
    draws = 0
    losses = 0

    for i in range(1, number_games + 1):
        result, depth_white, depth_black = ai_vs_ai(depth1, depth2, transposition_table_ai1, transposition_table_ai2, i)

        if (result == "1-0" and depth1 == depth_white) or (result == "0-1" and depth1 == depth_black):
            wins += 1
        elif (result == "1-0" and depth2 == depth_white) or (result == "0-1" and depth2 == depth_black):
            losses += 1
        else:
            draws += 1
    
    os.system('cls' if os.name == 'nt' else 'clear')

    print("\nTabela de Resultados:")
    print(f"AI (Depth {depth1}) vs AI (Depth {depth2})")
    print(f"Wins: {wins} | Draws: {draws} | Losses: {losses}")


n_games(3, 1, 1000)