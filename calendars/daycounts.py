"""
Author: Thiago Barros
"""

from .holidays import Holidays
from pandas import to_datetime, Timestamp, DatetimeIndex, date_range, \
    DateOffset
from pandas.tseries.offsets import MonthEnd, YearEnd
from pandas.core.series import Series
from numpy import busday_count, busday_offset, busdaycalendar, asarray, \
    broadcast, broadcast_arrays, ndarray, minimum, divmod, count_nonzero, \
    datetime64


class DayCounts(object):
    # Constants
    WKMASK      = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    BUS         = 'BUS'
    ACT         = 'ACT'
    SEP         = '/'
    NL_DC       = ['nl/365']
    OO_DC       = ['1/1']
    BUS_DC      = ['bus/30', 'bus/252', 'bus/1', 'bus/bus']
    ACT_DC      = ['act/act isda', 'act/365', 'act/365a', 'act/365f',
                   'act/364', 'act/360', 'act/365l', 'act/act afb',
                   'act/act icma']
    XX360_DC    = ['30a/360', '30e/360', '30e+/360', '30e/360 isda', '30u/360']
    # Properties
    __dc        = None
    __cal       = None
    __adj       = None
    __adjo      = None
    __busc      = None

    def __init__(self, dc, adj=None, calendar=None,
                 weekmask='Mon Tue Wed Thu Fri', adjoffset=0):
        """
        Day count constructor

        Parameters
        ----------
        dc : str
            Valid day count convention, e.g. 'act/360', 'bus/252', 'nl/365'.
            Currently supported values are listed via static method
            `dc_domain`.

        adj : None, 'following', 'preceding', 'modifiedfollowing',
        'modifiedpreceding', default None
            None denotes no adjustment. If specified, it determines how
            dates that do not fall on valid date are treated. Assuming
            `adjoffset` set to 0:
                - 'following' denotes next valid date
                - 'preceding' denotes previous valid date
                - 'modifiedfollowing' ('modifiedpreceding') is the next
                (previous) valid date unless it is across a month boundary,
                in which case it takes the first valid date earlier (later) in
                time

        calendar : None, str
            If specified, it must be the name of a calendar supported by the
            Holidays factory class

        weekmask : str or array)like of bool, default 'Mon Tue Wed Thu Fri'
            From numpy.busday_offset: A seven-element array indicating which
            of Monday through Sunday are valid days. May be specified as a
            length-seven list or array, like [1,1,1,1,1,0,0]; a length-seven
            string, like ‘1111100’; or a string like “Mon Tue Wed Thu Fri”,
            made up of 3-character abbreviations for weekdays, optionally
            separated by white space. Valid abbreviations are: Mon Tue Wed
            Thu Fri Sat Sun

        adjoffset : int, default 0
            Scalar indicating the offset value that will be used if
            adjustment rule is not set to None

        Returns
        -------
        self : DayCounts
            New instance of object

        Notes
        -----
            (1) THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESSED OR
            IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
            WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
            PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR
            CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
            SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
            BUT NOT LIMITED TO,  PROCUREMENT OF SUBSTITUTE GOODS OR
            SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
            INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
            WHETHER IN CONTRACT, STRICT  LIABILITY, OR TORT (INCLUDING
            NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
            THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
            (2) Builds on numpy.datetime64 and pandas.Timestamp. As a rule,
            inputs of methods are any type/value that can be properly parsed
            by pandas.to_datetime() without optional inputs. Several methods
            from these packaged are used.
        """
        self.dc         = dc
        self.adj        = adj
        self.adjoffset  = adjoffset
        h               = Holidays.holidays(cdr=calendar)
        self.__busc     = busdaycalendar(weekmask=weekmask, holidays=h)
        self.calendar   = calendar

    def tf(self, d1, d2):
        """Calculates time fraction (in year fraction) between two dates given
        day count convention"""
        d1 = self.adjust(d1)
        d2 = self.adjust(d2)
        # Save adjustment state and set it to none, so we can safely use the
        # days and dib functions of "date splits" we produce in for some
        # day counts
        state    = self.adj
        self.adj = None
        if self.dc == 'ACT/ACT ICMA':
            raise AttributeError('The time fraction function cannot be used '
                                 'for the %s convention' % self.dc)
        if not (self.dc == 'ACT/ACT ISDA' or self.dc == 'ACT/ACT AFB' or
                self.dc == '1/1'):
            yf = self.days(d1, d2) / self.dib(d1, d2)
        elif self.dc == 'ACT/ACT ISDA':
            # We could treat everything as an array, we leave the dual
            # implementation because vectorizing is clumsy. So, we just
            # mimic the interface
            if isinstance(d1, Timestamp) and isinstance(d2, Timestamp):
                # We place the assertion here to save some thought in the
                # recursion (we check one by one or delegate)
                assert d1 <= d2, 'First date must be smaller or equal to ' \
                                 'second date'
                if d1.year == d2.year:
                    yf = self.days(d1, d2) / self.dib(d1, d2)
                else:
                    ey1 = to_datetime(str(d1.year)+'-12-31')
                    ey2 = to_datetime(str(d2.year-1)+'-12-31')
                    yf = (d2.year-d1.year-1) + \
                         (self.days(d1, ey1) / self.dib(d1, d1)) + \
                         (self.days(ey2, d2) / self.dib(d2, d2))
            else:  # This is the dreaded vectorized case that, for now,
                # will be dealt by simulating the interface
                result = list()
                f = result.append
                for t1, t2 in broadcast(d1, d2):
                    f(self.tf(t1, t2))
                yf = asarray(result, dtype='float64')
        elif self.dc == '1/1':
            # See notes in the ACT/ACT sections about vectorization
            if isinstance(d1, Timestamp) and isinstance(d2, Timestamp):
                # We place the assertion here to save some thought in the
                # recursion (we check one by one or delegate)
                assert d1 <= d2, 'First date must be smaller or equal to ' \
                                 'second date'
                if (d1.day == d2.day and d1.month == d2.month) \
                        or (d1.month == 2 and d2.month == 2 and
                            d1.day in [28, 29] and d2.day in [28, 29]):
                    yf = int(0.5 + self.days(d1, d2) / self.dib(d1, d2))
                else:
                    # This is the same as ACT/ACT. We tweak the DC and bring
                    # it back. This is computationally costly (as a parsing
                    # of the day count is involved at each step), but safer
                    # from an implementation perspective.
                    self.dc = 'act/act isda'
                    yf = self.tf(d1, d2)
                    self.dc = '1/1'
            else:  # This is the dreaded vectorized case that, for now,
                # will be dealt by simulating the interface
                result = list()
                f = result.append
                for t1, t2 in broadcast(d1, d2):
                    f(self.tf(t1, t2))
                yf = asarray(result, dtype='float64')
        elif self.dc == 'ACT/ACT AFB':
            if isinstance(d1, Timestamp) and isinstance(d2, Timestamp):
                # We place the assertion here to save some thought in the
                # recursion (we check one by one or delegate)
                assert d1 <= d2, 'First date must be smaller or equal to ' \
                                 'second date'
                # We need to loop back from d2 counting the number of
                # years we can subtract until we close interval. Note that
                # every time we fall on a Feb 29th, a year offset will land
                # us on Feb 28th. In this cases, we need to add the missing
                # day fraction (1/366). Note that we add it only once,
                # and not the number of leap days in interval divided by
                # 366. Why? While the documents are not super clear about
                # this, it seems reasonable to infer that from the "counting
                # back" rule, where we are always subtracting entire years.
                #
                # 2004-02-28 to 2008-02-27 = 3 + 365/366
                # 2004-02-28 to 2008-02-28 = 4
                # 2004-02-28 to 2008-02-29 = 4 + 1/366
                # 2004-02-28 to 2012-02-28 = 8
                # 2004-02-28 to 2012-02-29 = 8 + 1/366 (and NOT 2/366)
                n = 0
                offset = 0
                while d2 - DateOffset(years=1) >= d1:
                    if d2.day == 29 and d2.month == 2:
                        offset += 1/366
                    n += 1
                    d2 = d2 - DateOffset(years=1)
                yf = n + offset + (self.days(d1, d2) / self.dib(d1, d2))
            else:  # This is the dreaded vectorized case that, for now,
                # will be dealt by simulating the interface
                result = list()
                f = result.append
                for t1, t2 in broadcast(d1, d2):
                    f(self.tf(t1, t2))
                yf = asarray(result, dtype='float64')
        else:
            raise NotImplementedError('Day count %s not supported' % self.dc)
        # Return state
        self.adj = state
        return yf

    def days(self, d1, d2):
        """Number of days (integer) between two dates given day count
        convention"""
        d1 = self.adjust(d1)
        d2 = self.adjust(d2)
        # All business cases are the same and dealt at once
        bus_dc = [x.upper() for x in self.BUS_DC]
        if self.dc in bus_dc:
            if not isinstance(d1, Timestamp):
                d1 = d1.values.astype('datetime64[D]')
            else:
                d1 = datetime64(d1).astype('datetime64[D]')
            if not isinstance(d2, Timestamp):
                d2 = d2.values.astype('datetime64[D]')
            else:
                d2 = datetime64(d2).astype('datetime64[D]')
            return busday_count(d1, d2, busdaycal=self.buscore)
        # Deal with the 30/360 like conventions
        if self.dc == '30U/360':
            y1, m1, d1, y2, m2, d2 = self._date_parser(d1, d2)
            # Because the broadcasting occurred at parsing, everything is an
            # array

            # Adjustments (done in the following order)
            # (i) If d2 is the last day of Feb, we change it to 30 only
            # if d1 is the last day of feb
            mask2 = (self.isleap(y2) & (d2 == 29) & (m2 == 2)) | \
                    (~self.isleap(y2) & (d2 == 28) & (m2 == 2))
            mask1 = (self.isleap(y1) & (d1 == 29) & (m1 == 2)) | \
                    (~self.isleap(y1) & (d1 == 28) & (m1 == 2))
            mask  = mask1 & mask2
            d2[mask] = 30
            # (ii) If d1 is the last day of Feb, change it to 30
            d1[mask1] = 30
            # (iii) If d2 is 31, change it to 30 only if d1 (after ii) is 30
            #  or 31
            mask2 = d2 == 31
            mask1 = (d1 == 30) | (d1 == 31)
            mask  = mask1 & mask2
            d2[mask] = 30
            # (iv) If d1 is 31, change it to 30
            mask = d1 == 31
            d1[mask] = 30
            # Call core function
            days = self._days_30360_core(y1, m1, d1, y2, m2, d2)
            if len(days) == 1:
                return days[0]
            else:
                return days
        elif self.dc == '30A/360':
            y1, m1, d1, y2, m2, d2 = self._date_parser(d1, d2)
            # Adjustments (done in the following order)
            # (i) D1 = min(D1, 30)
            d1 = minimum(d1, 30)
            # (ii) If, after adjustment, d1 = 30, then d2 = min(d2, 30)
            mask = d1 == 30
            d2[mask] = minimum(d2[mask], 30)
            days = self._days_30360_core(y1, m1, d1, y2, m2, d2)
            if len(days) == 1:
                return days[0]
            else:
                return days
        elif self.dc == '30E/360':
            y1, m1, d1, y2, m2, d2 = self._date_parser(d1, d2)
            # No conditional adjustments in this case
            d1 = minimum(d1, 30)
            d2 = minimum(d2, 30)
            days = self._days_30360_core(y1, m1, d1, y2, m2, d2)
            if len(days) == 1:
                return days[0]
            else:
                return days
        elif self.dc == '30E/360 ISDA':
            y1, m1, d1, y2, m2, d2 = self._date_parser(d1, d2)
            # Adjustments:
            # (i) if d1 is EOM, set d1 to 30
            mask1 = self._eom_mask(y1, m1, d1)
            d1[mask1] = 30
            # (ii) if d2 is EOM, set d2 to 30
            mask2 = self._eom_mask(y2, m2, d2)
            d2[mask2] = 30
            # Call core function
            days = self._days_30360_core(y1, m1, d1, y2, m2, d2)
            if len(days) == 1:
                return days[0]
            else:
                return days
        elif self.dc == '30E+/360':
            y1, m1, d1, y2, m2, d2 = self._date_parser(d1, d2)
            # Adjustments:
            # (i) if d1 is 31, set d1 to 30
            d1      = minimum(d1, 30)
            # (ii) if d2 = 31, set date to first day of next month
            mask = d2 == 31
            d2[mask] = 1
            m2[mask] = (m2[mask] + 1) % 12
            i, r = divmod((m2[mask] + 1), 12)
            y2[mask] = y2[mask] + i
            # Call core function
            days = self._days_30360_core(y1, m1, d1, y2, m2, d2)
            if len(days) == 1:
                return days[0]
            else:
                return days
        # Deal with actual conventions
        if self.dc in ['ACT/ACT ISDA', 'ACT/365', 'ACT/365A', 'ACT/365F',
                       'ACT/364', 'ACT/360', 'ACT/365L', 'ACT/ACT AFB',
                       'ACT/ACT ICMA']:
            return self.daysnodc(d1, d2)
        elif self.dc == 'NL/365':
            return self.daysnodc(d1, d2) - self.leapdays(d1, d2)
        # Deal with the bizarre 1/1 convention
        if self.dc == '1/1':
            return self.daysnodc(d1, d2)

    def adjust(self, d):
        """Apply adjustment (following, preceding etc) to date d or array

        Note that we return either a Timestamp or a DatetimeIndex so that
        methods to come may use properties such as year or month on the array
        """
        if self.adj is None:
            return to_datetime(d)
        else:
            return self.busdateroll(d, roll=self.adj)

    def daysnodc(self, d1, d2):
        """Actual number of days, irrespective of daycount"""
        assert d1 is not None and d2 is not None, 'Inputs may not be None'
        d1 = self.adjust(d1)
        d2 = self.adjust(d2)
        if isinstance(d1, Timestamp) and isinstance(d2, Timestamp):
            return (d2-d1).days
        else:
            return (d2-d1).days.values

    def dib(self, d1=None, d2=None):
        """Days in base according to day count convention of the object

        Inputs:
            d1  - Initial date

            d2  - Final date

        Returns:
            dib - Integer or integer array with days in base

        Note: unlike other functions in this obj, function will only return
        array if two conditions are simultaneously met:
            (1) User is passing an array (standard); AND
            (2) There is potential ambiguity in the answer, i.e. if DB
            truly depends on the input dates.
        If one of the conditions above fails, function will return scalar.
        """

        # Handle fixed cases with dict
        dibd = {'NL/365': 365,
                'BUS/30': 30,
                'BUS/252': 252,
                'BUS/1': 1,
                'ACT/365': 365,
                'ACT/365F': 365,
                'ACT/364': 364,
                'ACT/360': 360,
                '30A/360': 360,
                '30E/360': 360,
                '30E+/360': 360,
                '30E/360 ISDA': 360,
                '30U/360': 360}
        # Simply cases end here
        try:
            return dibd[self.dc]
        except KeyError:
            pass
        # Throw error for ACT/ACT ISMA
        if self.dc == 'ACT/ACT ICMA':
            raise AttributeError('The concept of days in base does not apply '
                                 'to the ACT/ACT ICMA convention')
        # We worry about vectorization, so we will use pandas to do this
        if self.dc == 'BUS/BUS':
            # Error checking delegated to BDY
            return self.bdy(d2)
        elif self.dc == 'ACT/ACT ISDA':
            # Error checking delegated to DY
            return self.dy(d1)
        elif self.dc == 'ACT/365L':
            # Error checking delegated to DY
            return self.dy(d2)
        elif self.dc == 'ACT/365A':
            # Note that this is NOT the same as the FRENCH case below,
            # as the interval is standard (closed above, and not below)
            d1 = self.adjust(d1)
            d2 = self.adjust(d2)
            if isinstance(d1, Timestamp) and isinstance(d2, Timestamp):
                if d2.day == 29 and d2.month == 2:
                    return 366
                else:
                    if self.hasleap(d1, d2):
                        return 366
                    else:
                        return 365
            # For the vectorized case, we assume the ACT/ACT AFB logic and
            # then fix the boundary
            leap = self.hasleap(d1, d2)
            base = asarray(366 * leap + 365 * ~leap, dtype='int64')
            # Guarantee dimension conformity
            d2, base = broadcast_arrays(d2, base)
            d2   = DatetimeIndex(d2)
            mask = (d2.day == 29) & (d2.month == 2)
            base[mask] = 366
            return base
        elif self.dc == 'ACT/ACT AFB':
            # The bizarre french case. No surprise here.
            d1 = self.adjust(d1)
            d2 = self.adjust(d2)
            leap = self.hasleap(d1, d2)
            if isinstance(leap, bool):
                return 366 * leap + 365 * (not leap)
            else:
                return asarray(366 * leap + 365 * ~leap, dtype='int64')
        elif self.dc == '1/1':
            # There are two (seemingly?) very different definitions for this
            # guy. The "FBF Master Agreement for Financial Transactions,
            # Supplement to the Derivatives Annex, Edition 2004, section
            # 7a." document states that no matter what, this will return 1.
            # Same applies for the OpenGamma documentation. On the other
            # hand, there are places that say that this is equivalent to
            # DIB(ACT/ACT) unless d1 == d2, in which case DIB == 365.25
            d1 = self.adjust(d1)
            d2 = self.adjust(d2)
            if isinstance(d1, Timestamp) and isinstance(d2, Timestamp):
                if (d1.day == d2.day and d1.month == d2.month) \
                        or (d1.month == 2 and d2.month == 2 and
                            d1.day in [28, 29] and d2.day in [28, 29]):
                    return 365.25
                else:
                    return self.dy(d1)
            else:  # We have at least 1 array. Because we only accept the
                # combinations of equally sized arrays or array + scalar,
                # we don't care about the broadcast
                mask = ((d1.day == d2.day) & (d1.month == d2.month)) | \
                       ((d1.month == 2) & (d2.month == 2) %
                        ((d1.day == 28) | (d1.day == 29)) %
                        ((d2.day == 28) | (d2.day == 29)))
                base = self.dy(d1)
                if isinstance(base, int):
                    # We handle the mask as two separate cases as the
                    # negation ~True returns -2
                    if isinstance(mask, bool):
                        nmask = not mask
                    else:
                        nmask = ~mask
                    return asarray(base*nmask + 365.25*mask, dtype='float64')
                else:
                    base = base.astype('float64')
                    base[mask] = 365.25
                    return asarray(base, dtype='float64')
        else:
            raise NotImplementedError('Day count %s not supported' % self.dc)

    def bdy(self, d):
        """Business days in year of date(s) d"""
        assert d is not None, 'User may not pass None to BDY function'
        d   = self.adjust(d)
        if isinstance(d, Timestamp):
            res = busday_count(str(d.year), str(d.year + 1),
                               busdaycal=self.buscore)
        else:
            # This is brutal from a readability perspective,
            # but essentially it is a long list of casting executions
            res = busday_count(list(d.year.astype(str)),
                               list((d.year + 1).astype(str)),
                               busdaycal=self.buscore)
        return res

    def hasleap(self, d1, d2):
        """Check if there is a leap year in range between d1 and d2.

        Note that this requires the existence of a Feb 29 IN BETWEEN the
        range d1 and d2. More specifically, with loose notation, we require
            d1 <= Feb 29 < d2
        the interval is [d1, d2).

        This criteria is used in day counts such as ACT/365A and ACT/ACT AFB

        IMPORTANT: Non-business day counts calculate actual date differences in
        intervals of the type (d1, d2]. This is NOT how the French roll
        here, hence the interval [d1, d2) above. If you check page 53,
        "Base Exact/Exact", of:
        https://www.banque-france.fr/fileadmin/user_upload/banque_de_france/
        archipel/publications/bdf_bof/bdf_bof_1999/bdf_bof_01.pdf
        there is no clear mention to how this interval is calculated. But
        there seems to be a consensus between OpenGamma and Wikipedia that
        the interval is [d1, d2).

        NOTE: This is not a truly vectorized function, but it mimics the
        interface of one.
        """
        assert d1 is not None and d2 is not None, 'Inputs may not be None'
        d1 = self.adjust(d1)
        d2 = self.adjust(d2)
        if isinstance(d1, Timestamp) and isinstance(d2, Timestamp):
            # Give user some flexibility
            if d1 > d2:
                d1, d2 = d2, d1
            # Boundary cases
            # First year is leap, d1 <= 29 Feb < d2
            if (self.isleap(d1) and d1.month <= 2 and d1.day <= 29) and \
                    ((d2.year == d1.year and d2.month > 2) or
                     (d2.year > d1.year)):
                return True
            elif (self.isleap(d2) and d2.month > 2) and d1.year < d2.year:
                # d2 is leap and d2 is greater than 29 Feb. Note that we
                # don't care about d1.year == d2.year in this case, as it has
                # been dealt with above.
                return True
            elif d1.year == d2.year or d1.year + 1 == d2.year:
                # May or may not be a leap year, but dates are not
                # bracketing it (or we have consecutive years,
                # where same rule applies)
                return False
            else:
                # We have a range here to look for dates
                return any(self.isleap(x) for x in range(d1.year, d2.year))
        else:
            result = list()
            for t1, t2 in broadcast(d1, d2):
                result.append(self.hasleap(t1, t2))
            return asarray(result, dtype='bool')

    def leapdays(self, d1, d2):
        """Calculate number of leap days between two dates, in the interval
        (d1, d2].

        IMPORTANT: Note that the interval above is open below and closed
        above, as it is standard in calendar day counts (such as NL/365,
        in our case). This contrasts with function hasleap(d1, d2). To
        understand why, please refer to the help notes on hasleap(d1, d2).

        NOTE: This is not a truly vectorized function, but it mimics the
        interface of one.
        """
        assert d1 is not None and d2 is not None, 'Inputs may not be None'
        d1 = self.adjust(d1)
        d2 = self.adjust(d2)
        if isinstance(d1, Timestamp) and isinstance(d2, Timestamp):
            # Give user some flexibility
            if d1 > d2:
                d1, d2 = d2, d1
            # We only have to care about the open lower bound if we are
            # exactly at a Feb 29th. Given that we are we will use pandas
            # for this, we can pass a parameter to date_range to handle it.
            drange   = date_range(d1, d2, closed='right')
            return count_nonzero((drange.day == 29) & (drange.month == 2))
        else:
            result = list()
            for t1, t2 in broadcast(d1, d2):
                result.append(self.leapdays(t1, t2))
            return asarray(result, dtype='int64')

    def dy(self, d):
        """Days in year given by date(s) d"""
        assert d is not None, 'User may not pass None to DY function'
        d = self.adjust(d)
        leap = self.isleap(d)
        if isinstance(d, Timestamp):
            return 366*leap + 365*(not leap)
        else:
            return asarray(366*leap + 365*~leap, dtype='int64')

    def isleap(self, d):
        """Determine if year for input date(s) is leap (True) or not (False)"""
        assert d is not None, 'User may not pass None to ISLEAP function'
        if isinstance(d, int) or isinstance(d, ndarray):
            year = d
        else:
            d = self.adjust(d)
            year = d.year
        return (year % 4 == 0) & ((year % 100 != 0) | (year % 400 == 0))

    # Add methods respecting the interface of BWDate class for compatibility
    def isbus(self, d):
        """True if date is a business day"""
        return self.following(d) == d

    def busdateroll(self, d, roll):
        """Rolls business date according to convention specified in roll"""
        d = self._simple_cast(d)
        nd = busday_offset(d, offsets=self.adjoffset, roll=roll,
                           busdaycal=self.buscore)
        return to_datetime(nd)

    def workday(self, d, offset=0):
        """Mimics the workday function in Excel"""
        d = self._simple_cast(d)
        if self.adj is None and isinstance(offset, int):
            if offset >= 0:
                adj = 'preceding'
            else:
                adj = 'following'
            nd = busday_offset(d, offsets=offset, busdaycal=self.buscore,
                               roll=adj)
        elif self.adj is None and (isinstance(offset, ndarray) or
                                   isinstance(offset, Series)):
            if all(offset >= 0):
                adj = 'preceding'
            elif all(offset < 0):
                adj = 'following'
            else:
                raise NotImplementedError('If offset is an array like '
                                          'structure, then all values must '
                                          'have the same sign')
            nd = busday_offset(d, offsets=offset, busdaycal=self.buscore,
                               roll=adj)
        else:
            nd = busday_offset(d, offsets=offset, busdaycal=self.buscore,
                               roll=self.adj)
        return to_datetime(nd)

    def following(self, d):
        """Returns next business date if date is weekend or holiday"""
        return self.busdateroll(d, 'following')

    def modified_following(self, d):
        """Uses next business day unless it falls on a different month - in
        which case uses previous"""
        return self.busdateroll(d, 'modifiedfollowing')

    def preceding(self, d):
        """Find preceding business date if date is weekend or holiday"""
        return self.busdateroll(d, 'preceding')

    def modified_preceding(self, d):
        """Uses previous business day unless it falls on a different month - in
        which case uses following"""
        return self.busdateroll(d, 'modifiedpreceding')

    @staticmethod
    def eom(d, offset=0):
        """Unmodified end-of-month. Returns the last date of month for the
        same month and year as input d

        The offset parameter represents the number of months that will be
        added (if offset > 0) or subtracted (if offset < 0) to input date d.
        This is especially useful for offset = -1, which gives you the EOM
        of previous month, for example.
        """
        d = to_datetime(d)
        # Adding straight up the MonthEnd works as expected for MonthEnd(0),
        # but it gives weird results if using MonthEnd(1) and the input is
        # the last date of month. We leave the offset to a different function
        return d + DateOffset(months=offset) + MonthEnd(0)

    def eom_preceding(self, d, offset=0):
        """Returns last date of month for the same month and year as input
        d, unless it is not a BUS date - in that case, returns preceding
        date

        For an explanation of what offset does, please refer to EOM method
        """
        # We delegate the casting to base function
        d   = self.eom(d, offset)
        return self.preceding(d)

    def eom_following(self, d, offset=0):
        """Returns last date of month for the same month and year as input
        d, unless it is not a BUS date - in that case, returns following
        date

        For an explanation of what offset does, please refer to EOM method
        """
        # We delegate the casting to base function
        d   = self.eom(d, offset)
        return self.following(d)

    @staticmethod
    def eoy(d, offset=0):
        """Unmodified end-of-year. Returns the last date of year for the
        same year as in date d

        The offset parameter represents the number of years that will be
        added (if offset > 0) or subtracted (if offset < 0) to input date d.
        This is especially useful for offset = -1, which gives you the EOY
        of previous year, for example.
        """
        d = to_datetime(d)
        # As in the case of the EOM, we leave the offset to a different
        # function (see comments of EOM function)
        return d + DateOffset(years=offset) + YearEnd(0)

    def eoy_preceding(self, d, offset=0):
        """Returns last date of year for the same year as input d, unless it
        is not a BUS date - in that case, returns the preceding date

        For an explanation of what offset does, please refer to EOY method
        """
        # We delegate the casting to base function
        d   = self.eoy(d, offset)
        return self.preceding(d)

    def eoy_following(self, d, offset=0):
        """Returns last date of year for the same year as input d, unless it
        is not a BUS date - in that case, returns the following date

        For an explanation of what offset does, please refer to EOY method
        """
        # We delegate the casting to base function
        d   = self.eoy(d, offset)
        return self.following(d)

    def gendates(self, start_date, end_date):
        """Generator for dates in an interval assuming following in the
        lower end and preceding in the upper end

        Note: only scalar values are accepted
        """
        start_date = self.adjust(start_date)
        end_date   = self.adjust(end_date)
        assert isinstance(start_date, Timestamp), 'Start date must be scalar'
        assert isinstance(end_date, Timestamp), 'End date must be scalar'
        if start_date == end_date:
            start_date = self.preceding(start_date)
        else:
            start_date  = self.following(start_date)
        end_date    = self.preceding(end_date)
        while start_date <= end_date:
            yield start_date
            start_date  = self.workday(start_date, 1)

    @property
    def buscore(self):
        return self.__busc

    @property
    def adjoffset(self):
        return self.__adjo

    @adjoffset.setter
    def adjoffset(self, x):
        assert isinstance(x, int), 'Offset must be an integer'
        self.__adjo = x

    @property
    def weekmask(self):
        wkmask = list()
        for b, w in zip(self.buscore.weekmask, self.WKMASK):
            if b:
                wkmask.append(w)
        return ' '.join(wkmask)

    @weekmask.setter
    def weekmask(self, x):
        h = self.holidays.values.astype('datetime64[D]')
        self.__busc = busdaycalendar(weekmask=x, holidays=h)

    @property
    def weekends(self):
        wkends = set(self.WKMASK) - set(self.weekmask.split(' '))
        return ' '.join(wkends)

    @weekends.setter
    def weekends(self, x):
        raise AttributeError('User may not set the weekends property')

    @property
    def holidays(self):
        return to_datetime(self.buscore.holidays)

    @holidays.setter
    def holidays(self, x):
        raise AttributeError('User may not set the holidays property')

    @property
    def calendar(self):
        return self.__cal

    @calendar.setter
    def calendar(self, x):
        x = Holidays.modify_calendar_name(x)
        # Save calendar
        self.__cal = x
        # Update buscore engine
        h = Holidays.holidays(cdr=x)
        self.__busc = busdaycalendar(weekmask=self.weekmask, holidays=h)

    @property
    def adj(self):
        return self.__adj

    @adj.setter
    def adj(self, x):
        assert x is None or isinstance(x, str), 'If specified, adjustment ' \
                                                'must be a string'
        if x is None:
            self.__adj = x
        else:
            domain = ['following', 'preceding', 'modifiedfollowing',
                      'modifiedpreceding']
            assert x in domain, 'Adjustment must be one of: %s' % \
                                ', '.join(domain)
            self.__adj = x.lower()

    @property
    def dc(self):
        return self.__dc

    @dc.setter
    def dc(self, x):
        # We let user set it on the fly
        self.__dc = DayCounts.parse_dc(x)

    @staticmethod
    def dc_domain():
        """"Day count domain"""
        d = DayCounts.NL_DC + DayCounts.OO_DC + DayCounts.BUS_DC + \
            DayCounts.ACT_DC + DayCounts.XX360_DC
        return [x.upper() for x in d]

    @staticmethod
    def parse_dc(dc):
        """"Given string, code attempts to parse it to something known in the
        domain. If attempt fails, code raises and error."""
        assert isinstance(dc, str), 'Day count must be a string'
        n   = dc
        dc  = dc.upper()
        # User is giving a properly formatted dc
        if dc in DayCounts.dc_domain():
            return dc
        # Assertive cases
        if DayCounts.is_nl365(dc):
            dc = DayCounts.NL_DC[0]
            return dc.upper()
        if DayCounts.is_one_one_dc(dc):
            dc = DayCounts.OO_DC[0]
            return dc.upper()
        # Heuristics
        if DayCounts.appears_bus_dc(dc):
            return DayCounts.parse_bus_dc(dc)
        if DayCounts.appears_act_dc(dc):
            return DayCounts.parse_act_dc(dc)
        if DayCounts.appears_xx360_dc(dc):
            return DayCounts.parse_xx360_dc(dc)
        # No can do
        raise NotImplementedError('Convention %s cannot be parsed as a '
                                  'valid day count' % n)

    @staticmethod
    def parse_bus_dc(dc):
        """"Will try to parse any business day count type or raise error if
        fails. If day count is not of business type but is in internal domain,
        function will return it as well."""
        assert isinstance(dc, str), 'Day count must be a string'
        n  = dc
        dc = dc.upper()
        domain = DayCounts.dc_domain()
        # The trivial case where we have nothing to do
        if dc in domain:
            return dc
        parts = dc.split(DayCounts.SEP)
        if len(parts) != 2:
            raise NotImplementedError('Convention %s cannot be parsed as a '
                                      'business day count' % n)
        rp  = list()
        for dc in parts:
            # Bigger words first
            dc = dc.replace('BUSINESS', DayCounts.BUS)
            if dc == DayCounts.BUS:
                rp.append(dc)
                continue
            # Smaller
            dc = dc.replace('BD', DayCounts.BUS)
            if dc == DayCounts.BUS:
                rp.append(dc)
                continue
            # Smaller and overlapping
            dc = dc.replace('BU', DayCounts.BUS)
            if dc == DayCounts.BUS:
                rp.append(dc)
                continue
            rp.append(dc)
        dc = rp[0] + DayCounts.SEP + rp[1]
        if dc in domain:
            return dc
        raise NotImplementedError('Convention %s cannot be parsed as a '
                                  'business day count' % n)

    @staticmethod
    def parse_act_dc(dc):
        """Attempt to parse an actual day count convention. If it fails, it
        raises an error. Note that non-actual conventions in domain will also
        be returned."""
        assert isinstance(dc, str), 'Day count must be a string'
        n = dc
        dc = dc.upper()
        domain = DayCounts.dc_domain()
        # Safe replace
        dc  = dc.replace('ACTUAL', 'ACT')
        dc  = dc.replace('A/', 'ACT/')
        # Trivial case after capitalization
        if dc in domain:
            return dc
        # Exact matches go first
        if dc == 'ACT/ACT':
            dc = 'ACT/ACT ISDA'
        elif dc == 'ENGLISH' or ('FIXED' in dc and 'ACT/365' in dc):
            dc = 'ACT/365F'
        elif dc == 'FRENCH':
            dc = 'ACT/360'
        elif dc == 'ACT/365NL':
            dc = DayCounts.NL_DC[0].upper()
        elif dc == 'EXACT/EXACT':
            dc = 'ACT/ACT AFB'
        elif dc == 'EXACT/360':
            dc = 'ACT/360'
        elif dc == 'EXACT/365':
            dc = 'ACT/365'
        elif 'EXACT/365' in dc and 'FIXE' in dc:
            dc = 'ACT/365F'
        elif 'ACT/ACT' in dc and 'FRENCH' in dc:
            dc = 'ACT/ACT AFB'
        elif 'ACT/ACT' in dc and ('ISDA' in dc or 'SWAP' in dc or
                                  'HISTORICAL' in dc):
            dc = 'ACT/ACT ISDA'
        elif 'ACT/ACT' in dc and ('BOND' in dc or 'ICMA' in dc or 'ISMA' in
                                  dc):
            dc = 'ACT/ACT ICMA'
        elif 'ISMA' in dc and '99' in dc:
            dc = 'ACT/ACT ICMA'
        elif 'ACT/365' in dc and 'NO LEAP YEAR' in dc:
            dc = DayCounts.NL_DC[0].upper()
        elif ('ACT/365' in dc and 'LEAP YEAR' in dc) or ('YEAR' in dc and
                                                         'ISMA' in dc):
            dc = 'ACT/365L'
        if dc in domain:
            return dc
        else:
            raise NotImplementedError('Convention %s cannot be parsed as an '
                                      'actual day count' % n)

    @staticmethod
    def parse_xx360_dc(dc):
        assert isinstance(dc, str), 'Day count must be a string'
        n = dc
        dc = dc.upper()
        domain = DayCounts.dc_domain()
        # Safe replace - note that act/360 also falls into this category
        dc = dc.replace('ACTUAL', 'ACT')
        # Trivial case after capitalization
        if dc in domain:
            return dc
        if dc == 'BOND BASIS' or dc == '30/360':
            dc = '30A/360'
        elif '30/360' in dc and 'SIA' in dc:
            dc = '30A/360'
        elif '30/360' in dc and 'ISDA' in dc:
            dc = '30A/360'
        elif dc == '30S/360' or ('30S/360' in dc and 'SPECIAL GERMAN' in dc) \
                or dc == 'EUROBOND BASIS' or dc == 'SPECIAL GERMAN':
            dc = '30E/360'
        elif '30/360' in dc and ('ISMA' in dc or 'EUROPEAN' in dc
                                 or 'ICMA' in dc or 'SPECIAL GERMAN' in dc):
            dc = '30E/360'
        elif '30/360' in dc and 'GERMAN' in dc:  # This case needs to be
            # this same block
            dc = '30E/360 ISDA'
        elif dc == '30US/360' or ('30/360' in dc and 'US' in dc) or \
                ('30/360' in dc and 'US MUNI' in dc) or \
                ('30/360' in dc and ('SIFMA' in dc or 'PSA' in dc or 'BMA'
                                     in dc)):
            dc = '30U/360'
        elif dc == '28/360':
            dc = 'ACT/360'
        # Check, return or raise
        if dc in domain:
            return dc
        else:
            raise NotImplementedError('Convention %s cannot be parsed as an '
                                      'XX/360 day count' % n)

    @staticmethod
    def appears_bus_dc(dc):
        """Returns boolean indicating if the day count appears to be
        business"""
        assert isinstance(dc, str), 'Day count must be a string'
        dc = dc.lower()
        if 'bu' in dc or '252' in dc or 'bd' in dc:
            return True
        else:
            return False

    @staticmethod
    def appears_act_dc(dc):
        """Returns boolean indicating if the day count appears to be of type
        actual"""
        assert isinstance(dc, str), 'Day count must be a string'
        dc = dc.lower()
        if 'act' in dc or 'english' in dc or 'french' in dc or \
                'no leap year' in dc or 'exact' in dc or 'a/' in dc or (
                'isma' in dc and 'year' in dc) or ('isma' in dc and '99' in
                                                   dc):
            return True
        else:
            return False

    @staticmethod
    def appears_xx360_dc(dc):
        """Returns boolean indicating if the day count appears to be of type
        xx/360 or act/360"""
        assert isinstance(dc, str), 'Day count must be a string'
        dc = dc.lower()
        if (('30' in dc or '28' in dc) and '360' in dc) or 'bond' in dc or \
                'muni' in dc or 'german' in dc or 'act/360' in dc:
            return True
        else:
            return False

    @staticmethod
    def is_one_one_dc(dc):
        """Returns boolean indicating if day count is a valid 1/1 convention"""
        assert isinstance(dc, str), 'Day count must be a string'
        dc = dc.lower()
        if dc == '1/1' or dc == 'one/one':
            return True
        else:
            return False

    @staticmethod
    def is_nl365(dc):
        """Returns boolean indicating if day count is a valid nl/365
        convention"""
        assert isinstance(dc, str), 'Day count must be a string'
        dc = dc.lower()
        if dc == 'nl/365' or dc == 'nl365' or dc == 'act/365 no leap year':
            return True
        else:
            return False

    @staticmethod
    def _days_30360_core(y1, m1, d1, y2, m2, d2):
        """Core engine for 30/360 days counting

        Function takes date split into year, month, days (each of which is
        an integer or integer array)
        """
        return (y2-y1)*360+(m2-m1)*30+(d2-d1)

    @staticmethod
    def _date_parser(d1, d2):
        """Given Timestamps or DatetimeIndex, function splits dates into
        the following tuple (of integer or integer arrays)
                (y1, m1, d1, y2, m2, d2)

        Note: no checks performed
        """
        # Broadcast, no matter what. This will enable us to do logical
        # indexing even for the scalar case. Transforming time stamps to
        # lists is necessary for the proper broadcasting
        if isinstance(d1, Timestamp):
            d1 = [d1]
        if isinstance(d2, Timestamp):
            d2 = [d2]
        d1, d2 = broadcast_arrays(d1, d2)
        d1 = DatetimeIndex(d1)
        d2 = DatetimeIndex(d2)
        y1 = d1.year.values
        m1 = d1.month.values
        d1 = d1.day.values
        y2 = d2.year.values
        m2 = d2.month.values
        d2 = d2.day.values
        return y1, m1, d1, y2, m2, d2

    def _eom_mask(self, year, months, days):
        """Given an array of days and months, return bool array for dates
        which are in EOM"""
        febeom = (self.isleap(year) & (days == 29) & (months == 2)) | \
                 (~self.isleap(year) & (days == 28) & (months == 2))
        m30    = (days == 30) & ((months == 4) | (months == 6) |
                                 (months == 9) | (months == 11))
        m31    = (days == 31) & ((months == 1) | (months == 3) |
                                 (months == 5) | (months == 7) |
                                 (months == 8) | (months == 10) |
                                 (months == 12))
        return (febeom | m30) | m31

    @staticmethod
    def _simple_cast(d):
        """Cast date into Timestamp or numpy datetime64[D] array"""
        d = to_datetime(d)
        if not isinstance(d, Timestamp):
            d = d.values.astype('datetime64[D]')
        else:
            d = datetime64(d).astype('datetime64[D]')
        return d

