import chess
import random
from chess.polyglot import zobrist_hash
from Tables import piece_tables


transposition_table = {}

# Determine if the game is in the endgame
def is_endgame(board):
    piece_map = board.piece_map()
    minor_pieces = sum(1 for p in piece_map.values() if p.piece_type in {chess.BISHOP, chess.KNIGHT})
    major_pieces = sum(1 for p in piece_map.values() if p.piece_type in {chess.ROOK, chess.QUEEN})
    return major_pieces <= 1 or (major_pieces == 2 and minor_pieces < 3)

# Evaluate pieces with refined values and mobility
def piece_value(board, square):
    piece = board.piece_at(square)
    if not piece:
        return 0
    value = {'P': 1, 'N': 2.8, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}[piece.symbol().upper()]
    mobility = len(list(board.attacks(square))) * 0.1
    return (value + mobility) if piece.color == chess.WHITE else -(value + mobility)

# Improved king activity evaluation for endgame
def evaluate_king_activity(board):
    king_square = board.king(chess.WHITE if board.turn == chess.WHITE else chess.BLACK)
    opponent_king_square = board.king(chess.BLACK if board.turn == chess.WHITE else chess.WHITE)
    center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
    king_to_center = min(chess.square_distance(king_square, sq) for sq in center_squares)
    opponent_king_to_center = min(chess.square_distance(opponent_king_square, sq) for sq in center_squares)
    return (opponent_king_to_center - king_to_center) * 0.1

# Evaluate the board with improved evaluation logic
def evaluate_board(board):
    if board.is_game_over():
        if board.is_checkmate():
            return float('inf') if board.turn == chess.BLACK else -float('inf')
        elif board.is_stalemate() or board.is_fivefold_repetition() or board.is_insufficient_material() or board.is_seventyfive_moves():
            return 0

    material_score = sum(piece_value(board, square) for square in chess.SQUARES)
    positional_score = evaluate_positional(board)
    return material_score + positional_score

def evaluate_positional(board):
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue

        # Apply specific tables for each phase of the game
        if is_endgame(board) and piece.piece_type == chess.KING:
            table = piece_tables['K_end']
        else:
            table = piece_tables.get(piece.symbol().upper())

        if piece.color == chess.WHITE:
            score += table[square]
        else:
            score -= table[square]
    return score

# Refined move priority function
def move_priority(board, move):
    if board.gives_check(move):
        return 4
    elif board.is_capture(move):
        attacker = board.piece_at(move.from_square)
        victim = board.piece_at(move.to_square)
        victim_value = piece_value(board, move.to_square) if victim else 0
        attacker_value = piece_value(board, move.from_square) if attacker else 0
        return 3 + victim_value - attacker_value
    elif board.is_attacked_by(not board.turn, move.to_square):
        return 2
    return 1

# Quiescence search with more tactical depth
def quiescence(alpha, beta, board):
    stand_pat = evaluate_board(board)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=True)
    for move in moves:
        if board.is_capture(move) or board.gives_check(move):
            board.push(move)
            score = -quiescence(-beta, -alpha, board)
            board.pop()
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
    return alpha


# Minimax with alpha-beta pruning and ordered moves
def minimax_alpha_beta(depth, alpha, beta, is_maximizing, board):
    board_hash = zobrist_hash(board)

    if board_hash in transposition_table:
        return transposition_table[board_hash]

    if depth == 0 or board.is_game_over():
        score = quiescence(alpha, beta, board)
        transposition_table[board_hash] = score
        return score

    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=True)
    if is_maximizing:
        max_eval = -float('inf')
        for move in moves:
            board.push(move)
            random_value = random.random()
            random_value *= -1 if random.random() < 0.5 else 1
            eval = minimax_alpha_beta(depth - 1, alpha, beta, False, board) + random_value
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        transposition_table[board_hash] = max_eval
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            board.push(move)
            random_value = random.random()
            random_value *= -1 if random.random() < 0.5 else 1
            eval = minimax_alpha_beta(depth - 1, alpha, beta, True, board) + random_value
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        transposition_table[board_hash] = min_eval
        return min_eval


# Get the best move for the AI
def get_best_move(board, depth):
    best_move = None
    best_score = -float('inf')
    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=True)
    for move in moves:
        board.push(move)
        score = minimax_alpha_beta(depth - 1, -float('inf'), float('inf'), False, board)
        board.pop()
        if score > best_score:
            best_score = score
            best_move = move
    return best_move, best_score
