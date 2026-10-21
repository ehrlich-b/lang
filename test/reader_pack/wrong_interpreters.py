"""Deliberate defects for the interpreter-only track; never authoring references."""
import re
from interpreter import interpret


def wrong(source, stage, defect):
    if defect == 'wrong_arity':
        return interpret(source)  # Missing required stage argument.
    if defect == 'wrong_constant':
        return {'value': 1}
    if defect == 'wrong_boundary':
        words = source.split()
        return {'value': int(int(words[3]) > int(words[1]))}
    if defect == 'wrong_tail':
        return interpret(' '.join(source.split()[:4]), stage)
    if defect == 'wrong_numeric':
        numbers = re.fullmatch(r'threshold[ \t\r\n]+([0-9]+)[ \t\r\n]+value[ \t\r\n]+([0-9]+)', source)
        if numbers:
            return {'value': int(int(numbers[2]) >= int(numbers[1]))}
        return interpret(source, stage)
    raise ValueError(defect)
