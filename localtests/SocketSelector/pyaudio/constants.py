from enum import Enum
BUFFER_SIZE = 1024 * 4

class ServerResp(bytes, Enum):
    LISTEN_OK = b"Connection allowed as listener."
    CAST_OK = b"Connection allowed as caster."

class ServerID(str, Enum):
    MS = "Master System"
    GN = "Genesis"
    ST = "Saturn"
    DC = "Dreamcast"
    NM = "NAOMI"
    CI = "Chihiro"
    TF = "Triforce"
