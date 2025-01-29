import chess
import os
import pandas as pd
from EngineNoOpening import get_best_move

# Load the puzzles from the CSV file
def load_puzzles_from_csv(csv_filename):
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_filename)
    return df

# Get a random puzzle FEN from the DataFrame
def get_random_fen(df):
    # Randomly select a puzzle from the DataFrame
    random_row = df.sample(n=1)
    return random_row['FEN'].values[0]

def puzzle(board, fen, depth):
    board.set_fen(fen)
    os.system('cls')  # On Windows, to clear the terminal screen
    
    print(fen)
    
    print(board)

    move, score = get_best_move(board, depth)

    print()
    print(board.san(move))
    print(round(score, 5))
    print()

    board.push(move)
    print()
    print(board)

# File path to the decompressed puzzle database CSV
csv_filename = 'Chess/lichess_db_puzzle.csv'  # Update the filename if needed

# Load the puzzles from the CSV file
df_puzzles = load_puzzles_from_csv(csv_filename)

# Get a random puzzle's FEN
fen = get_random_fen(df_puzzles)

# Set up the board and solve the puzzle
board = chess.Board()
puzzle(board, fen, 3)
