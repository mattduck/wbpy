wbpy
================================================================================

A Python interface to the World Bank Indicators and Climate APIs.

:Docs:      http://wbpy.readthedocs.org/en/latest
:Source:    http://github.com/mattduck/wbpy 

Why use wbpy?
-------------

The Indicators API lets you access a large number of World Development
Indicators - country data on education, environment, gender, health, poverty, 
technology, etc. 

The Climate API lets you access modelled and historical data for temperature
and precipitation. 

(See http://data.worldbank.org/developers for full API docs.)

Some benefits:

- Simple interface - no need to learn the different REST structures.
- Data comes ready to use, separate from the associated
  metadata, and with all duplicate metadata removed.
- API codes and definitions are accessible and searchable in Python.
- One method call to get the equivalent data of several API calls.
- Built-in cache to prevent excessive calls and improve performance. You can 
  plug in your own ``fetch(url)`` function.

Install
-------

``pip install wbpy``, or download from source.


Indicators API
================================================================================

Basic use
---------

Connect to the Indicators API and get a time series:

.. code-block:: python

    import wbpy
    from pprint import pprint
    
    ind = wbpy.Indicators()
    api_codes = ['SP.POP.TOTL', # Population
                 'EN.URB.LCTY.UR.ZS'] # Population in largest city (% of urban popn)
    country_codes = ['GB', 'FR', 'JP'] # ISO alpha-2 codes
    data, metadata = ind.get_country_indicators(api_codes, country_codes, date="2003:2005")
    
    pprint(data)
    pprint(metadata)

.. parsed-literal::

    {'EN.URB.LCTY.UR.ZS': {'FR': {'2003': '20.0744557566877',
                                  '2004': '19.8430730967831',
                                  '2005': '19.6131454295651'},
                           'GB': {'2003': '17.9028975023227',
                                  '2004': '17.9056138864461',
                                  '2005': '17.8760686758404'},
                           'JP': {'2003': '33.1323182517128',
                                  '2004': '32.7683892783879',
                                  '2005': '32.4254722261792'}},
     'SP.POP.TOTL': {'FR': {'2003': '62242266',
                            '2004': '62701871',
                            '2005': '63175934'},
                     'GB': {'2003': '59566259',
                            '2004': '59867866',
                            '2005': '60224307'},
                     'JP': {'2003': '127718000',
                            '2004': '127761000',
                            '2005': '127773000'}}}

    {'EN.URB.LCTY.UR.ZS': 'Population in the largest city (% of urban population)',
     'SP.POP.TOTL': 'Population, total'}

.. note:: 

    Regarding country codes, wbpy supports ISO 3166 alpha-2 codes. The 
    APIs mostly use alpha-3 codes. Alpha-3 codes may work with some wbpy calls, 
    but this isn't guaranteed. 

Data and metadata are separate, so you should be able to make use of the
numbers without much further arranging. For example, if you use Pandas, 
you can pass the data straight in:

.. code-block:: python

    import pandas as pd
    
    panel = pd.Panel(data)
    print panel
    print panel['SP.POP.TOTL']

.. parsed-literal::

    <class 'pandas.core.panel.Panel'>
    Dimensions: 2 (items) x 3 (major_axis) x 3 (minor_axis)
    Items axis: EN.URB.LCTY.UR.ZS to SP.POP.TOTL
    Major_axis axis: 2003 to 2005
    Minor_axis axis: FR to JP

                FR        GB         JP
    2003  62242266  59566259  127718000
    2004  62701871  59867866  127761000
    2005  63175934  60224307  127773000

You can use ``get_indicators()`` to get a dictionary of indicator codes and 
their descriptions. At default, this returns over 8000 codes, 
many of which
have missing data. Pass ``common_only=True`` to limit results to the ~1500 
indicators listed at http://data.worldbank.org/indicator/all. These seem to
have better data coverage. There are further ways to filter the indicators, eg:

.. code-block:: python

    indicators = ind.get_indicators(
                match="GDP", # 199 indicators match "GDP"
                common_only=True, # 106 of those are listed on the main site
                topic=4, # 4 of those are under the 'Education' topic
                )

Pass the results to ``ind.print_codes()`` to print a clear list of the result's 
API codes:

.. code-block:: python

    ind.print_codes(indicators)

.. parsed-literal::

    SE.XPD.PRIM.PC.ZS       Expenditure per student, primary (% of GDP per capita)
    SE.XPD.SECO.PC.ZS       Expenditure per student, secondary (% of GDP per capita)
    SE.XPD.TERT.PC.ZS       Expenditure per student, tertiary (% of GDP per capita)
    SE.XPD.TOTL.GD.ZS       Public spending on education, total (% of GDP)

You might find ``print_codes()`` to be an easier way to view lists of `code` > 
`name` mappings, as the results can otherwise contain a lot of extra text:

.. code-block:: python

    pprint(indicators['SE.XPD.TERT.PC.ZS'])

.. parsed-literal::

    {'name': 'Expenditure per student, tertiary (% of GDP per capita)',
     'source': {'id': '2', 'value': 'World Development Indicators'},
     'sourceNote': 'Public expenditure per pupil as a % of GDP per capita. Tertiary is the total public expenditure per student in tertiary education as a percentage of GDP per capita. Public expenditure (current and capital) includes government spending on educational institutions (both public and private), education administration as well as subsidies for private entities (students/households and other privates entities).',
     'sourceOrganization': 'UNESCO Institute for Statistics',
     'topics': [{'id': '4', 'value': 'Education '}]}

There are a variety of ``get_()`` methods for different types of data - see 
the Indicators class page for full method documentation.

A `match` string can be passed to all Indicator methods to filter out
non-matching keys / values. You can also call the method directly:
    
.. code-block:: python

    print ind.match_data("public spending", indicators).keys()

.. parsed-literal::

    ['SE.XPD.TOTL.GD.ZS']

API options
-----------

Below are the documented URL options and their accepted data formats. The
method docstrings state which kwargs are applicable to that method.

:language:      ``EN``, ``ES``, ``FR``, ``AR`` or ``ZH``. Non-English languages 
                seem to have less info in the responses.

:date:          String formats - ``2001``, ``2001:2006``, ``2003M01:2004M06``, 
                ``2005Q2:2005Q4``. Replace the years with your own. Not all
                indicators have monthly or quarterly data.

:mrv:           Most recent value, ie. ``mrv=3`` returns the three most recent 
                values for an indicator.

:gapfill:       ``Y`` or ``N``. If using an MRV value, fills missing values 
                with the next available value (I think tracking back as far as 
                the MRV value allows). Defaults to ``N``.

:frequency:     Works with MRV, can specify quarterly (``Q``), monthly (``M``) 
                or yearly (``Y``). Not all indicators have monthly and quarterly 
                data. 

:source:        ID number to filter indicators by data source.

:topic:         ID number to filter indicators by their assigned category. 
                Cannot give both source and topic in the same request.

:incomelevel:   List of 3-letter IDs to filter results by income level category.

:lendingtype:   List of 3-letter IDs to filter results by lending type. 

:region:        List of 3-letter IDs to filter results by region.

If no date or MRV value is given, **MRV defaults to 1**, returning the most recent
value.

Any given kwarg that is not in the above list will be directly added to the query
string.

Climate API
================================================================================

Basic use
---------

To get historical / instrumental data, use either
``get_precip_instrumental()`` or ``get_temp_instrumental()``:

.. code-block:: python

    cl = wbpy.Climate()
    locations = ['AF', 'AU', 1, 100] # ISO codes or basin ID numbers
    interval = 'decade' 
    data, metadata = cl.get_temp_instrumental(locations, interval)
    pprint(data)

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
     u'AF': {1900: 12.6786585,
             1910: 12.673154,
             1920: 12.37222,
             1930: 12.323485,
             1940: 13.011024,
             1950: 12.605792,
             1960: 12.6369915,
             1970: 12.755891,
             1980: 13.170972,
             1990: 13.123372,
             2000: 14.186356},
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

Unlike the Indicators API, the codes required to make calls are not accessible
via the Climate API itself. You can instead access codes and their definitions 
via ``self.definitions``:

.. code-block:: python

    pprint(cl.definitions)

.. parsed-literal::

    {'gcm': {'bccr_bcm2_0': 'BCM 2.0',
             'cccma_cgcm3_1': 'CGCM 3.1 (T47)',
             'cnrm_cm3': 'CNRM CM3',
             'csiro_mk3_5': 'CSIRO Mark 3.5',
             'ensemble': 'x Percentile values of all models together,  for both A2 and B1 scenarios',
             'gfdl_cm2_0': 'GFDL CM2.0',
             'gfdl_cm2_1': 'GFDL CM2.1',
             'ingv_echam4': 'ECHAM 4.6',
             'inmcm3_0': 'INMCM3.0',
             'ipsl_cm4': 'IPSL-CM4',
             'microc3_2_medres': 'MIROC 3.2 (medres)',
             'miub_echo_g': 'ECHO-G',
             'mpi_echam5': 'ECHAM5/MPI-OM',
             'mri_cgcm2_3_2a': 'MRI-CGCM2.3.2',
             'ukmo_hadcm3': 'UKMO HadCM3',
             'ukmo_hadgem1': 'UKMO HadGEM3'},
     'sres': {'a2': 'A2 Scenario', 'b1': 'B1 Scenario'},
     'stat': {'ppt_days': 'Number of days with precipitation > 0.2mm',
              'ppt_days10': 'Number of days with precipitation > 10mm',
              'ppt_days2': 'Number of days with precipitation > 2mm',
              'ppt_days90th': "Number of days with precipitation > the control period's 90th percentile",
              'ppt_dryspell': 'Average number of days between precipitation events',
              'ppt_means': 'Average daily precipitation',
              'tmax_days10th': "Number of days with max temperature below the control period's 10th percentile (cool days)",
              'tmax_days90th': "Number of days with max temperature above the control period's 90th percentile (hot days)",
              'tmax_means': 'Average daily maximum temperature, Celsius',
              'tmin_days0': 'Number of days with min temperature below 0 degrees Celsius',
              'tmin_days10th': "Number of days with min temperature below the control period's 10th percentile (cold nights)",
              'tmin_days90th': "Number of days with min temperature above the control period's 90th percentile (warm nights)",
              'tmin_means': 'Average daily minimum temperature, Celsius'},
     'type': {'aanom': 'Average annual change (anomaly)',
              'aavg': 'Annual average',
              'manom': 'Average monthly change (anomaly)',
              'mavg': 'Monthly average'}}

For full explanation of the data and associated models etc, see
http://data.worldbank.org/developers/climate-data-api.

To get modelled data, use either ``get_precip_modelled()`` or
``get_temp_modelled()``:

.. code-block:: python

    locations = ['GB']
    data_type = 'aavg' # Annual average
    gcm = ['gfdl_cm2_0', 'gfdl_cm2_1'] # Global circulation models
    data, metadata = cl.get_precip_modelled(data_type, locations, gcm=gcm)
    pprint(data)

.. parsed-literal::

    {'gfdl_cm2_0': {u'GB': {1920: 985.60836181616,
                            1940: 1034.72117187508,
                            1960: 1049.8378686535202,
                            1980: 1019.8750146478401,
                            (2020, 'a2'): 1040.8490454109601,
                            (2020, 'b1'): 1072.33289062412,
                            (2040, 'a2'): 1055.0401171875603,
                            (2040, 'b1'): 1052.9096655271999,
                            (2060, 'a2'): 1056.10354492244,
                            (2060, 'b1'): 1116.2015747062399,
                            (2080, 'a2'): 1069.82929443312,
                            (2080, 'b1'): 1085.8730541992}},
     'gfdl_cm2_1': {u'GB': {1920: 1089.28617675788,
                            1940: 1055.7995996091602,
                            1960: 1094.85248046824,
                            1980: 1084.5603759764,
                            (2020, 'a2'): 1080.23193359412,
                            (2020, 'b1'): 1109.94289550812,
                            (2040, 'a2'): 1101.4879687508,
                            (2040, 'b1'): 1110.5482983407198,
                            (2060, 'a2'): 1122.1576318364,
                            (2060, 'b1'): 1118.4096606452003,
                            (2080, 'a2'): 1095.0342724610005,
                            (2080, 'b1'): 1105.12718994264}}}

Each Climate API modelled call requires some specific, irregular start date and 
end date pairs in the URL. 
There aren't many of them, so wbpy always returns all 
possible dates. The metadata dictionary shows the start and 
end dates for your results:

.. code-block:: python

    pprint(metadata)

.. parsed-literal::

    {'dates': {1920: 1939,
               1940: 1959,
               1960: 1979,
               1980: 1999,
               2020: 2039,
               2040: 2059,
               2060: 2079,
               2080: 2099},
     'gcm': {'gfdl_cm2_0': 'GFDL CM2.0', 'gfdl_cm2_1': 'GFDL CM2.1'},
     'sres': {'a2': 'A2 Scenario', 'b1': 'B1 Scenario'},
     'stat': 'Precipitation (rainfall and assumed water equvialent) in millimeters',
     'type': 'Annual average'}

You can also get statistics that are derived from the modelled data. The GCM
value for these is fixed as 'ensemble':

.. code-block:: python

    stat = 'ppt_days10' # No. of days with precipitation > 10mm
    data_type = 'aanom' # Average annual change (anomaly)
    locations = ['GH', 'BA']
    data, metadata = cl.get_derived_stat(stat, data_type, locations)
    pprint(data)
    pprint(metadata)

.. parsed-literal::

    {('ensemble', 10): {u'BA': {(2046, 'a2'): -0.12631953259313333,
                                (2046, 'b1'): -0.063055552668361,
                                (2081, 'a2'): -0.25375003119299994,
                                (2081, 'b1'): -0.07243058531694001},
                        u'GH': {(2046, 'a2'): -0.8916320229564166,
                                (2046, 'b1'): -0.6130904344223334,
                                (2081, 'a2'): -1.6921528677137498,
                                (2081, 'b1'): -0.6577777924648583}},
     ('ensemble', 50): {u'BA': {(2046, 'a2'): 0.04583339889845,
                                (2046, 'b1'): 0.07222219804926668,
                                (2081, 'a2'): 0.007291714350416663,
                                (2081, 'b1'): 0.12187497814505},
                        u'GH': {(2046, 'a2'): 0.07343747183520166,
                                (2046, 'b1'): 0.07743045994240001,
                                (2081, 'a2'): 0.022743043295696666,
                                (2081, 'b1'): 0.133333288133125}},
     ('ensemble', 90): {u'BA': {(2046, 'a2'): 0.12159721056623334,
                                (2046, 'b1'): 0.1736110846200667,
                                (2081, 'a2'): 0.157777780046,
                                (2081, 'b1'): 0.2120138779281667},
                        u'GH': {(2046, 'a2'): 0.29857638726641667,
                                (2046, 'b1'): 0.24673612291600003,
                                (2081, 'a2'): 0.3521874782940833,
                                (2081, 'b1'): 0.47364581500483327}}}
    {'dates': {2046: 2065, 2081: 2100},
     'gcm': {'ensemble': 'x Percentile values of all models together,  for both A2 and B1 scenarios'},
     'sres': {'a2': 'A2 Scenario', 'b1': 'B1 Scenario'},
     'stat': 'Number of days with precipitation > 10mm',
     'type': 'Average annual change (anomaly)'}

.. note::

    The basin ID numbers (1-468) are mapped out in a PDF file which is linked at
    http://data.worldbank.org/developers/climate-data-api. There is no easy way 
    to show a text definition of the IDs, because there isn't one (and I'm not
    aware of these IDs being standardised or defined elsewhere).

.. note::

    The KML file calls for country and basin IDs are not currently supported. 
    If there is interest, this can be added.

.. note::

    There are no immediate plans to add the World Bank Finance and Project APIs.
    If there is interest, they can be added.

See the Climate class page for full method documentation.

Cache
================================================================================

The default cache function uses system temporary files. You can specify your own
when instantiating an ``Indicators`` or ``Climate`` object:

.. code-block:: python

    ind = wbpy.Indicators(cache=my_cache_func)
    cl = wbpy.Climate(cache=my_cache_func)

You can also point ``ind.fetch`` or ``cl.fetch`` to your function. The given 
function must take a url, and return the web page as a string.
