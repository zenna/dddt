# Composition of Modules
import asl.archs as archs
import torch
from torch import nn
import torch.nn.functional as F

def sizes_match(sz1, sz2):
  if sz1 is None or sz2 is None:
    return True
  else:
    return sz1 == sz2

def check_all_sizes_match(szs1, szs2):
  "Check size one and size 2 are consistent"
  if not all((sizes_match(sz1, sz2) for sz1, sz2 in zip(szs1, szs2))):
    raise ValueError

def compose(modulegens, params, rand_in):
  if len(modulegens) != len(params):
    raise ValueError
  if "in_sizes" not in params[0]:
    raise ValueError

  modules = []
  for i, modulegen in enumerate(modulegens):
    extra_params = modulegen.arg_from_sizes()
    module = modulegen(params[i])
    rand_out = module(*rand_in)
    modules.append(module) # Save the module if all sizes ok
    if i < len(modulegens) - 1:
      in_sizes = out_sizes
      out_sizes = params[i+1].get("out_sizes", None) # or none
  
  return nn.Sequential(modules)

def test_composition():
  in_sizes = [(1, 10, 10), (1, 5, 5)]
  out_sizes = [(10,)]
  rand_in = [torch.rand(sz) for sz in in_sizes]


  module = compose([archs.CombineNet,
                    nn.Reshape,
                    nn.Linear,
                    F.softmax],
                    [{"in_sizes": in_sizes},
                     {"out_channels": 5},
                     {"out_sizes": out_sizes},
                     {"out_sizes": out_sizes}],
                     rand_in)
  in_data = [torch.rand(sz) for sz in in_sizes]
  output = module(*in_data)

if __name__ == "__main__":
  test_composition()