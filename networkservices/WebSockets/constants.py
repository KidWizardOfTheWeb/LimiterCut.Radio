from enum import Enum, EnumDict
# Note: this should be modifiable before a channel is started, per channel.
BUFFER_SIZE = 1024 * 4

class ServerResp(bytes, Enum):
    LISTEN_OK = b"Connection allowed as listener."
    CAST_OK = b"Connection allowed as caster."
    CHAT_OK = b"Connection allowed as chatter."

# TODO: This should be placeholder for all-access servers, let users have a file of their own that they can use later.
class ServerID(str, Enum):
    MS = "Master System"
    GN = "Genesis"
    ST = "Saturn"
    DC = "Dreamcast"
    NM = "NAOMI"
    CI = "Chihiro"
    TF = "Triforce"


# NOTE: below this comment is from the websockets example, ignore this for now (unused).
# But feel free to refactor in the future when we want to keep data on each channel instance (highly likely!)
__all__ = ["PLAYER1", "PLAYER2", "Connect4"]

PLAYER1, PLAYER2 = "red", "yellow"


class Connect4:
    """
    A Connect Four game.

    Play moves with :meth:`play`.

    Get past moves with :attr:`moves`.

    Check for a victory with :attr:`winner`.

    """

    def __init__(self):
        self.moves = []
        self.top = [0 for _ in range(7)]
        self.winner = None

    @property
    def last_player(self):
        """
        Player who played the last move.

        """
        return PLAYER1 if len(self.moves) % 2 else PLAYER2

    @property
    def last_player_won(self):
        """
        Whether the last move is winning.

        """
        b = sum(1 << (8 * column + row) for _, column, row in self.moves[::-2])
        return any(b & b >> v & b >> 2 * v & b >> 3 * v for v in [1, 7, 8, 9])

    def play(self, player, column):
        """
        Play a move in a column.

        Returns the row where the checker lands.

        Raises :exc:`ValueError` if the move is illegal.

        """
        if player == self.last_player:
            raise ValueError("It isn't your turn.")

        row = self.top[column]
        if row == 6:
            raise ValueError("This slot is full.")

        self.moves.append((player, column, row))
        self.top[column] += 1

        if self.winner is None and self.last_player_won:
            self.winner = self.last_player

        return row
