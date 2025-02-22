import chess
import chess.engine
from ChessEngine\Engine import Engine
import pygame as p
import random

p.init()
WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}
DARK_SQ = (190, 104, 53)
LIGHT_SQ = (224, 172, 125)


def load_images():
    pieces = ["wP", "wR", "wN", "wB", "wQ", "wK", "bP", "bR", "bN", "bB", "bQ", "bK"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("Images/" + piece + ".png"),
                                          (SQ_SIZE, SQ_SIZE))


def main():
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color('white'))
    board = chess.Board()
    load_images()
    running = True

    player_is_white = random.choice([True, False])
    player_turn = player_is_white  # Jogador começa se for branco
    selected_square = None

    while running:
        for event in p.event.get():
            if event.type == p.QUIT:
                running = False
            elif event.type == p.MOUSEBUTTONDOWN and player_turn:
                selected_square = handle_human_move(event, board, selected_square, player_is_white)
                if selected_square is None:
                    player_turn = False  # Alterna para a IA

        if not player_turn:
            ai_move = Engine.get_best_move(board)
            board.push(ai_move)
            player_turn = True  # Volta para o jogador

        drawGameState(screen, board, player_is_white)
        clock.tick(MAX_FPS)
        p.display.flip()


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
            p.draw.rect(screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def drawPieces(screen, board, player_is_white):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)  # Ajusta para a indexação da GUI
            if not player_is_white:
                row = 7 - row  # Inverte para as negras
                col = 7 - col
            screen.blit(IMAGES[piece.symbol()], p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))


if __name__ == "__main__":
    main()
