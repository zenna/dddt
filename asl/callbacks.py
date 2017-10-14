import shutil
import torch

"Callbacks to be passed to optimization"
def tb_loss(i, writer, loss, **kwargs):
  "Plot loss on tensorboard"
  writer.add_scalar('data/scalar1', loss.data[0], i)


def print_stats(i, running_loss, **kwargs):
  "Print optimization statistics"
  print('[%5d] loss: %.3f' %
          (i + 1, running_loss / 2000))


def every_n(callback, n):
  "Higher order function that makes a callback run just once every n"
  def every_n_cb(i, **kwargs):
    if i % n == 0:
      callback(i=i, **kwargs)
  return every_n_cb


def print_loss(every, log_tb=True):
  "Print loss per every n"
  def print_loss_gen(every):
    running_loss = 0.0
    while True:
      data = yield
      running_loss += data.loss
      if (data.i + 1) % every == 0:
        loss_per_sample = running_loss / every
        print('loss per sample (avg over %s) : %.3f' % (every, loss_per_sample))
        if log_tb:
          data.writer.add_scalar('loss', loss_per_sample, data.i)
        running_loss = 0.0
  gen = print_loss_gen(every)
  next(gen)
  return gen


import asl
import os
import math


def save_checkpoint(every, model, verbose=True):
  "Save data every every steps"
  def save_checkpoint_innner(log_dir, i, optimizer, **kwargs):
    savepath = os.path.join(log_dir, "checkpoint.pth")
    if (i + 1) % every == 0:
      if verbose:
        print("Saving...")
      torch.save({'i': i + 1,
                  'state_dict': model.state_dict(),
                  'optimizer': optimizer.state_dict()},
                 savepath)
  return save_checkpoint_innner


def load_checkpoint(resume_path, model, optimizer, verbose=True):
  "Load data from checkpoint"
  if verbose:
    print("Loading...")
  torch.load(resume_path)
  checkpoint = torch.load(resume_path)
  # optimizer.load_state_dict(checkpoint['optimizer'])
  model.load_state_dict(checkpoint['state_dict'])
  model.eval()

# def save_checkpoint(every, model, verbose=True):
#   "Save check point every every iterations and best seen so far"
#   def save_checkpoint_gen(every, model):
#     best_loss = math.inf
#     while True:
#       data = yield
#       best_loss = min(best_loss, data.loss)
#       savepath = os.path.join(data.log_dir, "checkpoint.pth")
#       if (data.i + 1) % every == 0:
#         torch.save({'i': data.i + 1,
#                     'state_dict': model.state_dict(),
#                     'best_loss': best_loss,
#                     'optimizer': data.optimizer.state_dict()},
#                    savepath)
#         print(data.loss, " ", best_loss)
#         if data.loss <= best_loss:
#           if verbose:
#             print("Currently at best")
#           shutil.copyfile(savepath,
#                           os.path.join(data.log_dir, 'checkpoint_best.pth.tar'))
#
#   gen = save_checkpoint_gen(every, model)
#   next(gen)
#   return gen


def converged(every, print_change=True, change_thres=-0.000005):
  "Has the optimization converged?"
  def converged_gen(every):
    running_loss = 0.0
    last_running_loss = 0.0
    show_change = False
    cont = True
    while True:
      data = yield cont
      if data.loss is None:
        continue
      running_loss += data.loss
      if (data.i + 1) % every == 0:
        if show_change:
          change = (running_loss - last_running_loss)
          print('absolute change (avg over {}) {}'.format(every, change))
          if last_running_loss != 0:
            relchange = change / last_running_loss
            per_iter = relchange / every
            print('relative_change: {}, per iteration: {}'.format(relchange,
                                                                  per_iter))
            if per_iter > change_thres:
              print("Relative change insufficeint, stopping!")
              cont = False
        else:
          show_change = True
        last_running_loss = running_loss
        running_loss = 0.0

  gen = converged_gen(every)
  next(gen)
  return gen
