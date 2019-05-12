"""
Author: Gustavo Amarante
"""

import numpy as np
import pandas as pd
import pykalman
from scipy.optimize import minimize
import statsmodels.api as sm
import matplotlib.pyplot as plt
import time

# TODO write example file


class Rstar(object):
    """
    This class replicates the model developed by holston, laubach & williams (2016).
    """

    def __init__(self, logGDP, inflation, NominalRate, RealRate, ar_c=None, by_c=None, run_se=False, niter=500,
                 charts=False, smoothed=True):
        """
        :param logGDP: natural logarithm of real GDP index
        :param inflation: seasonally adjusted annualized quarterly inflation rate
        :param NominalRate: Nominal short-term interest rate
        :param RealRate: Your preferred measure of real interest rate
        :param ar_c: Upper bound constraint for the slope of the IS curve
        :param by_c: Lower bound constraint for the slope of the phillips curve
        :param run_se: if True, runs the bootstrap to compute standard errors for the est
        :param niter: number of repetitions for the bootstrap of the standard errors
        :param charts: if True, makes charts for Rstar, output gap and trend growth
        :param smoothed: If True, state varibles are the smoothed estimates. If False, they are the filtered estimates
        """
        self.logGDP = logGDP
        self.inflation = inflation
        self.NominalRate = NominalRate
        self.RealRate = RealRate
        self.ar_c = ar_c
        self.by_c = by_c
        self.run_se = run_se
        self.niter = niter
        self.Charts = charts
        self.smoothed = smoothed

    def RunEstimation(self):
        """
        Takes the series and parameters of the estimation and calls the methods for each stage of the estimation.
        :return: DataFrame containing the Kalman estimates for output gap, trend growth, R star and other factors z
        """

        start_time = time.time()
        print('Starting estimation... \n')

        # Run the stage 1 model
        OutStage1 = self.RstarStage1()

        # Median Unbiased Estimate of lambda_g
        lambda_g = Rstar.MedianUnbiasedEstimatorStage1(OutStage1)

        # Run the stage 2 model
        y_mue, x_mue = self.RstarStage2(lambda_g)

        # Median Unbiased Estimate of lambda_z
        lambda_z = Rstar.MedianUnbiasedEstimatorStage2(y_mue, x_mue)

        # Run the stage 3 model
        trend_smoothed, z_smoothed, rstar_smoothed, potential_smoothed, output_gap_smoothed, trend_se, z_se, potential_se, rstar_se = self.RstarStage3(lambda_g, lambda_z)

        # TIME!
        print("===== Estimation DONE =====\nTotal time: %s minutes" % round(((time.time() - start_time) / 60), 2))

        # Organize Output in a DataFrame / MoE = Margin of Error for 90% confidence
        output_size = rstar_smoothed.shape[0]
        outputDF = pd.DataFrame({'R Star': rstar_smoothed,
                                 'Output Gap': output_gap_smoothed,
                                 'Trend Growth': trend_smoothed,
                                 'Z': z_smoothed,
                                 'MoE R Star': 1.644*rstar_se,
                                 'MoE Output Gap': 1.644 * potential_se*100,
                                 'MoE Trend Growth': 1.644 * trend_se,
                                 'MoE Z': 1.644 * z_se},
                                index=self.logGDP.index[-output_size:])

        # Make Charts
        if self.Charts:
            fig = plt.figure(figsize=(11, 8))

            # R Star
            ax_rs = plt.subplot2grid((2, 2), (0, 0), colspan=2)
            ax_rs.plot(outputDF['R Star'], label=r'Neutral Real Rate $R^{\star}$')
            ax_rs.plot(self.RealRate, label='Effective Real Rate')
            ax_rs.set_title(r'Real Interest Rates')
            ax_rs.fill_between(outputDF['R Star'].index, outputDF['R Star'] + outputDF['MoE R Star'], outputDF['R Star'] - outputDF['MoE R Star'], color='blue', alpha=0.1)
            ax_rs.grid(axis='y', alpha=0.3)
            ax_rs.axhline(0, color='black', linewidth=0.5)
            plt.legend(loc='upper left')

            # Output gap
            ax_og = plt.subplot2grid((2, 2), (1, 0))
            ax_og.plot(outputDF['Output Gap'], label=r'Output Gap')
            ax_og.set_title(r'Output Gap')
            ax_og.fill_between(outputDF['Output Gap'].index, outputDF['Output Gap'] + outputDF['MoE Output Gap'], outputDF['Output Gap'] - outputDF['MoE Output Gap'], color='blue', alpha=0.1)
            ax_og.grid(axis='y', alpha=0.3)
            ax_og.axhline(0, color='black', linewidth=0.5)

            # Trend Growth
            ax_tg = plt.subplot2grid((2, 2), (1, 1))
            ax_tg.plot(outputDF['Trend Growth'], label=r'Trend Growth')
            ax_tg.set_title(r'Trend Growth')
            ax_tg.fill_between(outputDF['Trend Growth'].index, outputDF['Trend Growth'] + outputDF['MoE Trend Growth'], outputDF['Trend Growth'] - outputDF['MoE Trend Growth'], color='blue', alpha=0.1)
            ax_tg.grid(axis='y', alpha=0.3)
            ax_tg.axhline(0, color='black', linewidth=0.5)

            plt.show()

        return outputDF

    def RstarStage1(self):

        print('===== STAGE 1 =====')

        stage = 1

        # Data must start 4 quarters before the estimation period
        T = self.logGDP.shape[0] - 4

        # Original output gap estimate (linear time trend)
        x_og = np.concatenate((np.ones((T, 1)), np.arange(1, T + 1, 1).reshape((T, 1))), axis=1)
        y_og = self.logGDP[4:].values.reshape((T, 1))
        output_gap = (y_og - x_og.dot(np.linalg.solve(x_og.T.dot(x_og), x_og.T.dot(y_og)))) * 100

        # Initialization of state vector for the Kalman filter using HP trend of log output
        logGDP_HP_cycle, logGDP_HP_trend = sm.tsa.filters.hpfilter(self.logGDP, 1600)
        g_pot = np.flip(logGDP_HP_trend[0:3].values, axis=0).reshape((3, 1))
        xi_00 = 100*g_pot

        # IS curve
        y_is = output_gap[2: T]
        # y_is = logGDP_HP_cycle.values[6:].reshape((T - 2, 1))
        x_is = np.concatenate((output_gap[1:T-1], output_gap[0:T-2]), axis=1)
        b_is = np.linalg.solve(x_is.T.dot(x_is), x_is.T.dot(y_is))  # b stands for beta
        r_is = y_is - x_is.dot(b_is)  # r stands for residuals
        s_is = np.sqrt(r_is.T.dot(r_is) / (r_is.shape[0] - x_is.shape[1]))[0, 0]  # s stands for standard deviation of residuals (unbiased estimate)

        # Phillips Curve
        y_ph = self.inflation[4: T].values.reshape((T-4, 1))  # RESHAPE T-4
        x_ph = np.concatenate((self.inflation[3: T-1].values.reshape((T-4, 1)),
                               (self.inflation[2: T-2].values.reshape((T-4, 1)) + self.inflation[1: T-3].values.reshape((T-4, 1)) + self.inflation[0: T-4].values.reshape((T-4, 1))) / 3,
                               output_gap[3: T-1]), axis=1)
        b_ph = np.linalg.solve(x_ph.T.dot(x_ph), x_ph.T.dot(y_ph))  # b stands for beta
        r_ph = y_ph - x_ph.dot(b_ph)  # r stands for residuals
        s_ph = np.sqrt(r_ph.T.dot(r_ph) / (r_ph.shape[0] - x_ph.shape[1]))[0, 0]  # s stands for standard deviation of residuals (unbiased estimate)

        # Organize date in state-space form
        y_data = np.concatenate((100 * self.logGDP[4:T].values.reshape((T-4, 1)),
                                 self.inflation[4:T].values.reshape((T-4, 1))), axis=1)

        x_data = np.concatenate((100 * self.logGDP[3:T-1].values.reshape((T-4, 1)),
                                 100 * self.logGDP[2:T-2].values.reshape((T-4, 1)),
                                 self.inflation[3:T-1].values.reshape((T-4, 1)),
                                 (self.inflation[2:T-2].values.reshape((T-4, 1)) +
                                  self.inflation[1:T-3].values.reshape((T-4, 1)) +
                                  self.inflation[0:T-4].values.reshape((T-4, 1)) / 3)), axis=1)

        # Starting values for parameter vector (size 8) of stage 1 (Some of the guesses might be different for brazil)
        initial_parameters = np.array([b_is[0, 0], b_is[1, 0], b_ph[0, 0], b_ph[2, 0], 0.85, s_is, s_ph, 0.5])

        # Set an upper and lower bound on the parameter vectors
        theta_bounds = [(None, None),
                        (None, None),
                        (None, None),
                        (self.by_c, None),  # lower bound for the slope of the IS curve
                        (None, None),
                        (0, None),
                        (0, None),
                        (0, None)]

        # Make sure that the initial guess satisfies the bound
        if not (self.by_c is None):
            if initial_parameters[3] < self.by_c:
                initial_parameters[3] = self.by_c

        # Set the initial covariance matrix (see footnote 6 from the paper)
        P_00 = Rstar.CalculateCovariance(initial_parameters.copy(), theta_bounds.copy(), y_data.copy(), x_data.copy(), stage, None, None, xi_00.copy())

        # Increase P_00 precision. Note that this only happens in stage 1
        P_00 = P_00 + 0.0001 * np.eye(P_00.shape[0])

        # Get parameter estimates via maximum likelihood with bounds
        def f(theta):
            return -Rstar.LogLikelihoodWrapper(theta, y_data.copy(), x_data.copy(), stage, None, None, xi_00.copy(), P_00.copy())

        print('Starting Model Optimization')

        optimization_output = minimize(fun=f,
                                       x0=initial_parameters,
                                       method='L-BFGS-B',
                                       options={'disp': False,
                                                'maxiter': 500},
                                       jac=lambda x: Rstar.Gradient(f, x),
                                       bounds=theta_bounds,
                                       tol=0.0001)

        # verify if the optimization went right
        if optimization_output.success:
            print('Success! \n')
        else:
            # THE PROGRAM SHOULD STOP THE EXCUTION HERE
            print('FAILED \n')

        # Grabs the optimal values for parameters and the likelihood
        theta_star = optimization_output.x
        loglike_star = -optimization_output.fun

        # Get state vectors (xi.tt, xi.ttm1, xi.tT, P.tt, P.ttm1, P.tT) via Kalman filter
        filtered_states, filtered_cov, smoothed_states, smoothed_cov = Rstar.KalmanStatesWrapper(theta_star.copy(), y_data.copy(), x_data.copy(), stage, None, None, xi_00.copy(), P_00.copy())

        # One-sided (filtered) estimates
        potential_filtered = (filtered_states[:, 0] / 100).reshape((filtered_states[:, 0].shape[0], 1))  # <- states$filtered$xi.tt[,1]/100
        output_gap_filtered = y_data[:, 0].reshape((y_data[:, 0].shape[0], 1)) - (potential_filtered * 100)  # <- y.data[,1] - (potential.filtered * 100)

        # Two-sided (smoothed) estimates
        potential_smoothed = (smoothed_states[:, 0] / 100).reshape((smoothed_states[:, 0].shape[0], 1))  # <- as.vector(states$smoothed$xi.tT[,1])/100
        output_gap_smoothed = y_data[:, 0].reshape((y_data[:, 0].shape[0], 1)) - (potential_smoothed * 100)   # y.data[,1] - (potential.smoothed * 100)

        return potential_smoothed  # theta_star, loglike_star, states, xi_00, P_00, potential_filtered, output_gap_filtered, potential_smoothed, output_gap_smoothed, logGDP_HP_cycle

    def RstarStage2(self, lambda_g):

        print('===== STAGE 2 =====')

        stage = 2

        # Data must start 4 quarters before the estimation period
        T = self.logGDP.shape[0] - 4

        # Original output gap estimate (linear time trend)
        x_og = np.concatenate((np.ones((T, 1)), np.arange(1, T + 1, 1).reshape((T, 1))), axis=1)
        y_og = self.logGDP[4:].values.reshape((T, 1))
        output_gap = (y_og - x_og.dot(np.linalg.solve(x_og.T.dot(x_og), x_og.T.dot(y_og)))) * 100

        # Initialization of state vector for the Kalman filter using HP trend of log output
        logGDP_HP_cycle, logGDP_HP_trend = sm.tsa.filters.hpfilter(self.logGDP, 1600)
        g_pot = logGDP_HP_trend.values
        g_pot_diff = np.diff(g_pot)
        xi_00 = np.array([100*g_pot[2], 100*g_pot[1], 100*g_pot[0], 100*g_pot_diff[1]]).reshape((4, 1))

        # IS curve
        y_is = output_gap[2: T]
        # y_is = logGDP_HP_cycle.values[6:].reshape((T - 2, 1))
        x_is = np.concatenate((output_gap[1:T - 1].reshape((T-2, 1)), output_gap[0:T - 2].reshape((T-2, 1)),
                               (self.RealRate[1:T-1].values.reshape((T-2, 1)) + self.RealRate[0:T-2].values.reshape((T-2, 1)))/2,
                               np.ones((T-2, 1))), axis=1)
        b_is = np.linalg.solve(x_is.T.dot(x_is), x_is.T.dot(y_is))  # b stands for beta
        r_is = y_is - x_is.dot(b_is)  # r stands for residuals
        s_is = np.sqrt(r_is.T.dot(r_is) / (r_is.shape[0] - x_is.shape[1]))[0, 0]  # s stands for standard deviation of residuals (unbiased estimate)

        # Phillips Curve
        y_ph = self.inflation[4: T].values.reshape((T - 4, 1))  # RESHAPE T-4
        x_ph = np.concatenate((self.inflation[3: T - 1].values.reshape((T - 4, 1)),
                               (self.inflation[2: T - 2].values.reshape((T - 4, 1)) + self.inflation[1: T - 3].values.reshape((T - 4, 1)) + self.inflation[0: T - 4].values.reshape((T - 4, 1))) / 3,
                               output_gap[3: T - 1]), axis=1)
        b_ph = np.linalg.solve(x_ph.T.dot(x_ph), x_ph.T.dot(y_ph))  # b stands for beta
        r_ph = y_ph - x_ph.dot(b_ph)  # r stands for residuals
        s_ph = np.sqrt(r_ph.T.dot(r_ph) / (r_ph.shape[0] - x_ph.shape[1]))[0, 0]  # s stands for standard deviation of residuals (unbiased estimate)

        # Organize date in state-space form
        y_data = np.concatenate((100 * self.logGDP[4:T].values.reshape((T - 4, 1)),
                                 self.inflation[4:T].values.reshape((T - 4, 1))), axis=1)

        x_data = np.concatenate((100 * self.logGDP[3:T - 1].values.reshape((T - 4, 1)),
                                 100 * self.logGDP[2:T - 2].values.reshape((T - 4, 1)),
                                 self.RealRate[3:T - 1].values.reshape((T - 4, 1)),
                                 self.RealRate[2:T - 2].values.reshape((T - 4, 1)),
                                 self.inflation[3:T - 1].values.reshape((T - 4, 1)),
                                 (self.inflation[2:T - 2].values.reshape((T - 4, 1)) +
                                  self.inflation[1:T - 3].values.reshape((T - 4, 1)) +
                                  self.inflation[0:T - 4].values.reshape((T - 4, 1))) / 3,
                                 np.ones((T-4, 1))), axis=1)

        # Starting values for the parameter vector (size 10) of stage 2
        initial_parameters = np.array([b_is[0, 0], b_is[1, 0], b_is[2, 0], b_is[3, 0],
                                       -b_is[2, 0], b_ph[0, 0], b_ph[2, 0], s_is, s_ph, 0.5])

        # Set an upper and lower bound on the parameter vectors
        theta_bounds = [(None, None),
                        (None, None),
                        (None, self.ar_c),
                        (None, None),  # lower bound for the slope of the IS curve
                        (None, None),
                        (None, None),
                        (self.by_c, None),
                        (0, None),
                        (0, None),
                        (0, None)]

        # Make sure that the initial guess satisfies the bound
        if not (self.by_c is None):
            if initial_parameters[6] < self.by_c:
                initial_parameters[6] = self.by_c

        if not (self.ar_c is None):
            if initial_parameters[2] > self.ar_c:
                initial_parameters[2] = self.ar_c

        # Set the initial covariance matrix (see footnote 6 from the paper)
        P_00 = Rstar.CalculateCovariance(initial_parameters.copy(), theta_bounds.copy(), y_data.copy(), x_data.copy(),
                                         stage, lambda_g, None, xi_00.copy())

        # Get parameter estimates via maximum likelihood with bounds
        def f(theta):
            return -Rstar.LogLikelihoodWrapper(theta, y_data.copy(), x_data.copy(), stage, lambda_g, None, xi_00.copy(),
                                               P_00.copy())

        print('Starting Model Optimization')

        optimization_output = minimize(fun=f,
                                       x0=initial_parameters,
                                       method='L-BFGS-B',
                                       options={'disp': False,
                                                'maxiter': 500},
                                       jac=lambda x: Rstar.Gradient(f, x),
                                       bounds=theta_bounds,
                                       tol=0.0001)

        # verify if the optimization went right
        if optimization_output.success:
            print('Success! \n')
        else:
            # THE PROGRAM SHOULD STOP THE EXCUTION HERE
            print('FAILED \n')

        # Grabs the optimal values for parameters and the likelihood
        theta_star = optimization_output.x
        loglike_star = -optimization_output.fun

        # Get state vectors (xi.tt, xi.ttm1, xi.tT, P.tt, P.ttm1, P.tT) via Kalman filter
        filtered_states, filtered_cov, smoothed_states, smoothed_cov = Rstar.KalmanStatesWrapper(theta_star.copy(), y_data.copy(), x_data.copy(), stage, lambda_g, None, xi_00.copy(), P_00.copy())

        # Two-sided (smoothed) estimates
        trend_smoothed = smoothed_states[:, 3] * 4
        potential_smoothed = np.concatenate((smoothed_states[0:2, 2], smoothed_states[:, 0]), axis=0)
        output_gap_smoothed = 100*self.logGDP.values[6:] - potential_smoothed

        # Inputs for MedianUnbiasedEstimatorStage2
        size = output_gap_smoothed.shape[0]
        y_mue = output_gap_smoothed[2:size].reshape((size-2, 1))
        x_mue = np.concatenate((output_gap_smoothed[1:size-1].reshape((size-2, 1)),
                                output_gap_smoothed[0:size-2].reshape((size-2, 1)),
                                (x_data[:, 2].reshape((size-2, 1)) + x_data[:, 4].reshape((size-2, 1)))/2,
                                smoothed_states[:, 3].reshape((size - 2, 1)),
                                np.ones((size-2, 1))), axis=1)

        # One-sided (filtered) estimates
        trend_filtered = filtered_states[:, 3] * 4
        potential_filtered = np.concatenate((filtered_states[0:2, 2], filtered_states[:, 0]), axis=0)
        output_gap_filtered = 100 * self.logGDP.values[6:] - potential_filtered

        # save variables to return

        return y_mue, x_mue

    def RstarStage3(self, lambda_g, lambda_z):

        print('===== STAGE 3 =====')

        stage = 3

        # Data must start 4 quarters before the estimation period
        T = self.logGDP.shape[0] - 4

        # Original output gap estimate (linear time trend)
        x_og = np.concatenate((np.ones((T, 1)), np.arange(1, T + 1, 1).reshape((T, 1))), axis=1)
        y_og = self.logGDP[4:].values.reshape((T, 1))
        output_gap = (y_og - x_og.dot(np.linalg.solve(x_og.T.dot(x_og), x_og.T.dot(y_og)))) * 100

        # Initialization of state vector for the Kalman filter using HP trend of log output
        logGDP_HP_cycle, logGDP_HP_trend = sm.tsa.filters.hpfilter(self.logGDP, 1600)
        g_pot = logGDP_HP_trend.values
        g_pot_diff = np.diff(g_pot)
        xi_00 = np.array([100 * g_pot[2], 100 * g_pot[1], 100 * g_pot[0],
                          100 * g_pot_diff[2], 100 * g_pot_diff[1], 0, 0]).reshape((7, 1))

        # IS curve
        y_is = output_gap[2: T]
        # y_is = logGDP_HP_cycle.values[6:].reshape((T - 2, 1))
        x_is = np.concatenate((output_gap[1:T - 1].reshape((T - 2, 1)), output_gap[0:T - 2].reshape((T - 2, 1)),
                               (self.RealRate[1:T - 1].values.reshape((T - 2, 1)) + self.RealRate[0:T - 2].values.reshape((T - 2, 1))) / 2,
                               np.ones((T - 2, 1))), axis=1)
        b_is = np.linalg.solve(x_is.T.dot(x_is), x_is.T.dot(y_is))  # b stands for beta
        r_is = y_is - x_is.dot(b_is)  # r stands for residuals
        s_is = np.sqrt(r_is.T.dot(r_is) / (r_is.shape[0] - x_is.shape[1]))[0, 0]  # s stands for standard deviation of residuals (unbiased estimate)

        # Phillips Curve
        y_ph = self.inflation[4: T].values.reshape((T - 4, 1))  # RESHAPE T-4
        x_ph = np.concatenate((self.inflation[3: T - 1].values.reshape((T - 4, 1)),
                               (self.inflation[2: T - 2].values.reshape((T - 4, 1)) + self.inflation[1: T - 3].values.reshape((T - 4, 1)) + self.inflation[0: T - 4].values.reshape((T - 4, 1))) / 3,
                               output_gap[3: T - 1]), axis=1)
        b_ph = np.linalg.solve(x_ph.T.dot(x_ph), x_ph.T.dot(y_ph))  # b stands for beta
        r_ph = y_ph - x_ph.dot(b_ph)  # r stands for residuals
        s_ph = np.sqrt(r_ph.T.dot(r_ph) / (r_ph.shape[0] - x_ph.shape[1]))[0, 0]  # s stands for standard deviation of residuals (unbiased estimate)

        # Organize date in state-space form
        y_data = np.concatenate((100 * self.logGDP[4:T].values.reshape((T - 4, 1)),
                                 self.inflation[4:T].values.reshape((T - 4, 1))), axis=1)

        x_data = np.concatenate((100 * self.logGDP[3:T - 1].values.reshape((T - 4, 1)),
                                 100 * self.logGDP[2:T - 2].values.reshape((T - 4, 1)),
                                 self.RealRate[3:T - 1].values.reshape((T - 4, 1)),
                                 self.RealRate[2:T - 2].values.reshape((T - 4, 1)),
                                 self.inflation[3:T - 1].values.reshape((T - 4, 1)),
                                 (self.inflation[2:T - 2].values.reshape((T - 4, 1)) +
                                  self.inflation[1:T - 3].values.reshape((T - 4, 1)) +
                                  self.inflation[0:T - 4].values.reshape((T - 4, 1))) / 3), axis=1)

        # Starting values for the parameter vector (size 10) of stage 2
        initial_parameters = np.array([b_is[0, 0], b_is[1, 0], b_is[2, 0],
                                       b_ph[0, 0], b_ph[2, 0], s_is, s_ph, 0.7])

        # Set an upper and lower bound on the parameter vectors
        theta_bounds = [(None, None),
                        (None, None),
                        (None, self.ar_c),
                        (None, None),
                        (self.by_c, None),
                        (0, None),
                        (0, None),
                        (0, None)]

        # Make sure that the initial guess satisfies the bound
        if not (self.by_c is None):
            if initial_parameters[4] < self.by_c:
                initial_parameters[4] = self.by_c

        if not (self.ar_c is None):
            if initial_parameters[2] > self.ar_c:
                initial_parameters[2] = self.ar_c

        # Set the initial covariance matrix (see footnote 6 from the paper)
        P_00 = Rstar.CalculateCovariance(initial_parameters.copy(), theta_bounds.copy(), y_data.copy(), x_data.copy(),
                                         stage, lambda_g, lambda_z, xi_00.copy())

        # Get parameter estimates via maximum likelihood with bounds
        def f(theta):
            return -Rstar.LogLikelihoodWrapper(theta, y_data.copy(), x_data.copy(), stage, lambda_g, lambda_z, xi_00.copy(),
                                               P_00.copy())

        print('Starting Model Optimization')

        optimization_output = minimize(fun=f,
                                       x0=initial_parameters,
                                       method='L-BFGS-B',
                                       options={'disp': False,
                                                'maxiter': 500},
                                       jac=lambda x: Rstar.Gradient(f, x),
                                       bounds=theta_bounds,
                                       tol=0.0001)

        # verify if the optimization went right
        if optimization_output.success:
            print('Success! \n')
        else:
            # THE PROGRAM SHOULD STOP THE EXCUTION HERE
            print('FAILED \n')

        # Grabs the optimal values for parameters and the likelihood
        theta_star = optimization_output.x
        loglike_star = -optimization_output.fun

        # Get state vectors (xi.tt, xi.ttm1, xi.tT, P.tt, P.ttm1, P.tT) via Kalman filter
        filtered_states, filtered_cov, smoothed_states, smoothed_cov = Rstar.KalmanStatesWrapper(theta_star.copy(),
                                                                                                 y_data.copy(),
                                                                                                 x_data.copy(), stage,
                                                                                                 lambda_g, lambda_z,
                                                                                                 xi_00.copy(),
                                                                                                 P_00.copy())

        if self.smoothed:

            trend_smoothed = smoothed_states[:, 3] * 4
            z_smoothed = smoothed_states[:, 5]
            rstar_smoothed = trend_smoothed + z_smoothed
            potential_smoothed = smoothed_states[:, 0] / 100
            output_gap_smoothed = 100 * (self.logGDP.values[8:] - potential_smoothed)

            trend_se_smoothed = np.sqrt(smoothed_cov[:, 3, 3]) * 4  # multiply by 4 as well? YES?
            z_se_smoothed = np.sqrt(smoothed_cov[:, 5, 5])
            potential_se_smoothed = np.sqrt(smoothed_cov[:, 0, 0]) / 100  # divide by 100 as well? Yes?
            rstar_se_smoothed = np.sqrt(smoothed_cov[:, 3, 3] * 4 + smoothed_cov[:, 5, 5] + 2 * smoothed_cov[:, 3, 5])

            return trend_smoothed, z_smoothed, rstar_smoothed, potential_smoothed, output_gap_smoothed, trend_se_smoothed, z_se_smoothed, potential_se_smoothed, rstar_se_smoothed

        else:

            trend_filtered = filtered_states[:, 3] * 4
            z_filtered = filtered_states[:, 5]
            rstar_filtered = trend_filtered + z_filtered
            potential_filtered = filtered_states[:, 0] / 100
            output_gap_filtered = 100 * (self.logGDP.values[8:] - potential_filtered)

            trend_se_filtered = np.sqrt(filtered_cov[:, 3, 3]) * 4  # multiply by 4 as well? YES?
            z_se_filtered = np.sqrt(filtered_cov[:, 5, 5])
            potential_se_filtered = np.sqrt(filtered_cov[:, 0, 0]) / 100  # divide by 100 as well? Yes?
            rstar_se_filtered = np.sqrt(filtered_cov[:, 3, 3] * 4 + filtered_cov[:, 5, 5] + 2 * filtered_cov[:, 3, 5])

            return trend_filtered, z_filtered, rstar_filtered, potential_filtered, output_gap_filtered, trend_se_filtered, z_se_filtered, potential_se_filtered, rstar_se_filtered

    @staticmethod
    def UnpackStage1(parameters, y_data, x_data):
        stage = 1

        A = np.zeros((2, 4))
        A[0, 0] = parameters[0]
        A[0, 1] = parameters[1]
        A[1, 0] = parameters[3]
        A[1, 2] = parameters[2]
        A[1, 3] = 1 - parameters[2]

        H = np.zeros((2, 3))
        H[0, 0] = 1
        H[0, 1] = -parameters[0]
        H[0, 2] = -parameters[1]
        H[1, 1] = -parameters[3]

        R = np.zeros((2, 2))
        R[0, 0] = parameters[5] ** 2
        R[1, 1] = parameters[6] ** 2

        Q = np.zeros((3, 3))
        Q[0, 0] = parameters[7] ** 2

        F = np.zeros((3, 3))
        F[0, 0] = 1
        F[1, 0] = 1
        F[2, 1] = 1

        # Make Data Stationary
        y_data[:, 0] = y_data[:, 0] - np.arange(1, y_data.shape[0] + 1, 1) * parameters[4]
        x_data[:, 0] = x_data[:, 0] - np.arange(0, x_data.shape[0], 1) * parameters[4]
        x_data[:, 1] = x_data[:, 1] - np.arange(-1, x_data.shape[0] - 1, 1) * parameters[4]

        return stage, A, H, R, Q, F, x_data, y_data

    @staticmethod
    def UnpackStage2(parameters, lambda_g):
        """
        ??????
        :param parameters:
        :param lambda_g:
        :return:
        """

        stage = 2

        A = np.zeros((2, 7))
        A[0, 0] = parameters[0]
        A[0, 1] = parameters[1]
        A[0, 2] = parameters[2] / 2
        A[0, 3] = parameters[2] / 2
        A[0, 6] = parameters[3]
        A[1, 0] = parameters[6]
        A[1, 4] = parameters[5]
        A[1, 5] = 1 - parameters[5]

        H = np.zeros((2, 4))
        H[0, 0] = 1
        H[0, 1] = -parameters[0]
        H[0, 2] = -parameters[1]
        H[0, 3] = parameters[4]
        H[1, 1] = -parameters[6]

        R = np.zeros((2, 2))
        R[0, 0] = parameters[7] ** 2
        R[1, 1] = parameters[8] ** 2

        Q = np.zeros((4, 4))
        Q[0, 0] = parameters[9] ** 2
        Q[3, 3] = (lambda_g * parameters[9]) ** 2

        F = np.zeros((4, 4))
        F[0, 0] = 1
        F[0, 3] = 1
        F[1, 0] = 1
        F[2, 1] = 1
        F[3, 3] = 1

        return stage, A, H, R, Q, F

    @staticmethod
    def UnpackStage3(parameters, lambda_g, lambda_z):

        stage = 3

        A = np.zeros((2, 6))
        A[0, 0] = parameters[0]
        A[0, 1] = parameters[1]
        A[0, 2] = parameters[2] / 2
        A[0, 3] = parameters[2] / 2
        A[1, 0] = parameters[4]
        A[1, 4] = parameters[3]
        A[1, 5] = 1 - parameters[3]

        H = np.zeros((2, 7))
        H[0, 0] = 1
        H[0, 1] = -parameters[0]
        H[0, 2] = -parameters[1]
        H[0, 3] = -(parameters[2] / 2) * 4  # annualized
        H[0, 4] = -(parameters[2] / 2) * 4  # annualized
        H[0, 5] = -parameters[2] / 2
        H[0, 6] = -parameters[2] / 2
        H[1, 1] = -parameters[4]

        R = np.zeros((2, 2))
        R[0, 0] = parameters[5] ** 2
        R[1, 1] = parameters[6] ** 2

        Q = np.zeros((7, 7))
        Q[0, 0] = (1 + lambda_g ** 2) * parameters[7] ** 2
        Q[0, 3] = (lambda_g * parameters[7]) ** 2
        Q[3, 0] = (lambda_g * parameters[7]) ** 2
        Q[3, 3] = (lambda_g * parameters[7]) ** 2
        Q[5, 5] = ((lambda_z * parameters[5]) / parameters[2]) ** 2

        F = np.zeros((7, 7))
        F[0, 0] = 1
        F[0, 3] = 1
        F[1, 0] = 1
        F[2, 1] = 1
        F[3, 3] = 1
        F[4, 3] = 1
        F[5, 5] = 1
        F[6, 5] = 1

        return stage, A, H, R, Q, F

    @staticmethod
    def LogLikelihoodWrapper(parameters, y_data, x_data, stage, lambda_g, lambda_z, xi_00, P_00):

        if stage == 1:
            stage, A, H, R, Q, F, x_data, y_data = Rstar.UnpackStage1(parameters, y_data, x_data)

        elif stage == 2:
            stage, A, H, R, Q, F = Rstar.UnpackStage2(parameters, lambda_g)

        elif stage == 3:
            stage, A, H, R, Q, F = Rstar.UnpackStage3(parameters, lambda_g, lambda_z)

        else:
            pass  # PROGRAM SHOULD STOP HERE

        exogenous_variables = (A.dot(x_data.T)).transpose()

        loglike = pykalman.KalmanFilter(transition_matrices=F,
                                        transition_offsets=np.zeros((xi_00.shape[0])),
                                        transition_covariance=Q,
                                        observation_matrices=H,
                                        observation_offsets=exogenous_variables,
                                        observation_covariance=R,
                                        initial_state_mean=xi_00.reshape(xi_00.shape[0]),
                                        initial_state_covariance=P_00).loglikelihood(y_data)

        return loglike

    @staticmethod
    def KalmanStatesWrapper(parameters, y_data, x_data, stage, lambda_g, lambda_z, xi_00, P_00):

        if stage == 1:
            stage, A, H, R, Q, F, x_data, y_data = Rstar.UnpackStage1(parameters, y_data, x_data)

        elif stage == 2:
            stage, A, H, R, Q, F = Rstar.UnpackStage2(parameters, lambda_g)

        elif stage == 3:
            stage, A, H, R, Q, F = Rstar.UnpackStage3(parameters, lambda_g, lambda_z)

        else:
            pass  # PROGRAM SHOULD STOP HERE

        exogenous_variables = (A.dot(x_data.T)).transpose()  # NEED TO CHECK THE DIMENSION

        kf = pykalman.KalmanFilter(transition_matrices=F,
                                   transition_offsets=np.zeros((xi_00.shape[0])),
                                   transition_covariance=Q,
                                   observation_matrices=H,
                                   observation_offsets=exogenous_variables,
                                   observation_covariance=R,
                                   initial_state_mean=xi_00.reshape(xi_00.shape[0]),
                                   initial_state_covariance=P_00)

        # SHOULD I PUT THIS ON A DATAFRAME?
        filtered_states, filtered_cov = kf.filter(y_data)
        smoothed_states, smoothed_cov = kf.smooth(y_data)

        # If we are on the first stage, we should retrend the esimated states
        if stage == 1:
            T = filtered_states.shape[0]
            filtered_states  = filtered_states + parameters[4]*np.concatenate((np.arange(1, T+1, 1).reshape((T, 1)),
                                                                               np.arange(0, T, 1).reshape((T, 1)),
                                                                               np.arange(-1, T-1, 1).reshape((T, 1))), axis=1)

            smoothed_states = smoothed_states + parameters[4] * np.concatenate((np.arange(1, T + 1, 1).reshape((T, 1)),
                                                                                np.arange(0, T, 1).reshape((T, 1)),
                                                                                np.arange(-1, T - 1, 1).reshape((T, 1))), axis=1)

        return filtered_states, filtered_cov, smoothed_states, smoothed_cov

    @staticmethod
    def CalculateCovariance(initial_parameters, theta_bounds, y_data, x_data, stage, lambda_g, lambda_z, xi_00):

        n_state_vars = xi_00.shape[0]

        # Set covariance matrix equal to 0.2 times the identity matrix
        P_00 = 0.2 * np.eye(n_state_vars)

        # Get parameter estimates via maximum likelihood
        def f(theta):
            return -Rstar.LogLikelihoodWrapper(theta, y_data.copy(), x_data.copy(), stage, lambda_g, lambda_z, xi_00.copy(), P_00.copy())

        print('Starting Covariance Optimization')

        optimization_output = minimize(fun=f,
                                       x0=initial_parameters,
                                       method='L-BFGS-B',
                                       options={'disp': False,
                                                'maxiter': 500},
                                       jac=lambda x: Rstar.Gradient(f, x),
                                       bounds=theta_bounds,
                                       tol=0.0001)

        # verify if the optimization went right
        if optimization_output.success:
            print('Success!\n')
        else:
            # THE PROGRAM SHOULD STOP THE EXCUTION HERE
            print('FAILED\n')

        # Grabs the optimal values for parameters
        theta_star = optimization_output.x

        filtered_states, filtered_cov, smoothed_states, smoothed_cov = Rstar.KalmanStatesWrapper(theta_star.copy(), y_data.copy(), x_data.copy(), stage, lambda_g, lambda_z, xi_00.copy(), P_00.copy())

        # return the first covariance matrix
        return filtered_cov[0]

    @staticmethod
    def Gradient(f, x, delta=0.00001):

        # generates a g vector of zeros with the same size as x
        g = x * 0

        for i in range(x.shape[0]):
            x1 = x
            x1[i] = x1[i] + delta
            f1 = f(x1)
            x2 = x
            x2[i] = x2[i] - delta
            f2 = f(x2)
            g[i] = (f1 - f2) / (2*delta)

        return g

    @staticmethod
    def MedianUnbiasedEstimatorStage1(series):

        print('Mean Unbiased Estimator for lambda_g \n')

        T = series.shape[0]
        y = 400*np.diff(series, axis=0)

        stat = np.zeros(T - 2*4)

        for i in range(4, T - 4):
            xr = np.concatenate((np.ones((T-1, 1)), np.concatenate((np.zeros((i, 1)), np.ones((T-i-1, 1))), axis=0)), axis=1)
            xi = np.linalg.solve(xr.T.dot(xr), np.eye(2))
            b  = np.linalg.solve(xr.T.dot(xr), xr.T.dot(y))
            s3 = ((y - xr.dot(b)).T.dot(y - xr.dot(b))[0, 0]) / (T - 3)
            stat[i-4] = b[1, 0] / np.sqrt(s3*xi[1, 1])

        # Exponential wald statistic (ew), mean wald statistic (mw) and the teste statistic (qlr)
        ew = 0

        for i in range(0, stat.shape[0]):
            ew = ew + np.exp((stat[i]**2) / 2)

        ew = np.log(ew / stat.shape[0])
        mw = np.sum(np.square(stat)) / stat.shape[0]
        qlr = np.max(np.square(stat))

        # Values are from Table 3 in Stock and Watson (1998)
        # Test Statistic: Exponential Wald (EW)
        valew = np.array([0.426, 0.476, 0.516, 0.661, 0.826, 1.111,
                          1.419, 1.762, 2.355, 2.91,  3.413, 3.868, 4.925,
                          5.684, 6.670, 7.690, 8.477, 9.191, 10.693, 12.024,
                          13.089, 14.440, 16.191, 17.332, 18.699, 20.464,
                          21.667, 23.851, 25.538, 26.762, 27.874])

        # Test Statistic: Mean Wald (MW)
        valmw = np.array([0.689, 0.757, 0.806, 1.015, 1.234, 1.632,
                          2.018, 2.390, 3.081, 3.699, 4.222, 4.776, 5.767,
                          6.586, 7.703, 8.683, 9.467, 10.101, 11.639, 13.039,
                          13.900, 15.214, 16.806, 18.330, 19.020, 20.562,
                          21.837, 24.350, 26.248, 27.089, 27.758])

        # Test Statistic: QLR
        valql = np.array([3.198, 3.416, 3.594, 4.106, 4.848, 5.689,
                          6.682, 7.626, 9.16,  10.66, 11.841, 13.098, 15.451,
                          17.094, 19.423, 21.682, 23.342, 24.920, 28.174, 30.736,
                          33.313, 36.109, 39.673, 41.955, 45.056, 48.647, 50.983,
                          55.514, 59.278, 61.311, 64.016])

        lame = None
        lamm = None
        lamq = None

        # Median-unbiased estimator of lambda_g for given values of the test
        # statistics are obtained using the procedure described in the
        # footnote to Stock and Watson (1998) Table 3.

        # exponential wald
        if ew <= valew[0]:
            lame = 0
        else:
            for i in range(0, valew.shape[0] - 1):
                if (ew > valew[i]) and (ew <= valew[i+1]):
                    lame = i + (ew - valew[i]) / (valew[i+1] - valew[i])

        # median wald
        if mw <= valmw[0]:
            lamm = 0
        else:
            for i in range(0, valmw.shape[0] - 1):
                if (mw > valmw[i]) and (mw <= valmw[i+1]):
                    lamm = i + (mw - valmw[i]) / (valmw[i+1] - valmw[i])

        # qlr stat
        if qlr <= valql[0]:
            lamq = 0
        else:
            for i in range(0, valql.shape[0] - 1):
                if (qlr > valql[i]) and (qlr <= valql[i+1]):
                    lamq = i + (qlr - valql[i]) / (valql[i+1] - valql[i])

        # check for statistics outside of table
        if all([lame is None, lamm is None, lamq is None]):
            print('At least one statistic has an NA value.'
                  'Check to see if your EW, MW, and/or QLR value is outside of Table 3.')

        return lame/(T - 1)

    @staticmethod
    def MedianUnbiasedEstimatorStage2(y_mue, x_mue):

        print('Mean Unbiased Estimator for lambda_z \n')

        T = y_mue.shape[0]

        stat = np.zeros(T - 2*4 + 1)

        for i in range(4, T - 4):
            xr = np.concatenate((x_mue, np.concatenate((np.zeros((i, 1)), np.ones((T - i, 1))), axis=0)), axis=1)
            xi = np.linalg.solve(xr.T.dot(xr), np.eye(6))
            b = np.linalg.solve(xr.T.dot(xr), xr.T.dot(y_mue))
            s3 = ((y_mue - xr.dot(b)).T.dot(y_mue - xr.dot(b))[0, 0]) / (T - 6)
            stat[i + 1 - 4] = b[5, 0] / np.sqrt(s3 * xi[5, 5])

        # Exponential wald statistic (ew), mean wald statistic (mw) and the teste statistic (qlr)
        ew = 0

        for i in range(0, stat.shape[0]):
            ew = ew + np.exp((stat[i] ** 2) / 2)

        ew = np.log(ew / stat.shape[0])
        mw = np.mean(np.square(stat))
        qlr = np.max(np.square(stat))

        # Values are from Table 3 in Stock and Watson (1998)
        # Test Statistic: Exponential Wald (EW)
        valew = np.array([0.426, 0.476, 0.516, 0.661, 0.826, 1.111,
                          1.419, 1.762, 2.355, 2.91, 3.413, 3.868, 4.925,
                          5.684, 6.670, 7.690, 8.477, 9.191, 10.693, 12.024,
                          13.089, 14.440, 16.191, 17.332, 18.699, 20.464,
                          21.667, 23.851, 25.538, 26.762, 27.874])

        # Test Statistic: Mean Wald (MW)
        valmw = np.array([0.689, 0.757, 0.806, 1.015, 1.234, 1.632,
                          2.018, 2.390, 3.081, 3.699, 4.222, 4.776, 5.767,
                          6.586, 7.703, 8.683, 9.467, 10.101, 11.639, 13.039,
                          13.900, 15.214, 16.806, 18.330, 19.020, 20.562,
                          21.837, 24.350, 26.248, 27.089, 27.758])

        # Test Statistic: QLR
        valql = np.array([3.198, 3.416, 3.594, 4.106, 4.848, 5.689,
                          6.682, 7.626, 9.16, 10.66, 11.841, 13.098, 15.451,
                          17.094, 19.423, 21.682, 23.342, 24.920, 28.174, 30.736,
                          33.313, 36.109, 39.673, 41.955, 45.056, 48.647, 50.983,
                          55.514, 59.278, 61.311, 64.016])

        lame = None
        lamm = None
        lamq = None

        # Median-unbiased estimator of lambda_z for given values of the test
        # statistics are obtained using the procedure described in the
        # footnote to Stock and Watson (1998) Table 3.

        # exponential wald
        if ew <= valew[0]:
            lame = 0
        else:
            for i in range(0, valew.shape[0] - 1):
                if (ew > valew[i]) and (ew <= valew[i + 1]):
                    lame = i - 1 + (ew - valew[i]) / (valew[i + 1] - valew[i])

        # median wald
        if mw <= valmw[0]:
            lamm = 0
        else:
            for i in range(0, valmw.shape[0] - 1):
                if (mw > valmw[i]) and (mw <= valmw[i + 1]):
                    lamm = i - 1 + (mw - valmw[i]) / (valmw[i + 1] - valmw[i])

        # qlr stat
        if qlr <= valql[0]:
            lamq = 0
        else:
            for i in range(0, valql.shape[0] - 1):
                if (qlr > valql[i]) and (qlr <= valql[i + 1]):
                    lamq = i - 1 + (qlr - valql[i]) / (valql[i + 1] - valql[i])

        # check for statistics outside of table
        if all([lame is None, lamm is None, lamq is None]):
            print('At least one statistic has an NA value.'
                  'Check to see if your EW, MW, and/or QLR value is outside of Table 3.')

        return lame / T
