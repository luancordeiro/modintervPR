import numpy as np
from lmfit import Parameters, Minimizer
from scipy.signal import argrelmin
from tsmoothie.smoother import LowessSmoother
from scipy.signal import find_peaks

from datetime import datetime
from scipy.integrate import odeint
import logging

logger = logging.getLogger('my_logger')
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


def deriv(y, t, r1, a1, K1, p1, q1):
    C = y
    r = r1
    K = K1
    a = a1
    p = p1
    q = q1
    dCdt = r * (C ** q) * (1 - (C / K) ** a) ** p
    return dCdt


def deriv1(y, t, r1, a1, K1, p1, q1, r2, a2, K2, p2, q2, rho, t_0):
    C = y
    r = r1 + 0.5 * (r2 - r1) * (1 + np.tanh(0.5 * rho * (t - t_0)))
    K = K1 + 0.5 * (K2 - K1) * (1 + np.tanh(0.5 * rho * (t - t_0)))
    a = a1 + 0.5 * (a2 - a1) * (1 + np.tanh(0.5 * rho * (t - t_0)))
    p = p1 + 0.5 * (p2 - p1) * (1 + np.tanh(0.5 * rho * (t - t_0)))
    q = q1 + 0.5 * (q2 - q1) * (1 + np.tanh(0.5 * rho * (t - t_0)))
    dCdt = r * (C ** q) * (1 - (C / K) ** a) ** p
    return dCdt


def deriv2(y, t, r1, a1, K1, p1, q1, r2, a2, K2, p2, q2, r3, a3, K3, p3, q3, rho, t_0, rho1, t_1):
    C = y
    r = r1 + 0.5 * (r2 - r1) * (1 + np.tanh(0.5 * rho * (t - t_0))) + 0.5 * (r3 - r2) * (
            1 + np.tanh(0.5 * rho1 * (t - t_1)))
    K = K1 + 0.5 * (K2 - K1) * (1 + np.tanh(0.5 * rho * (t - t_0))) + 0.5 * (K3 - K2) * (
            1 + np.tanh(0.5 * rho1 * (t - t_1)))
    a = a1 + 0.5 * (a2 - a1) * (1 + np.tanh(0.5 * rho * (t - t_0))) + 0.5 * (a3 - a2) * (
            1 + np.tanh(0.5 * rho1 * (t - t_1)))
    p = p1 + 0.5 * (p2 - p1) * (1 + np.tanh(0.5 * rho * (t - t_0))) + 0.5 * (p3 - p2) * (
            1 + np.tanh(0.5 * rho1 * (t - t_1)))
    q = q1 + 0.5 * (q2 - q1) * (1 + np.tanh(0.5 * rho * (t - t_0))) + 0.5 * (q3 - q2) * (
            1 + np.tanh(0.5 * rho1 * (t - t_1)))
    dCdt = r * (C ** q) * (1 - (C / K) ** a) ** p
    return dCdt


def func(params, t, data):  # Objective function to be minimized
    r1 = params['r1']
    a1 = params['a1']
    K1 = params['K1']
    p1 = params['p1']
    q1 = params['q1']
    ret = odeint(deriv, y0, t, args=(r1, a1, K1, p1, q1))
    C = ret.T
    resid = []
    pre_resid = []
    pre_resid.append(C)
    pre_resid = np.array(pre_resid)
    resid.append(pre_resid - data)
    resid = np.array(resid)
    return resid


def func1(params, t, data):
    r1 = params['r1']
    a1 = params['a1']
    K1 = params['K1']
    p1 = params['p1']
    q1 = params['q1']
    r2 = params['r2']
    a2 = params['a2']
    K2 = params['K2']
    p2 = params['p2']
    q2 = params['q2']
    rho = params['rho']
    t_0 = params['t_0']
    ret = odeint(deriv1, y0, t, args=(r1, a1, K1, p1, q1, r2, a2, K2, p2, q2, rho, t_0))
    C = ret.T
    resid = []
    pre_resid = []
    pre_resid.append(C)
    pre_resid = np.array(pre_resid)
    resid.append(pre_resid - data)
    resid = np.array(resid)
    return resid


def func2(params, t, data):
    r1 = params['r1']
    a1 = params['a1']
    K1 = params['K1']
    p1 = params['p1']
    q1 = params['q1']
    r2 = params['r2']
    a2 = params['a2']
    K2 = params['K2']
    p2 = params['p2']
    q2 = params['q2']
    r3 = params['r3']
    a3 = params['a3']
    K3 = params['K3']
    p3 = params['p3']
    q3 = params['q3']
    rho = params['rho']
    t_0 = params['t_0']
    rho1 = params['rho1']
    t_1 = params['t_1']
    ret = odeint(deriv2, y0, t, args=(r1, a1, K1, p1, q1, r2, a2, K2, p2, q2, r3, a3, K3, p3, q3, rho, t_0, rho1, t_1))
    C = ret.T
    resid = []
    pre_resid = []
    pre_resid.append(C)
    pre_resid = np.array(pre_resid)
    resid.append(pre_resid - data)
    resid = np.array(resid)
    return resid


def fit(deaths):
    global y0  # Gambiarra

    deaths = deaths.to_numpy()
    temp_inicio = datetime.now()
    logger.info('O fit começou...')

    daily1 = []
    daily1.append(deaths[0])
    for i in range(0, len(deaths) - 1):
        daily1.append(deaths[i + 1] - deaths[i])

    # operate smoothing
    smoother = LowessSmoother(smooth_fraction=0.1, iterations=1)
    smoother.smooth(daily1)

    # generate intervals
    low, up = smoother.get_intervals('prediction_interval')

    peaks, _ = find_peaks(-smoother.smooth_data[0])
    print(f"picos: {peaks}")
    peaks1, _ = find_peaks(smoother.smooth_data[0])
    print(f"picos1: {peaks1}")
    if len(deaths) - peaks1[-1] > 100:
        peaks1[-1] = len(deaths) - 1
    print()

    t = np.linspace(0, int(1 * len(deaths)) - 1, 2000)
    t_plot = np.linspace(0, int(1.2 * len(deaths)), 2000)
    t0 = np.array(range(len(deaths)))
    tw1 = int(.5 * (peaks[len(peaks) - 2] + peaks1[len(peaks1) - 2]))
    tw1 = 210
    t1 = np.array(range(tw1))
    deaths1 = deaths[0:tw1]
    tw2 = int(.5 * (peaks[-1] + peaks1[-1]))
    tw2 = 320
    t2 = np.array(range(tw2))
    deaths2 = deaths[0:tw2]
    deaths3 = deaths

    daily2 = smoother.smooth_data[0]

    relmin = argrelmin(daily2)
    print(relmin)
    print()

    ###########################################################

    # Initial conditions vector
    y0 = deaths[0]

    # Data to be fited
    data2 = []
    data2.append(deaths)
    data2 = np.array(data2)

    ###########################################################

    params = Parameters()
    params.add('r1', value=0.2, min=0, max=1)
    params.add('a1', value=0.2, min=0, max=1)
    params.add('K1', value=1.1 * deaths1[len(deaths1) - 1], min=deaths1[len(deaths1) - 1])
    params.add('p1', value=1, min=1, vary=True)
    # params.add('q1', value=q1.value, min=0, max=1, vary=False)
    params.add('q1', value=0.6, min=0, max=1)

    minner = Minimizer(func, params, fcn_args=(t1, deaths1))

    # Fit using Nelder-Mead
    logger.info('Começou o primeiro processo de minimização...')
    out1 = minner.minimize(method='nelder')
    # lmfit.report_fit(out1)
    logger.info('Terminou o primeiro processo de minimização...')

    print('R2=', 1 - out1.residual.var() / np.var(deaths1))
    print(out1.chisqr)

    # Fit using the Levenberg-Marquardt method with the result of the previous fit as initial guess
    # logger.info('Começou o segundo processo de minimização...')
    # out2 = minner.minimize(method='leastsq', params=out1.params)
    # lmfit.report_fit(out2)
    # logger.info('Terminou o segundo processo de minimização...')
    out2 = out1

    print('R2=', 1 - out2.residual.var() / np.var(deaths1))
    print()
    params = out2.params
    r1 = params['r1']
    a1 = params['a1']
    K1 = params['K1']
    p1 = params['p1']
    q1 = params['q1']

    ###########################################################

    params.add('r1', value=r1.value, min=0, max=1, vary=True)
    params.add('a1', value=a1.value, min=0, max=1, vary=True)
    params.add('K1', value=K1.value, min=0, vary=True)
    params.add('p1', value=p1.value, min=1, vary=True)
    params.add('q1', value=q1.value, min=0, max=1, vary=True)
    # params.add('r2', value=1, min=0, max=1, vary=False)
    params.add('r2', value=0.3, min=0, max=1)
    params.add('a2', value=1, min=0, max=1, vary=False)
    # params.add('a2', value=0.5, min=0, max=1)
    params.add('K2', value=1.1 * deaths2[-1], min=deaths2[-1], vary=True)
    # params.add('K2', value=1.1*K1.value, min=K1.value, vary=True)
    params.add('p2', value=1, min=1, vary=True)
    # params.add('q2', value=1, min=0, max=1, vary=False)
    params.add('q2', value=0.6, min=0, max=1)
    params.add('rho', value=0.01, min=0, max=0.2)
    params.add('t_0', value=tw1, min=0, max=len(t2))

    minner1 = Minimizer(func1, params, fcn_args=(t2, deaths2))

    # Fit using Nelder-Mead
    logger.info('Começou o terceiro processo de minimização...')
    out3 = minner1.minimize(method='least_squares')
    # lmfit.report_fit(out3)
    logger.info('Terminou o terceiro processo de minimização...')

    print('R2=', 1 - out3.residual.var() / np.var(deaths2))

    # Fit using the Levenberg-Marquardt method with the result of the previous fit as initial guess
    logger.info('Começou o quarto processo de minimização...')
    out4 = minner1.minimize(method='least_squares', params=out3.params)
    # lmfit.report_fit(out4)
    logger.info('Terminou o quarto processo de minimização...')

    print('R2=', 1 - out4.residual.var() / np.var(deaths2))
    print()
    params = out4.params
    r1 = params['r1']
    a1 = params['a1']
    K1 = params['K1']
    p1 = params['p1']
    q1 = params['q1']
    r2 = params['r2']
    a2 = params['a2']
    K2 = params['K2']
    p2 = params['p2']
    q2 = params['q2']
    rho = params['rho']
    t_0 = params['t_0']

    ###########################################################

    params.add('r1', value=r1.value, min=0, max=1, vary=True)
    params.add('a1', value=a1.value, min=0, max=1, vary=True)
    params.add('K1', value=K1.value, min=0, vary=True)
    params.add('p1', value=p1.value, min=1, vary=True)
    params.add('q1', value=q1.value, min=0, max=1, vary=True)
    params.add('r2', value=r2.value, min=0, max=1)
    params.add('a2', value=a2.value, min=0, max=1, vary=False)
    params.add('K2', value=K2.value, min=deaths2[-1], vary=True)
    params.add('p2', value=p2.value, min=1, vary=True)
    params.add('q2', value=q2.value, min=0, max=1)
    params.add('rho', value=rho.value, min=0, max=0.2)
    params.add('t_0', value=t_0.value, min=0)
    params.add('r3', value=0.3, min=0, max=1)
    params.add('a3', value=1, min=0, max=1, vary=False)
    # params.add('a2', value=0.5, min=0, max=1)
    params.add('K3', value=1.1 * deaths3[-1], min=deaths3[-1], vary=True)
    # params.add('K2', value=1.1*K1.value, min=K1.value, vary=True)
    params.add('p3', value=1, min=0, vary=False)
    # params.add('q2', value=1, min=0, max=1, vary=False)
    params.add('q3', value=0.6, min=0, max=1)
    params.add('rho1', value=0.05, min=0, max=0.2)
    params.add('t_1', value=tw2, min=0, max=len(t0))

    minner2 = Minimizer(func2, params, fcn_args=(t0, deaths3))

    # Fit using Nelder-Mead
    logger.info('Começou o quinto processo de minimização...')
    out5 = minner2.minimize(method='least_squares')
    # lmfit.report_fit(out5)
    logger.info('Terminou o quinto processo de minimização...')

    print('R2=', 1 - out5.residual.var() / np.var(deaths3))
    print()

    # Fit using the Levenberg-Marquardt method with the result of the previous fit as initial guess
    logger.info('Começou o sexto processo de minimização...')
    out6 = minner2.minimize(method='least_squares', params=out5.params)
    # lmfit.report_fit(out6)
    logger.info('Terminou o quinto processo de minimização...')

    print('R2=', 1 - out6.residual.var() / np.var(deaths3))
    print()

    param_err = []
    for name_par, param in out5.params.items():
        if (not (param.stderr is None)) & (param.value != 0):
            param_err.append(param.stderr / param.value)

    param_err1 = []
    for name_par, param in out6.params.items():
        if (not (param.stderr is None)) & (param.value != 0):
            param_err1.append(param.stderr / param.value)

    for i in param_err1:
        if i > 1:
            print('hello mf!')
            out6 = out5

    if any(x > 1 for x in param_err1) or np.sum(param_err1) > np.sum(param_err):
        print('hello mf!')
        out6 = out5

    params = out6.params
    r1 = params['r1']
    a1 = params['a1']
    K1 = params['K1']
    p1 = params['p1']
    q1 = params['q1']
    r2 = params['r2']
    a2 = params['a2']
    K2 = params['K2']
    p2 = params['p2']
    q2 = params['q2']
    rho = params['rho']
    t_0 = params['t_0']
    r3 = params['r3']
    a3 = params['a3']
    K3 = params['K3']
    p3 = params['p3']
    q3 = params['q3']
    rho1 = params['rho1']
    t_1 = params['t_1']

    logger.info('O fit terminou...')
    temp_final = datetime.now()
    logger.info(f"Duração: {temp_final - temp_inicio}")

    return (r1, a1, K1, p1, q1, r2, a2, K2, p2, q2, r3, a3, K3, p3, q3, rho, t_0, rho1, t_1)


def modelo_acumulado(params, deltaTempo, tmax, y0):
    t = np.linspace(0, int(1 * tmax) - 1 + deltaTempo, 2000)
    C1 = odeint(deriv2, y0, t, args=params).T[0]
    return [t, C1]


def modelo_diario(params, deltaTempo, tmax, y0):
    t = np.linspace(0, int(1 * tmax) - 1 + deltaTempo, 2000)
    C1 = odeint(deriv2, y0, t, args=params).T[0]

    params = list(params)
    params.insert(0, t)
    params.insert(0, C1)

    daily_theo = deriv2(*params)
    peaks, _ = find_peaks(daily_theo)
    peaks1, _ = find_peaks(-daily_theo)

    return [t, daily_theo, peaks, peaks1]