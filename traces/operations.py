from traces import decorators


@decorators.ignorant
def ignorant_sum(*args, **kwargs):
    return sum(*args, **kwargs)


@decorators.strict
def strict_sum(*args, **kwargs):
    return sum(*args, **kwargs)
