from Engine import get_best_move
import chess
import time
import os


def save_game(moves, white, black):
    # Criar um nome de arquivo baseado no tempo atual para evitar sobrescrever arquivos
    filename = f"game_{time.strftime('%Y%m%d_%H%M%S')}.pgn"

    # Determinar o resultado do jogo
    result = "1-0" if moves[-1] == "#" and len(moves) % 2 == 1 else "0-1" if moves[-1] == "#" else "1/2-1/2"

    # Construir o cabeçalho PGN
    pgn_header = (
        f"[Event \"AI vs AI Game\"]\n"
        f"[Site \"Local\"]\n"
        f"[Date \"{time.strftime('%Y.%m.%d')}\"]\n"
        f"[Round \"1\"]\n"
        f"[White \"{white}\"]\n"
        f"[Black \"{black}\"]\n"
        f"[Result \"{result}\"]\n\n"
    )

    # Escrever o cabeçalho no arquivo
    with open(filename, 'w') as file:
        file.write(pgn_header)

        # Escrever os movimentos em formato PGN
        move_text = ""
        for i in range(0, len(moves), 2):
            move_text += f"{i // 2 + 1}. {moves[i]}"
            if i + 1 < len(moves):
                move_text += f" {moves[i + 1]}"
            move_text += " "

        # Adicionar o resultado no final dos movimentos
        move_text += result

        file.write(move_text.strip())

    print(f"Game saved to {filename}")

# Function to test AI vs AI
def ai_vs_ai(depth_ai1, depth_ai2):
    board = chess.Board()
    sequence = []

    while not board.is_game_over():
        os.system('cls')
        print(board)
        if board.turn == chess.WHITE:
            best_move = get_best_move(board, depth_ai1, sequence)  # Adjust depth as needed
            sequence.append(board.san(best_move))
            board.push(best_move)
        else:
            best_move = get_best_move(board, depth_ai2, sequence)  # Adjust depth as needed
            sequence.append(board.san(best_move))
            board.push(best_move)


    if board.is_checkmate():
        print("Checkmate!")
    elif board.is_stalemate() or board.is_fivefold_repetition() or board.is_insufficient_material() or board.is_seventyfive_moves():
        print("Draw!")
    save_game(sequence, f"AI (Depth {depth_ai1})",f"AI (Depth {depth_ai2})")



# Start AI vs AI game
start = time.time()
ai_vs_ai(4,3)
elapsed = time.time() - start
print(f'Tempo para terminar este jogo foi de: {elapsed:.3f} segundos')