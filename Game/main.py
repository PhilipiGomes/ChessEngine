import os
import random
import time

import chess
import pygame as p
from Engine import get_best_move

p.init()
WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 30
IMAGES = {}
DARK_SQ = (190, 104, 53)
LIGHT_SQ = (224, 172, 125)


def load_images():
    # Mapeamento das chaves das peças para os nomes dos arquivos de imagem
    piece_image_map = {
        "P": "wP.png",
        "N": "wN.png",
        "B": "wB.png",
        "R": "wR.png",
        "Q": "wQ.png",
        "K": "wK.png",
        "p": "bP.png",
        "n": "bN.png",
        "b": "bB.png",
        "r": "bR.png",
        "q": "bQ.png",
        "k": "bK.png",
    }
    for piece, img_name in piece_image_map.items():
        IMAGES[piece] = p.transform.scale(
            p.image.load(os.path.join("Game", "Images", img_name)), (SQ_SIZE, SQ_SIZE)
        )


def save_game(moves, white, black, board):
    if board.is_checkmate():
        if board.turn == chess.BLACK:
            result = "1-0"
        else:
            result = "0-1"
    else:
        result = "1/2-1/2"

    pgn_header = (
        f'[Event "AI vs Human Game"]\n'
        f'[Site "Local"]\n'
        f"[Date \"{time.strftime('%Y.%m.%d')}\"]\n"
        f'[Round "1"]\n'
        f'[White "{white}"]\n'
        f'[Black "{black}"]\n'
        f'[WhiteElo "1500"]\n'
        f'[BlackElo "1500"]\n'
        f'[Result "{result}"]\n\n'
    )
    filename = f"Codes/Games/game_{time.strftime('%Y_%m_%d')}_HumanvsAI.pgn"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
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


def main(ai_depth, sequence):
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    board = chess.Board()
    load_images()
    running = True

    # trunk-ignore(bandit/B311)
    player_is_white = random.choice([True, False])
    player_turn = player_is_white  # Jogador começa se for branco
    selected_square = None

    moves_san = []  # Lista para armazenar os lances em SAN

    # Nomes dos jogadores
    white_name = "Human" if player_is_white else "AI"
    black_name = "AI" if player_is_white else "Human"

    while running:
        for event in p.event.get():
            if event.type == p.QUIT:
                running = False
            elif event.type == p.MOUSEBUTTONDOWN and player_turn:
                prev_board = board.copy()
                selected_square = handle_human_move(
                    event, board, selected_square, player_is_white
                )
                if selected_square is None and len(board.move_stack) > len(moves_san):
                    move = board.move_stack[-1]
                    moves_san.append(prev_board.san(move))
                    player_turn = False  # Alterna para a IA

        if not player_turn and not board.is_game_over():
            prev_board = board.copy()
            ai_move = get_best_move(board, ai_depth, sequence)
            if not ai_move:
                # trunk-ignore(bandit/B311)
                ai_move = random.choice(list(board.legal_moves))
            board.push(ai_move)
            moves_san.append(prev_board.san(ai_move))
            player_turn = True  # Volta para o jogador

        drawGameState(screen, board, player_is_white)
        clock.tick(MAX_FPS)
        p.display.flip()

        if board.is_game_over():
            save_game(moves_san, white_name, black_name, board)
            running = False


def handle_human_move(event, board, selected_square, player_is_white):
    x, y = event.pos
    col = x // SQ_SIZE
    row = y // SQ_SIZE
    if not player_is_white:
        row = 7 - row  # Inverte para as negras
        col = 7 - col

    square = chess.square(col, 7 - row)  # Ajusta para a indexação do python-chess

    if selected_square is None:
        piece = board.piece_at(square)
        if piece and piece.color == board.turn:  # Verifica se é uma peça do jogador
            return square  # Seleciona a peça
    else:
        move = chess.Move(selected_square, square)
        if move in board.legal_moves:
            board.push(move)
            return None  # Move feito, deseleciona
        return selected_square  # Mantém a seleção se o movimento for inválido


def drawGameState(screen, board, player_is_white):
    drawBoard(screen)
    drawPieces(screen, board, player_is_white)


def drawBoard(screen):
    colors = [LIGHT_SQ, DARK_SQ]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            p.draw.rect(
                screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            )


def drawPieces(screen, board, player_is_white):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)  # Ajusta para a indexação da GUI
            if not player_is_white:
                row = 7 - row  # Inverte para as negras
                col = 7 - col
            screen.blit(
                IMAGES[piece.symbol()],
                p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE),
            )


if __name__ == "__main__":
    main(2, [])
