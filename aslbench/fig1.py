import asl
import pandas as pd
import os
import stdargs
import numpy as np
import matplotlib.pyplot as plt


def extension(path):
  filename, file_extension = os.path.splitext(path)
  return file_extension

def loaddf(path):
  return pd.read_pickle(path)

def isopt(path):
  return extension(path) == ".pkl"


def isdf(path):
  return extension(path) == ".df"


"Loads all rundata files in `searchdir`"
def walkoptdata(searchdir):
  return walkload(searchdir, isopt, asl.load_opt)


"Loads all rundata files in `searchdir`"
def walkdfdata(searchdir):
  return walkload(searchdir, isdf, loaddf)


def walkload(searchdir, isgood, loaddata):
  data = []
  for root, dir, files in os.walk(searchdir, followlinks=True):
    for file in files:
      if isgood(file):
        print(root)
        data.append(loaddata(os.path.join(root, file)))

  return data

## Make figure 1
path = "/home/zenna/sshfs/omdata/runs/mnistsetsun"
optdata = walkoptdata(path)
dfdata = walkdfdata(path)

def nm_to_df(dfdata):
  nm_to_df_ = {}
  for df in dfdata:
    try:
      nm = df['runname'][0:1][0]
      nm_to_df_[nm] = df
    except:
      print("Missing data!")
  return nm_to_df_


def nm_to_opt(optdata):
  nm_to_opt_ = {}
  for opt in optdata:
    try:
      nm = opt['name']
      nm_to_opt_[nm] = opt
    except:
      print("Missing data!")
  return nm_to_opt_

def optrunnames(optdata):
  optrunnames = []
  for df in dfdata:
    try:
      optrunnames.append(df['runname'][0:1][0])
    except:
      print("Missing data!")
  return optrunnames  

# Get all the data frames where the number of items is 1, find the optimal loss

def dfs_where_opt(filter_func, nm_to_df_, nm_to_opt_):
  dfs = []
  for nm, opt in nm_to_opt_.items():
    if filter_func(opt):
      dfs.append(nm_to_df_[nm])
  return dfs

nm_to_df_ = nm_to_df(dfdata)
nm_to_opt_ = nm_to_opt(optdata)

keys = set(list(nm_to_df_.keys())).intersection(set(list(nm_to_opt_.keys())))

nm_to_df_ = {k:v for k,v in nm_to_df_.items() if k in keys}
nm_to_opt_ = {k:v for k,v in nm_to_opt_.items() if k in keys}

## Figure 1.a)
def optima_per_nitems(nm_to_df_, nm_to_opt_):
  optima = []
  for nitems in range(1, 10):
    dfs = dfs_where_opt(lambda opt: opt['nitems'] == nitems, nm_to_df_, nm_to_opt_)
    min_losses = [min(df['loss']) for df in dfs]
    print(min_losses)
    min_min_losses = min(min_losses)
    optima.append(min_min_losses)
  return optima

nitems_vs_loss = optima_per_nitems(nm_to_df_, nm_to_opt_)

plt.bar(np.arange(1, 10),
        nitems_vs_loss)
plt.xlabel("Number of items")
plt.ylabel("Mean square error")
plt.title('Baseline Training Loss')

def runname(df):
  return df['runname'][0:1][0]

## Figure 2.a) Loss curves
def loss_curve_for_item(nitems, nm_to_df_, nm_to_opt_):
  dfs = dfs_where_opt(lambda opt: opt['nitems'] == nitems, nm_to_df_, nm_to_opt_)
  df = dfs[0]
  for df2 in dfs[1:]:
    df = df.join(df2, on='iteration', how='outer', lsuffix=runname(df2))
  return df


def optimalloss(searchdir, nitems):
  def nitemsisnitems(opt):
    return opt["nitems"] == nitems
  get_df_where_opt(nitemsisnitems)