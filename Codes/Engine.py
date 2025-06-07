import chess
import random
from chess.polyglot import zobrist_hash
from Tables import piece_tables
from Openings import openings
from typing import Dict, List, Tuple, Optional, Any

transposition_table: Dict[int, float] = {}

# Select a random opening
def select_random_opening(ope: Dict[str, List[str]]) -> Optional[Tuple[str, List[str]]]:
    if not ope:
        print("No openings available.")
        return None
    return random.choice(list(ope.items()))

# Filter openings based on the current sequence of moves
def filter_openings(op: Dict[str, List[str]], sequence: List[str]) -> Dict[str, List[str]]:
    if sequence:
        filtered_openings = {}
        for opening, moves in op.items():
            if moves[:len(sequence)] == sequence and (len(moves) > len(sequence) if len(sequence) > 0 else 1 == 1):
                filtered_openings[opening] = moves
        return filtered_openings
    else:
        return op

# Determine if the game is in the endgame
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
    value = {'P': 1, 'N': 3, 'B': 3.2, 'R': 5, 'Q': 9}[piece.symbol().upper()]
    return value if piece.color == chess.WHITE else -value

# Evaluate the board with improved evaluation logic
def evaluate_board(board: chess.Board) -> float:
    if board.is_game_over():
        if board.is_checkmate():
            return 999999 if board.turn == chess.BLACK else -999999
        elif board.is_stalemate() or board.is_fivefold_repetition() or board.is_insufficient_material() or board.is_seventyfive_moves():
            return 0

    material_score = sum(piece_value(board, square) for square in chess.SQUARES)
    positional_score = evaluate_positional(board)
    return material_score + positional_score

# Function to get the correct index for piece-square tables based on color
def get_table_index(square: int, color: bool) -> int:
    # For white, flip the square vertically to match the table orientation
    return square if color == chess.WHITE else chess.square_mirror(square)

# Function that evaluates the position of pieces based on piece-square tables
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

        if table:
            table_index = get_table_index(square, piece.color)
            if piece.color == chess.WHITE:
                score += table[table_index]
            else:
                score -= table[table_index]
    return score

# Refined move priority function
def move_priority(board: chess.Board, move: chess.Move) -> float:
    def piece_value_type(piece):
        if not piece or piece.symbol().upper() == 'K':
            return 0
        value = {'P': 1, 'N': 3, 'B': 3.2, 'R': 5, 'Q': 9}[piece.symbol().upper()]
        return value if piece.color == chess.WHITE else -value

    guess = 0
    values = {chess.PAWN: 1, chess.KNIGHT: 2.8, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
    attacker = board.piece_at(move.from_square)
    victim = board.piece_at(move.to_square)

    if board.is_capture(move):
        guess = 10 * (piece_value_type(victim) - piece_value_type(attacker))
    if bool(move.promotion):
        promo_value = values[move.promotion]
        guess += promo_value if board.turn == chess.WHITE else -promo_value
    if board.is_attacked_by(not board.turn, move.to_square):
        guess -= piece_value_type(attacker) if board.turn == chess.WHITE else -piece_value_type(attacker)
    
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
def minimax_alpha_beta(depth: int, alpha: float, beta: float, is_maximizing: bool, board: chess.Board, max_depth: int) -> float:
    board_hash = zobrist_hash(board)

    if board_hash in transposition_table:
        return transposition_table[board_hash]

    if depth == 0 or board.is_game_over():
        score = evaluate_board(board)
        if board.is_game_over():
            score += -(depth - max_depth)*10 if board.turn == chess.BLACK else (depth - max_depth)*10
        # score = quiescence(-999999, 999999, board)
        transposition_table[board_hash] = score
        return score

    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=board.turn != chess.BLACK)
    if is_maximizing:
        max_eval = -999999
        for move in moves:
            board.push(move)
            eval = minimax_alpha_beta(depth - 1, alpha, beta, False, board, max_depth)
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
            eval = minimax_alpha_beta(depth - 1, alpha, beta, True, board, max_depth)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        transposition_table[board_hash] = min_eval
        return min_eval


# Get the best move for the AI
def get_best_move(board: chess.Board, depth: int, sequence: List[str]) -> Optional[chess.Move]:
    if sequence or board.fen() == chess.STARTING_FEN:
        filtered_openings = filter_openings(openings, sequence)
        if filtered_openings:
            opening = random.choice(list(filtered_openings.items()))
            if opening[0] == "Barnes Opening: Fool's Mate":
                if random.randint(1,1000) == random.randint(1,1000):
                    pass
                else:
                    opening = random.choice(list(filtered_openings.items()))
            move = opening[1][len(sequence)]
            return chess.Move.from_uci(board.parse_san(san=move).uci())

    best_move = None
    best_score = -999999 if board.turn == chess.WHITE else 999999
    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=board.turn != chess.BLACK)
    for move in moves:
        board.push(move)
        score = minimax_alpha_beta(depth - 1, -999999, 999999, board.turn == chess.WHITE, board, depth)
        board.pop()
        if score >= best_score if board.turn == chess.WHITE else score <= best_score:
            best_score = score
            best_move = move
    return best_move
