import chess
import random
from chess.polyglot import zobrist_hash
import neat
import pickle
from Openings import openings


# Select a random opening
def select_random_opening(ope):
    if not ope:
        print("No openings available.")
        return None
    return random.choice(list(ope.items()))

# Filter openings based on the current sequence of moves
def filter_openings(op, sequence):
    if sequence:
        filtered_openings = {}
        for opening, moves in op.items():
            if moves[:len(sequence)] == sequence and (len(moves) > len(sequence) if len(sequence) > 0 else 1 == 1):
                filtered_openings[opening] = moves
        return filtered_openings
    else:
        return op

# Determine if the game is in the endgame
def is_endgame(board):
    piece_map = board.piece_map()
    minor_pieces = sum(1 for p in piece_map.values() if p.piece_type in {chess.BISHOP, chess.KNIGHT})
    major_pieces = sum(1 for p in piece_map.values() if p.piece_type in {chess.ROOK, chess.QUEEN})
    return major_pieces <= 1 or (major_pieces == 2 and minor_pieces < 3)

# Avaliação do valor de uma peça com base na posição no tabuleiro
def piece_value(board, square):
    piece = board.piece_at(square)
    if not piece or piece.symbol().upper() == 'K':
        return 0
    value = {'P': 1, 'N': 2.8, 'B': 3, 'R': 5, 'Q': 9}[piece.symbol().upper()]
    return value if piece.color == chess.WHITE else -value

# Função para converter o tabuleiro em entrada para a rede NEAT
def board_to_input(board):
    """Convert a chess board to a 64-element input array"""
    PIECE_VALUES = {'P': 1, 'N': 2.8, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    board_list = [0] * 64  # Initialize with empty squares
    for square, piece in board.piece_map().items():  # Iterate over occupied squares
        value = PIECE_VALUES[piece.symbol().upper()]
        board_list[square] = value if piece.symbol().isupper() else -value
    return board_list

# Função para carregar os pesos pré-treinados da rede neural
def load_neat_weights():
    try:
        with open("best_weights.pkl", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        raise ValueError("No trained weights found. Train the network first.")

# Função para avaliar o tabuleiro usando o NEAT
def evaluate_board(board, net):
    X = board_to_input(board)  # A entrada para a rede neural
    output = net.activate(X)  # Usar o método 'activate' da rede FeedForward
    return output[0]

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
def quiescence(alpha, beta, board, net):
    stand_pat = evaluate_board(board, net)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=board.turn == chess.BLACK)
    for move in moves:
        if board.is_capture(move) or board.gives_check(move):
            board.push(move)
            score = -quiescence(-beta, -alpha, board, net)
            board.pop()
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
    return alpha

# Função principal de busca Minimax com poda alfa-beta
def minimax_alpha_beta(depth, alpha, beta, is_maximizing, board, transposition_table, net):
    board_hash = zobrist_hash(board)

    if board_hash in transposition_table:
        return transposition_table[board_hash]

    if depth == 0 or board.is_game_over():
        score = evaluate_board(board, net)
        transposition_table[board_hash] = score
        return score

    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=board.turn == chess.BLACK)
    if is_maximizing:
        max_eval = -float('inf')
        for move in moves:
            board.push(move)
            eval = minimax_alpha_beta(depth - 1, alpha, beta, False, board, transposition_table, net)
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
            eval = minimax_alpha_beta(depth - 1, alpha, beta, True, board, transposition_table, net)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        transposition_table[board_hash] = min_eval
        return min_eval

# Get the best move for the AI
def get_best_move(board, depth, sequence, transpositon_table):
    # Carregar a configuração e a população NEAT
    config_path = "config-feedforward.txt"  # Caminho para o arquivo de configuração do NEAT
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)
    p = neat.Population(config)

    # A rede neural FeedForward que faz a avaliação
    best_genome = p.best_genome
    net = best_genome.net  # Aqui é que obtemos a rede FeedForward do genoma

    if sequence or board.fen() == chess.STARTING_FEN:
        filtered_openings = filter_openings(openings, sequence)
        if filtered_openings:
            opening = random.choice(list(filtered_openings.items()))
            if opening[0] == "Barnes Opening: Fool's Mate":
                if random.randint(1, 1000) == random.randint(1, 1000):
                    pass
                else:
                    opening = random.choice(list(filtered_openings.items()))
            move = opening[1][len(sequence)]
            return chess.Move.from_uci(board.parse_san(san=move).uci())

    best_move = None
    best_score = -float('inf') if board.turn == chess.WHITE else float('inf')
    moves = sorted(board.legal_moves, key=lambda m: move_priority(board, m), reverse=board.turn == chess.BLACK)
    for move in moves:
        board.push(move)
        score = minimax_alpha_beta(depth - 1, -float('inf'), float('inf'), board.turn == chess.WHITE, board,
                                   transpositon_table, net)
        board.pop()
        if score >= best_score if board.turn == chess.WHITE else score <= best_score:
            best_score = score
            best_move = move
    return best_move
