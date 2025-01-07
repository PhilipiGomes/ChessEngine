from Tables import piece_tables


for piece in piece_tables.items():
    print(piece[0],':' ,len(piece[1]))
