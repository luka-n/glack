import regex

PARSERS = []

# EMOJI

EMOJI_REGEX = regex.compile(r'^:(\S+?):')


def parse_emoji(text, cursor):
    match = regex.match(EMOJI_REGEX, text[cursor:])
    if match:
        return (
            {
                'type': 'EMOJI',
                'value': match[1]
            },
            len(match[0])
        )
    else:
        return None


PARSERS.append(parse_emoji)

# LINKS

LINK_REGEX = regex.compile(r'''
    ^
    <
    ([^\n]+?)
    (?:\|([^\n]+?))?
    >
''', regex.X)


def parse_link(text, cursor):
    match = regex.match(LINK_REGEX, text[cursor:])
    if match:
        if match[1].startswith('#'):
            if not len(match[1]) > 1:
                return None
            return (
                {
                    'type': 'CHANNEL_LINK',
                    'value': match[1][1:]
                },
                len(match[0])
            )
        elif match[1].startswith('@'):
            if not len(match[1]) > 1:
                return None
            return (
                {
                    'type': 'USER_LINK',
                    'value': match[1][1:]
                },
                len(match[0])
            )
        else:
            return (
                {
                    'label': match[2],
                    'type': 'URL',
                    'value': match[1]
                },
                len(match[0])
            )
    else:
        return None


PARSERS.append(parse_link)

# QUOTED STRINGS

QUOTED_STRING_REGEX = r'''
    ^
    {delimiter}
    (\S[^\n]+?)
    {delimiter}
    (?=[\pP\s]|$)
'''

MULTILINE_QUOTED_STRING_REGEX = r'''
    ^
    {delimiter}
    (\S.+)
    {delimiter}
    (?=[\pP\s]|$)
'''


def quoted_string_parser(
        *,
        delimiter,
        multiline=False,
        node_type,
        recursive=True
):
    if multiline:
        quoted_string_regex = regex.compile(
            MULTILINE_QUOTED_STRING_REGEX
            .format(delimiter=regex.escape(delimiter)),
            regex.M | regex.X
        )
    else:
        quoted_string_regex = regex.compile(
            QUOTED_STRING_REGEX.format(delimiter=regex.escape(delimiter)),
            regex.X
        )

    def parser(text, cursor):
        if cursor > 0 and not regex.match(r'[\pP\s]', text[cursor - 1]):
            return None
        match = regex.match(quoted_string_regex, text[cursor:])
        if match:
            if recursive:
                return (
                    {
                        'children': parse_text(match[1]),
                        'type': node_type
                    },
                    len(match[0])
                )
            else:
                return (
                    {
                        'type': node_type,
                        'value': match[1]
                    },
                    len(match[0])
                )
        else:
            return None
    return parser


parse_bold = quoted_string_parser(
    delimiter='*',
    node_type='BOLD'
)

PARSERS.append(parse_bold)

parse_pre = quoted_string_parser(
    delimiter='```',
    multiline=True,
    node_type='PRE',
    recursive=False
)

PARSERS.append(parse_pre)

parse_code = quoted_string_parser(
    delimiter='`',
    node_type='CODE',
    recursive=False
)

PARSERS.append(parse_code)

parse_italic = quoted_string_parser(
    delimiter='_',
    node_type='ITALIC'
)

PARSERS.append(parse_italic)

parse_strike = quoted_string_parser(
    delimiter='~',
    node_type='STRIKE'
)

PARSERS.append(parse_strike)

# QUOTES

QUOTE_REGEX = regex.compile(r'^> ?(.+?)(\n|$)')


def parse_quote(text, cursor):
    if cursor > 0 and text[cursor - 1] != '\n':
        return None
    match = regex.match(QUOTE_REGEX, text[cursor:])
    if match:
        return (
            {
                'children': parse_text(match[1]),
                'type': 'QUOTE'
            },
            len(match[0])
        )
    else:
        return None


PARSERS.append(parse_quote)


def parse_text(text):
    cursor = 0
    nodes = []
    text_buffer = ''

    def flush():
        nonlocal text_buffer
        if text_buffer:
            nodes.append({
                'type': 'TEXT',
                'value': text_buffer
            })
            text_buffer = ''

    while cursor < len(text):
        match = None
        for parser in PARSERS:
            match = parser(text, cursor)
            if match:
                break
        if match:
            flush()
            nodes.append(match[0])
            cursor += match[1]
        else:
            text_buffer += text[cursor]
            cursor += 1

    flush()

    return nodes


class Mrkdwn:
    def __init__(self, text):
        self.text = text \
            .replace('&lt;', '<') \
            .replace('&gt;', '>') \
            .replace('&amp;', '&')

    def parse(self):
        return {
            'children': parse_text(self.text),
            'type': 'ROOT'
        }
