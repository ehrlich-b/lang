"""Deliberate defects for the interpreter-only track; never authoring references."""
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
        return interpret(source.replace('256', '255'), stage)
    raise ValueError(defect)
