"""
Authors: Daniel Dantas, Gustavo Amarante, Gustavo Soares, Wilson Felicio
"""

import datetime as dt
import pandas as pd
import numpy as np
import blpapi


class BBG(object):
    """
    This class is a wrapper around the Bloomberg API. To work, it requires an active bloomberg terminal running on
    windows (the API is not comaptible with other OS), a python 3.6 environment and the installation of the bloomberg
    API. Check out the guides on our github repository to learn how to install the API.
    """

    @staticmethod
    def fetch_series(securities, fields, startdate, enddate, period="DAILY", calendar="ACTUAL", fx=None,
                     fperiod=None, verbose=False):
        """
        Fetches time series for given tickers and fields, from startdate to enddate.

        Output is a DataFrame with tickers on the columns. If a single field is passed, the index are the dates.
        If a list of fields is passed, a multi-index DataFrame is returned, where the index is ['FIELD', date].

        Requests can easily get really big, this method allows for up to 30k data points.

        This replicates the behaviour of the BDH function of the excel API

        :param securities: str or list of str
        :param fields: str or list of str
        :param startdate: str, datetime or timestamp
        :param enddate: str, datetime or timestamp
        :param period: 'DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'SEMI ANNUAL' OR 'YEARLY'. Periodicity of the series
        :param calendar: 'ACTUAL', 'CALENDAR' or 'FISCAL'
        :param fx: str with a currency code. Converts the series to the chosen currency
        :param fperiod: ???
        :param verbose: prints progress
        :return:  DataFrame or Multi-index DataFrame (if more than one field is passed)
        """

        startdate = BBG._assert_date_type(startdate)
        enddate = BBG._assert_date_type(enddate)

        bbg_start_date = BBG._datetime_to_bbg_string(startdate)
        bbg_end_date = BBG._datetime_to_bbg_string(enddate)

        if startdate > enddate:
            ValueError("Start date is later than end date")

        session = blpapi.Session()

        if not session.start():
            raise ConnectionError("Failed to start session")

        try:
            if not session.openService("//blp/refdata"):
                raise ConnectionError("Failed to open //blp/refdat")

            # Obtain the previously opened service
            refdata_service = session.getService("//blp/refdata")

            # Create and fill the request for historical data
            request = refdata_service.createRequest("HistoricalDataRequest")

            # grab securities
            if type(securities) is list:
                for sec in securities:
                    request.getElement("securities").appendValue(sec)
            else:
                request.getElement("securities").appendValue(securities)

            # grab fields
            if type(fields) is list:
                for f in fields:
                    request.getElement("fields").appendValue(f)
            else:
                request.getElement("fields").appendValue(fields)

            request.set("periodicityAdjustment", calendar)
            request.set("periodicitySelection", period)
            request.set("startDate", bbg_start_date)
            request.set("endDate", bbg_end_date)
            request.set("maxDataPoints", 30000)

            if not (fx is None):
                request.set("currency", fx)

            if not (fperiod is None):
                overrides_bdh = request.getElement("overrides")
                override1_bdh = overrides_bdh.appendElement()
                override1_bdh.setElement("fieldId", "BEST_FPERIOD_OVERRIDE")
                override1_bdh.setElement("value", fperiod)

            if verbose:
                print("Sending Request:", request.getElement("date").getValue())

            # send request
            session.sendRequest(request)

            # process received response
            results = {}

            while True:
                ev = session.nextEvent()

                for msg in ev:

                    if verbose:
                        print(msg)

                    if msg.messageType().__str__() == "HistoricalDataResponse":
                        sec_data = msg.getElement("securityData")
                        sec_name = sec_data.getElement("security").getValue()
                        field_data = sec_data.getElement("fieldData")

                        if type(fields) is list:

                            results[sec_name] = {}

                            for day in range(field_data.numValues()):

                                fld = field_data.getValue(day)

                                for fld_i in fields:
                                    if fld.hasElement(fld_i):
                                        results[sec_name] \
                                            .setdefault(fld_i, []).append([fld.getElement("date").getValue(),
                                                                           fld.getElement(fld_i).getValue()])
                        else:
                            results[sec_name] = []
                            for day_i in range(field_data.numValues()):
                                fld = field_data.getValue(day_i)
                                results[sec_name].append([
                                    fld.getElement("date").getValue(),
                                    fld.getElement(fields).getValue()])

                if ev.eventType() == blpapi.Event.RESPONSE:  # Response completly received, break out of the loop
                    break

        finally:
            session.stop()

        if not type(securities) is list:
            results = results[securities]

        # parse the results as a DataFrame
        df = pd.DataFrame()

        if not (type(securities) is list) and not (type(fields) is list):
            # single ticker and single field
            # returns a dataframe with a single column
            results = np.array(results)
            df[securities] = pd.Series(index=pd.to_datetime(results[:, 0]), data=results[:, 1])

        elif (type(securities) is list) and not (type(fields) is list):
            # multiple tickers and single field
            # returns a single dataframe for the field with the ticker on the columns

            for tick in results.keys():
                aux = np.array(results[tick])

                if len(aux) == 0:
                    df[tick] = np.nan
                else:
                    df = pd.concat([df, pd.Series(index=pd.to_datetime(aux[:, 0]), data=aux[:, 1], name=tick)],
                                   axis=1, join='outer', sort=True)

        elif not (type(securities) is list) and (type(fields) is list):
            # single ticker and multiple fields
            # returns a single dataframe for the ticker with the fields on the columns

            for fld in results.keys():
                aux = np.array(results[fld])
                df[fld] = pd.Series(index=pd.to_datetime(aux[:, 0]), data=aux[:, 1])

        else:
            # multiple tickers and multiple fields
            # returns a multi-index dataframe with [field, ticker] as index

            for tick in results.keys():

                for fld in results[tick].keys():
                    aux = np.array(results[tick][fld])
                    df_aux = pd.DataFrame(data={'FIELD': fld,
                                                'TRADE_DATE': pd.to_datetime(aux[:, 0]),
                                                'TICKER': tick,
                                                'VALUE': aux[:, 1]})
                    df = df.append(df_aux)

            df['VALUE'] = df['VALUE'].astype(float, errors='ignore')

            df = pd.pivot_table(data=df, index=['FIELD', 'TRADE_DATE'], columns='TICKER', values='VALUE')

        return df

    @staticmethod
    def fetch_contract_parameter(securities, field):
        """
        Grabs a characteristic of a contract, like maturity dates, first notice dates, strikes, contract sizes, etc.

        Returns a DataFrame with the tickers on the index and the field on the columns.

        This replicates the behaviour of the BDP Function from the excel API.

        OBS: For now, it only allows for a single field. An extension that allows for multiple fields is a good idea.

        :param securities: str or list of str
        :param field: str
        :return: DataFrame
        """

        session = blpapi.Session()
        session.start()

        if not session.openService("//blp/refdata"):
            raise ConnectionError("Failed to open //blp/refdat")

        service = session.getService("//blp/refdata")
        request = service.createRequest("ReferenceDataRequest")

        if type(securities) is list:

            for each in securities:
                request.append("securities", str(each))

        else:
            request.append("securities", securities)

        request.append("fields", field)
        session.sendRequest(request)

        name, val = [], []
        end_reached = False
        while not end_reached:

            ev = session.nextEvent()

            if ev.eventType() == blpapi.Event.RESPONSE or ev.eventType() == blpapi.Event.PARTIAL_RESPONSE:

                for msg in ev:

                    for i in range(msg.getElement("securityData").numValues()):
                        sec = str(msg.getElement("securityData").getValue(i).getElement(
                            "security").getValue())  # here we get the security
                        name.append(sec)

                        value = msg.getElement("securityData").getValue(i).getElement("fieldData").getElement(
                            field).getValue()
                        val.append(value)  # here we get the field value we have selected

            if ev.eventType() == blpapi.Event.RESPONSE:
                end_reached = True
                session.stop()

        df = pd.DataFrame(val, columns=[field], index=name)

        return df

    @staticmethod
    def fetch_futures_list(generic_ticker):
        """
        Given a generic ticker for a future contract, it returns all of the historical contracts that composed the
        generic.
        :param generic_ticker: str
        :return: list
        """

        session = blpapi.Session()

        if not session.start():
            raise ConnectionError("Failed to start session.")

        if not session.openService("//blp/refdata"):
            raise ConnectionError("Failed to open //blp/refdat")

        service = session.getService("//blp/refdata")
        request = service.createRequest("ReferenceDataRequest")

        request.append("securities", generic_ticker)
        request.append("fields", "FUT_CHAIN")

        overrides = request.getElement("overrides")
        override1 = overrides.appendElement()
        override1.setElement("fieldId", "INCLUDE_EXPIRED_CONTRACTS")
        override1.setElement("value", "Y")
        override2 = overrides.appendElement()
        override2.setElement("fieldId", "CHAIN_DATE")
        override2.setElement("value", pd.to_datetime('today').date().strftime('%Y%m%d'))

        session.sendRequest(request)

        # process received events
        end_reached = True
        contract_list = []
        while end_reached:

            ev = session.nextEvent()

            if ev.eventType() == blpapi.Event.RESPONSE or ev.eventType() == blpapi.Event.PARTIAL_RESPONSE:

                for msg in ev:

                    elements = msg.getElement("securityData").getValue().getElement("fieldData").getElement("FUT_CHAIN")
                    num_values = elements.numValues()

                    for cont in range(num_values):
                        contract_list.append(elements.getValue(cont).getElement("Security Description").getValue())

            if ev.eventType() == blpapi.Event.RESPONSE:
                end_reached = False
                session.stop()

        return contract_list

    @staticmethod
    def fetch_index_weights(index_name, ref_date):
        """
        Given an index (e.g. S&P500, IBOV) and a date, it returns a DataFrame of its components as the index an
        their respective weights as the value for the given date.
        :param index_name: str
        :param ref_date: str, datetime or timestamp
        :return: DataFrame
        """

        ref_date = BBG._assert_date_type(ref_date)

        session = blpapi.Session()

        if not session.start():
            raise ConnectionError("Failed to start session.")

        if not session.openService("//blp/refdata"):
            raise ConnectionError("Failed to open //blp/refdat")

        service = session.getService("//blp/refdata")
        request = service.createRequest("ReferenceDataRequest")

        request.append("securities", index_name)
        request.append("fields", "INDX_MWEIGHT_HIST")

        overrides = request.getElement("overrides")
        override1 = overrides.appendElement()
        override1.setElement("fieldId", "END_DATE_OVERRIDE")
        override1.setElement("value", ref_date.strftime('%Y%m%d'))
        session.sendRequest(request)  # there is no need to save the response as a variable in this case

        end_reached = False
        df = pd.DataFrame()
        while not end_reached:

            ev = session.nextEvent()

            if ev.eventType() == blpapi.Event.RESPONSE:

                for msg in ev:

                    security_data = msg.getElement('securityData')
                    security_data_list = [security_data.getValueAsElement(i) for i in range(security_data.numValues())]

                    for sec in security_data_list:

                        field_data = sec.getElement('fieldData')
                        field_data_list = [field_data.getElement(i) for i in range(field_data.numElements())]

                        for fld in field_data_list:

                            for v in [fld.getValueAsElement(i) for i in range(fld.numValues())]:

                                s = pd.Series()

                                for d in [v.getElement(i) for i in range(v.numElements())]:
                                    s[str(d.name())] = d.getValue()

                                df = df.append(s, ignore_index=True)

                if not df.empty:
                    df.columns = ['', ref_date]
                    df = df.set_index(df.columns[0])

                end_reached = True

        return df

    @staticmethod
    def fetch_cash_flow(bond, date):
        """
        Grabs all the future cash flows from a bond and their payment dates.

        Returns a DataFrame with payment dates as the index and cash flows are separated between
        'Principal' and 'Coupon' payments.

        :param bond: str. Bloomber ID number for the bond (this is not the ticker)
        :param date: str, datetime or timestamp. Date from which to look ahead and grab the future cash flows
        :return: DataFrame
        """

        date = BBG._assert_date_type(date)

        session = blpapi.Session()

        if not session.start():
            raise ConnectionError("Failed to start a connection")

        if not session.openService("//blp/refdata"):
            raise ConnectionError("Failed to open //blp/refdat")

        service = session.getService("//blp/refdata")
        request = service.createRequest("ReferenceDataRequest")

        request.append("securities", bond)
        request.append("fields", "DES_CASH_FLOW")
        overrides = request.getElement("overrides")
        override1 = overrides.appendElement()
        override1.setElement("fieldId", "SETTLE_DT")
        override1.setElement("value", date.strftime('%Y%m%d'))

        _ = session.sendRequest(request)

        df = pd.DataFrame()
        end_reached = False
        while not end_reached:
            ev = session.nextEvent()

            if ev.eventType() == blpapi.Event.RESPONSE:

                for msg in ev:

                    sec_data = msg.getElement('securityData')
                    field_data = sec_data.getValueAsElement(0).getElement('fieldData')

                    for v in [field_data.getElement(0).getValueAsElement(i) for i in
                              range(field_data.getElement(0).numValues())]:

                        s = pd.Series()

                        for d in [v.getElement(i) for i in range(v.numElements())]:

                            try:
                                s[str(d.name())] = d.getValue()

                            except:
                                s[str(d.name())] = np.nan

                        df = df.append(
                            s[['Coupon Amount', 'Principal Amount']].to_frame(s['Payment Date']).transpose())

                end_reached = True

        return df

    @staticmethod
    def _assert_date_type(input_date):
        """
        Assures the date is in datetime format
        :param input_date: str, timestamp, datetime
        :return: input_date in datetime format
        """

        if not (type(input_date) is dt.date):

            if type(input_date) is pd.Timestamp:
                input_date = input_date.date()

            elif type(input_date) is str:
                input_date = pd.to_datetime(input_date).date()

            else:
                raise TypeError("Date format not supported")

        return input_date

    @staticmethod
    def _datetime_to_bbg_string(input_date):
        """
        converts datetime to string in bloomberg format
        :param input_date:
        :return:
        """
        return str(input_date.year) + str(input_date.month).zfill(2) + str(input_date.day).zfill(2)

    @staticmethod
    def fetch_bulk_data(index_name, field, ref_date, pg_override=None):
        """
        Allows to grab fields with bulk data
        :param index_name: str
        :param field: str, field name
        :param ref_date: str, datetime or timestamp
        :param pg_override: str, bloomberg override option
        :return: DataFrame
        """

        ref_date = BBG._assert_date_type(ref_date)

        session = blpapi.Session()

        if not session.start():
            raise ConnectionError("Failed to start session.")

        if not session.openService("//blp/refdata"):
            raise ConnectionError("Failed to open //blp/refdat")

        service = session.getService("//blp/refdata")
        request = service.createRequest("ReferenceDataRequest")

        request.append("securities", index_name)
        request.append("fields", field)

        overrides = request.getElement("overrides")
        override1 = overrides.appendElement()
        override1.setElement("fieldId", "END_DATE_OVERRIDE")
        override1.setElement("value", ref_date.strftime('%Y%m%d'))

        if not (pg_override is None):
            overrides_bdh = request.getElement("overrides")
            override1_bdh = overrides_bdh.appendElement()
            override1_bdh.setElement("fieldId", "PRODUCT_GEO_OVERRIDE")
            override1_bdh.setElement("value", pg_override)

        session.sendRequest(request)  # there is no need to save the response as a variable in this case

        end_reached = False
        df = pd.DataFrame()
        while not end_reached:

            ev = session.nextEvent()

            if ev.eventType() == blpapi.Event.RESPONSE:

                for msg in ev:

                    security_data = msg.getElement('securityData')
                    security_data_list = [security_data.getValueAsElement(i) for i in range(security_data.numValues())]

                    for sec in security_data_list:

                        field_data = sec.getElement('fieldData')
                        field_data_list = [field_data.getElement(i) for i in range(field_data.numElements())]

                        for fld in field_data_list:

                            for v in [fld.getValueAsElement(i) for i in range(fld.numValues())]:

                                s = pd.Series()

                                for d in [v.getElement(i) for i in range(v.numElements())]:
                                    s[str(d.name())] = d.getValue()

                                df = df.append(s, ignore_index=True)

                if not df.empty:
                    df = df.set_index(df.columns[0])

                end_reached = True

        return df
