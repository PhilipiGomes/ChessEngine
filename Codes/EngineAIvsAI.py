import random
from typing import Dict, List, Optional, Tuple

import chess
from chess.polyglot import zobrist_hash
from Openings import openings
from Tables import piece_tables

MATE_SCORE = 100000


# Select a random opening
def select_random_opening(ope: Dict[str, List[str]]) -> Optional[Tuple[str, List[str]]]:
    if not ope:
        print("No openings available.")
        return None
    # trunk-ignore(bandit/B311)
    return random.choice(list(ope.items()))


# Filter openings based on the current sequence of moves
def filter_openings(
    op: Dict[str, List[str]], sequence: List[str]
) -> Dict[str, List[str]]:
    if sequence:
        filtered_openings = {}
        for opening, moves in op.items():
            if moves[: len(sequence)] == sequence and (
                len(moves) > len(sequence) if len(sequence) > 0 else True
            ):
                filtered_openings[opening] = moves
        return filtered_openings
    else:
        return op


# Determine if the game is in the endgame
def is_endgame(board: chess.Board) -> bool:
    piece_map = board.piece_map()
    minor_pieces = sum(
        1 for p in piece_map.values() if p.piece_type in {chess.BISHOP, chess.KNIGHT}
    )
    major_pieces = sum(
        1 for p in piece_map.values() if p.piece_type in {chess.ROOK, chess.QUEEN}
    )
    return major_pieces <= 1 or (major_pieces == 2 and minor_pieces < 3)


# Avaliação do valor de uma peça com base na posição no tabuleiro
def piece_value(board: chess.Board, square: chess.Square) -> float:
    piece = board.piece_at(square)
    if not piece or piece.symbol().upper() == "K":
        return 0
    value = {"P": 1, "N": 3, "B": 3.2, "R": 5, "Q": 9}[piece.symbol().upper()]
    return value if piece.color == chess.WHITE else -value


def endgame_eval(
    friendly_king_square: int,
    enemy_king_square: int,
    endgame_weight: float,
    is_white: bool,
) -> float:
    # Encourage the friendly king to approach the enemy king and push the enemy king to the edge
    eval_score = 0

    # Distance of enemy king from center (encourage pushing to edge)
    enemy_file = chess.square_file(enemy_king_square)
    enemy_rank = chess.square_rank(enemy_king_square)
    center_files = [3, 4]
    center_ranks = [3, 4]
    dist_from_center = min(abs(enemy_file - c) for c in center_files) + min(
        abs(enemy_rank - c) for c in center_ranks
    )
    eval_score += dist_from_center

    # Distance between kings (encourage friendly king to approach)
    king_distance = chess.square_manhattan_distance(
        friendly_king_square, enemy_king_square
    )
    eval_score += (14 - king_distance) * 5  # 14 is max manhattan distance on 8x8

    # For black, invert the sign so that positive is good for white, negative for black
    return eval_score * endgame_weight if is_white else -eval_score * endgame_weight


def evaluate_board(board: chess.Board) -> float:
    # Piece values
    values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3.2,
        chess.ROOK: 5,
        chess.QUEEN: 9,
    }
    evaluation = 0.0

    # Game over checks
    if board.is_game_over():
        if board.is_checkmate():
            return -MATE_SCORE if board.turn else MATE_SCORE
        else:
            return 0.0

    # Material and positional evaluation
    white_material = 0.0
    black_material = 0.0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece or piece.piece_type == chess.KING:
            continue
        value = values.get(piece.piece_type, 0)
        if piece.color == chess.WHITE:
            white_material += value
        else:
            black_material += value

    # Remove pawns for endgame weighting
    white_no_pawns = white_material - sum(
        values[chess.PAWN]
        for sq in chess.SQUARES
        if (p := board.piece_at(sq))
        and p.color == chess.WHITE
        and p.piece_type == chess.PAWN
    )
    black_no_pawns = black_material - sum(
        values[chess.PAWN]
        for sq in chess.SQUARES
        if (p := board.piece_at(sq))
        and p.color == chess.BLACK
        and p.piece_type == chess.PAWN
    )

    # Endgame weight calculation
    endgame_material_start = (
        values[chess.ROOK] * 2 + values[chess.BISHOP] + values[chess.KNIGHT]
    )

    def endgame_weight(material_no_pawns: float) -> float:
        return (
            1 - min(1, material_no_pawns / endgame_material_start)
            if endgame_material_start > 0
            else 1
        )

    endgame_weight_white = endgame_weight(white_no_pawns)
    endgame_weight_black = endgame_weight(black_no_pawns)

    # Material and positional score
    material_score = white_material - black_material
    positional_score = evaluate_positional(board)
    evaluation += material_score + positional_score

    # Endgame evaluation if appropriate
    if is_endgame(board):
        wk = board.king(chess.WHITE)
        bk = board.king(chess.BLACK)
        if wk is not None and bk is not None:
            evaluation += endgame_eval(wk, bk, endgame_weight_white, True)
            evaluation += endgame_eval(bk, wk, endgame_weight_black, False)

    return evaluation


# Function to get the correct index for piece-square tables based on color
def get_table_index(square: int, color: bool) -> int:
    # For white, flip the square vertically to match the table orientation
    return square if color == chess.WHITE else chess.square_mirror(square)


# Função que avalia a posição das peças com base nas tabelas
def evaluate_positional(board: chess.Board) -> float:
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue
        if is_endgame(board) and piece.piece_type == chess.KING:
            table = piece_tables["K_end"]
        elif is_endgame(board) and piece.piece_type == chess.PAWN:
            table = piece_tables["P_end"]
        else:
            table = piece_tables.get(piece.symbol().upper())

        if table:
            table_index = get_table_index(square, piece.color)
            if piece.color == chess.WHITE:
                score += table[table_index]
            else:
                score -= table[table_index]
    return score


def piece_value_type(piece: Optional[chess.Piece]) -> float:
    if not piece or piece == chess.KING:
        return 0
    value = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3.2,
        chess.ROOK: 5,
        chess.QUEEN: 9,
    }
    return (
        value.get(piece.piece_type, 0)
        if piece.color == chess.WHITE
        else -value.get(piece.piece_type, 0)
    )


# Refined move priority function
def move_priority(board: chess.Board, move: chess.Move) -> float:
    guess = 0
    values = {
        chess.PAWN: 1,
        chess.KNIGHT: 2.8,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0,
    }
    attacker = board.piece_at(move.from_square)
    victim = board.piece_at(move.to_square)

    if board.is_capture(move):
        guess = 0.1 * (piece_value_type(victim) - piece_value_type(attacker))
    if bool(move.promotion):
        promo_value = values.get(move.promotion, 0)
        guess += promo_value if board.turn == chess.WHITE else -promo_value
    if board.is_attacked_by(not board.turn, move.to_square):
        guess -= piece_value_type(attacker)
    if board.gives_check(move):
        guess += 10

    return guess


# Quiescence search with more tactical depth
def quiescence(alpha: float, beta: float, board: chess.Board) -> float:
    stand_pat = evaluate_board(board)

    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat
    # Only consider capture moves and checks
    capture_moves = [
        m for m in board.legal_moves if board.is_capture(m) or board.gives_check(m)
    ]
    moves = sorted(
        capture_moves,
        key=lambda m: move_priority(board, m),
        reverse=board.turn != chess.BLACK,
    )
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
def minimax_alpha_beta(
    depth: int,
    alpha: float,
    beta: float,
    is_maximizing: bool,
    board: chess.Board,
    transposition_table: Dict[int, float],
    max_depth: int,
) -> float:
    board_hash = zobrist_hash(board)
    transpos_table = transposition_table

    if board_hash in transposition_table:
        return transposition_table[board_hash]

    if depth == 0 or board.is_game_over():
        # score = evaluate_board(board)
        score = quiescence(-MATE_SCORE, MATE_SCORE, board)
        if board.is_game_over():
            score += (
                -(depth - max_depth) * 10
                if board.turn == chess.BLACK
                else (depth - max_depth) * 10
            )
        transposition_table[board_hash] = score
        return score

    moves = sorted(
        board.legal_moves,
        key=lambda m: move_priority(board, m),
        reverse=board.turn == chess.BLACK,
    )
    if is_maximizing:
        max_eval = -MATE_SCORE
        for move in moves:
            board.push(move)
            eval = minimax_alpha_beta(
                depth - 1, alpha, beta, False, board, transpos_table, max_depth
            )
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        transposition_table[board_hash] = max_eval
        return max_eval
    else:
        min_eval = MATE_SCORE
        for move in moves:
            board.push(move)
            eval = minimax_alpha_beta(
                depth - 1, alpha, beta, True, board, transpos_table, max_depth
            )
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        transposition_table[board_hash] = min_eval
        return min_eval


openings_names: List[str] = []
seq_with_move: List[str] = []


# Get the best move for the AI
def get_best_move(
    board: chess.Board,
    depth: int,
    sequence: List[str],
    transpositon_table: Dict[int, float],
) -> Optional[chess.Move]:
    if sequence or board.fen() == chess.STARTING_FEN:
        filtered_openings = filter_openings(openings, sequence)
        if filtered_openings:
            seq_with_move = sequence.copy()
            # trunk-ignore(bandit/B311)
            opening = random.choice(list(filtered_openings.items()))
            try:
                move = opening[1][len(sequence)]
            except IndexError:
                print("Opening move index out of range.")
                move = None
            if move:
                seq_with_move.append(move)
                opening_name = "Unknown Opening"
                for name, moves in filtered_openings.items():
                    if seq_with_move == moves:
                        opening_name = name
                        openings_names.append(name)
                        break
                    else:
                        opening_name = (
                            openings_names[-1] if openings_names else "Unknown Opening"
                        )
                print(board.san(board.parse_san(san=move)), opening_name)
                return chess.Move.from_uci(board.parse_san(san=move).uci())
            else:
                print("No move found in opening book.")

    moves = sorted(
        board.legal_moves,
        key=lambda m: move_priority(board, m),
        reverse=board.turn == chess.BLACK,
    )
    best_move: Optional[chess.Move] = moves[0]
    best_score = -MATE_SCORE if board.turn == chess.WHITE else MATE_SCORE
    for move in moves:
        board.push(move)
        score = minimax_alpha_beta(
            depth - 1,
            -MATE_SCORE,
            MATE_SCORE,
            board.turn == chess.WHITE,
            board,
            transpositon_table,
            depth,
        )
        board.pop()
        if score >= best_score if board.turn == chess.WHITE else score <= best_score:
            best_score = score
            best_move = move
    if len(moves) == 1:
        best_move = moves[0]
    return best_move, best_score
