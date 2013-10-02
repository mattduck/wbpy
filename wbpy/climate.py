# -*- coding: utf-8 -*-
import re
import datetime
import pprint

import pycountry

import utils
import indicators


class ClimateDataset(object):
    """ A single World Bank Climate Data API dataset. Includes the JSON
    response, various metadata, and methods to convert the data into useful
    objects.
    """

    def __init__(self, api_calls, data_type, data_stat, call_date):
        """
        :param api_calls:
            List of dicts with the keys "url" and "resp". Necessary as multiple
            responses can form one dataset.
        """
        self.api_call_date = call_date
        self.api_calls = api_calls

        for resp in self.api_calls:
            region = str(resp["url"].split("/")[-1])
            try:
                code = utils.convert_country_code(region.upper(), "alpha2")
                val = pycountry.countries.get(alpha2=code).name
            except KeyError: # If not country code, assume it's a basin
                code = region
                val = "http://data.worldbank.org/sites/default/files/climate_data_api_basins.pdf"
            resp["region"] = (code, val)


        # For historical data, will either be "monthly", "yearly", etc. 
        # For modelled, "mavg" etc.
        self.type = data_type

        # For historical, either precip or temp.
        # For modelled, could also be a derived stat, eg. tmin_means.
        self.stat = data_stat

    def __repr__(self):
        s = "<%s.%s(%r, %r) with id: %r>"
        return s % (
            self.__class__.__module__,
            self.__class__.__name__,
            self.stat,
            self.type,
            id(self),
            )

    def __str__(self):
        return pprint.pformat(self.data_as_dict())

class HistoricalDataset(ClimateDataset):

    def __init__(self, *args, **kwargs):
        super(HistoricalDataset, self).__init__(*args, **kwargs)
        self.dates = "data.worldbank.org/developers/climate-data-api: "\
            "Country averages are for 1901-2009, basin averages are for "\
            "1960-2009."

        if self.type == "decade":
            self.dates += " For decadal requests, '1900' averages only 9 "\
                "years, as the year 1900 is not included. "


    def data_as_dict(self, use_datetime=False):
        results = {}
        if self.type == "month":
            resp_key = "month"
            get_datetime = lambda x: datetime.date(2009, x + 1, 1)
        else:
            resp_key = "year"
            get_datetime = lambda x: utils.worldbank_date_to_datetime(str(x))

        for call in self.api_calls:
            region_code = call["region"][0]
            this_region = {}
            results[region_code] = this_region
            for row in call["resp"]:
                if use_datetime:
                    key = get_datetime(row[resp_key])
                else:
                    key = str(row[resp_key])
                this_region[key] = float(row["data"])
        return results


class ModelledDataset(ClimateDataset):

    def __init__(self, *args, **kwargs):
        super(ModelledDataset, self).__init__(*args, **kwargs)

    def dates(self, use_datetime=False):
        data_dates = set()
        all_urls = [call["url"] for call in self.api_calls]
        for url in all_urls:
            start, end = re.findall("\d+/\d+", url)[0].split("/")
            if use_datetime:
                start = utils.worldbank_date_to_datetime(start)
                end = utils.worldbank_date_to_datetime(end)
            data_dates.add((start, end))
        return sorted(list(data_dates))

    def data_as_dict(self, use_datetime=False):
        call_url = self.api_calls[0]["url"]
        if "ensemble" in call_url:
            get_gcm_key = lambda row: "ensemble_%d" % row["percentile"]
        else:
            get_gcm_key = lambda row: row["gcm"]

        results = {}
        for call in self.api_calls:
            region_code = call["region"][0]

            for row in call["resp"]:
                gcm_key = get_gcm_key(row)
                if gcm_key not in results:
                    results[gcm_key] = {}

                if row["scenario"] not in results[gcm_key]:
                    results[gcm_key][row["scenario"]] = {}
                scenario_dict = results[gcm_key][row["scenario"]]

                if region_code not in scenario_dict:
                    scenario_dict[region_code] = {}
                region_dict = scenario_dict[region_code]

                year = str(row["toYear"])

                if "annual" in call_url:
                    if year not in region_dict:
                        if use_datetime: 
                            year = utils.worldbank_date_to_datetime(year)
                        val = float(row["annualData"][0])
                        region_dict[year] = val
                else:
                    # Assume these are monthly values
                    for i in xrange(12):
                        month = "%sM%02d" % (year, i + 1)
                        if use_datetime:
                            month = utils.worldbank_date_to_datetime(month)
                        if month not in region_dict:
                            val = float(row["monthVals"][i])
                            region_dict[month] = val
        return results
                

class ClimateAPI(object):

    # ========================================================================
    # PUBLIC METHODS
    # ========================================================================

    def __init__(self, fetch=None):
        """ A connection to the World Bank Climate API. 

        You can override the default tempfile cache by passing a ``fetch`` 
        function, which fetches a url and returns a string. ``self.fetch`` can
        also be set after instantiation.
        """
        self.base_url = "http://climatedataapi.worldbank.org/climateweb/rest/"
        self._valid_modelled_dates = (
            (1920, 1939),
            (1940, 1959),
            (1960, 1979),
            (1980, 1999),
            (2020, 2039),
            (2040, 2059),
            (2060, 2079),
            (2080, 2099),
            )
        self._valid_stat_dates = (
            (1961, 2000),
            (2046, 2065),
            (2081, 2100),
            )
        self.definitions = dict(
            # Unlike Indicators, can't get these from the API, so they'll
            # have to be static, copied from /developers/climate-data-api.
            type=dict(
                mavg="Monthly average",
                aavg="Annual average",
                manom="Average monthly change (anomaly).",
                aanom="Average annual change (anomaly).",
                ),
            stat=dict(
                tmin_means="Average daily minimum temperature, Celsius",
                tmax_means="Average daily maximum temperature, Celsius",
                tmax_days90th="Number of days with max temperature above the "\
                              "control period's 90th percentile (hot days)",
                tmin_days90th="Number of days with min temperature above the "\
                              "control period's 90th percentile (warm nights)",
                tmax_days10th="Number of days with max temperature below the "\
                              "control period's 10th percentile (cool days)",
                tmin_days10th="Number of days with min temperature below the "\
                              "control period's 10th percentile (cold nights)",
                tmin_days0="Number of days with min temperature below "\
                           "0 degrees Celsius",
                ppt_days="Number of days with precipitation > 0.2mm",
                ppt_days2="Number of days with precipitation > 2mm",
                ppt_days10="Number of days with precipitation > 10mm",
                ppt_days90th="Number of days with precipitation > the control "\
                             "period's 90th percentile",
                ppt_dryspell="Average number of days between precipitation "\
                             "events",
                ppt_means="Average daily precipitation",
                ),
            gcm=dict(
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
                ),
            sres=dict(
                a2="A2 Scenario",
                b1="B1 Scenario",
                ),
            )
        self._definitions = dict(
            # Definitions where using different codes to the Climate API.
            pr="Precipitation (rainfall and assumed water equvialent) in "\
               "millimeters",
            tas="Temperature, in degrees Celsisus",
            annualavg=self.definitions["type"]["aavg"],
            annualanom=self.definitions["type"]["aanom"],
            anom_cp="The control period is 1961 - 1999.",
            anom_cp_stat="The control period is 1961 - 2000.",
            )

        if fetch:
            self.fetch = fetch
        else: 
            self.fetch = _fetch


    def get_precip_instrumental(self, locations, interval="year"):
        """ Get historical precipitation data, `based on gridded climatologies
        from the Climate Research Unit`. These `are proxies, where modelling has
        been used to extrapolate estimates where instrumental (station) data
        were unavailable or unreliable`. 

        :param locations:   Get data for list of ISO country codes and World 
                            Bank basin IDs.

        :param interval:    `year`, `month` or `decade`.
        
        :returns:   Data and metadata dicts. Data keys are 
                    `location` > `time` > `value`.
        """
        return self._get_instrumental(var="pr", locations=locations,
                interval=interval)


    def get_temp_instrumental(self, locations, interval="year"):
        """ Get historical temperature data. See ``get_precip_instrumental()``. 
        """
        return self._get_instrumental(var="tas", locations=locations,
                interval=interval)


    def get_precip_modelled(self, data_type, locations, gcm=None, sres=None):
        """ Get precipitation data derived from global circulation models. 

        :param data_type:   Single type ID. See ``self.definitions['type']``.

        :param locations:   Get data for list of ISO country codes and World 
                            Bank basin IDs.

        :param gcm:         List of GCMs. If None, gets all except `ensembles`. 
                            See ``self.definitions['gcm']``.

        :param sres:        Scenario ID - either `a2` or `b1`. If None, gets 
                            both scenarios.

        :returns:   Namedtuple with *data* and *metadata* attrs.
        """
        return self._get_modelled(var="pr", data_type=data_type,
                locations=locations, gcm=gcm, sres=sres)
                

    def get_temp_modelled(self, data_type, locations, gcm=None, sres=None):
        """ Get modelled temperature data. ``See get_precip_modelled()``. """
        return self._get_modelled(var="tas", data_type=data_type,
                locations=locations, gcm=gcm, sres=sres)
    

    def get_derived_stat(self, stat, data_type, locations,
            ensemble_gcm=None, sres=None): 
        """ Get precipitation or temperature statistic derived from `ensemble`
        data - ie. from all GCMs. 

        :param stat:          Single stat ID. See ``self.definitions['stat']``.

        :param data_type:     Single type ID. See ``self.definitions['type']``.

        :param locations:     Get data for list of ISO country codes and World 
                              Bank basin IDs.

        :param ensemble_gcm:    List of any of the "ensemble" GCM values.
                                Defaults to ["ensemble"], which gets all
                                percentiles.

        :param sres:        Scenario ID - either `a2` or `b1`. If None, gets 
                            both scenarios.

        :returns:   Namedtuple with *data* and *metadata* attrs.
        """
        if not ensemble_gcm:
            ensemble_gcm = ["ensemble"]

        return self._get_modelled(var=stat, data_type=data_type,
                locations=locations, sres=sres, gcm=ensemble_gcm)


    # ========================================================================
    # PRIVATE METHODS
    # ========================================================================

    def _get_instrumental(self, var, locations, interval="year"):
        # Construct URLs
        urls = []
        for loc in locations:
            try:
                int(loc)
                basins_url = "v1/basin/cru/{0}/{1}/{2}".format(var, interval,
                                str(loc))
                full_url = "".join([self.base_url, basins_url, ".json"])
                urls.append((loc, full_url))
            except ValueError:
                loc = _convert_to_alpha3(loc)
                countries_url = "v1/country/cru/{0}/{1}/{2}".format(var, 
                                interval, loc)
                full_url = "".join([self.base_url, countries_url, ".json"])
                urls.append((loc, full_url))

        results = {}
        for loc, url in urls:
            loc = _convert_to_alpha2(loc)
            response = json.loads(self.fetch(url))
            results[loc] = {}
            for data in response:
                # The response has different keys depending on the interval
                if interval == "month":
                    # + 1 to month as it uses keys 0-11, unless I missing some
                    # standard I think 1-12 more sensible.
                    results[loc][data["month"] + 1] = data["data"]
                else:
                    results[loc][data["year"]] = data["data"]
        metadata = {}
        metadata["stat"] = self._definitions[var] # pr or tas
        metadata["interval"] = interval
        return _ClimateDataTuple(results, metadata)


    def _get_modelled(self, var, data_type, locations, gcm=None, sres=None):
        """ Handles the different modelled calls - ensemble, derived
        stat, etc. 
        """
        # You can input 'aavg', 'aanom', to go w/ the proper 'mavg', 'manom'.
        # The actual API code is 'annualavg', etc.
        if data_type.startswith("a"):
            data_type = data_type.replace("a", "annual", 1) 

        locations = [_convert_to_alpha3(code) for code in locations]

        # Info dict can be arranged from input
        metadata = {}
        metadata["gcm"] = {}
        if gcm:
            for model in gcm: 
                metadata["gcm"][model.lower()] = \
                    self.definitions["gcm"][model.lower()]
        else:
            for gcm_k, gcm_v in self.definitions["gcm"].items():
                if not gcm_v.startswith("ensemble"):
                    metadata["gcm"][gcm_k] = gcm_v
        if sres:
            metadata["sres"] = self.definitions["sres"][sres.lower()]
        else:
            metadata["sres"] = self.definitions["sres"]
        try:
            metadata["stat"] = self.definitions["stat"][var.lower()]
        except KeyError:
            metadata["stat"] = self._definitions[var] # pr or tas
        try:
            metadata["type"] = self.definitions["type"][data_type.lower()]
        except KeyError:
            metadata["type"] = self._definitions[data_type.lower()]

        # Stats have a different control period to pr and tas for manom and
        # aanom data.
        if "anom" in data_type:
            if var in ["tas", "pr"]:
                metadata["type"] += " " + self._definitions["anom_cp"]
            else:
                metadata["type"] += " " + self._definitions["anom_cp_stat"]

        # Ensemble requests are separated from other modelled requests, as they 
        # have a different URL and response structure, and it's messy having
        # a single method with lots of clauses etc.
        results = {}
        metadata["dates"] = {}
        ensemble_gcms = []
        if gcm:
            for val in gcm:
                if val.startswith("ensemble"):
                    ensemble_gcms.append(val)
        if ensemble_gcms:
            results, dates = self._get_modelled_ensemble(var=var, 
                 data_type=data_type, locations=locations, sres=sres,
                 gcms=ensemble_gcms) 
            for from_date, to_date in dates:
                metadata["dates"][from_date] = to_date

        another_request = False
        if gcm:
            gcm = filter(lambda name: not name.startswith("ensemble"), gcm)
            if gcm:
                # If there are more GCM models to come, they'll be passed on 
                # with the "ensemble" ones filtered out.
                another_request = True
        else:
            # No GCM given, must make request
            another_request = True
        
        if another_request:
            gcm_results, dates = self._get_modelled_gcm(var=var, 
                 data_type=data_type, locations=locations, 
                 sres=sres, gcm=gcm)
            for from_date, to_date in dates:
                metadata["dates"][from_date] = to_date

            # These results will never have the same top-level keys as the
            # ensemble results, so update the original dictionary.
            results.update(gcm_results)

        return _ClimateDataTuple(results, metadata)


    def _get_modelled_gcm(self, var, data_type, locations, gcm=None,
        sres=None):
        # Construct the requested urls
        valid_dates = self._valid_modelled_dates
        urls = []
        for start_date, end_date in valid_dates:
            for loc in locations:
                try:
                    int(loc) # basin ids are ints
                    loc_type = "basin"
                except ValueError:
                    loc_type = "country"
                rest_url = "v1/{0}/{1}/{2}/{3}/{4}/{5}".format(
                        loc_type, data_type,
                        var, start_date, end_date, loc)
                full_url = "".join([self.base_url, rest_url, ".json"])
                urls.append((loc, full_url))

        # Get responses and tidy results
        results = {}
        dates = [] # dates metadata
        for loc, url in urls:
            loc = _convert_to_alpha2(loc)
            response = json.loads(self.fetch(url))
            for data in response:
                # L1 - GCM
                if data.has_key("gcm"):
                    gcm_key = data["gcm"]
                if gcm_key not in results:
                    results[gcm_key] = {}
                # L2 - Location
                if loc not in results[gcm_key]:
                    results[gcm_key][loc] = {}
                # L3 - year / scenario
                time = data["fromYear"]
                dates.append((time, data["toYear"]))
                if data.has_key("scenario"):
                    time = (time, data["scenario"])
                if time not in results[gcm_key][loc]:
                    results[gcm_key][loc][time] = {}
                # L4 - values / months, depending on the result
                if data.has_key("monthVals"):
                    for i, val in enumerate(data["monthVals"], 1):
                        results[gcm_key][loc][time][i] = val
                elif data.has_key("annualData"):
                    results[gcm_key][loc][time] = data["annualData"][0]

        # If sres or gcm values given, filter out unwanted
        # results. Best to get data in small no. of calls and to take out
        # unwanted, than to make a call for every percentile/GCM/SRES
        # variation.
        if gcm:
            res_keys = results.keys()
            for k in res_keys:
                if k not in gcm:
                    del(results[k])
        if sres:
            # Fine to iterate over this dict, as we're not deleting top-level
            # keys
            for gcm_key in results:
                for loc in results[gcm_key]:
                    time_keys = results[gcm_key][loc].keys()
                    for k in time_keys:
                        if sres:
                            try: 
                                if k[1].lower() != sres.lower():
                                    del(results[gcm_key][loc][k])
                            except TypeError: 
                                # (Time only subscriptable if a tuple, ie.
                                # a future value with a sres)
                                pass
        return results, set(dates)


    def _get_modelled_ensemble(self, var, data_type, locations, sres=None,
            gcms=None):
        # GCMs are assumed to be "ensemble" ones

        if var not in ["pr", "tas"]:
            # Then assume it's a stat. Stat directly replaces the var API arg.
            valid_dates = self._valid_stat_dates
        else:
            valid_dates = self._valid_modelled_dates

        # Construct the urls
        urls = []
        for start_date, end_date in valid_dates:
            for loc in locations:
                try:
                    int(loc) # basin ids are ints
                    loc_type = "basin"
                except ValueError:
                    loc_type = "country"
                rest_url = "v1/{0}/{1}/ensemble/{2}/{3}/{4}/{5}".format(
                        loc_type, data_type, var, start_date, end_date, loc)
                full_url = "".join([self.base_url, rest_url, ".json"])
                urls.append((loc, full_url))

        # Get responses and tidy results
        results = {}
        dates = [] 
        for loc, url in urls:
            loc = _convert_to_alpha2(loc)
            response = json.loads(self.fetch(url))
            for data in response:
                # L1 - percentile
                gcm_key = "_".join(["ensemble", str(data["percentile"])])
                if gcm_key not in results:
                    results[gcm_key] = {}
                # L2 - Location
                if loc not in results[gcm_key]:
                    results[gcm_key][loc] = {}
                # L3 - year / scenario
                time = data["fromYear"]
                dates.append((time, data["toYear"]))
                if data.has_key("scenario"):
                    time = (time, data["scenario"])
                if time not in results[gcm_key][loc]:
                    results[gcm_key][loc][time] = {}
                # L4 - values / months, depending on the result
                if data.has_key("monthVals"):
                    for i, val in enumerate(data["monthVals"], 1):
                        results[gcm_key][loc][time][i] = val
                elif data.has_key("annualVal"):
                    results[gcm_key][loc][time] = data["annualVal"][0]

        # If "ensemble" is given as a gcm, it should get all percentiles.
        # If eg. "ensemble_50" is given, it should only return 50th percentile.
        if gcms and "ensemble" not in gcms:
            for k in results.keys():
                if k not in gcms:
                    del(results[k])

        if sres:
            for gcm_key in results:
                for loc in results[gcm_key]:
                    time_keys = results[gcm_key][loc].keys()
                    for k in time_keys:
                        if sres:
                            try: 
                                if k[1].lower() != sres.lower():
                                    del(results[gcm_key][loc][k])
                            except TypeError: 
                                # (Time only subscriptable if a tuple, ie.
                                # a future value with a sres)
                                pass
        return results, set(dates)


