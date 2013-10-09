# -*- coding: utf-8 -*-
import numbers
import re
import datetime
import pprint
try:
    import simplejson as json
except ImportError:
    import json

import utils


class IndicatorDataset(object):
    """ A single World Bank Indicator dataset. Includes the raw JSON response,
    various metadata, and methods to convert the data into useful objects.
    """

    def __init__(self, json_resp, url=None, date_of_call=None):
        self.api_url = url
        self.api_call_date = date_of_call
        self.api_response = json_resp

        # The country codes and names
        self.countries = {}
        for country_data in self.api_response[1]:
            country_id = country_data["country"]["id"]
            country_val = country_data["country"]["value"]
            if country_id not in self.countries:
                self.countries[country_id] = country_val

        self.indicator_code = self.api_response[1][0]["indicator"]["id"]
        self.indicator_name = self.api_response[1][0]["indicator"]["value"]

        # For some use cases, it's nice to have direct access to all the
        # `get_indicator()` metadata (eg. the sources, full description). 
        # It won't always be wanted, so it's requested lazily. 
        self._metadata_response = None

    def __repr__(self):
        s = "<%s.%s(%r, %r) with id: %r>"
        return s % (
            self.__class__.__module__,
            self.__class__.__name__,
            self.indicator_code,
            self.indicator_name,
            id(self),
            )

    def __str__(self):
        return pprint.pformat(self.as_dict())

    def dates(self, use_datetime=False):
        dates = []
        for country_data in self.as_dict().values():
            for date in country_data.keys():
                if date not in dates:
                    dates.append(date)

        if use_datetime:
            dates = [utils.worldbank_date_to_datetime(d) for d in dates]

        return sorted(dates)

    def _get_metadata_response(self):
        api = IndicatorAPI()
        indicators = api.get_indicators([self.indicator_code])
        self._metadata_response = indicators[self.indicator_code]

    @property
    def indicator_source(self):
        if not self._metadata_response:
            self._get_metadata_response()
        return self._metadata_response["source"]

    @property
    def indicator_source_note(self):
        if not self._metadata_response:
            self._get_metadata_response()
        return self._metadata_response["sourceNote"]

    @property
    def indicator_source_org(self):
        if not self._metadata_response:
            self._get_metadata_response()
        return self._metadata_response["sourceOrganization"]

    @property
    def indicator_topics(self):
        if not self._metadata_response:
            self._get_metadata_response()
        return self._metadata_response["topics"]


    def as_dict(self, use_datetime=False):
        clean_dict = {}
        response_data = self.api_response[1]
        for row in response_data:
            country_id = row["country"]["id"]
            date = row["date"]
            if use_datetime:
                date = utils.worldbank_date_to_datetime(date)

            if country_id not in clean_dict:
                clean_dict[country_id] = {}
            if date not in clean_dict[country_id]:
                # Sometimes values are missing
                if row["value"]:
                    clean_dict[country_id][date] = float(row["value"])
                else:
                    clean_dict[country_id][date] = None

        return clean_dict


class IndicatorAPI(object):
    """ Request data from the World Bank Indicators API """

    BASE_URL = "http://api.worldbank.org/"

    # The API uses some non-ISO 2-digit and 3-digit codes. Make them available.
    NON_STANDARD_REGIONS = utils.NON_STANDARD_REGIONS

    def __init__(self, fetch=None):
        """ You can override the default tempfile cache by passing a function,
        ``fetch``, which requests a URL and returns a string.
        """
        self.fetch = fetch if fetch else utils.fetch


    # ========================================================================
    # PUBLIC METHODS
    # ========================================================================

    def get_country_indicators(self, indicator_codes, country_codes=None, 
            **kwargs):
        """ Get specific indicator data for countries.

        :param indicator_codes:     Required list of API indicator codes.

        :param country_codes:   List of countries to get data for. 
                                If None, queries all countries.

        :param kwargs:      These map directly to the API query args:
                            *Language*, 
                            *date*, 
                            *mrv*, 
                            *gapfill*, 
                            *frequency*.

        :returns:   Namedtuple with *data*, *countries* and *indicators* attrs.
        """
        datasets = []
        if country_codes:
            country_codes = [utils.convert_country_code(c, "alpha3") for c in
                country_codes]
            country_string = ";".join(country_codes)
        else:
            country_string = "all"
        for indicator_string in indicator_codes:
            url = "countries/{0}/indicators/{1}?".format(country_string, 
                    indicator_string)
            url = self._generate_indicators_url(url, **kwargs)
            call_date = datetime.datetime.now()
            json_resp = json.loads(self.fetch(url))
            self._raise_if_response_contains_error(json_resp, url)

            datasets.append(IndicatorDataset(json_resp, url, call_date))
        return datasets

    def get_indicators(self, indicator_codes=None, search=None,
            search_full=False, common_only=False, **kwargs):
        """ Get metadata on specific World Bank indicators.

        :param indicator_codes: List of codes, eg. SP.POP.TOTL for population.
                                If None, queries all (~8000).

        :param common_only:     Many of the indicators do not have wide country 
                                coverage. If True, filters out those 
                                indicators that do not appear on the 
                                main World Bank website (leaving ~1500).

        :param search:  Regexp string to filter results. By default, this only
                        searches the main name of the entity. If *search_full*
                        is True, all fields are searched.

        :param kwargs:      These map directly to the API query args:
                            *language*,
                            *source*,
                            *topic*.
        
        :returns:   Dictionary of indicators with API IDs as keys.
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
                        searches the main name of the entity. If *search_full*
                        is True, all fields are searched.

        :param kwargs:      These map directly to the API query args:
                            *language*,
                            *incomeLevel*,
                            *lendingType*,
                            *region*.

        :returns:   Dictionary of countries using 2-letter ISO codes as keys.
        """
        func_params = {
            "response_key": "iso2Code",
            "rest_url": "country",
            "search_key": "name",
            }
        if country_codes:
            country_codes = [utils.convert_country_code(c, "alpha3") for c in
                country_codes]

        return self._get_indicator_data(func_params, 
            country_codes, search=search, search_full=search_full, 
            **kwargs) 


    def get_income_levels(self, income_codes=None, search=None,
            search_full=False, **kwargs):
        """ Get income categories.

        :param income_codes:    List of 3-letter ID codes. If None, queries all 
                                (~10). 

        :param search:  Regexp string to filter results. By default, this only
                        searches the main name of the entity. If *search_full*
                        is True, all fields are searched.

        :param kwargs:      These map directly to the API query args:
                            *language*.

        :returns:   Dictionary of income levels using ID codes as keys.
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
                        searches the main name of the entity. If *search_full*
                        is True, all fields are searched.

        :param kwargs:      These map directly to the API query args:
                            *language*.

        :returns:   Dictionary of lending types using ID codes as keys.
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
                        searches the main name of the entity. If *search_full*
                        is True, all fields are searched.

        :param kwargs:      These map directly to the API query args:
                            *language*.
                        
        :returns:   Dictionary of regions, using ID codes as keys.
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
                        searches the main name of the entity. If *search_full*
                        is True, all fields are searched.

        :param kwargs:      These map directly to the API query args:
                            *language*.

        :returns:   Dictionary of topics usings ID numbers as keys.
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
                        searches the main name of the entity. If *search_full*
                        is True, all fields are searched.

        :param kwargs:      These map directly to the API query args:
                            *language*.

        :returns:   Dictionary of sources using ID numbers as keys.
        """
        func_params = {
            "response_key": "id",
            "rest_url": "source",
            "search_key": "name",
            }
        return self._get_indicator_data(func_params, 
            source_codes, search=search, search_full=search_full, 
            **kwargs)


    def print_codes(self, results, search=None, search_full=None):
        """ Print formatted list of API IDs and their corresponding values.
        
        :param results:     A dictionary that was returned by one of the ``get``
                            functions.

        :param search:  Regexp string to filter results. By default, this only
                        searches the main name of the entity. If *search_full*
                        is True, all fields are searched.
        """
        # Natural sort the result keys for nicer print order
        def try_int(text):
            return int(text) if text.isdigit() else text
        def natural_keys(item):
            key = item[0]
            return [try_int(s) for s in re.split("(\d+)", key)]

        if search:
            # Either search everything, or just the main "name" value of the
            # entity.
            if search_full:
                results = self.search_results(search, results)
            else:
                results = self.search_results(search, results,
                    func_params["search_key"])

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


    # ========================================================================
    # PRIVATE METHODS
    # ========================================================================

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
        if "source" in kwargs:
            rest_url = "".join(["source/", str(kwargs["source"]), "/", 
                                rest_url])
            del(kwargs["source"])
        if "topic" in kwargs:
            rest_url = "".join(["topic/", str(kwargs["topic"]), "/", 
                                rest_url])
            del(kwargs["topic"])
        # Prepend language last, as it should be at front of url.
        if "language" in kwargs:
            rest_url = "{}/".format(kwargs["language"]) + rest_url
            del(kwargs["language"])

        if "gapfill" in kwargs:
            if kwargs["gapfill"] is True:
                kwargs["gapfill"] = "Y"

        # Other options can be passed to the query string,
        # with numbers / lists converted to the right format for the url.
        for k, v in kwargs.items():
            if isinstance(v, numbers.Number):
                v = str(v)
            if not isinstance(v, basestring): 
                v = ";".join([str(x) for x in v]) 
            options.append(u"{0}={1}".format(k, v))

        query_string = "&".join(options)
        new_url = "".join([self.BASE_URL, rest_url, query_string])
        return new_url


    def _get_api_response_as_json(self, url):
        """ Returns JSON content from Indicators URL. Concatenates the returned
        list if request requires multiple-page responses.
        """
        web_page = self.fetch(url)
        json_resp = json.loads(web_page)
        self._raise_if_response_contains_error(json_resp, url)
        header = json_resp[0]
        content = json_resp[1]
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

        :returns:       Dictionary with keys that are the given response_key
                        for the API response.
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

    def _raise_if_response_contains_error(self, json_resp, url):
        if len(json_resp) == 1:
            str_resp = str(json_resp).lower()
            if ("message" in str_resp) or ("pages: 0" in str_resp):
                raise ValueError, utils.EXC_MSG % (url, json_resp)

