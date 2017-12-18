"Utils common for benchmarking"
from asl.sketch import Mode

def plot_observes(i, log, writer, batch=0, **kwargs):
  "Show the empty set in tensorboardX"
  for j in range(len(log['observes'])):
    refimg = log['ref_observes'][j].value
    neuimg = log['observes'][j].value
    writer.add_image('comp{}/ref'.format(j), refimg[batch], i)
    writer.add_image('comp{}/neural'.format(j), neuimg[batch], i)


def plot_empty(i, log, writer, **kwargs):
  "Show the empty set in tensorboardX"
  img = log['empty'][0].value
  writer.add_image('Empty', img, i)


def plot_internals(i, log, writer, batch=0, **kwargs):
  "Show internal structure. Shows anything log[NEURAL/internal]"
  internals = log["{}/internal".format(Mode.NEURAL.name)]
  for (j, internal) in enumerate(internals):
    writer.add_image('internals/{}'.format(j), internal.value[batch], i)
