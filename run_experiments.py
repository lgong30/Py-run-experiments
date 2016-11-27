#!/usr/bin/python

import subprocess
import threading
import multiprocessing
import yaml
import json
import numpy as np
from copy import deepcopy
import itertools
import sys

VERSION = (0, 1, 0, 'beta', 0)


def parse_option_values(vp):
    if type(vp['val']) == type(dict()):
        if (not vp['val'].has_key('type')) or vp['val']['type'] == 'linear':
            if vp['val'].has_key('number'):
                values = np.linspace(vp['val']['start'], vp['val']['end'], num=vp['val']['number']).tolist()
            elif vp['val'].has_key('step'):
                values = np.arange(vp['val']['start'], vp['val']['end'], vp['val']['step']).tolist()

                if values[-1] + vp['val']['step'] == vp['val']['end']:
                    values.append(vp['val']['end'])
        elif vp['val']['type'] == 'exponential':
            exponents_dict = vp['val']['exponents']
            if type(exponents_dict['val']) == type(dict()):
                if (not exponents_dict['val'].has_key('type')) or exponents_dict['val']['type'] == 'linear':
                    if exponents_dict['val'].has_key('number'):
                        exponents = np.linspace(exponents_dict['val']['start'], exponents_dict['val']['end'], num=exponents_dict['val']['number']).tolist()
                    elif exponents_dict['val'].has_key('step'):
                        exponents = np.arange(exponents_dict['val']['start'], exponents_dict['val']['end'], exponents_dict['val']['step']).tolist()

                        if exponents[-1] + exponents_dict['val']['step'] == exponents_dict['val']['end']:
                            exponents.append(exponents_dict['val']['end'])
                else:
                    print "Value type is not supported"
                    exit(1)
            else:
                exponents = exponents_dict['val']

            values = [vp['val']['base'] ** i for i in exponents]
        else:
            print "Value type is not supported"
            exit(1)

    else:
        values = vp['val']

    return values
"""
O_Serenade_1:

"""
def load_experiments(exp_conf, redirect=True):
    if exp_conf.endswith(".yml"):
        loader = yaml.safe_load
    elif exp_conf.endswith(".json"):
        loader = json.load
    else:
        print "Configuration file type ", os.path.splitext(exp_conf)[-1], "is not supported"
        print "Currently, only json and yaml are supported"
        exit(1)
    data = None
    with open(exp_conf, 'r') as fp:
        data = loader(fp)

    exp_template_fixed = '{exe} {fixed_args}'
    exp_template_var = ' -{opt} {val}'
    exp_template_outred = ' >{output_file}'
    experiments = []
    for exp_family_id, exp_family in data.iteritems():

        if not (exp_family.has_key('v_options')):
            # experiments.append(exp_template_fixed.format(**exp_family))
            if not redirect:
                yield exp_template_fixed.format(**exp_family)
            else:
                myexp = exp_template_fixed.format(**exp_family)
                of = "".join(myexp.split()) + ".txt"
                yield myexp + exp_template_outred.format(output_file=of)
        else:
            # 
            values = []
            options = []
            for vp in exp_family['v_options']:
                values.append(deepcopy(parse_option_values(vp)))
                options.append(vp['opt'])

            for v in itertools.product(*values):
                op = ''
                for opt, val in zip(options, v):
                    op += exp_template_var.format(opt=opt, val=val)
                if not redirect:
                    yield exp_template_fixed.format(**exp_family) + op
                else:
                    myexp = exp_template_fixed.format(**exp_family) + op 
                    myexp_p = myexp.replace('.', '_')
                    of = "".join(myexp_p.split()) + ".txt"
                    yield myexp + exp_template_outred.format(output_file=of)                    


def run_experiments(command, exp_semaphore):
    exp_semaphore.acquire()
    print "Experiment to run: ", command 
    subprocess.call(command, shell=True)
    exp_semaphore.release()


if __name__ == "__main__":
    # with open("sample.yml", "r") as yf:
    #     exp_conf = yaml.safe_load(yf)
    #     print exp_conf
    # for exp in load_experiments("samples/sample3.yml"):
    #     print exp
    try:
        exp_conf = sys.argv[1]
    except IndexError:
        print "Usage:\n\t{0} {1}\n\tExample configuration files can be found in ./samples".format(sys.argv[0], "experiment_configuration_file")
        exit(1)
    threads = []
    exp_semaphore = threading.Semaphore(multiprocessing.cpu_count())
    for exp in load_experiments(exp_conf):
        threads.append(threading.Thread(target=run_experiments, args=(exp, exp_semaphore)))
    print '\n'
    [t.start() for t in threads]
    [t.join() for t in threads]
    print 'finished', len(threads), 'experiments'



