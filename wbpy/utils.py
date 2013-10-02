# -*- coding: utf-8 -*-
import os
import tempfile
import urllib2
import time
import logging
import datetime
import hashlib

import pycountry # For ISO 1366 code conversions

logger = logging.getLogger(__name__)

EXC_MSG = "The URL %s returned a bad response: %s"


def fetch(url):
    """ Cache function, take a url and return the response. """
    # Use system tempfile for cache path. 
    cache_dir = os.path.join(tempfile.gettempdir(), "wbpy")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        logger.debug("Created cache directory " + cache_dir)

    logger.debug("Fetching url: %s ...", url)
    url_hash = hashlib.md5(url).hexdigest()

    # If the cache file is < one day old, return cache, else get new response.
    cache_path = os.path.join(cache_dir, url_hash)
    if os.path.exists(cache_path):
        seconds_in_day = 86400
        if int(time.time()) - os.path.getmtime(cache_path) < seconds_in_day:
            logger.debug("Retrieving web response from cache.")
            return open(cache_path, "rb").read()

    logger.debug("URL not found in cache. Getting web response...")
    response = urllib2.urlopen(url).read()
    fd, tempname = tempfile.mkstemp()
    fp = os.fdopen(fd, "w")
    fp.write(response)
    fp.close()
    os.rename(tempname, cache_path)
    logger.debug("New url saved to cache: %s" % url)
    return response


# The Indicators API (but not Climate API) uses a couple of non-ISO 2-digit
# and 3-digit codes for regions. Make these accessible so they can be
# converted, and users can see them.
NON_STANDARD_CODES = [
    {"alpha2": "KV", "alpha3": "KSV", "name": "Kosovo"}, 
    {"alpha2": "JG", "alpha3": "CHI", "name": "Channel Islands"}, 
    ]


def convert_country_code(code, return_alpha):
    """ Convert an ISO 1366 alpha-2 or alpha-3 code into either alpha-2 or
    alpha-3. 

    :param code:
        The code to convert. If it isn't a valid ISO code, it gets returned as
        given.
    :param return_alpha:
        `2` or `3`, the returned format.

    """
    try:
        # Try to get code from ISO 1366 standard
        code = code.upper()
        if len(code) == 2:
            country = pycountry.countries.get(alpha2=code)
        elif len(code) == 3:
            country = pycountry.countries.get(alpha3=code)
        else:
            raise ValueError, "`code` is not a valid alpha-2 or alpha-3 code"
        return getattr(country, return_alpha)

    except (KeyError, ValueError):
        # Try the world bank non-standard codes
        for row in NON_STANDARD_CODES:
            if code in row:
                return row[return_alpha]

        # No match found
        return code

def worldbank_date_to_datetime(date):
    """ Convert given world bank date string to datetime.date object. """
    if "Q" in date:
        year, quarter = date.split("Q")
        return datetime.date(int(year), (int(quarter) * 3) - 2, 1)
    
    if "M" in date:
        year, month = date.split("M")
        return datetime.date(int(year), int(month), 1)

    return datetime.date(int(date), 1, 1)
