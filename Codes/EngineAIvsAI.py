import chess
import random
from chess.polyglot import zobrist_hash
from Tables import piece_tables
from Openings import openings


# Filter openings based on the current sequence of moves
def filter_openings(op: dict, sequence: list) -> dict:
    if sequence:
        filtered_openings = {}
        for opening, moves in op.items():
            if moves[:len(sequence)] == sequence and (len(moves) > len(sequence) if len(sequence) > 0 else True):
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
def piece_value(board: chess.Board, square: chess.Square) -> float:
    piece = board.piece_at(square)
    if not piece or piece.symbol().upper() == 'K':
        return 0
    value = {'P': 1, 'N': 2.8, 'B': 3, 'R': 5, 'Q': 9}[piece.symbol().upper()]
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

# Function to flip the piece tables (inverting the values for black)
def get_flipped_table(piece: chess.Piece) -> list:
    table_key = piece.symbol().upper()
    # Flipping the table for black pieces
    flipped_table = piece_tables.get(table_key, [])
    if flipped_table:
        flipped_table = flipped_table[::-1]  # Reverse the table
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

# Refined move priority function
def move_priority(board: chess.Board, move: chess.Move) -> float:
    if board.gives_check(move):
        return 4
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
def quiescence(alpha: float, beta: float, board: chess.Board) -> float:
    stand_pat = evaluate_board(board)
    
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=board.turn == chess.BLACK)
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

# Função principal de busca Minimax com poda alfa-beta
def minimax_alpha_beta(depth: int, alpha: float, beta: float, is_maximizing: bool, board: chess.Board, transposition_table: dict, max_depth: int) -> float:
    board_hash = zobrist_hash(board)
    transpos_table = transposition_table

    if board_hash in transposition_table:
        return transposition_table[board_hash]

    if depth == 0 or board.is_game_over():
        score = evaluate_board(board)
        if board.is_game_over():
            score += -(depth - max_depth)*10 if board.turn == chess.BLACK else (depth - max_depth)*10
        # score = quiescence(-999999, 999999, board)
        transposition_table[board_hash] = score
        return score

    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=board.turn == chess.BLACK)
    if is_maximizing:
        max_eval = -999999
        for move in moves:
            board.push(move)
            eval = minimax_alpha_beta(depth - 1, alpha, beta, False, board, transpos_table, max_depth)
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
            eval = minimax_alpha_beta(depth - 1, alpha, beta, True, board, transpos_table, max_depth)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        transposition_table[board_hash] = min_eval
        return min_eval


openings_names = []
seq_with_move = []

# Get the best move for the AI
def get_best_move(board: chess.Board, depth: int, sequence: list, transpositon_table: dict) -> chess.Move:
    if sequence or board.fen() == chess.STARTING_FEN:
        filtered_openings = filter_openings(openings, sequence)
        if filtered_openings:
            seq_with_move = sequence.copy()
            opening = random.choice(list(filtered_openings.items()))
            if opening[0] == "Barnes Opening: Fool's Mate" or opening[0] == "Scotch Game: Sea-Cadet Mate":
                if random.randint(1,1000) == random.randint(1,1000):
                    pass
                else:
                    opening = random.choice(list(filtered_openings.items()))
            move = opening[1][len(sequence)]
            seq_with_move.append(move)
            for name, moves in filtered_openings.items():
                if seq_with_move == moves:
                    opening_name = name
                    openings_names.append(name)
                    break
                else:
                    opening_name = openings_names[-1] if openings_names else "Unknown Opening"
            print(board.san(board.parse_san(san=move)), opening_name)
            return chess.Move.from_uci(board.parse_san(san=move).uci())

    best_move = None
    best_score = -999999 if board.turn == chess.WHITE else 999999
    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=board.turn == chess.BLACK)
    for move in moves:
        board.push(move)
        score = minimax_alpha_beta(depth - 1, -999999, 999999, board.turn == chess.WHITE, board, transpositon_table, depth)
        board.pop()
        if score >= best_score if board.turn == chess.WHITE else score <= best_score:
            best_score = score
            best_move = move
    print(board.san(best_move), round(best_score, 5), "white" if board.turn else "black")
    return best_move
