
wbpy
====


A Python interface to the World Bank Indicators and Climate APIs.

-  `Readthedocs <http://wbpy.readthedocs.org/en/latest>`_
-  `Github source <https://github.com/mattduck/wbpy>`_

-  `World Bank API docs <http://data.worldbank.org/developers>`_

The Indicators API lets you access a large number of world development
indicators - country data on education, environment, gender, health,
population, poverty, technology, etc.

The Climate API lets you access modelled and historical data for
temperature and precipitation.

``This file was built from an IPython Notebook. Download README.ipynb from Github to poke around.``

Why use wbpy?
-------------


-  Removes duplicate API response metadata.
-  Separates useful numbers from metadata, so the data is more or less
   ready to use.
-  Works with both ISO 1366 alpha-2 and alpha-3 country codes (the API
   mostly just supports alpha-3).
-  Single method calls to do the equivalent of multiple API requests
   (eg. multiple countries and indicators in one call).


Install
-------


``pip install wbpy``, or build from source.

Indicators API
==============


Basic use
---------


Here's a small case where we already know the API codes that we want:

.. code:: python

    import wbpy
    
    api = wbpy.Indicators()
    iso_country_codes = ["GB", "FR", "JP"]
    api_codes = ["SP.POP.TOTL"] # The code for population
    
    results = api.get_country_indicators(api_codes, iso_country_codes)
The ``get_country_indicators`` method removes the duplicate metadata
from the JSON response, and returns a namedtuple with separate data and
metadata:

.. code:: python

    results.data



.. parsed-literal::

    {'SP.POP.TOTL': {'FR': {'2012': '65696689'},
      'GB': {'2012': '63227526'},
      'JP': {'2012': '127561489'}}}



.. code:: python

    results.indicators



.. parsed-literal::

    {'SP.POP.TOTL': 'Population, total'}



.. code:: python

    results.countries



.. parsed-literal::

    {'FR': 'France', 'GB': 'United Kingdom', 'JP': 'Japan'}



``wbpy`` primarily supports ISO 1366 alpha-2 codes. Results are returned
using alpha-2 codes, and you can query the API using alpha-2 codes. You
can also query the API using alpha-3 codes (which is mostly what the API
uses).

There are a couple of 2-digit and 3-digit codes that the API uses that
are not part of the ISO 1366 standard. These are stored on the
``nonstandard_codes`` attribute:

.. code:: python

    api.nonstandard_codes



.. parsed-literal::

    {'JG': {'3-digit': 'CHI', 'name': 'Channel Islands'},
     'KV': {'3-digit': 'KSV', 'name': 'Kosovo'}}



Searching the responses
-----------------------


We don't always know what indicators we want to use, so we can search:

.. code:: python

    population_indicators = api.get_indicators(search="population")
    len(population_indicators)



.. parsed-literal::

    1179



Ah. That's not a very manageable number. The API returns over 8000
indicator codes, and lots of them have "population" in the title.
Luckily, most of those indicators don't really have much data, so we can
forget about them. You can browse the indicators with the best data
coverage at http://data.worldbank.org/indicator, and you can pass
``common_only=True`` to throw away all indicators that aren't included
on that page:

.. code:: python

    population_indicators = api.get_indicators(search="population", common_only=True)
    print "There are now only %d indicators to browse!" % len(population_indicators)


.. parsed-literal::

    There are now only 61 indicators to browse!


We don't want to print that many results in the documentation, so let's
filter some more. The API query string parameters are directly mapped to
kwargs for each method. For the ``get_indicators`` method, this means we
can filter by topic or source:

.. code:: python

    # "8" is the ID for the "health" topic. 
    health_indicators = api.get_indicators(search="population", common_only=True, topic=8)
    print "We've narrowed it down to %d indicators!" % len(health_indicators)

.. parsed-literal::

    We've narrowed it down to 18 indicators!


Each indicator has a variety of metadata:

.. code:: python

    health_indicators.items()[0]



.. parsed-literal::

    ('SN.ITK.DEFC.ZS',
     {'name': 'Prevalence of undernourishment (% of population)',
      'source': {'id': '2', 'value': 'World Development Indicators'},
      'sourceNote': 'Population below minimum level of dietary energy consumption (also referred to as prevalence of undernourishment) shows the percentage of the population whose food intake is insufficient to meet dietary energy requirements continuously. Data showing as 2.5 signifies a prevalence of undernourishment below 2.5%.',
      'sourceOrganization': 'Food and Agriculture Organization, The State of Food Insecurity in the World (http://www.fao.org/publications/sofi/food-security-indicators/en/).',
      'topics': [{'id': '8', 'value': 'Health '}]})



That data might be useful, but it's not very friendly if you just want
to grab some API codes. If that's what you want, you can pass the
results to the ``print_codes`` method:

.. code:: python

    api.print_codes(health_indicators)

.. parsed-literal::

    SH.CON.1524.FE.ZS              Condom use, population ages 15-24, female (% of females ages 15-24)
    SH.CON.1524.MA.ZS              Condom use, population ages 15-24, male (% of males ages 15-24)
    SH.DYN.AIDS.FE.ZS              Women's share of population ages 15+ living with HIV (%)
    SH.DYN.AIDS.ZS                 Prevalence of HIV, total (% of population ages 15-49)
    SH.MLR.NETS.ZS                 Use of insecticide-treated bed nets (% of under-5 population)
    SH.STA.ACSN                    Improved sanitation facilities (% of population with access)
    SH.STA.ACSN.RU                 Improved sanitation facilities, rural (% of rural population with access)
    SH.STA.ACSN.UR                 Improved sanitation facilities, urban (% of urban population with access)
    SN.ITK.DEFC.ZS                 Prevalence of undernourishment (% of population)
    SP.POP.0014.TO.ZS              Population ages 0-14 (% of total)
    SP.POP.65UP.TO.ZS              Population ages 65 and above (% of total)
    SP.POP.1564.TO.ZS              Population ages 15-64 (% of total)
    SP.POP.DPND                    Age dependency ratio (% of working-age population)
    SP.POP.DPND.OL                 Age dependency ratio, old (% of working-age population)
    SP.POP.DPND.YG                 Age dependency ratio, young (% of working-age population)
    SP.POP.GROW                    Population growth (annual %)
    SP.POP.TOTL                    Population, total
    SP.POP.TOTL.FE.ZS              Population, female (% of total)


There are ``get_`` functions matching all API endpoints (countries,
regions, sources, etc.), and the ``search`` parameter and
``print_codes`` method can be used on any of them. For example:

.. code:: python

    countries = api.get_countries(search="united")
    api.print_codes(countries)

.. parsed-literal::

    AE                             United Arab Emirates
    GB                             United Kingdom
    US                             United States


API options
-----------


All endpoint query string parameters are directly mapped to method
kwargs. Different kwargs are available for each ``get_`` method
(documented in the method's docstring).

-  **language:** ``EN``, ``ES``, ``FR``, ``AR`` or ``ZH``. Non-English
   languages seem to have less info in the responses.

-  **date:** String formats - ``2001``, ``2001:2006``,
   ``2003M01:2004M06``, ``2005Q2:2005Q4``. Replace the years with your
   own. Not all indicators have monthly or quarterly data.

-  **mrv:** Most recent value, ie. ``mrv=3`` returns the three most
   recent values for an indicator.

-  **gapfill:** ``Y`` or ``N``. If using an MRV value, fills missing
   values with the next available value (I think tracking back as far as
   the MRV value allows). Defaults to ``N``.

-  **frequency:** Works with MRV, can specify quarterly (``Q``), monthly
   (``M``) or yearly (``Y``). Not all indicators have monthly and
   quarterly data.

-  **source:** ID number to filter indicators by data source.

-  **topic:** ID number to filter indicators by their assigned category.
   Cannot give both source and topic in the same request.

-  **incomelevel:** List of 3-letter IDs to filter results by income
   level category.

-  **lendingtype:** List of 3-letter IDs to filter results by lending
   type.

-  **region:** List of 3-letter IDs to filter results by region.

An example:

.. code:: python

    from pprint import pprint
    results = api.get_country_indicators(["SP.POP.TOTL", "SP.POP.GROW"], ["BR"], date="2004:2008")
    pprint(results.data)
    pprint(results.indicators)
    pprint(results.countries)

.. parsed-literal::

    {'SP.POP.GROW': {'BR': {'2004': '1.23432890464563',
                            '2005': '1.1520346395149',
                            '2006': '1.0644160915339',
                            '2007': '0.985200701687338',
                            '2008': '0.926546454089764'}},
     'SP.POP.TOTL': {'BR': {'2004': '184010283',
                            '2005': '186142403',
                            '2006': '188134315',
                            '2007': '189996976',
                            '2008': '191765567'}}}
    {'SP.POP.GROW': 'Population growth (annual %)',
     'SP.POP.TOTL': 'Population, total'}
    {'BR': 'Brazil'}


If no date or MRV value is given, **MRV defaults to 1**, returning the
most recent value.

Any given kwarg that is not in the above list will be directly added to
the query string, eg. ``foo="bar"`` might add ``&foo=bar`` to the URL.

Other features
--------------


If you're not sure what to search for, just leave out the ``search``
parameter. By default, the ``get_`` methods return all API results:

.. code:: python

    all_regions = api.get_regions()
    all_sources = api.get_sources()
    
    print "There are %d regions and %d sources." % (len(all_regions), len(all_sources))

.. parsed-literal::

    There are 32 regions and 28 sources.


The ``search`` parameter actually just calls a ``search_results``
method. You can use it directly:

.. code:: python

    pprint(api.search_results("debt", all_sources))

.. parsed-literal::

    {'20': {'description': '', 'name': 'Public Sector Debt', 'url': ''},
     '22': {'description': '',
            'name': 'Quarterly External Debt Statistics (QEDS) - Special Data Dissemination Standard (SDDS)',
            'url': ''},
     '23': {'description': '',
            'name': 'Quarterly External Debt Statistics (QEDS) - General Data Dissemination System (GDDS)',
            'url': ''},
     '6': {'description': '', 'name': 'International Debt Statistics', 'url': ''}}


By default, the ``search`` parameter only searches the title of an
entity (eg. a country name, or source title). If you want to search all
fields, set the ``search_full`` flag to ``True``:

.. code:: python

    narrow_matches = api.get_topics(search="poverty")
    wide_matches = api.get_topics(search="poverty", search_full=True)
    
    print "%d topic(s) match(es) 'poverty' in the title field, and %d topics match 'poverty' in all fields." % (len(narrow_matches), len(wide_matches))

.. parsed-literal::

    1 topic(s) match(es) 'poverty' in the title field, and 7 topics match 'poverty' in all fields.


Climate API
===========


The Climate API has multiple endpoints for useful data, but the URL
structures are more complex than the Indicators API. ``wbpy`` tries to
separate these into some simpler methods and arguments.

Historical data
---------------


The ``get_temp_instrumental`` and ``get_precip_instrumental`` methods
are used to get historical temperature and precipitation data. They
return a namedtuple with "data" and "metadata" attributes.

(For full explanation of the data and associated models, see
http://data.worldbank.org/developers/climate-data-api).

.. code:: python

    c_api = wbpy.Climate()
    
    # For now, we'll assume that we already know what our location codes
    # should be.
    iso_codes_and_basin_codes = ["AU", 1, 100]
    
    # An interval can be set to "year", "month" or "decade". It defaults
    # to year. 
    interval = "decade"
    
    historical_temp = c_api.get_temp_instrumental(iso_codes_and_basin_codes, interval=interval)
    historical_precip = c_api.get_precip_instrumental(iso_codes_and_basin_codes, interval=interval)
.. code:: python

    pprint(historical_temp.data)

.. parsed-literal::

    {1: {1960: 5.975941,
         1970: 6.1606956,
         1980: 6.3607564,
         1990: 6.600332,
         2000: 7.3054743},
     100: {1960: 25.733957,
           1970: 25.674582,
           1980: 26.041042,
           1990: 25.721668,
           2000: 26.217083},
     u'AU': {1900: 21.078014,
             1910: 21.296726,
             1920: 21.158426,
             1930: 21.245909,
             1940: 21.04456,
             1950: 21.136906,
             1960: 21.263151,
             1970: 21.306032,
             1980: 21.633171,
             1990: 21.727072,
             2000: 21.741446}}


.. code:: python

    pprint(historical_temp.metadata)

.. parsed-literal::

    {'interval': 'decade', 'stat': 'Temperature, in degrees Celsisus'}


Modelled data
-------------


``get_temp_modelled`` and ``get_precip_modelled`` return data derived
from Global Climate Models: Unlike the Indicators API, the codes
required to make these calls are not accessible via the Climate API
itself. Instead, these have been taken from the official documentation
and stored in ``api.definitions``.

``data_type`` specifies the kind of aggregate data to be returned.

.. code:: python

    for item in c_api.definitions["type"].items():
        pprint(item)

.. parsed-literal::

    ('manom', 'Average monthly change (anomaly).')
    ('aavg', 'Annual average')
    ('aanom', 'Average annual change (anomaly).')
    ('mavg', 'Monthly average')


``gcm`` specifies the Global Climate Model to use. If none given, it
returns data for every model except for the "ensemble" values.

.. code:: python

    for item in c_api.definitions["gcm"].items():
        pprint(item)

.. parsed-literal::

    ('miub_echo_g', 'ECHO-G')
    ('ukmo_hadcm3', 'UKMO HadCM3')
    ('bccr_bcm2_0', 'BCM 2.0')
    ('ukmo_hadgem1', 'UKMO HadGEM3')
    ('ensemble_90', '90th percentile values of all models together')
    ('cccma_cgcm3_1', 'CGCM 3.1 (T47)')
    ('gfdl_cm2_1', 'GFDL CM2.1')
    ('gfdl_cm2_0', 'GFDL CM2.0')
    ('csiro_mk3_5', 'CSIRO Mark 3.5')
    ('ensemble_50', '50th percentile values of all models together')
    ('cnrm_cm3', 'CNRM CM3')
    ('ensemble_10', '10th percentile values of all models together')
    ('ipsl_cm4', 'IPSL-CM4')
    ('mri_cgcm2_3_2a', 'MRI-CGCM2.3.2')
    ('microc3_2_medres', 'MIROC 3.2 (medres)')
    ('inmcm3_0', 'INMCM3.0')
    ('ingv_echam4', 'ECHAM 4.6')
    ('mpi_echam5', 'ECHAM5/MPI-OM')
    ('ensemble', 'All percentile values of all models together')


``sres`` specifies Special Report on Emissions Scenarios. If none given,
it tries to returns data for both scenarios.

.. code:: python

    for item in c_api.definitions["sres"].items():
        pprint(item)

.. parsed-literal::

    ('a2', 'A2 Scenario')
    ('b1', 'B1 Scenario')


These values can be passed to the ``get_temp_modelled`` and
``get_precip_modelled`` methods:

.. code:: python

    data_type = "aavg"
    gcm = ["mpi_echam5", "ingv_echam4"] 
    sres = "a2"
    
    modelled_temp = c_api.get_temp_modelled(data_type, iso_codes_and_basin_codes, gcm=gcm, sres=sres)
    modelled_precip = c_api.get_precip_modelled(data_type, iso_codes_and_basin_codes, gcm=gcm, sres=sres)
.. code:: python

    pprint(modelled_temp.data["mpi_echam5"])

.. parsed-literal::

    {1: {1920: 6.776967433902464,
         1940: 7.032464640030124,
         1960: 6.590775445597703,
         1980: 6.894800653519572,
         (2020, 'a2'): 7.857167629217703,
         (2040, 'a2'): 8.868584437088419,
         (2060, 'a2'): 10.72215624676723,
         (2080, 'a2'): 11.944098668382976},
     100: {1920: 28.0732727051,
           1940: 28.4932556152,
           1960: 28.073638916,
           1980: 28.8731079102,
           (2020, 'a2'): 28.893157959,
           (2040, 'a2'): 29.4224853516,
           (2060, 'a2'): 31.1801452637,
           (2080, 'a2'): 32.4705200195},
     u'AU': {1920: 21.91360799153809,
             1940: 22.11201510959036,
             1960: 21.992819959853882,
             1980: 22.632078993055373,
             (2020, 'a2'): 23.34301744249338,
             (2040, 'a2'): 23.795883517798035,
             (2060, 'a2'): 25.028675808381863,
             (2080, 'a2'): 26.40219306098183}}


The dates are actually pairs of specific start / end years. They're
saved in the metadata:

.. code:: python

    pprint(modelled_temp.metadata)

.. parsed-literal::

    {'dates': {1920: 1939,
               1940: 1959,
               1960: 1979,
               1980: 1999,
               2020: 2039,
               2040: 2059,
               2060: 2079,
               2080: 2099},
     'gcm': {'ingv_echam4': 'ECHAM 4.6', 'mpi_echam5': 'ECHAM5/MPI-OM'},
     'sres': 'A2 Scenario',
     'stat': 'Temperature, in degrees Celsisus',
     'type': 'Annual average'}


Derived statistics
------------------


You can also request statistics which are derived specifically from the
"ensemble" ``gcm`` values. These are accessed using
``get_derived_stat``. You must specify a ``stat`` argument, which
denotes the type of statistic:

.. code:: python

    for item in c_api.definitions["stat"].items():
        pprint(item)

.. parsed-literal::

    ('tmax_days90th',
     "Number of days with max temperature above the control period's 90th percentile (hot days)")
    ('tmin_means', 'Average daily minimum temperature, Celsius')
    ('ppt_dryspell', 'Average number of days between precipitation events')
    ('tmax_means', 'Average daily maximum temperature, Celsius')
    ('ppt_days2', 'Number of days with precipitation > 2mm')
    ('ppt_days90th',
     "Number of days with precipitation > the control period's 90th percentile")
    ('tmin_days90th',
     "Number of days with min temperature above the control period's 90th percentile (warm nights)")
    ('tmin_days0', 'Number of days with min temperature below 0 degrees Celsius')
    ('ppt_days', 'Number of days with precipitation > 0.2mm')
    ('tmin_days10th',
     "Number of days with min temperature below the control period's 10th percentile (cold nights)")
    ('tmax_days10th',
     "Number of days with max temperature below the control period's 10th percentile (cool days)")
    ('ppt_days10', 'Number of days with precipitation > 10mm')
    ('ppt_means', 'Average daily precipitation')


.. code:: python

    # For derived statistics, an ensemble GCM must be used. The arg defaults to
    # ["ensemble"], which gets the 10th, 50th and 90th percentile values. 
    # You can request specific percentiles in the same way as the ``gcm`` argument
    # above.
    ensemble_gcm = ["ensemble_50", "ensemble_90"]
    stat = "tmax_means"
    
    statistic = c_api.get_derived_stat(stat, data_type, iso_codes_and_basin_codes)
    pprint(statistic.data["ensemble_90"])

.. parsed-literal::

    {1: {1961: 12.082352292754566,
         (2046, 'a2'): 14.628635992275896,
         (2046, 'b1'): 13.925387968290336,
         (2081, 'a2'): 16.850792013253706,
         (2081, 'b1'): 14.787311040802052},
     100: {1961: 33.6869010925,
           (2046, 'a2'): 35.5453910828,
           (2046, 'b1'): 35.2058067322,
           (2081, 'a2'): 37.9925308228,
           (2081, 'b1'): 36.3306732178},
     u'AU': {1961: 28.86428188323858,
             (2046, 'a2'): 30.75957291496786,
             (2046, 'b1'): 30.45445651584376,
             (2081, 'a2'): 32.62275881449282,
             (2081, 'b1'): 31.010441873332315}}


Locations
---------


Like the Indicators API, locations can be ISO-1366 alpha-2 or alpha-3
country codes. They can also be IDs corresponding to regional river
basins. A basin map can be found in the official Climate API
documentation. The API includes a KML interface that returns basin
definitions, but this is currently not supported by ``wbpy``.

Cache
=====


The default cache function uses system temporary files. You can specify
your own. The function has to take a url, and return the corresponding
web page as a string.

.. code:: python

    def my_cache_func(url):
        # Basic function that doesn't do any caching
        import urllib2
        return urllib2.urlopen(url).read()
    
    # Either pass it in on instantiation...
    ind_api = wbpy.Indicators(fetch=my_cache_func)
    
    # ...or point api.fetch to it. 
    climate_api = wbpy.Climate()
    climate_api.fetch = my_cache_func