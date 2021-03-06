from enum import Enum
from multipledispatch import dispatch
import torch.nn as nn
from torch.autograd import Variable
import asl.util as util
from asl.util.misc import cuda
from asl.util.torch import onehot
from asl.type import Type
import torch

"Common encodings"
# One Hot Encodings
class Encoding():
  def __init__(self, value):
    self.value = value

  def size(self):
    return self.value.size()


class OneHot1D(Encoding):
  pass


class OneHot2D(Encoding):
  pass


def encode(cls, encoding, typesize):
  "This was something clever, but I can't remember what!"
  class ClsEncoding(cls, encoding):
    def __init__(self, value, expand_one=True):
      self.value = util.maybe_expand(ClsEncoding, value, expand_one)
  ClsEncoding.typesize = typesize
  ClsEncoding.__name__ = cls.__name__ + encoding.__name__
  return ClsEncoding


@dispatch(OneHot1D, OneHot1D)
def equal(x, y):
  same = torch.max(x.value, 1)[1] == torch.max(y.value, 1)[1]
  return same.data[0]

@dispatch(OneHot1D, OneHot1D)
def dist(x, y):
  # Check length
  return nn.BCEWithLogitsLoss()(x.value, y.value)


def compound_encoding(cl, encoding):
  "Class that is ClassEncoding"
  return next(x for x in cl.__subclasses__() if issubclass(x, encoding))


@dispatch(Enum)
def onehot1d(enum, length=None):
  "Encode an Enum as a one hot vector"
  EnumOneHot1D = compound_encoding(enum.__class__.__bases__[0], OneHot1D)
  length = EnumOneHot1D.typesize[0] if length is None else length
  return EnumOneHot1D(Variable(cuda(onehot(enum.value, length, 1))))


@dispatch(Enum)
def onehot2d(enum):
  EnumOneHot2D = compound_encoding(enum.__class__.__bases__[0], OneHot2D)
  var = torch.zeros(EnumOneHot2D.typesize)
  var[enum.value, enum.value] = 1.0
  return EnumOneHot2D(var)
