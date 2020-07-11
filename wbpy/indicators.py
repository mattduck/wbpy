# -*- coding: utf-8 -*-
import re
import datetime
import pprint
from six.moves.urllib.parse import urlencode
try:
    import simplejson as json
except ImportError:
    import json

from . import utils


class IndicatorDataset(object):

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
        self._indicator_response = None

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
        """Return list of dates used in the dataset.

        :param use_datetime:
            If True, return dates as datetime.date() objects, rather than
            strings.

        """
        dates = []
        for country_data in self.as_dict().values():
            for date in country_data.keys():
                if date not in dates:
                    dates.append(date)

        if use_datetime:
            dates = [utils.worldbank_date_to_datetime(d) for d in dates]

        return sorted(dates)

    @property
    def _indicator(self):
        """Lazy loading of the dataset's indicator metadata from the API."""
        if not self._indicator_response:
            api = IndicatorAPI()
            indicators = api.get_indicators([self.indicator_code])
            self._indicator_response = indicators[self.indicator_code]
        return self._indicator_response

    @property
    def indicator_source(self):
        return self._indicator["source"]

    @property
    def indicator_source_note(self):
        return self._indicator["sourceNote"]

    @property
    def indicator_source_org(self):
        return self._indicator["sourceOrganization"]

    @property
    def indicator_topics(self):
        return self._indicator["topics"]

    def as_dict(self, use_datetime=False):
        """Return dictionary of the dataset's data.

        Keys are: data[country_code][date]

        :param use_datetime:
            Use datetime.date() object as the date key, rather than string.

        """
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

    """Request data from the World Bank Indicators API.

    You can override the default tempfile cache by passing a function
    ``fetch``, which requests a URL and returns the response as a string.
    """

    BASE_URL = "http://api.worldbank.org/v2/"

    # The API uses some non-ISO 2-digit and 3-digit codes. Make them available.
    NON_STANDARD_REGIONS = utils.NON_STANDARD_REGIONS

    def __init__(self, fetch=None):
        self.fetch = fetch if fetch else utils.fetch

    def get_dataset(self, indicator, country_codes=None,
            **kwargs):
        """Request a dataset from the API.

        :param indicator:
            The API indicator code, eg. SP.POP.TOTL for total population.

        :param country_codes:
            List of ISO 1366 alpha-2 or alpha-3 country codes. If None, returns
            data for all countries.

        :param kwargs:
            The following map directly to the API query args:
            ``language``
            ``date``
            ``mrv``
            ``gapfill``
            ``frequency``

        :returns:
            IndicatorDataset instance containing the dataset and metadata.

        """
        if country_codes:
            country_codes = [utils.convert_country_code(c, "alpha3") for c in
                country_codes]
            country_string = ";".join(country_codes)
        else:
            country_string = "all"

        url = "countries/{0}/indicators/{1}?".format(country_string,
                indicator)
        url = self._generate_indicators_url(url, dataset_params=True, **kwargs)
        call_date = datetime.datetime.now().date()
        json_resp = json.loads(self.fetch(url))
        self._raise_if_bad_response(json_resp, url)
        return IndicatorDataset(json_resp, url, call_date)

    def get_indicators(self, indicator_codes=None, search=None,
            search_full=False, common_only=False, **kwargs):
        """Request metadata on specific World Bank indicators.

        :param indicator_codes:
            A list of codes to get metadata for, eg. ["SP.POP.GROW"]. If None,
            all indicators are returned (~8000)

        :param common_only:
            Many of the indicators do not have wide data coverage. If True,
            filter out the ~6500 indicators that do not appear on the main
            World Bank website (http://data.worldbank.org/indicators/all),

        :param search:
            Regexp string to filter out non-matching results.
            By default, this searches the main name of the entity. If
            ``search_full`` is assigned True, it will search all fields for the
            entity.

        :param kwargs:
            The following map directly to the API query args:
            ``language``
            ``source``
            ``topic``

        :returns:
            Dictionary of indicators and their metadata, with their IDs as
            keys.

        """
        func_params = {
            "response_key": "id",
            "rest_url": "indicator",
            "search_key": "name",
            }
        results = self._get_indicator_data(func_params,
            indicator_codes, search=search, search_full=search_full,
            **kwargs)

        if common_only:
            # Compile a list of codes that are on the main website (and have
            # better data coverage), and filter out any results that cannot be
            # found on the site.
            page = self.fetch("https://data.worldbank.org/indicator?tab=all")
            ind_codes = re.compile(r"(?<=/indicator/)[^?]+")
            common_matches = {}
            code_matches = set([code.lower() for code in
                                ind_codes.findall(page)])
            assert code_matches, "That common_matches search algorithm isn't fatally broken."

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
        """Request country metadata.

        eg. ISO code, coordinates, capital, income level, etc.

        :param country_codes:
            List of alpha-2 or alpha-3 codes. If None, queries all countries.

        :param search:
            Regexp string to filter out non-matching results.
            By default, this searches the main name of the entity. If
            ``search_full`` is assigned True, it will search all fields for the
            entity.

        :param kwargs:
            The following map directly to the API query args:
            ``language``
            ``incomeLevel``
            ``lendingType``
            ``region``

        :returns:
            Dictionary of metadata with alpha-2 codes as keys.

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
        """Request income categories.

        :param income_codes:
            List of 3-letter ID codes. If None, queries all (~10).

        :param search:
            Regexp string to filter out non-matching results.
            By default, this searches the main name of the entity. If
            ``search_full`` is assigned True, it will search all fields for the
            entity.

        :param kwargs:
            The following map directly to the API query args:
            ``language``

        :returns:
            Dictionary of income levels using ID codes as keys.

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
        """Request lending type categories.

        :param lending_codes:
            List of lending codes. If None, queries all (4).

        :param search:
            Regexp string to filter out non-matching results.
            By default, this searches the main name of the entity. If
            ``search_full`` is assigned True, it will search all fields for the
            entity.

        :param kwargs:
            The following map directly to the API query args:
            ``language``


        :returns:
            Dictionary of lending types using ID codes as keys.

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
        """Request region names and codes.

        :param region_codes:
            List of 3-letter codes. If None, queries all (~26).

        :param search:
            Regexp string to filter out non-matching results.
            By default, this searches the main name of the entity. If
            ``search_full`` is assigned True, it will search all fields for the
            entity.

        :param kwargs:
            The following map directly to the API query args:
            ``language``

        :returns:
            Dictionary of regions, using ID codes as keys.

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
        """Request API topics.

        All indicators are mapped to a topic, eg. Health, Private Sector. You
        can use the topic ID as a kwarg to ``get_indicators()``.

        :param topic_codes:
            List of topic IDs. If None, queries all (~20).

        :param search:
            Regexp string to filter out non-matching results.
            By default, this searches the main name of the entity. If
            ``search_full`` is assigned True, it will search all fields for the
            entity.

        :param kwargs:
            The following map directly to the API query args:
            ``language``

        :returns:
            Dictionary of topics usings ID numbers as keys.

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
        """Request API source info.

        :param source_codes:
            List of source IDs. If None, queries all (~27).

        :param search:
            Regexp string to filter out non-matching results.
            By default, this searches the main name of the entity. If
            ``search_full`` is assigned True, it will search all fields for the
            entity.

        :param kwargs:
            The following map directly to the API query args:
            ``language``

        :returns:
            Dictionary of sources using ID numbers as keys.

        """
        func_params = {
            "response_key": "id",
            "rest_url": "source",
            "search_key": "name",
            }
        return self._get_indicator_data(func_params,
            source_codes, search=search, search_full=search_full,
            **kwargs)

    def print_codes(self, results, search=None, search_key=None):
        """Print formatted list of API IDs and their corresponding values.

        :param search:
            Regexp string to filter out non-matching results.
            By default, this searches the main name of the entity.

        :param search_key:
            A second-level KEY in your dict, eg. ``{foo: {KEY: val}}``.
            If given, will only search the value corresponding to the key.
            Only used if ``search`` is given.

        :param results:
            A dictionary that was returned by one of the ``get`` functions.

        """
        # Natural sort the result keys for nicer print order
        def try_int(text):
            return int(text) if text.isdigit() else text

        def natural_keys(item):
            key = item[0]
            return [try_int(s) for s in re.split(r"(\d+)", key)]

        if search:
            # Either search everything, or just the main "name" value of the
            # entity.
            if search_key:
                results = self.search_results(search, results)
            else:
                results = self.search_results(search, results, search_key)

        for k, v in sorted(results.items(), key=natural_keys):
            # Value will either be a dict or string
            if hasattr(v, "get"):
                main_value = v.get("name", v.get("value", v))
            else:
                main_value = v
            print(u"{0:30} {1}".format(k, main_value))

    def search_results(self, regexp, results, key=None):
        """For a given dict of ``get_`` results, filter out all keys that do
        not match the given regexp in either the key or the value. The search
        is not case sensitive.

        :param regexp:
            The regexp string, passed to ``re.search``.

        :param results:
            A dictionary of ``get_foo()`` results.

        :param key:
            A second-level KEY in your dict, eg. ``{foo: {KEY: val}}``.
            If given, will only search the value corresponding to the key.

        :returns:
            The input dictionary, with non-matching keys removed.

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


    def _generate_indicators_url(
        self,
        rest_url,
        dataset_params=False,
        **kwargs):
        """Add API root and query string options to an otherwise complete
        endpoint.

        :param rest_url:
            eg. "incomeLevel?", or "lendingType?key=val".

        :param dataset_params:
            Add query values that are only relevant to the get_dataset() call.

        """
        kwargs = dict([(k.lower(), v) for k, v in kwargs.items()])
        assert not ("topic" in kwargs and "source" in kwargs)

        # Fix any API options that shouldn't be accessible via wbpy.
        fixed_options = {"format": "json", "per_page": "10000"}
        banned_options = ["page"]
        kwargs.update(fixed_options)
        for k in banned_options:
            if k in kwargs.keys():
                del(kwargs[k])

        # The dataset call has some extra query params
        if dataset_params:
            # If no dates given, use most recent value
            if all(key not in kwargs.keys() for key in ["mrv", "date"]):
                kwargs["mrv"] = 1
            if kwargs.get("gapfill") is True:
                kwargs["gapfill"] = "Y"

        # Some options are part of the url structure.
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
            rest_url = "{0}/".format(kwargs["language"]) + rest_url
            del(kwargs["language"])

        # The kwarg dict doesn't guarantee order, and we want the same args to
        # always generate the same URL (for caching purposes), so need to
        # convert to a sorted list before passing to urlencode().
        sorted_kwargs = sorted([(k, v) for k, v in kwargs.items()])
        query_string = urlencode(sorted_kwargs)

        new_url = "".join([self.BASE_URL, rest_url, query_string])
        print(new_url)
        return new_url

    def _get_api_response_as_json(self, url):
        """Return JSON content from Indicators URL.

        Concatenates the returned list if request requires multiple-page
        responses.

        """
        web_page = self.fetch(url)
        json_resp = json.loads(web_page)
        self._raise_if_bad_response(json_resp, url)
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
        :param func_params:
            Dict of variables to build this function:
            rest_url - the REST part of the url, eg. topic, region.
            response_key - the val of this key in the JSON response is used as
                the top-level, identifying key in the returned dictionary.
            search_key - if search_full is False, this will be the only key
                searched - the main name of the entity.

        :param api_ids:
            API codes for the indicator, eg. if calling a topic might be [1, 2,
            5].

        :param rest_url:
            The access point, eg. 'indicators', 'lendingType'.

        :returns:
            Dictionary with keys that are the given response_key for the API
            response.
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

    def _raise_if_bad_response(self, json_resp, url):
        if json_resp[0].get("pages") == 0 or json_resp[0].get("message"):
            raise ValueError(utils.EXC_MSG % (url, json_resp))
