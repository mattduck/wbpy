# -*- coding: utf-8 -*-
import os
import tempfile
from six.moves.urllib import request
import time
import logging
import datetime
import hashlib
import json
import sys

import pycountry  # For ISO 1366 code conversions

logger = logging.getLogger(__name__)

EXC_MSG = "The URL %s returned a bad response: %s"

# The Indicators API (but not Climate API) uses a few non-ISO 2-digit and
# 3-digit codes, for either regions or groups of regions. Make them accessible
# so that they can be converted, and users can see them.
#
# The file contains the results of IndicatorAPI.get_countries(), with all the
# ISO countries excluded.
path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
    "non_ISO_region_codes.json")
NON_STANDARD_REGIONS = json.loads(open(path).read())


def fetch(url, check_cache=True, cache_response=True):
    """Return response from a URL, and cache results for one day."""
    # Use system tempfile for cache path.
    cache_dir = os.path.join(tempfile.gettempdir(), "wbpy")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        logger.debug("Created cache directory " + cache_dir)

    logger.debug("Fetching url: %s ...", url)

    # Python3 hashlib requires bytestring
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    cache_path = os.path.join(cache_dir, url_hash)

    # If the cache file is < one day old, return cache, else get new response.
    if check_cache:
        if os.path.exists(cache_path):
            logger.debug("URL found in cache...")
            secs_in_day = 86400
            if int(time.time()) - os.path.getmtime(cache_path) < secs_in_day:
                logger.debug("Retrieving response from cache.")
                response = open(cache_path, "rb").read().decode("utf-8")
                return response
            else:
                logger.debug("Cache file has expired, removing...")
                os.remove(cache_path)
        else:
            logger.debug("URL not found in cache....")

    logger.debug("Getting web response...")
    response = request.urlopen(url).read()

    # py3 returns bytestring
    if sys.version_info >= (3,):
        response = response.decode("utf-8")

    logger.debug("Response received.")
    if cache_response:
        logger.debug("Caching response... ")
        _cache_response(response, url, cache_path)
    return response


def _cache_response(response, url, cache_path):
    fd, tempname = tempfile.mkstemp()
    f = os.fdopen(fd, "w")
    f.write(response)
    f.close()
    os.rename(tempname, cache_path)
    logger.debug("New url saved to cache: %s" % url)


def convert_country_code(code, return_alpha):
    """Convert ISO code into either alpha-2 or alpha-3.

    :param code:
        The code to convert. If it isn't a valid ISO code, it gets returned as
        given.

    :param return_alpha:
        "alpha2" or "alpha3".

    """
    try:
        # Try to get code from ISO 1366 standard
        code = code.upper()
        country = None
        if len(code) == 2:
            try:
                country = pycountry.countries.get(alpha_2=code)
            except KeyError:
                country = pycountry.countries.get(alpha2=code)
        elif len(code) == 3:
            try:
                country = pycountry.countries.get(alpha_3=code)
            except KeyError:
                country = pycountry.countries.get(alpha3=code)
        else:
            raise ValueError("`code` is not a valid alpha-2 or alpha-3 code")
        if country is None:
            # Ugly way to get to the except branch below. Pycountry will raise
            # KeyError automatically in versions < 18.12.8
            raise KeyError
        try:
            return getattr(country, return_alpha)
        except AttributeError:
            if "_" not in return_alpha:
                return_alpha = return_alpha.replace("2", "_2").replace("3", "_3")
                return getattr(country, return_alpha)

    except (KeyError, ValueError):
        # Try the world bank non-standard codes
        if "2" in return_alpha and code in NON_STANDARD_REGIONS:
            return NON_STANDARD_REGIONS[code]["id"]

        elif "3" in return_alpha:
            for alpha2, vals in NON_STANDARD_REGIONS.items():
                if vals["id"] == code:
                    return alpha2

        # No match found
        return code


def worldbank_date_to_datetime(date):
    """Convert given world bank date string to datetime.date object."""
    if "Q" in date:
        year, quarter = date.split("Q")
        return datetime.date(int(year), (int(quarter) * 3) - 2, 1)

    if "M" in date:
        year, month = date.split("M")
        return datetime.date(int(year), int(month), 1)

    return datetime.date(int(date), 1, 1)
