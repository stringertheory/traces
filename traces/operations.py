from .decorators import ignorant, strict


@ignorant
def ignorant_sum(*args, **kwargs):
    return sum(*args, **kwargs)


@strict
def strict_sum(*args, **kwargs):
    return sum(*args, **kwargs)
