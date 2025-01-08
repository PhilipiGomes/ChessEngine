import chess
import random
from chess.polyglot import zobrist_hash
from Tables import piece_tables
from Openings import openings

# Initialize the transposition table
transposition_table = {}

# Select a random opening
def select_random_opening(openings):
    if not openings:
        print("No openings available.")
        return None
    return random.choice(list(openings.items()))

# Filter openings based on the current sequence of moves
def filter_openings_by_sequence(openings, sequence):
    filtered_openings = {}
    for opening, moves in openings.items():
        if moves[:len(sequence)] == sequence and (len(moves) > len(sequence) if len(sequence) > 0 else 1 == 1):
            filtered_openings[opening] = moves
    return filtered_openings

# Execute the first move of an opening and return the new list of openings
def execute_opening_moves(opening, board):
    if not opening:
        return None
    move = opening[1][len(board.move_stack)]
    board.push_san(move)
    return board

# Determine if the game is in the endgame
def is_endgame(board):
    piece_map = board.piece_map()
    minor_pieces = sum(1 for p in piece_map.values() if p.piece_type in {chess.BISHOP, chess.KNIGHT})
    queens = sum(1 for p in piece_map.values() if p.piece_type == chess.QUEEN)
    return queens == 0 or (queens == 1 and minor_pieces < 3)

# Endgame evaluation
def endgame_eval(board):
    material_score = sum(piece_value(board, square) for square in chess.SQUARES)
    king_dist_penalty = evaluate_king_activity(board)
    return material_score - king_dist_penalty

# Helper to evaluate pieces
def piece_value(board, square):
    piece = board.piece_at(square)
    if not piece:
        return 0
    value = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}[piece.symbol().upper()]
    return value if piece.color == chess.WHITE else -value

# Evaluate king activity
def evaluate_king_activity(board):
    king_squares = [
        square for square in chess.SQUARES
        if board.piece_at(square).piece_type == chess.KING
    ]
    dist = chess.square_distance(*king_squares)
    return dist * 0.1

# Evaluate the board (similar to previous implementation)
def evaluate_board(board):
    if board.is_game_over():
        if board.is_checkmate():
            return float('inf') if board.turn == chess.BLACK else -float('inf')
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

        # Verifica se a peça está no final de jogo e ajusta a tabela de peças
        if is_endgame(board) and piece.piece_type == chess.KING:
            table = piece_tables['K_end']  # Tabela do Rei no final de jogo
        else:
            # Acessa a tabela específica da peça, utilizando o tipo da peça
            table = piece_tables.get(piece.symbol().upper())

        # Se a peça for branca, somamos, caso contrário, subtraímos (espelhando a tabela para peças negras)
        if piece.color == chess.WHITE:
            score += table[square]  # Acessa o valor da tabela para a posição
        else:
            score -= table[square]  # Para peças negras, subtraímos na posição refletida

    return score



# Function to rank moves for ordering
def move_priority(board, move):
    if board.gives_check(move):
        return 3
    elif board.is_capture(move):
        attacker = board.piece_at(move.from_square)
        victim = board.piece_at(move.to_square)
        victim_value = piece_value(board, move.to_square) if victim else 0
        attacker_value = piece_value(board, move.from_square) if attacker else 0
        return 2 + victim_value - attacker_value
    return 1

# Quiescence search with ordered moves
def quiescence(depth, alpha, beta, board):
    stand_pat = evaluate_board(board)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=True)
    for move in moves:
        if board.is_capture(move):
            board.push(move)
            score = -quiescence(depth - 1,-beta, -alpha, board)
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

    if board.is_game_over():
        score = evaluate_board(board)
        transposition_table[board_hash] = score
        return score

    if depth == 0:
        score = quiescence(depth, alpha, beta, board)
        transposition_table[board_hash] = score
        return score

    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=True)

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
def get_best_move(board, depth, moves):
    filtered_openings = filter_openings_by_sequence(openings, moves)
    if filtered_openings:
        opening = random.choice(list(filtered_openings.items()))
        move = opening[1][len(moves)]
        return chess.Move.uci(board.parse_san(san=move))

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
    return best_move
