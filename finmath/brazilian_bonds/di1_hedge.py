"""
Author: Lucas L. Sanches
"""

from finmath.brazilian_bonds.government_bonds import LTN, NTNF
from dataapi import DBConnect, DI1
from typing import Union, Optional
from scipy import optimize
import pandas as pd
import numpy as np

class DI1_Hedge(object):

    def __init__(self,
                 bonds: Union[list[LTN], list[NTNF]],
                 weights: list[float],
                 as_market_value: Optional[bool] = False,
                 convexity: Optional[bool] = False):

        """[summary]
        Class constructor.
        This class calculates DI1 contracts to hedge brazilian bonds portfolios.

        Arguments
        ----------
            bonds : list_like
                Bonds should be a list of LTN and/or NTNF bonds.
            weights : list_like
                Weights should be a list of weights, as quantities or market value.
            as_market_value : bool (default: False)
                If true, it indicates weights must be considered as market values.
            convexity : bool (default: False)
                If true, convexity must be considered for hedging.

        Returns
        ----------
            contracts:
                Dictionary containing code(s) and quantity(ies) of DI1 contracts for portfolio hedging.

        """

        if len(bonds) == 0:
            msg = f'No informed list of government bonds'
            raise TypeError(msg)

        if len(weights) == 0:
            msg = f'No informed list of government bonds'
            raise TypeError(msg)

        if len(weights) != len(bonds):
            msg = f'Length of bonds and weights lists are different!'
            raise TypeError(msg)

        # Check if all ref_date's are the same
        ref_date = bonds[0].ref_date
        for b in bonds:
            if b.ref_date != ref_date:
                msg = f'Not all ref_dates are the same!'
                raise TypeError(msg)
        di1_date_index = pd.Timestamp(ref_date)

        # Calculate market value for each position and for whole portfolio
        bond_mtm_values = []
        if as_market_value:
            bond_mtm_values = weights
        else:
            for w in weights:
                bond_mtm_values.append(w * bonds[weights.index(w)].price)
        self.portfolio_value = sum(bond_mtm_values)
        bonds_weights = [x / self.portfolio_value for x in bond_mtm_values]

        # Calculate portfolio duration and convexity
        self.portfolio_duration = sum([x * bonds[bonds_weights.index(x)].mod_duration for x in bonds_weights])
        self.portfolio_convexity = sum([x * bonds[bonds_weights.index(x)].convexity for x in bonds_weights])

        # Retrieve DI1 data and focus on January maturities for liquidity purposes
        dbc = DBConnect('fhreadonly', 'finquant')
        di1 = DI1(dbc)
        di1_series = di1.time_series.loc[di1_date_index, 'last_price']
        codes_of_interest = [x for x in di1_series.index if 'F' in x]
        df_di1 = pd.DataFrame(di1_series).loc[codes_of_interest]
        df_di1 = df_di1[df_di1.last_price > 0.]
        df_di1["code"] = df_di1.index
        df_di1["theoretical_price"] = [di1.theoretical_price(x, di1_date_index) for x in df_di1.index]
        df_di1["duration"] = [-di1.duration(x, di1_date_index) for x in df_di1.index]
        df_di1["convexity"] = [di1.convexity(x, di1_date_index) for x in df_di1.index]
        df_di1.index = [di1.maturity(x) for x in df_di1.index]
        df_di1 = df_di1.sort_index()

        # Find specific contracts for hedging, depending on portfolio duration and convexity
        first_contract_code = df_di1.code[0]
        first_contract_duration = df_di1.duration[0]
        first_contract_convexity = df_di1.convexity[0]
        first_contract_theoretical_price = df_di1.theoretical_price[0]
        second_contract_code = df_di1.code[0]
        second_contract_duration = df_di1.duration[0]
        second_contract_convexity = df_di1.convexity[0]
        second_contract_theoretical_price = df_di1.theoretical_price[0]
        for d in df_di1.iterrows():
            if d[1].duration < self.portfolio_duration and d[1].convexity < self.portfolio_convexity:
                first_contract_code = d[1].code
                first_contract_duration = d[1].duration
                first_contract_convexity = d[1].convexity
                first_contract_theoretical_price = d[1].theoretical_price
            if d[1].duration > self.portfolio_duration and d[1].convexity > self.portfolio_convexity:
                second_contract_code = d[1].code
                second_contract_duration = d[1].duration
                second_contract_convexity = d[1].convexity
                second_contract_theoretical_price = d[1].theoretical_price
                break

        # Find quantities, by estimating price variation after a 100 bps shock
        if convexity:
            variation = lambda pu, duration, convexity: (pu * (duration * (-0.01) + (convexity / 2) * (0.01 ** 2)))
            func = lambda x: abs(variation(self.portfolio_value, self.portfolio_duration, self.portfolio_convexity)
                                 + x[0] * variation(first_contract_theoretical_price,
                                                    first_contract_duration,
                                                    first_contract_convexity)
                                 + x[1] * variation(second_contract_theoretical_price,
                                                    second_contract_duration,
                                                    second_contract_convexity))
            res = optimize.minimize(func, [1, 1])
            self.hedge_contracts = { first_contract_code : -round(res.x[0]), second_contract_code : -round(res.x[1]) }
        else:
            x = (self.portfolio_value * self.portfolio_duration) / (first_contract_theoretical_price * first_contract_duration)
            self.hedge_contracts = { first_contract_code : round(x) }

        print("DI1 hedge contract(s):", self.hedge_contracts)
