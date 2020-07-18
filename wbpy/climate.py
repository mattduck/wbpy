# -*- coding: utf-8 -*-
import re
import datetime
import pprint
import json
import itertools

import pycountry
import six

from . import utils


class ClimateDataset(object):

    def __init__(self, api_calls, data_type, data_interval, call_date):
        """
        :param api_calls:
            List of dicts with the keys "url" and "resp". Necessary as multiple
            responses can form one dataset.

        :param data_type:
            eg. ``pr``, ``tas``, ``tmin_means``

        :param data_interval:
            eg. ``mavg``, ``decade``

        :param call_date:
            Date of the url call
        """
        self.api_call_date = call_date
        self.api_calls = api_calls

        self._data_type_arg = data_type
        self._interval_arg = data_interval

        for resp in self.api_calls:
            region = str(resp["url"].split("/")[-1])
            try:
                code = utils.convert_country_code(region.upper(), "alpha2")
                # This is a bit ugly. It's because of two breaking changes in
                # old pycountry versions - one to raise a KeyError instead of
                # returning None, and one to replace alpha2 with alpha_2.
                try:
                    country = pycountry.countries.get(alpha_2=code)
                except KeyError:
                    country = pycountry.countries.get(alpha2=code)
                if country is None:
                    raise KeyError
                val = country.name
            except KeyError:  # If not country code, assume it's a basin
                code = region
                val = "http://data.worldbank.org/sites/default/files"
                "/climate_data_api_basins.pdf"
            resp["region"] = (code, val)

    def __repr__(self):
        s = "<%s.%s(%r, %r) with id: %r>"
        return s % (
            self.__class__.__module__,
            self.__class__.__name__,
            self.data_type,
            self.interval,
            id(self),
            )

    def __str__(self):
        return pprint.pformat(self.as_dict())


class InstrumentalDataset(ClimateDataset):

    def __init__(self, *args, **kwargs):
        super(InstrumentalDataset, self).__init__(*args, **kwargs)

        dt = self._data_type_arg
        self.data_type = {dt: ClimateAPI._instrumental_types[dt]}
        self.interval = self._interval_arg

        self.dates = "data.worldbank.org/developers/climate-data-api: "\
            "Country averages are for 1901-2009, basin averages are for "\
            "1960-2009."

        if self.interval == "decade":
            self.dates += " For decadal requests, '1900' averages only 9 "\
                "years, as the year 1900 is not included. "

    def as_dict(self, use_datetime=False):
        """Return dataset data as dictionary.

        Keys are: data[location][date]

        :param use_datetime:
            Use datetime.date() objects for date keys, instead of strings.

        """
        results = {}

        if self.interval == "month":
            for call in self.api_calls:
                sorted_months = sorted(call["resp"],
                    key=lambda row: float(row["month"]))
                vals = [float(row["data"]) for row in sorted_months]

                region_code = call["region"][0]
                results[region_code] = vals
        else:
            for call in self.api_calls:
                region_code = call["region"][0]
                this_region = {}
                results[region_code] = this_region
                for row in call["resp"]:
                    if use_datetime:
                        key = utils.worldbank_date_to_datetime(
                            str(row["year"]))
                    else:
                        key = str(row["year"])
                    this_region[key] = float(row["data"])
        return results


class ModelledDataset(ClimateDataset):

    def __init__(self, *args, **kwargs):
        super(ModelledDataset, self).__init__(*args, **kwargs)

        dt = self._data_type_arg
        self.data_type = {dt: ClimateAPI._modelled_types[dt]}

        intv = self._interval_arg
        self.interval = {intv: ClimateAPI._modelled_intervals[intv]}

        self.gcms = {}
        for gcm_key in self.as_dict():
            if gcm_key in ClimateAPI._gcm:
                self.gcms[gcm_key] = ClimateAPI._gcm[gcm_key]

        all_sres = set()
        for call in self.api_calls:
            for row in call["resp"]:
                row_sres = row.get("scenario")
                if row_sres:
                    all_sres.add(row_sres)
        self.sres = list(all_sres)

        if self.data_type in ["pr", "tas"]:
            self.control_period = ("1961", "1999")
        else:
            self.control_period = ("1961", "2000")

    def dates(self, use_datetime=False):
        """Return dataset date start/end pairs.

        :param use_datetime:
            If True, return dates as datetime.date() object instead of strings.

        """
        dates = set()
        all_urls = [call["url"] for call in self.api_calls]
        for url in all_urls:
            start, end = re.findall(r"\d+/\d+", url)[0].split("/")
            if use_datetime:
                start = utils.worldbank_date_to_datetime(start)
                end = utils.worldbank_date_to_datetime(end)
            dates.add((start, end))
        return sorted(list(dates))

    def as_dict(self, sres="a2", use_datetime=False):
        """Return dataset data as dictionary.

        Keys are: data[gcm][location][date]

        :param sres:
            Which SRES to use for future values. The API supports A2 and B1,
            although not all GCMs have data for both.

        :param use_datetime:
            Use datetime.date() objects for date keys, instead of strings.

        """
        results = {}
        for call in self.api_calls:
            if "ensemble" in call["url"]:
                get_gcm_key = lambda row: "ensemble_%d" % row["percentile"]
                annual_data_key = "annualVal"
            else:
                get_gcm_key = lambda row: row["gcm"]
                annual_data_key = "annualData"

            region_code = call["region"][0]

            for row in call["resp"]:
                # Only future calls have scenarios. Limit results to one
                # scenario at a time, so we can have one value per time
                # period.
                row_scenario = row.get("scenario")
                if row_scenario and row_scenario != sres.lower():
                    continue

                gcm_key = get_gcm_key(row)
                if gcm_key not in results:
                    results[gcm_key] = {}

                if region_code not in results[gcm_key]:
                    results[gcm_key][region_code] = {}
                region_dict = results[gcm_key][region_code]

                year = str(row["toYear"])
                if use_datetime:
                    year = utils.worldbank_date_to_datetime(year)

                if year not in region_dict:
                    if "annual" in call["url"]:
                        val = float(row[annual_data_key][0])
                    else:
                        # Assume they are monthly values
                        val = row["monthVals"]
                    region_dict[year] = val

        return results


class ClimateAPI(object):

    """Request data from the World Bank Climate API.

    You can override the default tempfile cache by passing a function
    ``fetch``, which requests a URL and returns the response as a string.
    """

    _gcm = dict(
        bccr_bcm2_0="BCM 2.0",
        csiro_mk3_5="CSIRO Mark 3.5",
        ingv_echam4="ECHAM 4.6",
        cccma_cgcm3_1="CGCM 3.1 (T47)",
        cnrm_cm3="CNRM CM3",
        gfdl_cm2_0="GFDL CM2.0",
        gfdl_cm2_1="GFDL CM2.1",
        ipsl_cm4="IPSL-CM4",
        microc3_2_medres="MIROC 3.2 (medres)",
        miub_echo_g="ECHO-G",
        mpi_echam5="ECHAM5/MPI-OM",
        mri_cgcm2_3_2a="MRI-CGCM2.3.2",
        inmcm3_0="INMCM3.0",
        ukmo_hadcm3="UKMO HadCM3",
        ukmo_hadgem1="UKMO HadGEM1",
        ensemble="All percentile values of all models together",
        ensemble_10="10th percentile values of all models together",
        ensemble_50="50th percentile values of all models together",
        ensemble_90="90th percentile values of all models together",
        )

    _valid_modelled_dates = [
        (1920, 1939),
        (1940, 1959),
        (1960, 1979),
        (1980, 1999),
        (2020, 2039),
        (2040, 2059),
        (2060, 2079),
        (2080, 2099),
        ]

    _valid_stat_dates = [
        (1961, 2000),
        (2046, 2065),
        (2081, 2100),
        ]

    _instrumental_types = dict(
        pr="Precipitation (rainfall and assumed water equivalent), in "
        "millimeters",
        tas="Temperature, in degrees Celsius",
        )

    _instrumental_intervals = ["year", "month", "decade"]

    _modelled_types = dict(
        tmin_means="Average daily minimum temperature, Celsius",
        tmax_means="Average daily maximum temperature, Celsius",
        tmax_days90th="Number of days with max temperature above the "
        "control period's 90th percentile (hot days)",
        tmin_days90th="Number of days with min temperature above the "
        "control period's 90th percentile (warm nights)",
        tmax_days10th="Number of days with max temperature below the "
        "control period's 10th percentile (cool days)",
        tmin_days10th="Number of days with min temperature below the "
        "control period's 10th percentile (cold nights)",
        tmin_days0="Number of days with min temperature below "
        "0 degrees Celsius",
        ppt_days="Number of days with precipitation > 0.2mm",
        ppt_days2="Number of days with precipitation > 2mm",
        ppt_days10="Number of days with precipitation > 10mm",
        ppt_days90th="Number of days with precipitation > the control "
        "period's 90th percentile",
        ppt_dryspell="Average number of days between precipitation "
        "events",
        ppt_means="Average daily precipitation",
        pr=_instrumental_types["pr"],
        tas=_instrumental_types["tas"],
        )

    _modelled_intervals = dict(
        mavg="Monthly average",
        annualavg="Annual average",
        manom="Average monthly change (anomaly).",
        annualanom="Average annual change (anomaly).",
        )

    # Convenience codes
    _shorthand_codes = dict(
        aanom="annualanom",
        aavg="annualavg",
        )
    for _k, _d_key in _shorthand_codes.items():
        for _d in [_instrumental_types, _modelled_types,
            _instrumental_intervals, _modelled_intervals]:
            if _d_key in _d:
                _d[_k] = _d[_d_key]

    # Make them accessible via single attr
    ARG_DEFINITIONS = dict(
        instrumental_types=_instrumental_types,
        instrumental_intervals=_instrumental_intervals,
        modelled_types=_modelled_types,
        modelled_intervals=_modelled_intervals,
        )

    BASE_URL = "http://climatedataapi.worldbank.org/climateweb/rest/"

    def __init__(self, fetch=None):
        self.fetch = fetch if fetch else utils.fetch

    @staticmethod
    def _clean_api_code(code):
        code = code.lower()
        return ClimateAPI._shorthand_codes.get(code, code)

    def get_instrumental(self, data_type, interval, locations):
        """Get historical data for temperature or precipitation.

        :param data_type:
            Either ``pr`` for precipitation, or ``tas`` for temperature.

        :param interval:
            Either ``year``, ``month`` or ``decade``.

        :param locations:
            A list of API location codes - either ISO alpha-2 or alpha-3
            country codes, or basin ID numbers.

        """
        data_type = self._clean_api_code(data_type)
        interval = self._clean_api_code(interval)

        assert data_type in self.ARG_DEFINITIONS["instrumental_types"]
        assert interval in self.ARG_DEFINITIONS["instrumental_intervals"]

        # Construct URLs
        urls = []
        for loc in locations:
            try:
                int(loc)
                loc_type = "basin"
            except ValueError:
                loc = utils.convert_country_code(loc, "alpha3")
                loc_type = "country"

            data_url = "v1/{0}/cru/{1}/{2}/{3}".format(loc_type, data_type,
                interval, str(loc))
            full_url = "".join([self.BASE_URL, data_url])
            urls.append((loc, full_url))

        # If no exception from URL construction, make requests
        api_calls = []
        for loc, url in urls:
            resp = json.loads(self.fetch(url))
            api_calls.append(dict(
                url=url,
                resp=resp,
                ))

        call_date = datetime.datetime.now().date()
        return InstrumentalDataset(api_calls, data_interval=interval,
            data_type=data_type, call_date=call_date)

    def get_modelled(self, data_type, interval, locations):
        """Get modelled data for precipitation or temperature.

        :param data_type:
            The data statistic ID. See
            ``self.ARG_DEFINITIONS["modelled_types"]`` for IDs and values.

        :param interval:
            The interval ID. See ``self.ARG_DEFINITIONS["modelled_intervals"]``
            for IDs and values.

        :param locations:
            A list of API location codes - either ISO alpha-2 or alpha-3
            country codes, or basin ID numbers.

        """
        data_type = self._clean_api_code(data_type)
        interval = self._clean_api_code(interval)

        assert data_type in self.ARG_DEFINITIONS["modelled_types"]
        assert interval in self.ARG_DEFINITIONS["modelled_intervals"]

        # As there aren't many variants of each data type, it's simplest to
        # always call both GCM and ensemble data, for all dates, and not offer
        # any filtering options.

        # Derivived statistic requests are all of the "ensemble" kind, and they
        # have a different set of dates to GCM requests.
        if data_type in ["pr", "tas"]:
            all_urls = ["v1/{0}/{1}/{2}/{3}/{4}/{5}",
                "v1/{0}/{1}/ensemble/{2}/{3}/{4}/{5}"]
            all_dates = self._valid_modelled_dates
        else:
            all_urls = ["v1/{0}/{1}/ensemble/{2}/{3}/{4}/{5}"]
            all_dates = self._valid_stat_dates

        api_calls = []
        for loc in locations:
            try:
                int(loc)  # basin ids are ints
                loc_type = "basin"
            except ValueError:
                loc = utils.convert_country_code(loc, "alpha3")
                loc_type = "country"

            for dates, url in itertools.product(all_dates, all_urls):
                start_date = dates[0]
                end_date = dates[1]
                rest_url = url.format(loc_type, interval, data_type,
                    start_date, end_date, loc)
                full_url = "".join([self.BASE_URL, rest_url])

                resp = json.loads(self.fetch(full_url))
                api_calls.append(dict(
                    url=full_url,
                    resp=resp,
                    ))

        call_date = datetime.datetime.now().date()
        return ModelledDataset(api_calls, data_interval=interval,
            data_type=data_type, call_date=call_date)
