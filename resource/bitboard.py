
class Bitboards:
    def __init__(self):
        # 12 bitboards: 6 for white pieces, 6 for black pieces
        self.bitboards = {
            'wP': 0, 'wN': 0, 'wB': 0, 'wR': 0, 'wQ': 0, 'wK': 0,
            'bP': 0, 'bN': 0, 'bB': 0, 'bR': 0, 'bQ': 0, 'bK': 0
        }
        self.castling_rights = ''  # e.g. 'KQkq'

    def from_board_array(self, board, castling_rights='KQkq'):
        """Convert 2D board[y][x] into bitboards and store castling rights."""
        self.clear()
        self.castling_rights = castling_rights
        for rank in range(8):
            for file in range(8):
                piece = board[rank][file]
                if piece:
                    square = (7 - rank) * 8 + file  # Flip vertically to match bitboard order
                    self.bitboards[piece] |= 1 << square
        self.occupied = self.get_occupied()

    def clear(self):
        for key in self.bitboards:
            self.bitboards[key] = 0
        self.castling_rights = ''

    def get_occupied(self):
        return sum(self.bitboards.values())

    def get_color_occupied(self, color):
        if color == 'w':
            return self.bitboards['wP'] | self.bitboards['wN'] | self.bitboards['wB'] | self.bitboards['wR'] | self.bitboards['wQ'] | self.bitboards['wK']
        else:
            return self.bitboards['bP'] | self.bitboards['bN'] | self.bitboards['bB'] | self.bitboards['bR'] | self.bitboards['bQ'] | self.bitboards['bK']

    def has_castling_right(self, symbol):
        """Check if a specific castling right (e.g. 'K', 'q') exists."""
        return symbol in self.castling_rights
