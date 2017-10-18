"""Clevr Benchmark """
# FIXME: CLEANUP import hell
import asl.opt
from asl.templates.convnet import VarConvNet
from asl.templates.mlp import MLPNet
from asl.callbacks import every_n, print_loss, converged, save_checkpoint
from asl.util.misc import cuda
from asl.train import train, max_iters
from asl.modules.modules import ModuleDict
from asl.log import log_append, log
from asl.loss import vec_dist
from torch import optim

import torch
from typing import Any
from torch import nn
from benchmarks.clevr.clevr import scenes_iter, data_iter, ref_clevr, interpret, ans_tensor
from benchmarks.clevr.defns import *
from asl.sketch import Sketch

class ClevrSketch(Sketch):
  "Sketch for copy of list of elements"

  def __init__(self, model, ref_model):
    super(ClevrSketch, self).__init__(Any, Any, model, ref_model)

  def sketch(self, progs, objsets, rels, **kwargs):
    results = []
    def netapply(fname, inputs):
      f = kwargs[fname]
      return f(*inputs)[0]
    def tensor(value):
      x = value.tensor()
      return x.expand(1, *x.size())
    for (i, _) in enumerate(objsets):
      res = interpret(progs[i], objsets[i], rels[i], apply=netapply,
                      value_transform=tensor)
      results.append(res)

    return results


def reverse_args(parser):
  parser.add_argument('--seq_len', type=int, default=4, metavar='NI',
                      help='Length of sequence')
  parser.add_argument('--stack_len', type=int, default=8, metavar='NI',
                      help='Length oitemsf sequence')


def accuracy(est, target):
  "Find accuracy of estimation for target"
  est_int = [torch.max(t, 1)[1] for t in est]
  target_int = [torch.max(ans, 0)[1] for ans in target]
  diffs  = [est_int[i].data[0] == target_int[i].data[0] for i in range(len(target))]
  ncorrect = sum(diffs)
  acc = ncorrect / len(diffs)
  return acc, ncorrect

def print_accuracy(every, log_tb=True):
  "Print accuracy per every n"
  def print_accuracy_gen(every):
    running_accuracy = 0.0
    while True:
      data = yield
      acc = data.log['accuracy']
      running_accuracy += acc
      if (data.i + 1) % every == 0:
        accuracy_per_sample = running_accuracy / every
        print('accuracy per sample (avg over %s) : %.3f %%' % (every, accuracy_per_sample))
        if log_tb:
          data.writer.add_scalar('accuracy', accuracy_per_sample, data.i)
        running_accuracy = 0.0
  gen = print_accuracy_gen(every)
  next(gen)
  return gen

def benchmark_clevr_sketch(batch_size, template, log_dir, lr, template_opt, **kwargs):
  template = MLPNet
  template_opt = {}

  neu_clevr = {'unique': Unique(template=template, template_opt=template_opt),
               'relate': Relate(template=template, template_opt=template_opt),
               'count': Count(template=template, template_opt=template_opt),
               'exist': Exist(template=template, template_opt=template_opt),
               'filter_size': FilterSize(template=template, template_opt=template_opt),
               'filter_color': FilterColor(template=template, template_opt=template_opt),
               'filter_material': FilterMaterial(template=template, template_opt=template_opt),
               'filter_shape': FilterShape(template=template, template_opt=template_opt),
               'intersect': Intersect(template=template, template_opt=template_opt),
               'union': Union(template=template, template_opt=template_opt),
               'greater_than': GreaterThan(template=template, template_opt=template_opt),
               'less_than': LessThan(template=template, template_opt=template_opt),
               'equal_integer': EqualInteger(template=template, template_opt=template_opt),
               'equal_material': EqualMaterial(template=template, template_opt=template_opt),
               'equal_size': EqualSize(template=template, template_opt=template_opt),
               'equal_shape': EqualShape(template=template, template_opt=template_opt),
               'equal_color': EqualColor(template=template, template_opt=template_opt),
               'query_shape': QueryShape(template=template, template_opt=template_opt),
               'query_size': QuerySize(template=template, template_opt=template_opt),
               'query_material': QueryMaterial(template=template, template_opt=template_opt),
               'query_color': QueryColor(template=template, template_opt=template_opt),
               'same_shape': SameShape(template=template, template_opt=template_opt),
               'same_size': SameSize(template=template, template_opt=template_opt),
               'same_material': SameMaterial(template=template, template_opt=template_opt),
               'same_color': SameColor(template=template, template_opt=template_opt)}

  neuclevr = ModuleDict(neu_clevr)
  refclevr = ref_clevr
  clevr_sketch = ClevrSketch(neuclevr, refclevr)
  cuda(clevr_sketch)
  data_itr = data_iter(batch_size)

  def loss_gen():
    nonlocal data_itr
    try:
      progs, objsets, rels, answers = next(data_itr)
    except StopIteration:
      data_itr = data_iter(batch_size)
      progs, objsets, rels, answers = next(data_itr)

    outputs = clevr_sketch(progs, objsets, rels)
    anstensors = [ans_tensor(ans) for ans in answers]
    acc, ncorrect = accuracy(outputs, anstensors)
    log("accuracy", acc)
    log("ncorrect", ncorrect)
    log("outof", len(answers))
    deltas = [nn.BCEWithLogitsLoss()(outputs[i][0], anstensors[i]) for i in range(len(outputs))]
    return sum(deltas) / len(deltas)


  optimizer = optim.Adam(clevr_sketch.parameters(), lr)
  train(loss_gen,
        optimizer,
        cont=converged(1000),
        callbacks=[print_loss(10),
                  print_accuracy(10),
                  #  every_n(plot_sketch, 500),
                  #  common.plot_empty,
                  #  common.plot_observes,
                   save_checkpoint(1000, clevr_sketch)],
        log_dir=log_dir)

if __name__ == "__main__":
  opt = asl.opt.handle_args(reverse_args)
  opt = asl.opt.handle_hyper(opt, __file__)
  asl.opt.save_opt(opt)
  benchmark_clevr_sketch(**vars(opt))
