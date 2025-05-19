from EngineAIvsAI import get_best_move
import chess
import time

board = chess.Board()
board.set_fen("8/1N4k1/p3Q3/P5p1/3P4/7P/5PP1/4R1K1 w - - 0 1")

print(board)
n = 3  # número de lances para o mate
for depth in range(1, 11):
    temp_board = board.copy()
    found_mate = False
    transpositon_table = {}
    for ply in range(n * 2):  # numero de plies para o mate
        start = time.time()
        best_move = get_best_move(temp_board, depth, [], transpositon_table)
        if best_move is None:
            break
        elapsed_time = time.time() - start
        print(f"Depth: {depth}, Ply: {ply+1}, Move: {temp_board.san(best_move)}, Elapsed time: {elapsed_time:.3f} seconds")
        temp_board.push(best_move)
        if temp_board.is_checkmate():
            print(f"Checkmate found at depth {depth} in {ply+1} plies!")
            found_mate = True
            break
        if temp_board.is_game_over():
            break
    if not found_mate:
        print(f"No mate found at depth {depth}.")
    print()