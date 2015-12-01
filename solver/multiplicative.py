import multiprocessing as mp
from copy import deepcopy
from itertools import product

import numpy as np

from solver.constants import DEFAULT_FLOAT_TYPE, CONST_EPS, CONST_EPS_LOG
from solver.private.shared import *


def __make_a_matrix__(x, p, polynom):
    n = len(x[0][0])
    a_matrix = np.array([[np.log(polynom(p_j, j[k]) + 1 + CONST_EPS_LOG) for x_i in range(len(x)) for j in x[x_i] for
                          p_j in range(1, p[x_i])] for k in range(n)])
    return a_matrix


def make_model(data, degrees, weights, method, poly_type='chebyshev', find_split_lambdas=False, **kwargs):
    eps = CONST_EPS
    if 'epsilon' in kwargs:
        try:
            eps = DEFAULT_FLOAT_TYPE(kwargs['epsilon'])
        finally:
            pass

    x = deepcopy(data['x'])
    y = deepcopy(data['y'])

    dims_x_i = np.array([len(x[i]) for i in sorted(x)])

    x_matrix = np.array([x[i] for i in sorted(x)])
    y_matrix = np.array([y[i] for i in sorted(y)])

    # norm data
    x_normed_matrix, x_scales = normalize_x_matrix(x_matrix)
    y_normed_matrix, y_scales = normalize_y_matrix(y_matrix)

    ln_y_add_one = np.log(y_normed_matrix + 1)

    p = np.array(degrees)
    weights = np.array(weights)
    polynom_type = get_polynom_function(poly_type)

    b_matrix = make_b_matrix(ln_y_add_one, weights)
    a_matrix = __make_a_matrix__(x_normed_matrix, p, polynom_type)
    if find_split_lambdas:
        lambdas = make_split_lambdas(a_matrix, b_matrix, eps, method, dims_x_i, p)
    else:
        lambdas = make_lambdas(a_matrix, b_matrix, eps, method)
    psi_matrix = make_psi(a_matrix, x_normed_matrix, lambdas, p)
    a_small = make_a_small_matrix(ln_y_add_one, psi_matrix, eps, method, dims_x_i)
    f_i = make_f_i(a_small, psi_matrix, dims_x_i)
    c = make_c_small(ln_y_add_one, f_i, eps, method)
    f_log = make_f(f_i, c)
    f = np.exp(f_log) - 1
    f_real = make_real_f(y_scales, f)

    normed_error = np.linalg.norm(y_normed_matrix - f, np.inf, axis=1)

    error = np.linalg.norm(y_matrix - f_real, np.inf, axis=1)
    error = "normed Y errors - {:s}\nY errors - {:s}".format(str(normed_error), str(error))

    result = ''

    return "\n\n".join([result, error]), lambda: show_plots(y_matrix, f_real)


def __calculate_error_for_degrees__(degrees, x_normed_matrix, y_normed_matrix, ln_y_add_one, y_scales, b_matrix,
                                    dims_x_i,
                                    polynom_type, eps, method, find_split_lambdas):
    p = np.array(degrees)

    a_matrix = __make_a_matrix__(x_normed_matrix, p, polynom_type)
    if find_split_lambdas:
        lambdas = make_split_lambdas(a_matrix, b_matrix, eps, method, dims_x_i, p)
    else:
        lambdas = make_lambdas(a_matrix, b_matrix, eps, method)
    psi_matrix = make_psi(a_matrix, x_normed_matrix, lambdas, p)
    a_small = make_a_small_matrix(ln_y_add_one, psi_matrix, eps, method, dims_x_i)
    f_i = make_f_i(a_small, psi_matrix, dims_x_i)
    c = make_c_small(ln_y_add_one, f_i, eps, method)
    f = make_f(f_i, c)
    f_real = make_real_f(y_scales, f)

    return {'norm': np.linalg.norm(y_normed_matrix - f, np.inf, axis=1), 'degrees': p, 'f': f_real}


def find_best_degrees(data, max_degrees, weights, method, poly_type='chebyshev', find_split_lambdas=False, **kwargs):
    results = []

    eps = CONST_EPS
    if 'epsilon' in kwargs:
        try:
            eps = DEFAULT_FLOAT_TYPE(kwargs['epsilon'])
        finally:
            pass

    x = data['x']
    y = data['y']

    dims_x_i = np.array([len(x[i]) for i in sorted(x)])

    x_matrix = np.array([x[i] for i in sorted(x)])
    y_matrix = np.array([y[i] for i in sorted(y)])

    # norm data
    x_normed_matrix, x_scales = normalize_x_matrix(x_matrix)
    y_normed_matrix, y_scales = normalize_y_matrix(y_matrix)

    ln_y_add_one = np.log(y_normed_matrix + 1)

    max_p = np.array(max_degrees)
    weights = np.array(weights)
    polynom_type = get_polynom_function(poly_type)

    b_matrix = make_b_matrix(ln_y_add_one, weights)

    pool = mp.Pool()

    for current_degree in product(*[range(1, i) for i in max_p]):
        pool.apply_async(__calculate_error_for_degrees__, args=(
            current_degree, x_normed_matrix, y_normed_matrix, ln_y_add_one, y_scales, b_matrix, dims_x_i, polynom_type,
            eps, method,
            find_split_lambdas), callback=lambda result: results.append(result))
    pool.close()
    pool.join()

    best_results = []
    for i in range(len(ln_y_add_one)):
        res = min(results, key=lambda arg: arg['norm'][i])
        br = {'norm': res['norm'][i], 'degrees': res['degrees'], 'f': res['f'][i]}
        best_results.append(br)

    text_result = '\n'.join('Best degrees for Y{} are {} with normed error - {}'.format(i + 1,
                                                                                        convert_degrees_to_string(
                                                                                            best_results[i]['degrees']),
                                                                                        best_results[i]['norm']) for i
                            in range(len(best_results)))

    plots = lambda: show_plots(y_matrix, [br['f'] for br in best_results])

    return text_result, plots
