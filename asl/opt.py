"Options"
from collections import namedtuple

Opt = namedtuple('Opt', ['log_dir',
                         'resume_path',
                         'batch_size',
                         'lr',
                         'optim',
                         'template',
                         'template_opt',
                         'specific'],
                 verbose=False)
