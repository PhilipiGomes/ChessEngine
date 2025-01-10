import berserk
import chess
from Engine import get_best_move

LICHESS_API_TOKEN = 'lip_6ytXE1H5mMnoVi7tFgCX'


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

    board = chess.Board()  # Inicializando o tabuleiro principal
    board2 = chess.Board() # Tabuleiro para transformação de movimentos de UCI para SAN (Por causa das aberturas)
    white_player = None
    black_player = None
    account_username = client.account.get()['username'].lower()  # Armazenando o nome de usuário uma vez
    moves_san = []  # Lista para armazenar todos os movimentos em SAN
    initial_fen = chess.STARTING_FEN

    for event in game_stream:
        if event['type'] == 'gameFull':
            board.set_fen(initial_fen)  # Atualiza o tabuleiro principal
            board.set_fen(initial_fen)  # Atualiza o tabuleiro 2

            white_player = event['white']['id']
            black_player = event['black']['id']

            # Se for a vez do bot, faz a jogada da IA
            if board.turn == chess.WHITE and account_username == white_player:
                make_best_move(client, game_id, board, depth, moves_san)

        elif event['type'] == 'gameState':
            moves = event['moves'].split()

            for move in moves[len(board.move_stack):]:  # Aplica apenas os novos movimentos no tabuleiro
                board.push(chess.Move.from_uci(move))

            for move in moves[:-1]:
                board2.push(chess.Move.from_uci(move))

            # Adiciona os movimentos em SAN à lista moves_san (Usando o tabuleiro 2, resetando ele toda vez, para não travar na hra de executar movimentos.)
            move_san = board2.san(chess.Move.from_uci(moves[-1]))
            moves_san.append(move_san)
            board2.set_fen(initial_fen) # resetando de novo o tabuleiro.

            # Fazer a jogada da IA se for a vez do bot
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
        board.push(best_move)  # Atualiza o tabuleiro principal após a jogada
    else:
        print('Game Over')




# Start AI game as a Bot on Lichess
ai_play_on_lichess_bot(5)
