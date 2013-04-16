wbpy
====

Python wrapper for the various World Bank APIs. 

Full docs:  http://wbpy.readthedocs.org/en/latest
Source:     http://github.com/mattduck/wbpy 

Why use wbpy?
=============

- Single point of access to multiple APIs - Indicators, Climate Data,
  (`pending: Finances, Projects`).
- Easy access to the data, with all the usual API duplicate info removed
  (see below).
- Built-in search and pretty-printing for API codes.
- Built-in cache to prevent multiple calls and improve performance.
  You can plug in your own ``fetch(url)`` function.
- All API options are handled as kwargs, whether they're set in the 
  query string or the url structure. Allowed kwargs are
  documented in all methods.

Indicators
==========

Basic use
---------

Connect to the Indicators API and get a time series::

    >>> import wbpy
    >>> wb = wbpy.Indicators() 
    >>> data, info = wb.get_country_indicators(
    >>>             ['SP.POP.TOTL'],            # API code for total population.
    >>>             country_codes=['GB', 'FR', 'JP'],               # ISO codes.
    >>>             date="2000:2003") 

    >>> print data                   # Time series for all requested indicators.
    {'SP.POP.TOTL': {'FR': {'2000': '60910922',
                            '2001': '61355563',
                            '2002': '61803045',
                            '2003': '62242266'},
                     'GB': {'2000': '58892514',
                            '2001': '59107960',
                            '2002': '59325809',
                            '2003': '59566259'},
                     'JP': {'2000': '126870000',
                            '2001': '127149000',
                            '2002': '127445000',
                            '2003': '127718000'}}}

    >>> print info                          # Values for the included API codes.
    {'countries': {'FR': 'France',
                   'GB': 'United Kingdom',
                   'JP': 'Japan'},
     'indicators': {'SP.POP.TOTL': 'Population, total'}} 

If you use Pandas, you can pass the data straight in::

    >>> data, info = wb.get_country_indicators(
    >>>             ['SP.POP.TOTL', 
    >>>             'SI.DST.FRST.20'],        # Income share held by lowest 20%.
    >>>             mrv=10)                    # Get the ten most recent values.
    >>> panel = pandas.Panel(data)
    >>> panel
    <class 'pandas.core.panel.Panel'>
    Dimensions: 2 (items) x 10 (major_axis) x 246 (minor_axis)
    Items axis: SI.DST.FRST.20 to SP.POP.TOTL
    Major_axis axis: 2002 to 2011
    Minor_axis axis: 1A to ZW           
    >>> panel['SP.POP.TOTL']['BR']
    2002    179289227
    2003    181633074
    2004    183873377
    2005    185986964
    2006    187958211
    2007    189798070
    2008    191543237
    2009    193246610
    2010    194946470
    2011    196655014
    Name: BR

The Indicators API has over 8000 indicator codes. The ~1500 codes listed at 
http://data.worldbank.org/indicator/all seem to have the best data coverage.
You can request those codes specifically::

    >>> codes = wb.get_indicators( 
    >>>         match="GDP",                       # 199 indicators match "GDP".
    >>>         common_only=True,    # 106 of those are listed on the main site.
    >>>         topic=4)           # 4 of those are under the 'Education' topic.

You can pretty-print the API codes of all ``get`` function responses::

    >>> wb.print_codes(codes)
    SE.XPD.PRIM.PC.ZS   Expenditure per student, primary (% of GDP per capita)
    SE.XPD.SECO.PC.ZS   Expenditure per student, secondary (% of GDP per capita)
    SE.XPD.TERT.PC.ZS   Expenditure per student, tertiary (% of GDP per capita)
    SE.XPD.TOTL.GD.ZS   Public spending on education, total (% of GDP)

A `match` string can be passed to all Indicator functions (including 
``print_codes()``, or you can call the function directly::
    
    >>> print wb.match_data("public spending", codes).keys()
    ['SE.XPD.TOTL.GD.ZS']


API options
-----------

Below are the documented URL options and their accepted data formats. The
method docstrings state which kwargs are applicable to that method.

:language:      EN, ES, FR, AR or ZH. Non-English languages seem to have less
                info in the responses.

:date:          String formats - 2001, 2001:2006, 2003M01:2004M06, 2005Q2:2005Q4 .

:mrv:           Most recent value, ie. mrv=3 returns the three most recent 
                values for an indicator.

:gapfill:       Y/N. If using an MRV value, fills missing values with the next
                available value (I think tracking back as far as the MRV value 
                allows).

:frequency:     Works with MRV, can specify quarterly (Q), monthly (M) or 
                yearly (Y). Not all indicators have monthly and quarterly data. 

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

For full API documentation, see http://data.worldbank.org/developers/api-overview

Methods
-------

.. autoclass:: wbpy.Indicators
    :members:

Cache
=====

The default cache function uses system temporary files. You can specify your own
when instantiating an ``Indicators`` object::

    >>> wb = wbpy.Indicators(cache=my_cache_func)

You can also point ``wb.cache`` to your function. The given function must 
take a url, and return the web page as a string.

Misc
====

- Regarding country codes, wbpy supports ISO 3166 alpha-2 codes. The actual API
  mostly uses alpha-3 codes. Alpha-3 codes may work with some wbpy calls, 
  but this isn't guaranteed. 
