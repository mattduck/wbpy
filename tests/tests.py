import unittest

import wbpy

class TestIndicators(unittest.TestCase):
    def test_get_topics_returns_topics(self):
        ind = wbpy.Indicators()
        data = ind.get_topics()
        topic = data.values()[1] 
        self.assertTrue(topic.has_key('value'))
        self.assertTrue(topic.has_key('sourceNote'))

    def test_get_sources_returns_sources(self):
        ind = wbpy.Indicators()
        data = ind.get_sources()
        source = data.values()[1]
        self.assertTrue(source.has_key('name'))

    def test_get_countries_returns_countries(self):
        ind = wbpy.Indicators()
        test_keys = ['GB', 'AF', 'FR', 'IT', 'BR']
        data = ind.get_countries(test_keys)
        self.assertTrue(all([key in data for key in test_keys]))

    def test_get_income_levels_returns_income_levels(self):
        ind = wbpy.Indicators()
        test_keys = ['LMC', 'UMC']
        data = ind.get_income_levels(test_keys)
        self.assertTrue(all([key in test_keys for key in data]))
        
    def test_get_regions_returns_regions(self):
        ind = wbpy.Indicators()
        data = ind.get_regions(search="Latin")
        self.assertTrue(all(['latin' in v['name'].lower() for v in data.values()]))

    def test_get_indicators_returns_indicators(self):
        ind = wbpy.Indicators()
        data = ind.get_indicators()
        self.assertTrue(len(data) > 7500)

    def test_get_indicators_common_only_flag_filters_out_codes(self):
        ind = wbpy.Indicators()
        data = ind.get_indicators(common_only=True)
        self.assertTrue(len(data) < 2000)

    def test_get_country_indicators_returns_data_and_metadata_dicts(self):
        ind = wbpy.Indicators()
        results = ind.get_country_indicators(['SP.POP.TOTL'], ['GB', "US"], date=2010)

        self.assertEqual(len(results.indicators), 1)
        self.assertEqual(results.indicators.keys(), ["SP.POP.TOTL"])
        self.assertIn("population", results.indicators.values()[0].lower())

        self.assertEqual(len(results.countries), 2)
        self.assertEqual(results.countries.keys(), ["GB", "US"])
        self.assertTrue("united states" in results.countries["US"].lower())

        try:
            val = results.data['SP.POP.TOTL']['GB']['2010']
            assert True
        except KeyError:
            assert False

    def test_can_pass_own_cache_object(self):
        import urllib2
        def test_fetch(url):
            return urllib2.urlopen(url).read()

        ind = wbpy.Indicators(fetch=test_fetch)
        data = ind.get_topics()
        self.assertTrue(data.values()[1].has_key('sourceNote'))

    def test_url_structure_changing_kwargs_work(self):
        ind = wbpy.Indicators()
        indicators = ind.get_indicators(topic=4, language="EN")
        # Check that every indicator belongs to topic 4. 
        matches = []
        for v in indicators.values():
                matches.append('4' in [topic['id'] for topic in v['topics']])
        self.assertTrue(all(matches))

    def test_no_print_exceptions_for_indicators_data_metadata(self):
        ind = wbpy.Indicators()
        results = ind.get_country_indicators(['SP.POP.TOTL'])
        ind.print_codes(results.data)
        assert True

    def test_no_utf8_errors_when_printing_all_indicators(self):
        ind = wbpy.Indicators()
        ind.print_codes(ind.get_indicators())
        assert True

    def test_no_duplicate_key_vals_in_Get_results(self):
        # The response keys are 'iso2Code' and 'code' respectively
        ind = wbpy.Indicators()
        countries = ind.get_countries()
        keys = all([v.has_key('iso2Code') == False for v in countries.values()])
        self.assertTrue(keys)
        regions = ind.get_regions()
        keys = all([v.has_key('code') == False for v in regions.values()])
        self.assertTrue(keys)

    def test_get_indicators_common_only_not_empty(self):
        ind = wbpy.Indicators()
        data = ind.get_indicators(common_only=True)
        self.assertTrue(len(data) > 500)

    def test_that_default_search_is_of_keys_and_not_values(self):
        ind = wbpy.Indicators()
        data = ind.get_sources(search="11") # 11 is a key, and not in the value

        self.assertIn("11", data.keys())
        self.assertEqual(len(data), 1)

    def test_print_codes_func_handles_get_countries_func(self):
        ind = wbpy.Indicators()
        data = ind.get_countries()
        ind.print_codes(data)
        assert True

    def test_print_codes_func_handles_get_country_indicators_func(self):
        ind = wbpy.Indicators()
        results = ind.get_country_indicators(["SP.POP.TOTL"])
        ind.print_codes(results.data)
        ind.print_codes(results.indicators)
        ind.print_codes(results.countries)
        assert True

    def test_print_codes_func_handles_get_income_levels_func(self):
        ind = wbpy.Indicators()
        data = ind.get_income_levels()
        ind.print_codes(data)
        assert True

    def test_print_codes_func_handles_get_indicators_func(self):
        ind = wbpy.Indicators()
        data = ind.get_indicators()
        ind.print_codes(data)
        assert True

    def test_print_codes_func_handles_get_lending_types_func(self):
        ind = wbpy.Indicators()
        data = ind.get_lending_types()
        ind.print_codes(data)
        assert True

    def test_print_codes_func_handles_get_regions_func(self):
        ind = wbpy.Indicators()
        data = ind.get_regions()
        ind.print_codes(data)
        assert True

    def test_print_codes_func_handles_get_sources_func(self):
        ind = wbpy.Indicators()
        data = ind.get_sources()
        ind.print_codes(data)
        assert True

    def test_print_codes_func_handles_get_topics_func(self):
        ind = wbpy.Indicators()
        data = ind.get_topics()
        ind.print_codes(data)
        assert True

    def test_search_results_takes_regexp(self):
        # Check that case is ignored too
        ind = wbpy.Indicators()
        data = dict(
            foo="I hope this one will MATCH",
            bar="This one will not match, I hope",
            )

        results = ind.search_results("hope.+match", data)
        self.assertTrue("foo" in results.keys())
        self.assertFalse("bar" in results.keys())

    def test_search_results_takes_key(self):
        ind = wbpy.Indicators()
        data = ind.get_topics()

        results = ind.search_results("poverty", data, key="value")
        self.assertTrue(results.has_key("11")) # Code for Poverty topic
        self.assertEqual(len(results.keys()), 1)

        results = ind.search_results("poverty", data)
        self.assertGreater(len(results.keys()), 1)

    def test_search_full_flag_filters_descriptions(self):
        ind = wbpy.Indicators()

        # By default, should only be searching the name of the country
        data = ind.get_countries(search="america")
        for v in data.values():
            self.assertIn("america", v["name"].lower())
        default_len = len(data)

        # When full, should be searching the values too
        data = ind.get_countries(search="america", search_full=True)
        for v in data.values():
            self.assertIn("america", str(v).lower())
        full_len = len(data)

        self.assertGreater(full_len, default_len)

    def test_ISO_2_standard_codes_supported(self):
        ind = wbpy.Indicators()

        codes = ["US", "AF"]
        data = ind.get_countries(codes)
        self.assertEqual(data["US"]["name"], "United States")
        self.assertEqual(data["AF"]["name"], "Afghanistan")

    def test_ISO_3_standard_codes_supported(self):
        ind = wbpy.Indicators()

        codes = ["USA", "AFG"]
        data = ind.get_countries(codes)
        self.assertEqual(data["US"]["name"], "United States")
        self.assertEqual(data["AF"]["name"], "Afghanistan")

    def test_documentation_claim_that_nonstandard_codes_used_is_false(self):
        ind = wbpy.Indicators()

        countries = [
            # The API documentation claims that these countries use either
            # non-standard alpha-2 or alpha-3 codes. This test tries
            # all the official alpha-2 and alpha-3 values. If it fails, we 
            # need to convert them, so that the Indicators() class supports
            # all the offical codes.
            ("andorra", "ad", "and"),
            ("serbia", "rs", "srb"),
            ("congo, dem", "cd", "cod"),
            ("isle of man", "im", "imn"),
            ("romania", "ro", "rou"),
            ("timor-leste", "tl", "tls"),
            ("gaza", "ps", "pse"),

            # These are actually not standard - they don't have 
            # ISO 1366 entries
            ("channel islands", "jg", "chi"),
            ("kosovo", "kv", "ksv"),
            ]

        for name, iso2, iso3 in countries:
            for code in [iso2, iso3]:
                data = ind.get_countries([code])
                self.assertIn(name.lower(), 
                    data[iso2.upper()]["name"].lower())
                self.assertEqual(len(data), 1)


class TestClimate(unittest.TestCase):
    def test_get_precip_instrumental(self):
        # Test can use multiple locations.
        # Test ISO codes are upper case.
        # Test result in expected dict format 
        c = wbpy.Climate()
        data, md = c.get_precip_instrumental(locations=['bra', 'chn'], 
                                               interval='year')
        self.assertTrue(data['BR'].has_key(1990))
        self.assertTrue(data['CN'].has_key(1975))

    def test_get_temp_instrumental(self):
        # Test month keys get converted to 1-12, instead of 0-11
        # Test basin id numbers work 
        c = wbpy.Climate()
        data, md = c.get_temp_instrumental(locations=['gbr', 2], 
                                             interval='month')
        self.assertTrue(data['GB'].has_key(12))
        self.assertTrue(data[2].has_key(1))

    def test_get_precip_modelled_ensemble_has_right_gcm_keys(self):
        c = wbpy.Climate()
        data, md = c.get_precip_modelled(data_type='aavg', locations=['usa'],
                            gcm=['ensemble'])
        for k in data.keys():
            self.assertTrue(k.startswith("ensemble"))

    def test_get_precip_modelled_mavg(self):
        # General results layout - keys etc
        c = wbpy.Climate()
        data, md = c.get_precip_modelled(data_type='mavg', locations=['bra'])
        self.assertTrue(data['mpi_echam5']['BR'][1920].has_key(12))

    def test_get_temp_modelled_aanom(self):
        # Test sres filter works
        # Test can pass 'aanom' as data type
        c = wbpy.Climate()
        data, md = c.get_temp_modelled(data_type='aanom', 
                locations=['USA', 'AUS'], sres='A2')
        sres = []
        for country_data in data['gfdl_cm2_1'].values():
            for year_key in country_data.keys():
                try:
                    sres.append('a2' in year_key[1])
                except TypeError:
                    pass # Not all keys are tuples
        self.assertTrue(all(sres)) # All future keys should be a2 scenario.

    def test_get_temp_modelled_gcm_filter(self):
        c = wbpy.Climate()
        gcms = ['cnrm_cm3', 'ukmo_hadcm3']
        data, md = c.get_temp_modelled(data_type='mavg', locations=['gbr'],
                gcm=gcms)
        self.assertTrue(all([k in gcms for k in data.keys()]))

    def test_get_derived_stat(self):
        # Test can pass alpha2 codes
        c = wbpy.Climate()
        data, md = c.get_derived_stat(data_type='aanom', stat='tmin_days10th',
                locations=['gb', 'JP'])
        self.assertTrue(data["ensemble_10"]['JP'].has_key((2046, 'b1')))

    def test_returned_metadata_is_correct(self):
        # Also test Climate().definitions exist
        c = wbpy.Climate()
        data, md = c.get_derived_stat(data_type='aanom', stat='tmin_days10th',
                locations=['gb', 'JP'])
        self.assertTrue(md['sres'].has_key('a2'))
        self.assertTrue(md['sres'].has_key('b1'))
        self.assertTrue(md['stat'] == c.definitions['stat']['tmin_days10th'])

    def test_can_put_ensemble_as_a_model_in_gcm_list(self):
        # Also check dates exist in metadata
        c = wbpy.Climate()
        data, md = c.get_temp_modelled('aanom', ['AF'], 
            gcm=['ensemble', 'cccma_cgcm3_1'])

        expected_keys = ["ensemble_10", "ensemble_50", "ensemble_90",
                "cccma_cgcm3_1"] 
        self.assertTrue(all([k in expected_keys for k in data.keys()]))
        self.assertIsNotNone(md['dates'])

    def test_ensemble_percentile_gcms(self):
        c = wbpy.Climate()
        data, md = c.get_precip_modelled("mavg", ["GB"], 
            gcm=["ensemble_50"])
        self.assertEqual(data.keys(), ["ensemble_50"])

    def test_aanom_modelled_gcm_results_arent_blank(self):
        c = wbpy.Climate()
        data, md = c.get_precip_modelled('aanom', ['GB'])
        for locs in data.values():
            for value in locs['GB'].values():
                self.assertNotEqual({}, value )

    def test_ISO_2_standard_codes_supported(self):
        c = wbpy.Climate()

        codes = ["US", "AF"]
        data, md = c.get_precip_instrumental(codes)
        self.assertTrue(data.has_key("US"))
        self.assertTrue(data.has_key("AF"))

    def test_ISO_3_standard_codes_supported(self):
        c = wbpy.Climate()

        codes = ["USA", "AFG"]
        data, md = c.get_precip_instrumental(codes)
        self.assertTrue(data.has_key("US"))
        self.assertTrue(data.has_key("AF"))

    def test_the_nonstandard_ISO_codes_for_Indicators_countries(self):
        c = wbpy.Climate()

        countries = [
            # Check the supposed non-standard codes from the Indicators API.
            ("andorra", "ad", "and"),
            ("serbia", "rs", "srb"),
            ("congo, dem", "cd", "cod"),
            ("isle of man", "im", "imn"),
            ("romania", "ro", "rou"),
            ("timor-leste", "tl", "tls"),
            ("gaza", "ps", "pse"),

            # These non-standard entries that are used by the Indicators API
            # do NOT work for the Climate API.
            # 
            #("channel islands", "jg", "chi"),
            #("kosovo", "kv", "ksv"),
            ]

        for name, iso2, iso3 in countries:
            for code in [iso2, iso3]:
                data, md = c.get_precip_instrumental([code])
                self.assertTrue(data.has_key(iso2.upper()))
                self.assertEqual(len(data), 1)


if __name__ == '__main__':
    unittest.main()
