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
    value = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}[piece.symbol().upper()]
    return value if piece.color == chess.WHITE else -value

# Improved king activity evaluation for endgame
def evaluate_king_activity(board):
    king_square = board.king(chess.WHITE if board.turn == chess.WHITE else chess.BLACK)
    opponent_king_square = board.king(chess.BLACK if board.turn == chess.WHITE else chess.WHITE)
    center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
    king_to_center = min(chess.square_distance(king_square, sq) for sq in center_squares)
    opponent_king_to_center = min(chess.square_distance(opponent_king_square, sq) for sq in center_squares)
    distance_between_kings = chess.square_distance(king_square, opponent_king_square)
    return ((opponent_king_to_center - king_to_center) - distance_between_kings) * 0.1

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

# Function to flip the piece tables (inverting the values for black)
def get_flipped_table(piece):
    table_key = piece.symbol().upper()
    # Flipping the table for black pieces
    flipped_table = piece_tables.get(table_key, [])
    if flipped_table:
        flipped_table = flipped_table[::-1]  # Reverse the table
    return flipped_table


def evaluate_positional(board):
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue

        # Apply specific tables for each phase of the game
        if is_endgame(board) and piece.piece_type == chess.KING:
            table = piece_tables['K_end']
        elif is_endgame(board) and piece.piece_type == chess.PAWN:
            table = piece_tables['P_end']
        else:
            table = piece_tables.get(piece.symbol().upper())

        # Flip the table for black pieces
        if piece.color == chess.BLACK:
            table = get_flipped_table(piece)

        # Ensure that 'square' is correctly transformed into a valid index for the piece table
        if table:
            table_index = square  # Convert the square index to the corresponding table index
            if piece.color == chess.WHITE:
                score += (table[table_index]) * 0.1
            else:
                score -= (table[table_index]) * 0.1
        
    return score

# Refined move priority function
def move_priority(board, move):
    if board.gives_check(move):
        return 13
    elif board.is_capture(move):
        attacker = board.piece_at(move.from_square)
        victim = board.piece_at(move.to_square)
        victim_value = piece_value(board, move.to_square) if victim else 0
        attacker_value = piece_value(board, move.from_square) if attacker else 0
        return 3 + (victim_value - attacker_value)
    elif board.is_attacked_by(not board.turn, move.to_square):
        return 2
    return 1

# Quiescence search with more tactical depth
def quiescence(alpha, beta, board):
    # Avaliação da posição no estado atual
    stand_pat = evaluate_board(board)
    
    # Poda alfa-beta
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    # Ordenando os movimentos por prioridade
    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=True)
    
    # Itera sobre os movimentos para realizar a busca quiescente
    for move in moves:
        # Apenas movimentos que são captura ou xeque são considerados
        if board.is_capture(move) or board.gives_check(move):
            board.push(move)
            # Busca recursiva quiescente
            score = -quiescence(-beta, -alpha, board)
            board.pop()

            # Verificação de poda alfa-beta
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
        # score = quiescence(alpha, beta, board)
        score = evaluate_board(board)
        transposition_table[board_hash] = score
        return score

    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=is_maximizing)
    if is_maximizing:
        max_eval = -float('inf')
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
        min_eval = float('inf')
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


# Get the best move for the AI
def get_best_move(board, depth):
    best_move = None
    best_score = -float('inf') if board.turn == chess.WHITE else float('inf')
    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=board.turn == chess.BLACK)
    for move in moves:
        board.push(move)
        score = minimax_alpha_beta(depth - 1, -float('inf'), float('inf'), False, board)
        board.pop()
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
