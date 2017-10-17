"""Copy Benchmark - Can a neural network learn to copy
From NTM Paper:
- The network is presented with an input sequence of random binary vectors, followed by a delimiter flag.
- The networks were trained to copy sequences of eight bit random vectors, where the
sequence lengths were randomised between 1 and 20. The target sequence was simply a
copy of the input sequence (without the delimiter flag).
"""
from benchmarks.types import vec_queue, bern_seq
import benchmarks.common as common
import asl.opt

from asl.modules.templates import MLPNet
from asl.sketch import Sketch, soft_ch
from asl.callbacks import every_n, print_loss, converged, save_checkpoint
from asl.util.misc import cuda
from asl.opt import handle_hyper
from asl.util.generators import infinite_samples
from asl.type import Type
from asl.structs.nqueue import EnqueueNet, DequeueNet, ref_queue
from asl.util.misc import iterget, take
from asl.train import train, max_iters
from asl.modules.modules import ConstantNet, ModuleDict
from asl.modules.templates import MLPNet
from asl.log import log_append
from asl.loss import vec_dist
from torch import optim

from typing import List
import torch
from torch import nn
from torch.autograd import Variable
import torch.nn.functional as F

# TODO
# - Get the template sampling
# - Update the sketch so that it is possible
# - Make different modes for differnet kinds of training
   # opt both ovserve loss and supervised loss
   # opt just supervised loss
   # if doing both, minimize both functiosn
   # minimize one after the other
   # minimize one in each step


def onehot(i, onehot_len, batch_size):
  # Dummy input that HAS to be 2D for the scatter (you can use view(-1,1) if needed)
  y = torch.LongTensor(batch_size, 1).fill_(i)
  # One hot encoding buffer that you create out of the loop and just keep reusing
  y_onehot = torch.FloatTensor(batch_size, onehot_len)
  # In your for loop
  y_onehot.zero_()
  return Variable(cuda(y_onehot.scatter_(1, y, 1)), requires_grad=False)

class CopySketch(Sketch):
  "Sketch for copy of list of elements"

  def __init__(self, element_type, model, ref_model, seq_len):
    super(CopySketch, self).__init__([List[element_type]],
                                     [List[element_type]],
                                     model,
                                     ref_model)
    self.choice_len = 10
    self.onehot_len = seq_len
    self.choosenet = MLPNet([(self.onehot_len,)], [(seq_len,)])
    self.seq_len = seq_len

  def choose_item(self, i):
    "Given i choose i"
    ionehot = onehot(i, self.onehot_len, 1)
    (item_choice, ) = self.choosenet(ionehot)
    return F.sigmoid(item_choice) # FIXME: Net should do this sigmoiding

  def sketch(self, items, enqueue, dequeue, empty):
    # import pdb; pdb.set_trace()
    queue = empty
    out_items = []
    for i in range(self.seq_len):
      (queue,) = enqueue(queue,
                         soft_ch(items, self.choose_item(i)))

    for _ in range(self.seq_len):
      (queue, item) = dequeue(queue)
      out_items.append(item)

    return out_items

def plot_items(i, log, writer, **kwargs):
  writer.add_image('fwd/1', log['outputs'][0][0][0], i)
  writer.add_image('fwd/2', log['outputs'][0][1][0], i)
  writer.add_image('fwd/3', log['outputs'][0][2][0], i)
  writer.add_image('rev/1', log['items'][0][0][0], i)
  writer.add_image('rev/2', log['items'][0][1][0], i)
  writer.add_image('rev/3', log['items'][0][2][0], i)

def reverse_args(parser):
  parser.add_argument('--seq_len', type=int, default=8, metavar='NI',
                      help='Length of sequence')
  parser.add_argument('--queue_len', type=int, default=8, metavar='NI',
                      help='Length of sequence')


def benchmark_copy_sketch(batch_size, queue_len, seq_len, template, log_dir,
                          lr, template_opt, **kwargs):
  queue_len = queue_len
  seq_len = seq_len  # From paper: between 1 and 20
  BernSeq = bern_seq(seq_len)
  VecQueue = vec_queue(queue_len)
  nqueue = ModuleDict({'enqueue': EnqueueNet(VecQueue, BernSeq,
                                             template=MLPNet,
                                             template_opt={}),
                       'dequeue': DequeueNet(VecQueue, BernSeq,
                                             template=MLPNet,
                                             template_opt={}),
                       'empty': ConstantNet(VecQueue)})

  refqueue = ref_queue()
  copy_sketch = CopySketch(BernSeq, nqueue, refqueue, seq_len)
  cuda(copy_sketch)
  bern_iter = BernSeq.iter(batch_size)

  def loss_gen():
    # Should copy the sequence, therefore the output should
    items = take(bern_iter, seq_len)
    rev_items = items.copy()
    rev_items.reverse()
    outputs = copy_sketch(items)
    log_append("outputs", outputs)
    log_append("items", items)
    # import pdb; pdb.set_trace()
    return vec_dist(outputs, rev_items, dist=nn.BCELoss())

  optimizer = optim.Adam(copy_sketch.parameters(), lr)
  train(loss_gen,
        optimizer,
        cont=converged(1000),
        callbacks=[print_loss(100),
                  #  common.plot_empty,
                  #  common.plot_observes,
                   save_checkpoint(1000, copy_sketch)],
        log_dir=log_dir)

if __name__ == "__main__":
  opt = asl.opt.handle_args(reverse_args)
  opt = asl.opt.handle_hyper(opt, __file__)
  benchmark_copy_sketch(**vars(opt))
