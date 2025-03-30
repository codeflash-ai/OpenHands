import re

from pygments.lexers.python import PythonLexer
from pygments.token import Text, Whitespace


def tokenize_code(code):
    lexer = PythonLexer()
    return process_pygments_tokens(lexer.get_tokens(code))


def process_pygments_tokens(tokens):
    new_tokens_final = []
    prev_token = None

    for token_type, token_value in tokens:
        # Skip whitespace tokens
        if token_type in {Text, Whitespace} and re.match(r"\s+", token_value):
            continue

        # Check if the last added token was part of a "quoted string"
        if prev_token == '"STR"' and token_value == '"':
            prev_token = None
            continue

        # Efficiently update tokens by checking current and previous context
        if token_value == '"' and prev_token is None:
            prev_token = '"'
            continue
        elif prev_token == '"' and token_value == "STR":
            prev_token = '"STR"'
            continue

        # Append the previous token if it wasn't clearly matched as a quoted string
        if prev_token:
            new_tokens_final.append(prev_token)
            prev_token = None

        # Add the regular token
        new_tokens_final.append(token_value)

    # Handle any trailing '"STR"' tokens that were not fully formed
    if prev_token:
        new_tokens_final.append(prev_token)

    return new_tokens_final
