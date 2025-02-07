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
    """Avalia o valor de uma peça no tabuleiro, com ajustes para diferentes fases do jogo."""
    piece = board.piece_at(square)
    if not piece or piece.symbol().upper() == 'K':
        return 0

    value = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}[piece.symbol().upper()]

    # Considerar o valor de um peão no final do jogo
    if piece.piece_type == chess.PAWN and is_endgame(board):
        value = 1.12  # Mais valioso no final do jogo devido à possibilidade de promoção

    return value if piece.color == chess.WHITE else -value

# Improved king activity evaluation for endgame
def evaluate_king_activity(board):
    """Avalia a atividade do rei, considerando a segurança e proximidade ao centro no final do jogo."""
    king_square = board.king(chess.WHITE if board.turn == chess.WHITE else chess.BLACK)
    opponent_king_square = board.king(chess.BLACK if board.turn == chess.WHITE else chess.WHITE)
    center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
    
    # Distância do rei ao centro
    king_to_center = min(chess.square_distance(king_square, sq) for sq in center_squares)
    opponent_king_to_center = min(chess.square_distance(opponent_king_square, sq) for sq in center_squares)
    
    # Distância entre os reis
    distance_between_kings = chess.square_distance(king_square, opponent_king_square)
    
    # Reforçar a importância do rei estar mais próximo do centro no final do jogo
    if is_endgame(board):
        return ((opponent_king_to_center - king_to_center) - distance_between_kings) * 0.1
    else:
        return 0
    
# Function to flip the piece tables (inverting the values for black)
def get_flipped_table(piece):
    """Função para inverter as tabelas para peças negras"""
    table_key = piece.symbol().upper()
    # Flipping the table for black pieces
    flipped_table = piece_tables.get(table_key, [])
    if flipped_table:
        flipped_table = flipped_table[::-1]  # Reverse the table
    return flipped_table


def evaluate_positional(board):
    """Avalia a posição das peças no tabuleiro considerando diferentes fases do jogo."""
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue

        # Aplicar tabelas específicas para cada fase do jogo
        if is_endgame(board) and piece.piece_type == chess.KING:
            table = piece_tables['K_end']
        elif is_endgame(board) and piece.piece_type == chess.PAWN:
            table = piece_tables['P_end']
        else:
            table = piece_tables.get(piece.symbol().upper(), [])

        # Se a peça for preta, inverte a tabela
        if piece.color == chess.BLACK and table:
            table = table[::-1]  # Inverter a tabela para peças negras

        # Avaliar posição com base na tabela de peças
        if table:
            table_index = square  # O índice do quadrado no tabuleiro
            if piece.color == chess.WHITE:
                score += (table[table_index]) * 0.1
            else:
                score -= (table[table_index]) * 0.1

    return score

# Evaluate the board with improved evaluation logic
def evaluate_board(board):
    """Avalia a posição geral do tabuleiro, levando em consideração material e posição das peças."""
    if board.is_game_over():
        if board.is_checkmate():
            return float('inf') if board.turn == chess.BLACK else -float('inf')
        elif board.is_stalemate() or board.is_fivefold_repetition() or board.is_insufficient_material() or board.is_seventyfive_moves():
            return 0  # Empate

    # Avaliação material (soma do valor de todas as peças)
    material_score = sum(piece_value(board, square) for square in chess.SQUARES)
    
    # Avaliação posicional (considerando tabelas e a fase do jogo)
    positional_score = evaluate_positional(board)
    
    # Avaliação da atividade do rei no final do jogo
    king_activity_score = evaluate_king_activity(board)

    return material_score + positional_score + king_activity_score

# Refined move priority function
def move_priority(board, move):
    """Função de prioridade de movimento, considerando xeque, captura e ataques"""
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
    """Busca quiescente com poda alfa-beta"""
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
    """Função minimax com poda alfa-beta e movimentos ordenados"""
    board_hash = zobrist_hash(board)

    # Checar se o valor da posição já está na tabela de transposição
    if board_hash in transposition_table:
        return transposition_table[board_hash]

    if depth == 0 or board.is_game_over():
        score = evaluate_board(board)  # Usar a função de avaliação refinada
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
    """Obter o melhor movimento para a IA considerando a profundidade e avaliação do tabuleiro"""
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
