from optparse import OptionParser
import datetime as dt
import pandas as pd
import blpapi


class BBG(object):

    def __init__(self):
        self.options = BBG._parse_cmd_line()

    # TODO Rename the arguments
    def fetch_series(self, securities, fields, startdate, enddate, period="DAILY", calendar="ACTUAL", FX='', fperiod='',
                     verbose=False):
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

        # PAREI NA PARTE QUE TENHO QUE PEGAR OS DADOS HISTORICOS

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
* Test start_date > end_date
* test for different types of dates
* write documentation
* write README
"""