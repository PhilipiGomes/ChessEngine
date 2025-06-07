import sys
import chess
from Engine import get_best_move  # Certifique-se de que esta função está definida em Engine.py

def main():
    board = chess.Board()
    sequence = []

    while True:
        try:
            line = input()
        except EOFError:
            break

        if line == 'uci':
            print('id name PhiliEngine')
            print('id author Philipi')
            print('uciok')
        elif line == 'isready':
            print('readyok')
        elif line.startswith('position'):
            tokens = line.split()
            print(tokens)
            if 'startpos' in tokens:
                board.reset()
                moves_index = tokens.index('startpos') + 1
            elif 'fen' in tokens:
                fen_index = tokens.index('fen') + 1
                fen = ' '.join(tokens[fen_index:fen_index + 6])
                board.set_fen(fen)
                moves_index = fen_index + 6
            else:
                continue
            if 'moves' in tokens:
                moves_index = tokens.index('moves') + 1
                for move in tokens[moves_index:]:
                    board.push_uci(move)
        elif line == 'ucinewgame':
            board.reset()
            sequence = []
        elif line.startswith('go'):
            move = get_best_move(board, depth=3, sequence=sequence)
            if move:
                print(f'bestmove {move.uci()}')
            else:
                print('bestmove 0000')
        elif line == 'quit':
            break

if __name__ == '__main__':
    main()
