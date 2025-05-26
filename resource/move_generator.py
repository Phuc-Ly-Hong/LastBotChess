from bitboard_utility import *
from magic_bitboards import MagicBitboards

class MoveGenerator:
    def __init__(self, bitboards):
        self.bb = bitboards
        self.magic = MagicBitboards()
        self.moves = []

    def generate_all_moves(self, color):
        self.moves.clear()
        self.generate_rook_moves(color)
        self.generate_bishop_moves(color)
        self.generate_queen_moves(color)
        self.generate_knight_moves(color)
        self.generate_king_moves(color)
        self.generate_pawn_moves(color)
        self.generate_castling_moves(color)
        return self.moves

    def add_moves(self, from_square, target_bb):
        while target_bb:
            to_square, target_bb = pop_lsb(target_bb)
            self.moves.append((from_square, to_square))

    def generate_rook_moves(self, color):
        occupied = self.bb.get_occupied()
        rooks = self.bb.bitboards[color + 'R']
        own_pieces = self.bb.get_color_occupied(color)
        while rooks:
            sq, rooks = pop_lsb(rooks)
            attacks = self.get_rook_attacks(sq, occupied) & ~own_pieces
            self.add_moves(sq, attacks)

    def generate_bishop_moves(self, color):
        occupied = self.bb.get_occupied()
        bishops = self.bb.bitboards[color + 'B']
        own_pieces = self.bb.get_color_occupied(color)
        while bishops:
            sq, bishops = pop_lsb(bishops)
            attacks = self.get_bishop_attacks(sq, occupied) & ~own_pieces
            self.add_moves(sq, attacks)

    def generate_queen_moves(self, color):
        self.generate_rook_moves(color)
        self.generate_bishop_moves(color)

    def generate_knight_moves(self, color):
        knights = self.bb.bitboards[color + 'N']
        own_pieces = self.bb.get_color_occupied(color)
        while knights:
            sq, knights = pop_lsb(knights)
            attacks = self.knight_attack_mask(sq) & ~own_pieces
            self.add_moves(sq, attacks)

    def generate_king_moves(self, color):
        kings = self.bb.bitboards[color + 'K']
        own_pieces = self.bb.get_color_occupied(color)
        while kings:
            sq, kings = pop_lsb(kings)
            attacks = self.king_attack_mask(sq) & ~own_pieces
            self.add_moves(sq, attacks)

    
    def generate_pawn_moves(self, color):
        own_pawns = self.bb.bitboards[color + 'P']
        empty = ~self.bb.get_occupied() & 0xFFFFFFFFFFFFFFFF
        enemy = self.bb.get_color_occupied('b' if color == 'w' else 'w')

        if color == 'w':
            single_push = shift_north(own_pawns) & empty
            double_push = shift_north(single_push & 0x0000000000FF0000) & empty
            left_captures = shift_northwest(own_pawns) & enemy
            right_captures = shift_northeast(own_pawns) & enemy
        else:
            single_push = shift_south(own_pawns) & empty
            double_push = shift_south(single_push & 0x0000FF0000000000) & empty
            left_captures = shift_southwest(own_pawns) & enemy
            right_captures = shift_southeast(own_pawns) & enemy

        self.add_pawn_moves(own_pawns, single_push, direction='N' if color == 'w' else 'S')
        self.add_pawn_moves(own_pawns, double_push, direction='N' if color == 'w' else 'S', double=True)
        self.add_pawn_captures(own_pawns, left_captures, 'left', color)
        self.add_pawn_captures(own_pawns, right_captures, 'right', color)

        # En passant handling
        if hasattr(self.bb, "last_move") and self.bb.last_move:
            last_from, last_to = self.bb.last_move
            last_piece = self.bb.get_piece_on_square(last_to) if hasattr(self.bb, 'get_piece_on_square') else None
            if last_piece and last_piece[1] == 'P':
                if abs(last_from // 8 - last_to // 8) == 2:
                    ep_rank = 4 if color == 'w' else 3
                    ep_pawns = own_pawns & (0xFF << (8 * ep_rank))
                    for sq in bitscan(ep_pawns):
                        file = sq % 8
                        if abs(file - (last_to % 8)) == 1:
                            ep_target = sq + 8 if color == 'w' else sq - 8
                            self.moves.append((sq, ep_target))

    def add_pawn_moves(self, pawns, targets, direction='N', double=False):
        while targets:
            to_sq, targets = pop_lsb(targets)
            if direction == 'N':
                from_sq = to_sq - (16 if double else 8)
            else:
                from_sq = to_sq + (16 if double else 8)
            self.moves.append((from_sq, to_sq))

    def add_pawn_captures(self, pawns, captures, side, color):
        while captures:
            to_sq, captures = pop_lsb(captures)
            if color == 'w':
                from_sq = to_sq - 7 if side == 'left' else to_sq - 9
            else:
                from_sq = to_sq + 9 if side == 'left' else to_sq + 7
            self.moves.append((from_sq, to_sq))

    def get_rook_attacks(self, square, blockers):
        return self.magic.get_rook_attacks(square, blockers)

    def get_bishop_attacks(self, square, blockers):
        return self.magic.get_bishop_attacks(square, blockers)

    def knight_attack_mask(self, square):
        rank, file = divmod(square, 8)
        moves = [(-2, -1), (-1, -2), (-2, 1), (-1, 2), (1, -2), (2, -1), (1, 2), (2, 1)]
        result = 0
        for dr, df in moves:
            r, f = rank + dr, file + df
            if 0 <= r < 8 and 0 <= f < 8:
                result |= 1 << (r * 8 + f)
        return result

    def king_attack_mask(self, square):
        rank, file = divmod(square, 8)
        moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        result = 0
        for dr, df in moves:
            r, f = rank + dr, file + df
            if 0 <= r < 8 and 0 <= f < 8:
                result |= 1 << (r * 8 + f)
        return result
    
    def generate_castling_moves(self, color):
        if color == 'w':
            king_pos = 4  # e1
            kingside_clear = not any((self.bb.occupied >> i) & 1 for i in [5, 6])
            queenside_clear = not any((self.bb.occupied >> i) & 1 for i in [1, 2, 3])
            if 'K' in self.bb.castling_rights and kingside_clear:
                self.moves.append((4, 6))  # e1 -> g1
            if 'Q' in self.bb.castling_rights and queenside_clear:
                self.moves.append((4, 2))  # e1 -> c1
        else:
            king_pos = 60  # e8
            kingside_clear = not any((self.bb.occupied >> i) & 1 for i in [61, 62])
            queenside_clear = not any((self.bb.occupied >> i) & 1 for i in [57, 58, 59])
            if 'k' in self.bb.castling_rights and kingside_clear:
                self.moves.append((60, 62))  # e8 -> g8
            if 'q' in self.bb.castling_rights and queenside_clear:
                self.moves.append((60, 58))  # e8 -> c8
