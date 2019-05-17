"""
Author: Gustavo Amarante
"""

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
pd.options.mode.chained_assignment = None

# TODO allow for unspanned factors


class NominalACM(object):
    """
    This class estimates term premium based on the paper 'pricing term structures with linear regressions' by Adrian,
    Crump & Moench (2013). It takes the curve vertices and excess returns of positions from all of them and return the
    term premium and risk neutral yields as object attributes.
    """

    base_count_dict = {'daily': 252,
                       'monthly': 12,
                       'yearly': 1}

    def __init__(self, curve, excess_returns, freq='daily', interpolation='pchip', n_factors=5, compute_miy=False):
        """
        All inputs are saved as attributes.
        :param curve: DataFrame with equally spaced vertices as columns
        :param excess_returns: DataFrame with the excess returns of the vertices as columns
        :param freq: 'daily', 'monthly' or 'yearly'. Frequency of observations.
        :param interpolation: any interpolation method from the SciPy library.
        :param n_factors: number of principal components in the analysis.
        :param compute_miy: Boolean. If True, computes the model implied yield.
        """
        self.curve = curve

        self.excess_returns = excess_returns

        self.curve_exp = np.log(1+curve)

        self.freq = freq

        self.interpolation_method = interpolation

        self.n_factors = n_factors

        self.n_tenors = excess_returns.shape[1]

        self.tenors = excess_returns.columns

        self.sample_size = curve.shape[0] - 1

        self.base_count = self.base_count_dict[freq]

        self.compute_miy = compute_miy

        self._run_estimation()

    def _run_estimation(self):

        # Step 0 - get the PCA factor series
        self.PCA_factors = self._get_pca_factors()

        # Step 1 - VAR for the PCA equities
        Mu_hat, Phi_hat, V_hat, Sigma_hat = self._estimate_factor_var()

        # Step 2 - Excess return equation
        beta_hat, a_hat, B_star_hat, sigma2_hat, c_hat = self._estimate_excess_return_equation(v_hat=V_hat)

        # Step 3 - Estimate price of risk parameters
        lambda_0_hat, lambda_1_hat = self._retrieve_lambda(beta_hat, a_hat, B_star_hat, Sigma_hat, sigma2_hat, c_hat)

        # Step 4 - Equation for the Short Rate
        delta_0_hat, delta_1_hat = self._estimate_short_rate_equation()

        # Step 5 - Affine Recursions
        # model implied yield
        if self.compute_miy:
            miy = self._affine_recursions(Mu_hat, Phi_hat, Sigma_hat, sigma2_hat, lambda_0_hat, lambda_1_hat,
                                          delta_0_hat, delta_1_hat)

            miy = pd.DataFrame(data=miy[:, 1:],
                               index=self.PCA_factors[1:].index,
                               columns=list(range(1, self.tenors.max() + 1)))

            self.miy = np.exp(miy) - 1
        else:
            self.miy = None

        # risk neutral yield
        rny = self._affine_recursions(Mu_hat, Phi_hat, Sigma_hat, sigma2_hat, 0, 0, delta_0_hat, delta_1_hat)

        rny = pd.DataFrame(data=rny[:, 1:],
                           index=self.PCA_factors[1:].index,
                           columns=list(range(1, self.tenors.max() + 1)))

        self.rny = np.exp(rny) - 1
        self.term_premium = ((1 + self.curve) / (1 + self.rny) - 1).dropna(how='all')

    def _get_pca_factors(self):

        pca = PCA(n_components=self.n_factors)

        df_pca = pd.DataFrame(data=pca.fit_transform(self.curve_exp.values),
                              index=self.curve.index,
                              columns=['PC' + str(i) for i in range(1, self.n_factors + 1)])

        return df_pca

    def _estimate_factor_var(self):
        Y = self.PCA_factors.iloc[1:]
        Z = self.PCA_factors.iloc[:-1]
        Z['const'] = 1
        Z = Z[['const'] + ['PC' + str(x) for x in range(1, self.n_factors + 1)]].T

        # The VAR(1) estimator is given by equation (3.2.10) from Lutkepohl's book.
        mat_Z = np.matrix(Z)
        mat_Y = np.matrix(Y).T
        B_hat = np.dot(mat_Y, np.dot(mat_Z.T, np.linalg.inv(np.dot(mat_Z, mat_Z.T))))

        # Computes matrices Mu and Phi of the VAR(1) of the paper.
        Mu_hat = B_hat[:, 0]
        Phi_hat = B_hat[:, 1:self.n_factors + 1]

        # residuals matrix V_hat and the unbiased estimate of its covariance
        V_hat = mat_Y - np.dot(B_hat, mat_Z)
        Sigma_hat = np.dot((1 / (self.sample_size - self.n_factors - 1)), np.dot(V_hat, V_hat.T))

        return Mu_hat, Phi_hat, V_hat, Sigma_hat

    def _estimate_excess_return_equation(self, v_hat):

        mat_rx = self.excess_returns.iloc[1:].values.T.astype(float)

        Z = np.concatenate((np.ones((1, self.sample_size)), v_hat, np.matrix(self.PCA_factors.iloc[:-1]).T))

        D_hat = np.dot(mat_rx, np.dot(Z.T, np.linalg.inv(np.dot(Z, Z.T))))
        a_hat = D_hat[:, 0]
        beta_hat = D_hat[:, 1:self.n_factors + 1].T
        c_hat = D_hat[:, self.n_factors + 1:]

        E_hat = mat_rx - np.dot(D_hat, Z)
        sigma2_hat = np.trace(np.dot(E_hat, E_hat.T)) / (self.n_tenors * self.sample_size)

        # Builds the estimate of the B* matrix, defined in equation (13) of the paper
        B_star_hat = np.zeros((self.n_tenors, self.n_factors ** 2))
        for i in range(0, self.n_tenors):
            B_star_hat[i, :] = np.reshape(np.dot(beta_hat[:, i], beta_hat[:, i].T), (1, self.n_factors ** 2))

        return beta_hat, a_hat, B_star_hat, sigma2_hat, c_hat

    def _retrieve_lambda(self, beta_hat, a_hat, b_star_hat, Sigma_hat, sigma2_hat, c_hat):

        lambda_0_hat = np.dot(np.linalg.inv(np.dot(beta_hat, beta_hat.T)),
                              np.dot(beta_hat,
                                     a_hat + np.dot(0.5,
                                                    np.dot(b_star_hat,
                                                           np.reshape(Sigma_hat, (self.n_factors ** 2, 1)))
                                                    + np.dot(sigma2_hat,
                                                             np.ones((self.n_tenors, 1))
                                                             )
                                                    )
                                     )
                              )

        lambda_1_hat = np.dot(np.dot(np.linalg.inv(np.dot(beta_hat, beta_hat.T)), beta_hat), c_hat)

        return lambda_0_hat, lambda_1_hat

    def _estimate_short_rate_equation(self):

        X_star = self.PCA_factors
        X_star['const'] = 1
        X_star = X_star[['const'] + ['PC' + str(x) for x in range(1, self.n_factors + 1)]].values

        r1 = np.dot(1/self.base_count, self.curve_exp.iloc[:, 0].values.T)

        Delta_hat = np.dot(np.dot(np.linalg.inv(np.dot(X_star.T, X_star)), X_star.T), r1)
        delta_0_hat = Delta_hat[0]
        delta_1_hat = Delta_hat[1:self.n_factors + 1]

        return delta_0_hat, delta_1_hat

    def _affine_recursions(self, Mu_hat, Phi_hat, Sigma_hat, sigma2_hat, lambda_0_hat, lambda_1_hat, delta_0_hat,
                           delta_1_hat):

        X_star = self.PCA_factors
        X_star['const'] = 1
        X_star = X_star[['const'] + ['PC' + str(x) for x in range(1, self.n_factors + 1)]].values

        N_rec = self.tenors.max()

        Bn = np.matrix(np.zeros((self.n_factors, N_rec + 1)))
        Bn[:, 1] = -delta_1_hat.reshape((self.n_factors, 1))

        for i in range(2, N_rec + 1):
            Bn[:, i] = np.transpose(np.dot(Bn[:, i - 1].T, Phi_hat - lambda_1_hat) - delta_1_hat.T)

        An = np.matrix(np.zeros((1, N_rec + 1)))
        An[:, 1] = -delta_0_hat

        for i in range(2, N_rec + 1):
            An[:, i] = An[:, i - 1] + np.dot(np.transpose(Bn[:, i - 1]), Mu_hat - lambda_0_hat) + 0.5 * \
                       (np.dot(np.dot(np.transpose(Bn[:, i - 1]), Sigma_hat), Bn[:, i - 1]) + sigma2_hat) - delta_0_hat

        MIY = np.matrix(np.zeros((self.sample_size, N_rec + 1)))
        Xt = X_star[:, 1:self.n_factors + 1].T

        for t in range(0, self.sample_size):
            for n in range(1, N_rec + 1):  # iterates on the maturities
                MIY[t, n] = -(self.base_count / n) * (An[:, n] + np.dot(np.transpose(Bn[:, n]), Xt[:, t]))

        return MIY
