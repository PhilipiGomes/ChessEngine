import chess
import random
from chess.polyglot import zobrist_hash
from Tables import piece_tables, manhattan_distance_king
from Openings import openings
from typing import Dict, List, Tuple, Optional


class ChessEngine:
    def __init__(self, board: chess.Board, depth: int, color: bool, transposition_table: Dict[int, float]):
        self.board = board
        self.depth = depth
        self.color = color  # chess.WHITE or chess.BLACK
        self.transposition_table = transposition_table

    def select_random_opening(self, ope: Dict[str, List[str]]) -> Optional[Tuple[str, List[str]]]:
        if not ope:
            print("No openings available.")
            return None
        return random.choice(list(ope.items()))

    def filter_openings(self, op: Dict[str, List[str]], sequence: List[str]) -> Dict[str, List[str]]:
        if sequence:
            filtered_openings: Dict[str, List[str]] = {}
            for opening_name, moves in op.items():
                if moves[:len(sequence)] == sequence and (len(moves) > len(sequence) if len(sequence) > 0 else True):
                    filtered_openings[opening_name] = moves
            return filtered_openings
        else:
            return op

    def is_endgame(self) -> bool:
        piece_map = self.board.piece_map()
        minor_pieces = sum(
            1 for p in piece_map.values() if p.piece_type in {chess.BISHOP, chess.KNIGHT}
        )
        queens = sum(
            1 for p in piece_map.values() if p.piece_type == chess.QUEEN
        )
        major_pieces = sum(
            1 for p in piece_map.values() if p.piece.type == chess.ROOK
        )
        return queens == 0 or major_pieces <= 1 or (major_pieces == 2 and minor_pieces < 3)

    def piece_value_type(piece):
        if not piece or piece.symbol().upper() == 'K':
            return 0.0
        v = {'P': 1, 'N': 3, 'B': 3.2, 'R': 5, 'Q': 9}[piece.symbol().upper()]
        return v if piece.color == chess.WHITE else -v

    def get_table_index(self, square: int, color: bool) -> int:
        return square if color == chess.WHITE else chess.square_mirror(square)

    def evaluate_positional(self) -> float:
        score = 0.0
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if not piece:
                continue
            if self.is_endgame() and piece.piece_type == chess.KING:
                table = piece_tables['K_end']
            elif self.is_endgame() and piece.piece_type == chess.PAWN:
                table = piece_tables['P_end']
            else:
                table = piece_tables.get(piece.symbol().upper())

            if table:
                idx = self.get_table_index(square, piece.color)
                score += table[idx] if piece.color == chess.WHITE else -table[idx]
        return score
    
    def Mop_up_eval(self) -> float:
        enemy_square = self.board.king(not self.color)
        friend_square = self.board.king(self.color)

        cmd_enemy = manhattan_distance_king[enemy_square]

        md_kings = chess.square_manhattan_distance(friend_square, enemy_square)

        perspective = 1 if self.board.turn == chess.WHITE else -1

        return (4.7 * cmd_enemy + 1.6 * (14 - md_kings)) * perspective


    def evaluate_board(self) -> float:
        if self.board.is_game_over():
            if self.board.is_checkmate():
                return 999999.0 if self.board.turn == chess.BLACK else -999999.0
            if (
                self.board.is_stalemate() or
                self.board.is_fivefold_repetition() or
                self.board.is_insufficient_material() or
                self.board.is_seventyfive_moves()
            ):
                return 0.0 

        material = sum(self.piece_value_type(p) for p in self.board.piece_map.values())
        positional = self.evaluate_positional()

        if self.is_endgame():
            return self.Mop_up_eval() + material + positional
        
        return material + positional

    def move_priority(self, move: chess.Move) -> float:
        guess = 0.0
        values = {
            chess.PAWN: 1,
            chess.KNIGHT: 2.8,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0,
        }
        attacker = self.board.piece_at(move.from_square)
        victim = self.board.piece_at(move.to_square)

        if self.board.is_capture(move):
            guess = 10 * (self.piece_value_type(victim) - self.piece_value_type(attacker))
        if move.promotion:
            promo_value = values[move.promotion]
            guess += promo_value if self.board.turn == chess.WHITE else -promo_value
        if self.board.is_attacked_by(not self.board.turn, move.to_square):
            guess -= self.piece_value_type(attacker) if self.board.turn == chess.WHITE else -self.piece_value_type(attacker)

        return guess

    def quiescence(self, alpha: float, beta: float) -> float:
        stand_pat = self.evaluate_board()
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        capture_moves = [m for m in self.board.legal_moves if self.board.is_capture(m)]
        moves = sorted(
            capture_moves,
            key=lambda m: self.move_priority(m),
            reverse=self.board.turn != chess.BLACK,
        )
        for move in moves:
            self.board.push(move)
            score = -self.quiescence(-beta, -alpha)
            self.board.pop()
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha

    def minimax_alpha_beta(
        self,
        depth: int,
        alpha: float,
        beta: float,
        is_maximizing: bool,
        max_depth: int,
    ) -> float:
        board_hash = zobrist_hash(self.board)
        if board_hash in self.transposition_table:
            return self.transposition_table[board_hash]

        if depth == 0 or self.board.is_game_over():
            score = self.evaluate_board()
            if self.board.is_game_over():
                adjustment = (depth - max_depth) * 10
                score += -adjustment if self.board.turn == chess.BLACK else adjustment
            self.transposition_table[board_hash] = score
            return score

        moves = sorted(
            self.board.legal_moves,
            key=lambda m: self.move_priority(m),
            reverse=self.board.turn != chess.BLACK,
        )
        if is_maximizing:
            max_eval = -999999.0
            for move in moves:
                self.board.push(move)
                eval_score = self.minimax_alpha_beta(depth - 1, alpha, beta, False, max_depth)
                self.board.pop()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            self.transposition_table[board_hash] = max_eval
            return max_eval
        else:
            min_eval = 999999.0
            for move in moves:
                self.board.push(move)
                eval_score = self.minimax_alpha_beta(depth - 1, alpha, beta, True, max_depth)
                self.board.pop()
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            self.transposition_table[board_hash] = min_eval
            return min_eval

    def get_best_move(self, sequence: List[str]) -> Optional[chess.Move]:
        # Tenta abrir com abertura se houver sequência ou posição inicial
        if sequence or self.board.fen() == chess.STARTING_FEN:
            filtered = self.filter_openings(openings, sequence)
            if filtered:
                opening = random.choice(list(filtered.items()))
                if opening[0] == "Barnes Opening: Fool's Mate":
                    if random.randint(1, 1000) == random.randint(1, 1000):
                        pass
                    else:
                        opening = random.choice(list(filtered.items()))
                san_move = opening[1][len(sequence)]
                return chess.Move.from_uci(self.board.parse_san(san=san_move).uci())

        # Busca minimax
        best_move: Optional[chess.Move] = None
        # Se engine joga White, queremos maximizar; se joga Black, queremos minimizar
        best_score = -999999.0 if self.color == chess.WHITE else 999999.0

        moves = sorted(
            self.board.legal_moves,
            key=lambda m: self.move_priority(m),
            reverse=self.board.turn != chess.BLACK,
        )
        for move in moves:
            self.board.push(move)
            # is_maximizing começa True porque é a vez da engine ao aplicar este método
            score = self.minimax_alpha_beta(self.depth - 1, -999999.0, 999999.0, False, self.depth)
            self.board.pop()
            if self.color == chess.WHITE:
                if score >= best_score:
                    best_score = score
                    best_move = move
            else:
                if score <= best_score:
                    best_score = score
                    best_move = move
        return best_move
