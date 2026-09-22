import random
from enum import IntEnum
from typing import NamedTuple

import chess
from chess.polyglot import zobrist_hash
from openings import openings
from tables import manhattan_center_distance_king, piece_tables

MATE_SCORE = 100000.0

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3.2,
    chess.ROOK: 5,
    chess.QUEEN: 9,
}


class Bound(IntEnum):
    """Tipo de valor guardado na tabela de transposição (TT)."""

    EXACT = 0
    LOWER = 1  # falha-alta (beta cutoff): o valor real é >= score
    UPPER = 2  # falha-baixa: o valor real é <= score


class TTEntry(NamedTuple):
    depth: int
    score: float
    bound: Bound


class ChessEngine:
    def __init__(
        self,
        board: chess.Board,
        depth: int,
        color: chess.Color | None,
        name: str | None = None,
    ):
        self.board = board
        self.depth = depth
        self.color = color
        self.tt: dict[int, TTEntry] = {}
        self.name = name

    def select_random_opening(
        self, ope: dict[str, list[str]]
    ) -> tuple[str, list[str]] | None:
        if not ope:
            return None
        return random.choice(list(ope.items()))

    def filter_openings(
        self, op: dict[str, list[str]], sequence: list[str]
    ) -> dict[str, list[str]]:
        if not sequence:
            return op
        return {
            name: moves
            for name, moves in op.items()
            if moves[: len(sequence)] == sequence and len(moves) > len(sequence)
        }

    def piece_value(self, piece: chess.Piece | None) -> float:
        if not piece or piece.piece_type == chess.KING:
            return 0.0
        v = PIECE_VALUES[piece.piece_type]
        return v if piece.color == chess.WHITE else -v

    def mopup_eval(self, material: float) -> float:
        """
        Heuristica de final: incentiva o lado com mais material a empurrar o
        rei adversario para a borda e a aproximar o seu proprio rei, para
        ajudar a forcar o xeque-mate.

        Devolve sempre um valor do ponto de vista das Brancas (positivo
        favorece as Brancas), tal como `material`, para poderem ser somados
        de forma consistente em evaluate_board() -- independentemente de
        self.color ser WHITE ou BLACK.
        """
        if material == 0:
            return 0.0

        white_king = self.board.king(chess.WHITE)
        black_king = self.board.king(chess.BLACK)
        if white_king is None or black_king is None:
            return 0.0
        king_distance = chess.square_manhattan_distance(white_king, black_king)

        if material > 0:
            score = manhattan_center_distance_king[black_king] + (14 - king_distance)
            return 10 * score
        else:
            score = manhattan_center_distance_king[white_king] + (14 - king_distance)
            return -10 * score

    def is_endgame(self) -> bool:
        queens = len(self.board.pieces(chess.QUEEN, chess.WHITE)) + len(
            self.board.pieces(chess.QUEEN, chess.BLACK)
        )
        minor_pieces = (
            len(self.board.pieces(chess.KNIGHT, chess.WHITE))
            + len(self.board.pieces(chess.KNIGHT, chess.BLACK))
            + len(self.board.pieces(chess.BISHOP, chess.WHITE))
            + len(self.board.pieces(chess.BISHOP, chess.BLACK))
        )

        if queens == 0 and minor_pieces < 3:
            return True
        return queens == 1 and minor_pieces < 2

    def evaluate_positional(self, endgame: bool) -> float:
        score = 0.0
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if not piece:
                continue

            if endgame and piece.piece_type == chess.KING:
                table = piece_tables["K_end"]
            elif endgame and piece.piece_type == chess.PAWN:
                table = piece_tables["P_end"]
            else:
                table = piece_tables.get(piece.piece_type)

            if not table:
                continue

            idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
            score += table[idx] if piece.color == chess.WHITE else -table[idx]
        return score

    def evaluate_board(self) -> float:
        """
        Avalia a posicao atual. O calculo interno e sempre feito do ponto de
        vista das Brancas (positivo = bom para as Brancas); so no fim e que o
        sinal e invertido consoante o lado a jogar (self.board.turn), porque
        minimax()/quiescence() usam a convencao negamax, em que cada nivel
        espera o valor relativo a quem tem de jogar naquele no.
        """
        material = sum(self.piece_value(p) for p in self.board.piece_map().values())
        endgame = self.is_endgame()

        score = material + self.evaluate_positional(endgame)
        if endgame:
            score += self.mopup_eval(material)

        return score if self.board.turn == chess.WHITE else -score

    def move_score(self, move: chess.Move) -> float:
        score = 0.0
        piece_to_move = self.board.piece_at(move.from_square)
        piece_to_capture = self.board.piece_at(move.to_square)
        mover_value = (
            PIECE_VALUES.get(piece_to_move.piece_type, 0) if piece_to_move else 0
        )

        if piece_to_capture is not None:
            # MVV-LVA: capturar uma peca valiosa com uma peca barata pontua mais.
            victim_value = PIECE_VALUES.get(piece_to_capture.piece_type, 0)
            score += 10 * (victim_value - mover_value)

        if move.promotion is not None:
            score += PIECE_VALUES[move.promotion]

        # Quem pode recapturar na casa de destino e sempre o adversario de
        # quem esta a jogar agora (self.board.turn) -- nao o adversario fixo
        # do proprio engine (self.color), que pode nem ser quem esta a jogar
        # neste no da recursao.
        if self.board.attackers_mask(not self.board.turn, move.to_square):
            score -= mover_value * 5

        if self.board.gives_check(move):
            score += 10

        return score

    def move_ordering(self, moves: list[chess.Move]) -> list[chess.Move]:
        return sorted(moves, key=self.move_score, reverse=True)

    def quiescence(self, alpha: float, beta: float) -> float:
        stand_pat = self.evaluate_board()
        if stand_pat >= beta:
            return stand_pat
        alpha = max(alpha, stand_pat)

        capture_moves = [m for m in self.board.legal_moves if self.board.is_capture(m)]
        capture_moves = self.move_ordering(capture_moves)

        best = stand_pat
        for capture in capture_moves:
            self.board.push(capture)
            score = -self.quiescence(-beta, -alpha)
            self.board.pop()
            best = max(best, score)
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best

    def minimax(self, depth: int, alpha: float, beta: float) -> float:
        if self.board.is_game_over():
            if self.board.is_checkmate():
                return (self.depth - depth) - MATE_SCORE
            else:
                return 0.0

        original_alpha = alpha
        board_hash = zobrist_hash(self.board)

        entry = self.tt.get(board_hash)
        if entry is not None and entry.depth >= depth:
            if entry.bound == Bound.EXACT:
                return entry.score
            if entry.bound == Bound.LOWER:
                alpha = max(alpha, entry.score)
            elif entry.bound == Bound.UPPER:
                beta = min(beta, entry.score)
            if alpha >= beta:
                return entry.score

        moves = list(self.board.legal_moves)

        if depth == 0:
            score = self.quiescence(alpha, beta)
            self.tt[board_hash] = TTEntry(depth, score, Bound.EXACT)
            return score

        moves = self.move_ordering(moves)
        best_score = -MATE_SCORE
        for move in moves:
            self.board.push(move)
            score = -self.minimax(depth - 1, -beta, -alpha)
            self.board.pop()
            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break

        if best_score <= original_alpha:
            bound = Bound.UPPER
        elif best_score >= beta:
            bound = Bound.LOWER
        else:
            bound = Bound.EXACT
        self.tt[board_hash] = TTEntry(depth, best_score, bound)
        return best_score

    def get_best_move(self, sequence: list[str]) -> chess.Move:
        if sequence or self.board.fen() == chess.STARTING_FEN:
            filtered = self.filter_openings(openings, sequence)
            opening = self.select_random_opening(filtered)
            if opening is not None and len(opening[1]) > len(sequence):
                san_move = opening[1][len(sequence)]
                return self.board.parse_san(san_move)

        moves = list(self.board.legal_moves)

        moves = self.move_ordering(moves)
        best_move = moves[0]
        alpha, beta = -MATE_SCORE, MATE_SCORE

        for move in moves:
            self.board.push(move)
            score = -self.minimax(self.depth - 1, -beta, -alpha)
            self.board.pop()
            if score > alpha:
                alpha = score
                best_move = move

        return best_move
