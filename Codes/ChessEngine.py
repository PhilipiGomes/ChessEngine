import random
from typing import Dict, List, Optional, Tuple

import chess
from chess.polyglot import zobrist_hash
from Openings import openings
from Tables import manhattan_center_distance_king, piece_tables

MATE_SCORE = 100000.0

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3.2,
    chess.ROOK: 5,
    chess.QUEEN: 9,
}


class ChessEngine:
    def __init__(self, board: chess.Board, depth: int, color: chess.Color):
        self.board = board
        self.depth = depth
        self.color = color
        self.tt: Dict[int, float] = {}

    def select_random_opening(self, ope: Dict[str, List[str]]) -> Optional[Tuple[str, List[str]]]:
        if not ope:
            print("No openings available.")
            return None
        return random.choice(list(ope.items()))

    def filter_openings(self, op: Dict[str, List[str]], sequence: List[str]) -> Dict[str, List[str]]:
        if sequence:
            filtered_openings: Dict[str, List[str]] = {}
            for opening_name, moves in op.items():
                if moves[: len(sequence)] == sequence and (
                    len(moves) > len(sequence) if len(sequence) > 0 else True
                ):
                    filtered_openings[opening_name] = moves
            return filtered_openings
        else:
            return op

    def piece_value(self, piece: Optional[chess.Piece]) -> float:
        if not piece or piece.piece_type == chess.KING:
            return 0.0
        v = PIECE_VALUES[piece.piece_type]
        return v if piece.color == chess.WHITE else -v

    def mopup_eval(self) -> float:
        eval = 0

        my_king_square = self.board.king(self.color)
        opp_king_square = self.board.king(not self.color)
        
        distance_king_center = manhattan_center_distance_king[opp_king_square]

        eval += distance_king_center

        distance_between_kings = chess.square_manhattan_distance(my_king_square, opp_king_square)

        eval += 14 - distance_between_kings
        
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece and piece.piece_type != chess.KING:
                if self.board.attackers_mask(not self.color, sq) > 0 and self.board.attackers_mask(self.color, sq) == 0:
                    eval -= self.piece_value(piece) if piece.color == chess.WHITE else -self.piece_value(piece)

        return 10 * eval

    def is_endgame(self) -> bool:
        queens = 0
        minor_pieces = 0
        
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece:
                if piece.piece_type == chess.QUEEN:
                    queens += 1
                if piece.piece_type == chess.KNIGHT or piece.piece_type == chess.BISHOP:
                    minor_pieces += 1
        
        if queens == 0 and minor_pieces < 3:
            return True
        if queens == 1 and minor_pieces < 2:
            return True
        return False
    
    def evaluate_positional(self) -> float:
        score = 0.0
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if not piece:
                continue
            if self.is_endgame() and piece.piece_type == chess.KING:
                table = piece_tables["K_end"]
            elif self.is_endgame() and piece.piece_type == chess.PAWN:
                table = piece_tables["P_end"]
            else:
                table = piece_tables.get(piece.symbol().upper())

            if table:
                idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
                score += table[idx] if piece.color == chess.WHITE else -table[idx]
        return score
    
    def evaluate_board(self) -> float:
        eval = 0
        material = sum(self.piece_value(p) for p in self.board.piece_map().values())
        eval += material
        positional = self.evaluate_positional()
        eval += positional
        if self.is_endgame():
            return self.mopup_eval() + eval
        return eval

    def move_score(self, move: chess.Move) -> float:
        score = 0
        piece_to_move = self.board.piece_at(move.from_square)
        piece_to_capture = self.board.piece_at(move.to_square)

        if piece_to_capture is not None:
            score = 10 * self.piece_value(piece_to_move) - self.piece_value(piece_to_capture)

        if move.promotion is not None:
            score += PIECE_VALUES[move.promotion]

        if self.board.attackers_mask(not self.color, move.to_square) > 0:
            score -= self.piece_value(piece_to_move)

        return score

    def move_ordering(self, moves: List[chess.Move]) -> List[chess.Move]:
        return sorted(moves, key=self.move_score, reverse=True)

    def quiescence(self, alpha: float, beta: float) -> float:
        eval = self.evaluate_board()
        if eval >= beta:
            return beta
        alpha = max(alpha, eval)

        moves = list(self.board.legal_moves)
        capture_moves = list(filter(self.board.is_capture, moves))
        capture_moves = self.move_ordering(capture_moves)

        for capture in capture_moves:
            self.board.push(capture)
            eval = -self.quiescence(-beta, -alpha)
            self.board.pop()
            if eval >= beta:
                return beta
            alpha = max(alpha, eval)
        return alpha

    def minimax(self, depth: int, alpha: float, beta: float) -> float:
        
        board_hash = zobrist_hash(self.board)
        if board_hash in self.tt:
            return self.tt[board_hash]
        
        moves = list(self.board.legal_moves)
        if len(moves) == 0:
            start_depth = self.depth
            if self.board.is_check():
                # Cheque-Mate
                return start_depth - depth - MATE_SCORE
            else:
                # Empate
                return start_depth - depth

        if depth == 0:
            score = self.evaluate_board()
            self.tt[board_hash] = score
            return score

        moves = self.move_ordering(moves)
        for move in moves:
            self.board.push(move)
            eval_score = -self.minimax(depth - 1, -beta, -alpha)
            self.board.pop()
            if eval_score >= beta:
                return beta
            alpha = max(alpha, eval_score)
        return alpha

    def get_best_move(self, sequence: List[str]) -> chess.Move:
        # Tenta abrir com abertura se houver sequência ou posição inicial
        print('trying openings')
        if sequence or self.board.fen() == chess.STARTING_FEN:
            filtered = self.filter_openings(openings, sequence)
            if filtered:
                opening = random.choice(list(filtered.items()))
                san_move = opening[1][len(sequence)]
                print("Opening selected")
                return chess.Move.from_uci(self.board.parse_san(san=san_move).uci())
        print('going into search')
        best_move: Optional[chess.Move] = None
        # Se engine joga White, queremos maximizar; se joga Black, queremos minimizar
        if self.color == chess.WHITE:
            best_score = -MATE_SCORE
        else:
            best_score = MATE_SCORE

        moves = list(self.board.legal_moves)
        for move in moves:
            self.board.push(move)
            score = self.minimax(self.depth - 1, -MATE_SCORE, MATE_SCORE)
            self.board.pop()
            if self.color == chess.WHITE:
                if score >= best_score:
                    best_score = score
                    best_move = move
            else:
                if score <= best_score:
                    best_score = score
                    best_move = move
        if best_move:
            return best_move
        return random.choice(moves)
