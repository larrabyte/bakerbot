MESSAGE_CHARACTERS = 2000
MESSAGE_EMBEDS = 10
EMBED_CHARACTERS = 6000
EMBED_TITLE = 256
EMBED_DESCRIPTION = 4096
EMBED_FIELDS = 25
EMBED_FIELD_NAME = 256
EMBED_FIELD_VALUE = 1024
EMBED_FOOTER_TEXT = 2048
EMBED_AUTHOR_NAME = 256
VIEW_CHILDREN = 25
VIEW_ITEMS_PER_ROW = 5
SELECT_LABEL = 80
SELECT_VALUE = 100
SELECT_DESCRIPTION = 100
SELECT_OPTIONS = 25

def limit(string: str, n: int) -> str:
    """Limit a string to `n` characters."""
    if len(string) > n:
        return f"{string[0:n - 3]}..."

    return string