import chess
from chess.polyglot import zobrist_hash
from Tables import piece_tables
from typing import Dict, List, Optional

transposition_table: Dict[int, float] = {}

# Função que determina se estamos no final de jogo
def is_endgame(board: chess.Board) -> bool:
    piece_map = board.piece_map()
    minor_pieces = sum(1 for p in piece_map.values() if p.piece_type in {chess.BISHOP, chess.KNIGHT})
    major_pieces = sum(1 for p in piece_map.values() if p.piece_type in {chess.ROOK, chess.QUEEN})
    return major_pieces <= 1 or (major_pieces == 2 and minor_pieces < 3)

# Avaliação do valor de uma peça com base na posição no tabuleiro
def piece_value(board: chess.Board, square: int) -> float:
    piece = board.piece_at(square)
    if not piece or piece.symbol().upper() == 'K':
        return 0
    value = {'P': 1, 'N': 2.8, 'B': 3, 'R': 5, 'Q': 9}[piece.symbol().upper()]
    return value if piece.color == chess.WHITE else -value

# Função principal de avaliação do tabuleiro
def evaluate_board(board: chess.Board) -> float:
    if board.is_game_over():
        if board.is_checkmate():
            return 99999 if board.turn == chess.BLACK else -99999
        elif board.is_stalemate() or board.is_fivefold_repetition() or board.is_insufficient_material() or board.is_seventyfive_moves():
            return 0

    material_score = sum(piece_value(board, square) for square in chess.SQUARES)
    positional_score = evaluate_positional(board)
    return material_score + positional_score

# Função para virar a tabela de avaliação para peças pretas
def get_flipped_table(piece: chess.Piece) -> List[float]:
    table_key = piece.symbol().upper()
    flipped_table = piece_tables.get(table_key, [])
    if flipped_table:
        flipped_table = flipped_table[::-1]
    return flipped_table

# Função que avalia a posição das peças com base nas tabelas
def evaluate_positional(board: chess.Board) -> float:
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue
        if is_endgame(board) and piece.piece_type == chess.KING:
            table = piece_tables['K_end']
        elif is_endgame(board) and piece.piece_type == chess.PAWN:
            table = piece_tables['P_end']
        else:
            table = piece_tables.get(piece.symbol().upper())

        if piece.color == chess.WHITE:
            table = get_flipped_table(piece)

        if table:
            table_index = square
            if piece.color == chess.WHITE:
                score += table[table_index]
            else:
                score -= table[table_index]
    return score

def piece_value_by_type(piece: Optional[chess.Piece]) -> float:
    if not piece or piece.symbol().upper() == 'K':
        return 0
    value = {'P': 1, 'N': 2.8, 'B': 3, 'R': 5, 'Q': 9}[piece.symbol().upper()]
    return value if piece.color == chess.WHITE else -value

# Refined move priority function
def move_priority(board: chess.Board, move: chess.Move) -> float:
    guess = 0
    promotion_values = {chess.KNIGHT: 2.8, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
    attacker = board.piece_at(move.from_square)
    victim = board.piece_at(move.to_square)

    if board.is_capture(move):
        guess = 10 * (piece_value_by_type(victim) - piece_value_by_type(attacker))
    if bool(move.promotion):
        promo_value = promotion_values.get(move.promotion, 0)
        guess += promo_value if board.turn == chess.WHITE else -promo_value
    if board.is_attacked_by(not board.turn, move.to_square):
        guess -= piece_value_by_type(attacker)
    
    return guess


# Quiescence search with more tactical depth
def quiescence(alpha: float, beta: float, board: chess.Board) -> float:
    stand_pat = evaluate_board(board)
    
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    # Only consider capture moves
    capture_moves = [m for m in board.legal_moves if board.is_capture(m)]
    moves = sorted(capture_moves, key=lambda m: move_priority(board, m), reverse=board.turn != chess.BLACK)
    for move in moves:
        board.push(move)
        score = -quiescence(-beta, -alpha, board)
        board.pop()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha

# Função principal de busca Minimax com poda alfa-beta
def minimax_alpha_beta(depth: int, alpha: float, beta: float, is_maximizing: bool, board: chess.Board) -> float:
    board_hash = zobrist_hash(board)

    if board_hash in transposition_table:
        return transposition_table[board_hash]

    if depth == 0 or board.is_game_over():
        score = evaluate_board(board)
        # score = quiescence(-999999, 999999, board)
        transposition_table[board_hash] = score
        return score

    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=board.turn != chess.BLACK)
    if is_maximizing:
        max_eval = -999999
        for move in moves:
            board.push(move)
            eval = minimax_alpha_beta(depth - 1, alpha, beta, False, board)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        transposition_table[board_hash] = max_eval
        return max_eval
    else:
        min_eval = 999999
        for move in moves:
            board.push(move)
            eval = minimax_alpha_beta(depth - 1, alpha, beta, True, board)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        transposition_table[board_hash] = min_eval
        return min_eval

# Função para obter o melhor movimento
def get_best_move(board: chess.Board, depth: int) -> Optional[chess.Move]:
    best_move = None
    best_score = -999999 if board.turn == chess.WHITE else 999999
    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=board.turn != chess.BLACK)
    for move in moves:
        board.push(move)
        score = minimax_alpha_beta(depth - 1, -999999, 999999, board.turn == chess.WHITE, board)
        board.pop()
        if score >= best_score if board.turn == chess.WHITE else score <= best_score:
            best_score = score
            best_move = move
    return best_move
