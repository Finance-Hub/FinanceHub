from optparse import OptionParser
import datetime as dt
import pandas as pd
import blpapi
import numpy as np


class BBG(object):

    def __init__(self):
        self.options = BBG._parse_cmd_line()

    def fetch_series(self, securities, fields, startdate, enddate, period="DAILY", calendar="ACTUAL", fx=None,
                     fperiod=None, verbose=False):

        startdate = BBG._assert_date_type(startdate)
        enddate = BBG._assert_date_type(enddate)

        bbg_start_date = BBG._datetime_to_bbg_string(startdate)
        bbg_end_date = BBG._datetime_to_bbg_string(enddate)

        if startdate > enddate:
            ValueError("Start date is later than end date")

        session_options = blpapi.SessionOptions()
        session_options.setServerHost(self.options.host)
        session_options.setServerPort(self.options.port)
        session = blpapi.Session(session_options)

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
                                        results[sec_name]\
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
            df[securities] = pd.Series(index=results[:, 0], data=results[:, 1])

        elif (type(securities) is list) and not (type(fields) is list):
            # multiple tickers and single field
            # returns a single dataframe for the field with the ticker on the columns

            for tick in results.keys():
                aux = np.array(results[tick])

                if len(aux) == 0:
                    df[tick] = np.nan
                else:
                    df = pd.concat([df, pd.Series(index=aux[:, 0], data=aux[:, 1], name=tick)], axis=1, join='outer', sort=True)

        elif not (type(securities) is list) and (type(fields) is list):
            # single ticker and multiple fields
            # returns a single dataframe for the ticker with the fields on the columns

            for fld in results.keys():
                aux = np.array(results[fld])
                df[fld] = pd.Series(index=aux[:, 0], data=aux[:, 1])

        else:
            # multiple tickers and multiple fields
            # returns a multi-index dataframe with [field, ticker] as index

            for tick in results.keys():

                for fld in results[tick].keys():
                    aux = np.array(results[tick][fld])
                    df_aux = pd.DataFrame(data={'FIELD': fld,
                                                'TRADE_DATE': aux[:, 0],
                                                'TICKER': tick,
                                                'VALUE': aux[:, 1]})
                    df = df.append(df_aux)

            df['VALUE'] = df['VALUE'].astype(float, errors='ignore')
            df['TRADE_DATE'] = df['TRADE_DATE'].astype(pd.Timestamp)

            df = pd.pivot_table(data=df, index=['FIELD', 'TRADE_DATE'], columns='TICKER', values='VALUE')

        return df

    @staticmethod
    def fetch_contract_parameter(securities, field):

        session = blpapi.Session()
        session.start()

        # if not session.start():
        #     raise ConnectionError("Failed to start session.")

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

                        sec = str(msg.getElement("securityData").getValue(i).getElement("security").getValue())  # here we get the security
                        name.append(sec)

                        value = msg.getElement("securityData").getValue(i).getElement("fieldData").getElement(field).getValue()
                        val.append(value)  # here we get the field we have selected

            if ev.eventType() == blpapi.Event.RESPONSE:
                end_reached = True
                session.stop()

        df = pd.DataFrame(val, columns=[field], index=name)

        return df

    @staticmethod
    def fetch_futures_list(generic_ticker):

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

                df.columns = ['', ref_date]
                df = df.set_index(df.columns[0])
                end_reached = True

        return df

    @staticmethod
    def fetch_cash_flow(bond, date):

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
    def _parse_cmd_line():

        parser = OptionParser(description="Retrive reference data.")

        parser.add_option("-a", "--ip", dest="host", help="server name or IP (default: %default)",
                          metavar="ipAdress", default="localhost")

        parser.add_option("-p", dest="port", type="int", help="server port (default: %default)",
                          metavar="tcpPort", default=8194)

        (options, args) = parser.parse_args()

        return options

    @staticmethod
    def _assert_date_type(input_date):
        """

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
        return str(input_date.year)+str(input_date.month).zfill(2)+str(input_date.day).zfill(2)


"""
* Write documentation
    - no more than 30k point per request
    - explain the different outputs
* Write README
* Assert variable types
"""