CRYPTO_KEY_SIZE = 128
CRYPTO_K1 = "aGFua19lcl9ob21vX3Bvbw=="  # "hank_er_homo_poo"
CRYPTO_K2 = "ZGlsZG9zZXJ2aWNlX3N1eA=="  # "dildoservice_sux"
CLIENT_VERSION_NUMBER = "9.1.0"
CLIENT_OS = "Android"
CLIENT_TIMEOUT = 30
API_URL = "http://app.politikontroller.no"

NO_CONTROLS = "INGEN_KONTROLLER"
INGEN = "INGEN"
INGEN_PAAMELDTE_STEDER = "INGEN_PAAMELDTE_STEDER"
USER_NOT_AUTHORIZED = "USER_NOT_AUTHORIZED"
USER_NOT_AUTHORIZED_NOPREM = "USER_NOT_AUTHORIZED_NOPREM"
INVALID_AUTH = "INVALID_AUTH"
ERR = "ERR"

NO_ACCESS_RESPONSES = [
    USER_NOT_AUTHORIZED,
    USER_NOT_AUTHORIZED_NOPREM,
    INVALID_AUTH,
]
NO_CONTENT_RESPONSES = [
    NO_CONTROLS,
    INGEN,
    INGEN_PAAMELDTE_STEDER,
]
ERROR_RESPONSES = [
    ERR,
]

PHONE_PREFIXES = {
    "no": 47,
    "se": 46,
    "dk": 45,
}
PHONE_NUMBER_LENGTH = 8
DEFAULT_COUNTRY = "no"
DEFAULT_MAX_DISTANCE = 1.5

DESCRIPTION_TRUNCATE_LENGTH = 27
DESCRIPTION_TRUNCATE_SUFFIX = ".."
