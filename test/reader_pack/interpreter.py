"""Independent interpreter reference. No Lang parser, AST, compiler or network."""
import re

SPACE = ' \t\n\r'


def comments_closed(source):
    # Scan independently of the Lang tokenizer, including comments before bad syntax.
    index = 0
    while index < len(source):
        if source.startswith('//', index):
            end = source.find('\n', index + 2)
            index = len(source) if end < 0 else end
        elif source.startswith('/*', index):
            end = source.find('*/', index + 2)
            if end < 0:
                return False
            index = end + 2
        else:
            index += 1
    return True


def interpret(source, stage):
    if len(source.encode('utf-8')) > 65534:
        return {'diagnostic': 'input exceeds 65534 bytes'}
    if '\x00' in source:
        return {'diagnostic': 'expected text without NUL'}
    if not comments_closed(source):
        return {'diagnostic': 'unterminated block comment'}

    def skip(index):
        while index < len(source):
            if source[index] in SPACE:
                index += 1
            elif source.startswith('//', index):
                end = source.find('\n', index + 2)
                index = len(source) if end < 0 else end
            elif source.startswith('/*', index):
                index = source.index('*/', index + 2) + 2
            else:
                break
        return index

    index = skip(0)
    values = []
    for key in (['answer'] if stage == 'create' else ['threshold', 'value']):
        word = re.match(r'[A-Za-z_][A-Za-z_0-9]*', source[index:])
        if not word or word[0] != key:
            return {'diagnostic': 'expected keyword'}
        index = skip(index + len(word[0]))
        number = re.match(r'[0-9]+', source[index:])
        if not number or len(number[0]) > 3 or int(number[0]) > 255:
            return {'diagnostic': 'expected decimal byte'}
        end = index + len(number[0])
        index = skip(end)
        if index == end and index < len(source):
            return {'diagnostic': 'expected decimal byte'}
        values.append(int(number[0]))
    if index != len(source):
        return {'diagnostic': 'expected end of input'}
    return {'value': values[0] if stage == 'create' else int(values[1] >= values[0])}
