"""Independent interpreter reference. No Lang parser, AST, compiler or network."""
import re


def interpret(source, stage):
    # Tokenize independently; never accept a prefix of the input.
    source = re.sub(r'/\*[\s\S]*?\*/|//[^\n]*', ' ', source)
    words = source.split()
    keys = ['answer'] if stage == 'create' else ['threshold', 'value']
    if len(words) < len(keys) * 2:
        return {'diagnostic': 'expected decimal byte' if words and words[-1] in keys else 'expected keyword'}
    values = []
    for index, key in enumerate(keys):
        if words[index * 2] != key:
            return {'diagnostic': 'expected keyword'}
        number = words[index * 2 + 1]
        if not re.fullmatch(r'[0-9]{1,3}', number) or int(number) > 255:
            return {'diagnostic': 'expected decimal byte'}
        values.append(int(number))
    if len(words) != len(keys) * 2:
        return {'diagnostic': 'expected end of input'}
    return {'value': values[0] if stage == 'create' else int(values[1] >= values[0])}
