import berserk
import chess
from Engine import get_best_move

LICHESS_API_TOKEN = 'Your_API_token'


def ai_play_on_lichess_bot(depth):
    session = berserk.TokenSession(LICHESS_API_TOKEN)
    client = berserk.Client(session)

    print("Waiting for game events...")
    for event in client.bots.stream_incoming_events():
        print(f"Event received: {event['type']}")
        if event['type'] == 'challenge':
            challenge_id = event['challenge']['id']
            print(f"Accepting challenge {challenge_id}...")
            client.bots.accept_challenge(challenge_id)
            print("Challenge accepted.")
        elif event['type'] == 'gameStart':
            game_id = event['game']['id']
            print(f"Game started. Game ID: {game_id}")
            play_game(client, game_id, depth)
        else:
            print(f"Unhandled event type: {event['type']}")


def play_game(client, game_id, depth):
    game_stream = client.bots.stream_game_state(game_id)

    board = chess.Board()  # Starting Main board
    board2 = chess.Board() # Board to transform UCI moves in SAN moves (Because of the openings)
    white_player = None
    black_player = None
    account_username = client.account.get()['username'].lower()  # Storing the username
    moves_san = []  # List to store all the SAN moves
    initial_fen = chess.STARTING_FEN

    for event in game_stream:
        if event['type'] == 'gameFull':
            board.set_fen(initial_fen)  # Update main board
            board.set_fen(initial_fen)  # Update board 2

            white_player = event['white']['id']
            black_player = event['black']['id']

            # If it's bot's turn, then play
            if board.turn == chess.WHITE and account_username == white_player:
                make_best_move(client, game_id, board, depth, moves_san)

        elif event['type'] == 'gameState':
            moves = event['moves'].split()

            for move in moves[len(board.move_stack):]:  # Apply only the last move on the board
                board.push(chess.Move.from_uci(move))

            for move in moves[:-1]:
                board2.push(chess.Move.from_uci(move))

            # Add the moves in SAN to the moves_san list (Using board 2, resetting it every time, so as not to get stuck when executing moves.)
            move_san = board2.san(chess.Move.from_uci(moves[-1]))
            moves_san.append(move_san)
            board2.set_fen(initial_fen) # Resetting the board 2

            # Make the bot's play in his turn
            if (board.turn == chess.WHITE and account_username == white_player) or \
               (board.turn == chess.BLACK and account_username == black_player):
                make_best_move(client, game_id, board, depth, moves_san)

        elif event['type'] == 'gameFinish':
            print("Game finished.")
            break


def make_best_move(client, game_id, board, depth, moves):
    print('AI turn...')
    print(moves)
    print(board)
    best_move = get_best_move(board, depth, moves)
    if best_move is not None:
        move_uci = best_move.uci()
        client.bots.make_move(game_id, move_uci)
        board.push(best_move)  # Update main board after play
    else:
        print('Game Over')


# Start AI game as a Bot on Lichess
ai_play_on_lichess_bot(5)
