import os
import logging
import urllib2
import time
import md5
import tempfile
import re
import numbers
try: 
    import simplejson as json
except ImportError: 
    import json 

logger = logging.getLogger(__name__)

BASE_URL = "http://api.worldbank.org/"

def _fetch(url):
    """ Temp file cache, keeps pages for a day. """
    one_day_old = 60*60*24
    cache_dir = os.path.join(tempfile.gettempdir(), 'wbpy')
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
    fp = os.fdopen(fd, 'w')
    fp.write(web_page)
    fp.close()
    os.rename(tempname, cache_path)
    logger.debug("%s saved to cache." % url)
    return web_page

class Indicators(object):
    def __init__(self, cache=_fetch):
        """ A connection to the World Bank Indicators API.

        self.cache can point to your own fetch(url) function, which takes a url 
        and returns a web page as a string.
        """
        self.fetch = cache

    # ========== PUBLIC METHODS =========

    def get_country_indicators(self, indicator_codes, country_codes=None, 
            **kwargs):
        """ Get indicator metrics for countries.

        :param indicator_codes:     Required list of metric codes.
        :param country_codes:       List of countries to get indicator data for. 
                                    If None, queries all countries.
        :param match:               See ``match_data``.
        :param kwargs:              Language, date, mrv, gapfill, frequency.
        
        :returns:   Two dicts. The first contains the data, with nested keys: 
                    `Indicator code > ISO 2-digit country code > Date > Value`. 
                    The second dict contains the names/values for the 
                    indicator and country codes.
        """
        # Generate urls and concatenate multiple calls into one list.
        response_data = []
        if country_codes:
            country_string = ";".join(country_codes)
        else:
            country_string = "all"
        for indicator_string in indicator_codes:
            url = "countries/{0}/indicators/{1}?".format(country_string, 
                    indicator_string)
            url = self._generate_indicators_url(url, **kwargs)
            response_data += self._get_api_response_as_json(url)

        # Arrange JSON data to be more accessible.
        results = {}
        info = dict(indicators={}, countries={})
        for dataset in response_data:
            country_id = dataset['country']['id']
            indicator_id = dataset['indicator']['id']
            date = dataset['date']
            if indicator_id not in results:
                results[indicator_id] = {}
            if country_id not in results[indicator_id]:
                results[indicator_id][country_id] = {}
            if date not in results[indicator_id][country_id]:
                results[indicator_id][country_id][date] = dataset['value']

            if indicator_id not in info['indicators']:
                info['indicators'][indicator_id] = dict(
                        value=dataset['indicator']['value'])
            if country_id not in info['countries']:
                info['countries'][country_id] = dict(
                        value=dataset['country']['value'])
        return results, info

    def get_indicators(self, indicator_codes=None, match=None,
            common_only=False, **kwargs):
        """ Make call to retrieve indicator codes and information.

        :param indicator_codes: List of codes, eg. SP.POP.TOTL for population.
                                If None, queries all (~8000).
        :param common_only:     Many of the indicators do not have wide country 
                                coverage.  If True, filters out those 
                                indicators that do not appear on the 
                                main website (leaving ~1500).
        :param match:           See ``match_data``.
        :param kwargs:          Language, source, topic.
        
        :returns:   Dict of indicators, using ID codes as keys.
        """
        results = self._get_indicator_data(indicator_codes, rest_url="indicator",
                response_key="id", match=match, **kwargs)
        if common_only == True:
            page = self.fetch("http://data.worldbank.org/indicator/all")
            ind_codes = re.compile("(?<=http://data.worldbank.org/indicator/)"\
                                   "[A-Za-z0-9\.]+(?=\">)")
            common_matches = {}
            code_matches = set([code.lower() for code in ind_codes.findall(page)])
            # If value contains an indicator code, include the key in the
            # results.
            for k, v in results.items():
                v_string = "{}".format(v).lower()
                for code_match in code_matches:
                    if code_match in v_string:
                        common_matches[k] = v
                        break
            return common_matches
        else:
            return results

    def get_countries(self, country_codes=None, match=None, **kwargs):
        """ Get info on countries, eg. ISO codes,
        longitude/latitude, capital city, income level, etc.

        :param country_code:    List of 2 or 3 letter ISO codes. If None, 
                                queries all.
        :param match:           See ``match_data``.
        :param kwargs:          Language, incomeLevel, lendingType, region.

        :returns:   Dict of countries using 2-letter ISO codes as keys.
        """
        return self._get_indicator_data(country_codes, rest_url="country",
                match=match, response_key="iso2Code", **kwargs)

    def get_income_levels(self, income_codes=None, match=None, **kwargs):
        """ Get income categories.

        :param income_codes:    List of 3-letter ID codes. If None, queries all 
                                (~10). 
        :param match:           See ``match_data``.
        :param kwargs:          Language

        :returns:   Dict of income levels using ID codes as keys.
        """
        return self._get_indicator_data(income_codes, rest_url="incomelevel", 
                response_key="id", match=match, **kwargs)

    def get_lending_types(self, lending_codes=None, match=None, **kwargs):
        """ Get lending type categories. 

        :param lending_codes:   List of lending codes. If None, queries all (4).
        :param match:           See ``match_data``.
        :param kwargs:          Language

        :returns:   Dict of lending types using ID codes as keys.
        """
        return self._get_indicator_data(lending_codes, rest_url="lendingtype",
                response_key="id", match=match, **kwargs)

    def get_regions(self, region_codes=None, match=None, **kwargs):
        """ Get wider region names and codes. 

        :param region_codes:    List of 3-letter codes. If None, queries all 
                                (~26).
        :param match:           See ``match_data``.
        :param kwargs:          Language
                        
        :returns:   Dict of regions, using ID codes as keys.
        """
        return self._get_indicator_data(region_codes, rest_url="region", 
                response_key="code", match=match, **kwargs)

    def get_topics(self, topic_codes=None, match=None, **kwargs):
        """ Get Indicators topics. All indicators are mapped 
        to a topic, eg. Health, Private Sector. You can use the topic id as a
        filtering arg to ``get_indicators``. 

        :param topic_codes: List of topic IDs. If None, queries all (~20).
        :param match:       See ``match_data``.
        :param kwargs:      Language

        :returns:   Dict of topics usings ID numbers as keys.
        """
        return self._get_indicator_data(topic_codes, rest_url="topic", 
                response_key="id", match=match, **kwargs)

    def get_sources(self, source_codes=None, match=None, **kwargs):
        """ Get source info for the Indicators data .You can use the source id
        as a filtering arg to ``get_indicators``. (At time of
        writing, the API only returns source names, not the descriptions and
        URLs visible in the official documentation). 

        :param source_codes:    List of source IDs. If None, queries all (~27).
        :param match:           See ``match_data``.
        :param kwargs:          Language

        :returns:   Dict of sources using ID numbers as keys.
        """
        return self._get_indicator_data(source_codes, rest_url="source", 
                response_key="id", match=match, **kwargs)

    def print_codes(self, results, match=None):
        """ Print formatted list of API IDs + values/names for the results of
        any of the ``get`` functions.  (For ``get_country_indicators``, only the
        'info' dict will print properly, the 'data' one will not).

        :param match:   See ``match_data``.
        """
        # There some juggling depending on dict layout, as prefer to keep it
        # to one print function.

        # If this is the 'info' dict from ``get_country_indicators``, process
        # both halves (countries + indicators) separately:
        if results.has_key('countries'):
            self.print_codes(results['countries'])
        if results.has_key('indicators'):
            self.print_codes(results['indicators'])

        if match:
            results = self.match_data(match, results)

        # Natural sort the result keys for nicer print order
        def try_int(text):
            return int(text) if text.isdigit() else text
        def natural_keys(text):
            return [try_int(k) for k in re.split("(\d+)", text)]

        for k in sorted(results.keys(), key=natural_keys):
            v = results[k]
            for value_key in ['value', 'name']: 
                try:
                    print "{:30} {}".format(k, v[value_key])
                except KeyError:
                    pass

    def match_data(self, ss, results):
        """ For a given dict (eg. of ``get`` results), filter out all 
        keys that do not contain the match string in the value.
        (``get`` results mostly include the key as one of the value
        fields, so the key is searched implicitly). 

        :param ss:      The match string. You can pass a `match` param to other 
                        functions as a shorthand for filtering the data through 
                        this method.
        :param results: A dict. 

        :returns:   The input dict, with the non-matching keys filtered out.
        """
        ss = ss.lower()
        search_matches = {}
        for k, v in results.items():
            if ss in  "{}".format(v).lower():
                search_matches[k] = v
        return search_matches

    # ========== PRIVATE METHODS ==========

    def _generate_indicators_url(self, rest_url, **kwargs):
        """ Adds API root and query string options to an otherwise complete 
        endpoint, eg. "incomeLevel?", or "lendingType?key=val".
        """
        kwargs = {k.lower(): v for k, v in kwargs.items()}
        assert not (kwargs.has_key('topic') and kwargs.has_key('source'))

        # Fix any API options that shouldn't be accessible via wbpy.
        fixed_options = {'format': 'json', 'per_page': '10000'}
        banned_options = ['page']
        kwargs.update(fixed_options) 
        for k in banned_options:
            if k in kwargs.keys():
                del(kwargs[k])

        # If no dates given, use most recent value
        if all(key not in kwargs.keys() for key in ['mrv', 'date']):
            kwargs['mrv'] = 1

        # Some options are part of the url structure.
        options = []
        if 'source' in kwargs.keys():
            rest_url = "".join(["source/", str(kwargs["source"]), "/", 
                                rest_url])
            del(kwargs['source'])
        if 'topic' in kwargs.keys():
            rest_url = "".join(["topic/", str(kwargs["topic"]), "/", 
                                rest_url])
            del(kwargs['topic'])
        # Prepend language last, as it should be at front of url.
        if 'language' in kwargs.keys(): 
            rest_url = "{}/".format(kwargs['language']) + rest_url
            del(kwargs['language'])

        # Other options can be passed to the query string,
        # with numbers / lists converted to the right format for the url.
        for k, v in kwargs.items():
            if isinstance(v, numbers.Number):
                v = str(v)
            if not isinstance(v, basestring): 
                v = ";".join([str(x) for x in v]) 
            options.append("{0}={1}".format(k, v))

        query_string = '&'.join(options)
        new_url = "".join([BASE_URL, rest_url, query_string])
        return new_url

    def _get_api_response_as_json(self, url):
        """ Returns JSON content from Indicators URL. Concatenates the returned
        list if request requires multiple-page responses.
        """
        web_page = self.fetch(url)
        json_data = json.loads(web_page)
        header = json_data[0]
        content = json_data[1]
        current_page = header['page']
        if current_page < header['pages']:
            next_page = url + "&page={0}".format(current_page + 1)
            content += self._get_api_response_as_json(next_page)
        return content

    def _get_indicator_data(self, api_ids, rest_url, response_key, match=None, **kwargs):
        """ 
        :param api_ids:         API codes for the indicator, eg. if calling a 
                                topic might be [1, 2, 5].
        :param rest_url:        The access point, eg. 'indicators', 
                                'lendingType'.
        :param response_key:    The key in the JSON response that will be 
                                used as the top-level keys in the returned dict.

        :returns:       Dict with keys that are the given response_key for the
                        API response.
        """
        if api_ids:
            rest_string = ";".join([str(x) for x in api_ids])
            url = "{0}/{1}?".format(rest_url, rest_string)
        else:
            url = "{0}?".format(rest_url)
        url = self._generate_indicators_url(url, **kwargs)
        world_bank_response = self._get_api_response_as_json(url)
        tidier_data = {}
        for data in world_bank_response:
            tidier_data[data[response_key]] = data
        if match:
            tidier_data = self.match_data(match, tidier_data)
        return tidier_data
