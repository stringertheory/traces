"""This module is derived from the `infinity` package (at
https://pypi.org/project/infinity/ or
https://github.com/kvesteri/infinity), which is licensed under the BSD
3-Clause "New" or "Revised" License:

Copyright (c) 2014, Konsta Vesterinen
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this
  list of conditions and the following disclaimer in the documentation and/or
  other materials provided with the distribution.

* Neither the name of the {organization} nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

from functools import total_ordering


@total_ordering
class Infinity:
    def __init__(self, positive=True):
        self.positive = positive

    def __neg__(self):
        return Infinity(not self.positive)

    def __gt__(self, other):
        if self == other:
            return False
        return self.positive

    def __eq__(self, other):
        return (
            (
                isinstance(other, self.__class__)
                and other.positive == self.positive
            )
            or (self.positive and other == float("inf"))
            or (not self.positive and other == float("-inf"))
        )

    def __ne__(self, other):
        return not (self == other)

    def __bool__(self):
        return True

    def __nonzero__(self):
        return True

    def __str__(self):
        return "%sinf" % ("" if self.positive else "-")

    def __float__(self):
        return float(str(self))

    def __add__(self, other):
        if is_infinite(other) and other != self:
            return NotImplemented
        return self

    def __radd__(self, other):
        return self

    def __sub__(self, other):
        if is_infinite(other) and other == self:
            return NotImplemented
        return self

    def __rsub__(self, other):
        return self

    def timetuple(self):
        return ()

    def __abs__(self):
        return self.__class__()

    def __pos__(self):
        return self

    def __div__(self, other):
        if is_infinite(other):
            return NotImplemented

        return Infinity(
            other > 0 and self.positive or other < 0 and not self.positive
        )

    def __rdiv__(self, other):
        return 0

    def __repr__(self):
        return str(self)

    __truediv__ = __div__
    __rtruediv__ = __rdiv__
    __floordiv__ = __div__
    __rfloordiv__ = __rdiv__

    def __mul__(self, other):
        if other == 0:
            return NotImplemented
        return Infinity(
            other > 0 and self.positive or other < 0 and not self.positive
        )

    __rmul__ = __mul__

    def __pow__(self, other):
        if other == 0:
            return NotImplemented
        elif other == -self:
            return -0.0 if not self.positive else 0.0
        else:
            return Infinity()

    def __rpow__(self, other):
        if other in (1, -1):
            return NotImplemented
        elif other == -self:
            return -0.0 if not self.positive else 0.0
        else:
            return Infinity()

    def __hash__(self):
        return (self.__class__, self.positive).__hash__()


inf = Infinity()


def is_infinite(value):
    return value == inf or value == -inf
