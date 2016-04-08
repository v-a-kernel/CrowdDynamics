from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from timeit import default_timer as timer

from source.core.social_force import acceleration


def timeit(f):
    def wrapper(*args, **kwargs):
        start = timer()
        ret = f(*args, **kwargs)
        end = timer()
        print('Function time:', round(end - start, 4))
        return ret
    return wrapper


def system(agents, walls, constants, t_delta):
    """
    About
    -----
    Updates positions and velocities of agents using forces affecting them with
    given timestep.

    Params
    ------
    :param agents:
    :param constants:
    :param t_delta:
    :return:

    Resources
    ---------
    https://en.wikipedia.org/wiki/Euler_method
    """
    @timeit
    def update(i):
        kwargs = dict(agents, **constants)
        acc = acceleration(**kwargs)
        agents['velocity'] += acc * t_delta
        agents['position'] += agents['velocity'] * t_delta
        print('Simulation Time:', round(i * t_delta, 4), end=' ')

    iteration = 0
    while True:
        update(iteration)
        iteration += 1
        yield agents