# -*- coding: utf-8 -*-
import os
import logging
import urllib2
import time
import md5
import tempfile
import re
import numbers
from collections import namedtuple
try: 
    import simplejson as json
except ImportError: 
    import json 

import pycountry # For iso code conversions

logger = logging.getLogger(__name__)

def _fetch(url):
    """ Temp file cache, keeps pages for a day. """
    one_day_old = 60*60*24
    cache_dir = os.path.join(tempfile.gettempdir(), "wbpy")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        logger.debug("Created cache directory " + cache_dir)
    logger.debug("Fetching %s ...", url)
    cache_path = os.path.join(cache_dir, md5.new(url).hexdigest())
    if os.path.exists(cache_path):
        if int(time.time()) - os.path.getmtime(cache_path) < one_day_old:
            logger.debug("Retrieving web page from cache.")
            return open(cache_path).read()
    logger.debug("URL not found in cache. Getting web page...")
    web_page = urllib2.urlopen(url).read()
    fd, tempname = tempfile.mkstemp()
    fp = os.fdopen(fd, "w")
    fp.write(web_page)
    fp.close()
    os.rename(tempname, cache_path)
    logger.debug("%s saved to cache." % url)
    return web_page

def _convert_to_alpha2(code):
    # Convert code if it ISO one, else return
    try:
        code = code.upper()
        if len(code) == 2:
            return pycountry.countries.get(alpha2=code).alpha2
        if len(code) == 3:
            return pycountry.countries.get(alpha3=code).alpha2
    except (KeyError, AttributeError):
        return code

def _convert_to_alpha3(code):
    try:
        code = code.upper()
        if len(code) == 2:
            return pycountry.countries.get(alpha2=code).alpha3
        if len(code) == 3:
            return pycountry.countries.get(alpha3=code).alpha3
    except (KeyError, AttributeError):
        return code


_CountryIndicatorsTuple = namedtuple("WorldBankCountryIndicators", 
    ["data", "indicators", "countries"])


class Indicators(object):
    def __init__(self, fetch=_fetch):
        """ A connection to the World Bank Indicators API.

        You can override the default tempfile cache by passing a ``fetch`` 
        function, which fetches a url and returns a string. ``self.fetch`` can
        also be set after instantiation.
        """
        self.fetch = fetch
        self.base_url = "http://api.worldbank.org/"

    # ========== PUBLIC METHODS =========

    def get_country_indicators(self, indicator_codes, country_codes=None, 
            **kwargs):
        """ Get indicator metrics for countries.

        :param indicator_codes:     Required list of metric codes.

        :param country_codes:   List of countries to get indicator data for. 
                                If None, queries all countries.

        :param kwargs:      These map directly to the API query args:
                            *Language*, 
                            *date*, 
                            *mrv*, 
                            *gapfill*, 
                            *frequency*.

        :returns:   Namedtuple with the following attrs:
                    *data* - the data, organising by indicato
        
        :returns:   Two dicts. The first contains the data, with nested keys: 
                    `Indicator code > ISO 2-digit country code > Date > Value`. 
                    The second dict contains the names/values for the 
                    indicator and country codes.
        """
        # Generate urls and concatenate multiple calls into one list.
        response_data = []
        if country_codes:
            country_codes = [_convert_to_alpha3(code) for code in country_codes]
            country_string = ";".join(country_codes)
        else:
            country_string = "all"
        for indicator_string in indicator_codes:
            url = "countries/{0}/indicators/{1}?".format(country_string, 
                    indicator_string)
            url = self._generate_indicators_url(url, **kwargs)
            response_data += self._get_api_response_as_json(url)

        # Arrange JSON data to be more accessible.
        data = {}
        indicator_metadata = {}
        country_metadata = {}
        for dataset in response_data:
            country_id = dataset["country"]["id"]
            indicator_id = dataset["indicator"]["id"]
            date = dataset["date"]

            if indicator_id not in data:
                data[indicator_id] = {}
            if country_id not in data[indicator_id]:
                data[indicator_id][country_id] = {}
            if date not in data[indicator_id][country_id]:
                data[indicator_id][country_id][date] = dataset["value"]

            if indicator_id not in indicator_metadata:
                indicator_metadata[indicator_id] = dataset["indicator"]["value"]

            if country_id not in country_metadata:
                country_metadata[country_id] = dataset["country"]["value"]

        return _CountryIndicatorsTuple(data, indicator_metadata,
            country_metadata)

    def get_indicators(self, indicator_codes=None, search=None,
            search_full=False, common_only=False, **kwargs):
        """ Make call to retrieve indicator codes and information.

        :param indicator_codes: List of codes, eg. SP.POP.TOTL for population.
                                If None, queries all (~8000).

        :param common_only:     Many of the indicators do not have wide country 
                                coverage. If True, filters out those 
                                indicators that do not appear on the 
                                main World Bank website (leaving ~1500).

        :param search:  Regexp string to filter results. By default, this only
                        searches the main name of the entity, eg. a country
                        name. If *search_full* is True, all fields are searched.

        :param kwargs:      These map directly to the API query args:
                            *language*,
                            *source*,
                            *topic*.
        
        :returns:   Dict of indicators, using ID codes as keys.
        """
        func_params = {
            "response_key": "id",
            "rest_url": "indicator",
            "search_key": "name",
            }
        results = self._get_indicator_data(func_params, 
            indicator_codes, search=search, search_full=search_full, 
            **kwargs)

        if common_only == True:
            # Compile a list of codes that are on the main website (and have
            # better data coverage), and filter out any results that cannot be
            # found on the site.
            page = self.fetch("http://data.worldbank.org/indicator/all")
            ind_codes = re.compile("(?<=http://data.worldbank.org/indicator/)"\
                                   "[A-Za-z0-9\.]+(?=\">)")
            common_matches = {}
            code_matches = set([code.lower() for code in \
                                ind_codes.findall(page)])
            # If key matches common code, include in results.
            for k, v in results.items():
                low_k = k.lower()
                for code_match in code_matches:
                    if code_match in low_k:
                        common_matches[k] = v
                        break
            return common_matches
        else:
            return results

    def get_countries(self, country_codes=None, search=None,
            search_full=False, **kwargs):
        """ Get info on countries, eg. ISO codes, longitude/latitude, capital
        city, income level, etc.

        :param country_code:    List of 2 or 3 letter ISO codes. If None, 
                                queries all.

        :param search:  Regexp string to filter results. By default, this only
                        searches the main name of the entity, eg. a country
                        name. If *search_full* is True, all fields are searched.

        :param kwargs:      These map directly to the API query args:
                            *language*,
                            *incomeLevel*,
                            *lendingType*,
                            *region*.

        :returns:   Dict of countries using 2-letter ISO codes as keys.
        """
        func_params = {
            "response_key": "iso2Code",
            "rest_url": "country",
            "search_key": "name",
            }
        if country_codes:
            country_codes = [_convert_to_alpha3(code) for code in country_codes]

        return self._get_indicator_data(func_params, 
            country_codes, search=search, search_full=search_full, 
            **kwargs) 

    def get_income_levels(self, income_codes=None, search=None,
            search_full=False, **kwargs):
        """ Get income categories.

        :param income_codes:    List of 3-letter ID codes. If None, queries all 
                                (~10). 

        :param search:  Regexp string to filter results. By default, this only
                        searches the main name of the entity, eg. a country
                        name. If *search_full* is True, all fields are searched.

        :param kwargs:      These map directly to the API query args:
                            *language*.

        :returns:   Dict of income levels using ID codes as keys.
        """
        func_params = {
            "response_key": "id",
            "rest_url": "incomelevel",
            "search_key": "value",
            }
        return self._get_indicator_data(func_params, 
            income_codes, search=search, search_full=search_full, 
            **kwargs)

    def get_lending_types(self, lending_codes=None, search=None,
            search_full=False, **kwargs):
        """ Get lending type categories. 

        :param lending_codes:   List of lending codes. If None, queries all (4).

        :param search:  Regexp string to filter results. By default, this only
                        searches the main name of the entity, eg. a country
                        name. If *search_full* is True, all fields are searched.

        :param kwargs:      These map directly to the API query args:
                            *language*.

        :returns:   Dict of lending types using ID codes as keys.
        """
        func_params = {
            "response_key": "id",
            "rest_url": "lendingtype",
            "search_key": "value",
            }
        return self._get_indicator_data(func_params, 
            lending_codes, search=search, search_full=search_full, 
            **kwargs)

    def get_regions(self, region_codes=None, search=None, search_full=False, 
            **kwargs):
        """ Get wider region names and codes. 

        :param region_codes:    List of 3-letter codes. If None, queries all 
                                (~26).

        :param search:  Regexp string to filter results. By default, this only
                        searches the main name of the entity, eg. a country
                        name. If *search_full* is True, all fields are searched.

        :param kwargs:      These map directly to the API query args:
                            *language*.
                        
        :returns:   Dict of regions, using ID codes as keys.
        """
        func_params = {
            "response_key": "code",
            "rest_url": "region",
            "search_key": "name",
            }
        return self._get_indicator_data(func_params, 
            region_codes, search=search, search_full=search_full, 
            **kwargs)

    def get_topics(self, topic_codes=None, search=None,
            search_full=False, **kwargs):
        """ Get Indicators topics. All indicators are mapped 
        to a topic, eg. Health, Private Sector. You can use the topic id as a
        filtering arg to ``get_indicators``. 

        :param topic_codes: List of topic IDs. If None, queries all (~20).

        :param search:  Regexp string to filter results. By default, this only
                        searches the main name of the entity, eg. a country
                        name. If *search_full* is True, all fields are searched.

        :param kwargs:      These map directly to the API query args:
                            *language*.

        :returns:   Dict of topics usings ID numbers as keys.
        """
        func_params = {
            "response_key": "id",
            "rest_url": "topic",
            "search_key": "value",
            }
        return self._get_indicator_data(func_params, 
            topic_codes, search=search, search_full=search_full, 
            **kwargs)

    def get_sources(self, source_codes=None, search=None,
            search_full=False, **kwargs):
        """ Get source info for the Indicators data .You can use the source id
        as a filtering arg to ``get_indicators``. (At time of
        writing, the API only returns source names, not the descriptions and
        URLs visible in the official documentation). 

        :param source_codes:    List of source IDs. If None, queries all (~27).

        :param search:  Regexp string to filter results. By default, this only
                        searches the main name of the entity, eg. a country
                        name. If *search_full* is True, all fields are searched.

        :param kwargs:      These map directly to the API query args:
                            *language*.

        :returns:   Dict of sources using ID numbers as keys.
        """
        func_params = {
            "response_key": "id",
            "rest_url": "source",
            "search_key": "name",
            }
        return self._get_indicator_data(func_params, 
            source_codes, search=search, search_full=search_full, 
            **kwargs)

    def print_codes(self, results):
        """ Print formatted list of API IDs and their corresponding values.
        
        :param results:     A dictionary that was returned by one of the ``get``
                            functions.

        :param search:  Regexp string to filter results. By default, this only
                        searches the main name of the entity, eg. a country
                        name. If *search_full* is True, all fields are searched.
        """
        # Natural sort the result keys for nicer print order
        def try_int(text):
            return int(text) if text.isdigit() else text
        def natural_keys(item):
            key = item[0]
            return [try_int(s) for s in re.split("(\d+)", key)]

        for k, v in sorted(results.items(), key=natural_keys):
            # Value will either be a dict or string
            if hasattr(v, "get"):
                main_value = v.get("name", v.get("value", v))
            else:
                main_value = v
            print u"{:30} {}".format(k, main_value)


    def search_results(self, regexp, results, key=None):
        """ For a given dict of ``get_`` results, filter out all keys that do
        not match the given regexp in either the key or the value. The search
        is *not case sensitive*.

        :param regexp:      The regexp string, passed to ``re.search``.

        :param results:     A dictionary of ``get_`` results.

        :param key:         A second-level KEY in your dict, eg. 
                            {foo: {KEY: val}}. If given, will only search
                            the value corresponding to the key.

        :returns:       The input dictionary, with non-matching keys removed.
        """
        compiled_re = re.compile(regexp, flags=re.IGNORECASE)
        search_matches = {}
        if key:
            for k, v in results.items():
                row_string = u"{0} {1}".format(k, v[key])
                if compiled_re.search(row_string):
                    search_matches[k] = v
        else:
            for k, v in results.items():
                row_string = u"{0} {1}".format(k, v)
                if compiled_re.search(row_string):
                    search_matches[k] = v
        return search_matches

    # ========== PRIVATE METHODS ==========

    def _generate_indicators_url(self, rest_url, **kwargs):
        """ Adds API root and query string options to an otherwise complete 
        endpoint, eg. "incomeLevel?", or "lendingType?key=val".
        """
        kwargs = {k.lower(): v for k, v in kwargs.items()}
        assert not (kwargs.has_key("topic") and kwargs.has_key("source"))

        # Fix any API options that shouldn't be accessible via wbpy.
        fixed_options = {"format": "json", "per_page": "10000"}
        banned_options = ["page"]
        kwargs.update(fixed_options) 
        for k in banned_options:
            if k in kwargs.keys():
                del(kwargs[k])

        # If no dates given, use most recent value
        if all(key not in kwargs.keys() for key in ["mrv", "date"]):
            kwargs["mrv"] = 1

        # Some options are part of the url structure.
        options = []
        if "source" in kwargs.keys():
            rest_url = "".join(["source/", str(kwargs["source"]), "/", 
                                rest_url])
            del(kwargs["source"])
        if "topic" in kwargs.keys():
            rest_url = "".join(["topic/", str(kwargs["topic"]), "/", 
                                rest_url])
            del(kwargs["topic"])
        # Prepend language last, as it should be at front of url.
        if "language" in kwargs.keys(): 
            rest_url = "{}/".format(kwargs["language"]) + rest_url
            del(kwargs["language"])

        # Other options can be passed to the query string,
        # with numbers / lists converted to the right format for the url.
        for k, v in kwargs.items():
            if isinstance(v, numbers.Number):
                v = str(v)
            if not isinstance(v, basestring): 
                v = ";".join([str(x) for x in v]) 
            options.append(u"{0}={1}".format(k, v))

        query_string = "&".join(options)
        new_url = "".join([self.base_url, rest_url, query_string])
        return new_url

    def _get_api_response_as_json(self, url):
        """ Returns JSON content from Indicators URL. Concatenates the returned
        list if request requires multiple-page responses.
        """
        web_page = self.fetch(url)
        json_data = json.loads(web_page)
        header = json_data[0]
        content = json_data[1]
        current_page = header["page"]
        if current_page < header["pages"]:
            next_page = url + "&page={0}".format(current_page + 1)
            content += self._get_api_response_as_json(next_page)
        return content

    def _get_indicator_data(self, func_params, api_ids, search=None,
            search_full=False, **kwargs):
        """ 
        :param func_params:     Dict of variables to build this function...
        :rest_url:              The base endpoint url, eg. topic, region.
        :response_key:          The value of this key in the JSON response is
                                used as the top-level identifying key in the 
                                result dictionary.
        :search_key:            If search_full==False, this will be the only
                                key searched - the main name of the entity.


        :param api_ids:         API codes for the indicator, eg. if calling a 
                                topic might be [1, 2, 5].

        :param rest_url:        The access point, eg. 'indicators', 
                                'lendingType'.

        :returns:       Dict with keys that are the given response_key for the
                        API response.
        """
        # Make the URL and call the JSON data.
        if api_ids:
            rest_string = ";".join([str(x) for x in api_ids])
            url = "{0}/{1}?".format(func_params["rest_url"], rest_string)
        else:
            url = "{0}?".format(func_params["rest_url"])
        url = self._generate_indicators_url(url, **kwargs)
        world_bank_response = self._get_api_response_as_json(url)

        # Use the 'response_key' value as the top-level key for the dictionary.
        filtered_data = {}
        for row in world_bank_response:
            filtered_data[row[func_params["response_key"]]] = row
            
            # No point in keeping the key duplicated in the values, so delete
            # it
            del(row[func_params["response_key"]])

        if search:
            # Either search everything, or just the main "name" value of the
            # entity.
            if search_full:
                filtered_data = self.search_results(search, filtered_data)
            else:
                filtered_data = self.search_results(search, filtered_data,
                    func_params["search_key"])
        return filtered_data


class Climate(object):
    def __init__(self, fetch=_fetch):
        """ A connection to the World Bank Climate API. 

        You can override the default tempfile cache by passing a ``fetch`` 
        function, which fetches a url and returns a string. ``self.fetch`` can
        also be set after instantiation.
        """
        self.fetch = fetch
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
                ukmo_hadgem1="UKMO HadGEM3",
                ensemble="x Percentile values of all models together",
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

    def get_precip_modelled(self, data_type, locations, gcm=None,
        sres=None, ensemble_percentiles=None):
        """ Get precipitation data derived from global circulation models. 

        :param data_type:   Single type ID. See ``self.definitions['type']``.

        :param locations:   Get data for list of ISO country codes and World 
                            Bank basin IDs.

        :param gcm:         List of GCMs. If None, gets all except `ensemble`. 
                            See ``self.definitions['gcm']``.

        :param sres:        Scenario ID - either `a2` or `b1`. If None, gets 
                            both scenarios.

        :param ensemble_percentiles:    If `ensemble` is given in the GCMs, you 
                            can limit the percentile value of models. List, 
                            possible percentiles are `10`, `50`, `90`. 
                            If None, gets all.

        :returns:   Data and metadata dicts. Data dict keys are:
                    `gcm` > `location` > `(year, sres)` > `values`.
        """
        return self._get_modelled(var="pr", data_type=data_type,
                locations=locations, gcm=gcm, sres=sres,
                ensemble_percentiles=ensemble_percentiles)

    def get_temp_modelled(self, data_type, locations, gcm=None,
        sres=None, ensemble_percentiles=None):
        """ Get modelled temperature data. ``See get_precip_modelled()``. """
        return self._get_modelled(var="tas", data_type=data_type,
                locations=locations, gcm=gcm, sres=sres,
                ensemble_percentiles=ensemble_percentiles)

    def get_derived_stat(self, stat, data_type, locations, sres=None, 
            ensemble_percentiles=None):
        """ Get precipitation or temperature statistic derived from `ensemble`
        data - ie. from all GCMs. 

        :param stat:          Single stat ID. See ``self.definitions['stat']``.

        :param data_type:     Single type ID. See ``self.definitions['type']``.

        :param locations:     Get data for list of ISO country codes and World 
                              Bank basin IDs.

        :param sres:        Scenario ID - either `a2` or `b1`. If None, gets 
                            both scenarios.

        :param ensemble_percentiles:    If `ensemble` is given in the GCMs, you 
                            can limit the percentile value of models. List, 
                            possible percentiles are `10`, `50`, `90`. 
                            If None, gets all.

        :returns:   Data and metadata dicts. Data dict keys are:
                    `gcm` > `location` > `(year, sres)` > values.
        """
        return self._get_modelled(var=stat, data_type=data_type,
                locations=locations, sres=sres, 
                ensemble_percentiles=ensemble_percentiles, gcm=["ensemble"])

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
        return results, metadata

    def _get_modelled(self, var, data_type, locations, gcm=None,
        sres=None, ensemble_percentiles=None):
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
            metadata["gcm"] = self.definitions["gcm"].copy()
            del(metadata["gcm"]["ensemble"])
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

        # Ensemble and other modelled calls split into different methods, 
        # as have different url and response structures, and it messy having
        # having one function with lots of clauses etc.
        results = {}
        metadata["dates"] = {}
        if gcm and "ensemble" in gcm:
            results, dates = self._get_modelled_ensemble(var=var, 
                         data_type=data_type, locations=locations, 
                         sres=sres, ensemble_percentiles=ensemble_percentiles)
            for fr, to in dates:
                metadata["dates"][fr] = to
        try:
            more_gcms_given = len(gcm) > 1    
        except TypeError:
            pass
        if gcm == None or more_gcms_given:
            gcm_results, dates = self._get_modelled_gcm(var=var, 
                                 data_type=data_type, locations=locations, 
                                 sres=sres, gcm=gcm)
            for fr, to in dates:
                metadata["dates"][fr] = to
            results.update(gcm_results) # Dicts won't have same top-level keys
        return results, metadata

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
            ensemble_percentiles=None):
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
                gcm_key = ("ensemble", data["percentile"])
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

        # Filter unwanted
        if ensemble_percentiles:
            res_keys = results.keys()
            for k in res_keys:
                if str(k[1]) not in [str(x) for x in ensemble_percentiles]:
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
