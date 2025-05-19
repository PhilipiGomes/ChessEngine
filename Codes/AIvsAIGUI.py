from EngineAIvsAI import get_best_move
import chess
import time
import os
import random
import pygame as p

p.init()
WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}
DARK_SQ = (190, 104, 53)
LIGHT_SQ = (224, 172, 125)

def load_images():
    pieces = {'P': "wP", 'R': "wR", 'N': "wN", 'B': "wB", 'Q': "wQ", 'K': "wK",
              'p': "bP", 'r': "bR", 'n': "bN", 'b': "bB", 'q': "bQ", 'k': "bK"}
    for piece_key, piece in pieces.items():
        path = os.path.join("Images", piece + ".png")
        if os.path.exists(path):
            IMAGES[piece_key] = p.transform.scale(p.image.load(path), (SQ_SIZE, SQ_SIZE))
        else:
            print(f"Warning: Missing image file {path}")

def drawGameState(screen, board):
    drawBoard(screen)
    drawPieces(screen, board)
    p.display.update()

def drawBoard(screen):
    colors = [LIGHT_SQ, DARK_SQ]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            p.draw.rect(screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawPieces(screen, board):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)  # Ajuste para indexação da GUI
            screen.blit(IMAGES[piece.symbol()], p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def save_game(board, moves, white, black):
    filename = f"Games/game_{time.strftime('%Y_%m_%d')}_{white}_{black}.pgn"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    if board.is_checkmate():
        result = "1-0" if board.turn == chess.BLACK else "0-1"
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

    with open(filename, 'w') as file:
        file.write(pgn_header)
        move_text = " ".join(f"{i // 2 + 1}. {moves[i]} {moves[i + 1]}" if i + 1 < len(moves) else f"{i // 2 + 1}. {moves[i]}"
                             for i in range(0, len(moves), 2))
        file.write(move_text + " " + result)

    print(f"Game saved to {filename}")

def ai_vs_ai(depth_ai1, depth_ai2):
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color('white'))
    load_images()

    sequence = []
    board = chess.Board()

    transposition_table_ai1 = {}
    transposition_table_ai2 = {}

    depth_white = random.choice([depth_ai1, depth_ai2])
    depth_black = depth_ai2 if depth_white == depth_ai1 else depth_ai1

    print(f'White: AI (Depth {depth_white}), Black: AI (Depth {depth_black})')

    running = True
    game_over = False

    while running:
        for event in p.event.get():
            if event.type == p.QUIT:
                running = False

        if not game_over:
            if board.is_game_over():
                game_over = True
                continue

            if board.turn == chess.WHITE:
                best_move = get_best_move(board, depth_white, sequence, transposition_table_ai1)
            else:
                best_move = get_best_move(board, depth_black, sequence, transposition_table_ai2)

            if best_move:
                sequence.append(board.san(best_move))
                print(board.san(best_move))
                board.push(best_move)
            else:
                fallback_move = random.choice(list(board.legal_moves))
                sequence.append(board.san(fallback_move))
                board.push(fallback_move)

            drawGameState(screen, board)
            clock.tick(MAX_FPS)
            p.display.flip()

    print(f'White: AI (Depth {depth_white}), Black: AI (Depth {depth_black})')

    if board.is_checkmate():
        print("Checkmate!", "White Won!" if board.turn == chess.BLACK else "Black Won!")
    elif board.is_stalemate() or board.is_fivefold_repetition() or board.is_insufficient_material() or board.is_seventyfive_moves():
        print("Draw!")

    save_game(board, sequence, f"AI (Depth {depth_white})", f"AI (Depth {depth_black})")


# Iniciar o jogo AI vs AI
start = time.time()
ai_vs_ai(2, 2)
elapsed = time.time() - start
print(f'Time to finish this game: {elapsed:.3f} seconds')
