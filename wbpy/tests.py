import unittest

import wbpy

class TestIndicators(unittest.TestCase):
    def test_get_topics_returns_topics(self):
        wb = wbpy.Indicators()
        data = wb.get_topics()
        topic = data.values()[1] 
        self.assertTrue(topic.has_key('value'))
        self.assertTrue(topic.has_key('sourceNote'))
        self.assertTrue(topic.has_key('id'))

    def test_get_sources_returns_sources(self):
        wb = wbpy.Indicators()
        data = wb.get_sources()
        source = data.values()[1]
        self.assertTrue(source.has_key('name'))
        self.assertTrue(source.has_key('id'))

    def test_get_countries_returns_countries(self):
        wb = wbpy.Indicators()
        data = wb.get_countries()
        test_keys = ['GB', 'AF', 'FR', 'IT', 'BR']
        self.assertTrue(all([key in data for key in test_keys]))

    def test_get_income_levels_returns_income_levels(self):
        wb = wbpy.Indicators()
        test_keys = ['LMC', 'UMC']
        data = wb.get_income_levels(test_keys)
        self.assertTrue(all([key in test_keys for key in data]))
        
    def test_get_regions_returns_regions(self):
        wb = wbpy.Indicators()
        data = wb.get_regions(match="Latin")
        self.assertTrue(all(['latin' in v['name'].lower() for v in data.values()]))

    def test_get_indicators_returns_indicators(self):
        wb = wbpy.Indicators()
        data = wb.get_indicators()
        self.assertTrue(len(data) > 7500)

    def test_get_indicators_common_only_flag_filters_out_codes(self):
        wb = wbpy.Indicators()
        data = wb.get_indicators(common_only=True)
        self.assertTrue(len(data) < 2000)

    def test_get_country_indicators_returns_data_and_info_dicts(self):
        wb = wbpy.Indicators()
        data, info = wb.get_country_indicators(['SP.POP.TOTL'], ['GB'], date=2010)
        self.assertIsNotNone(data)
        self.assertIsNotNone(info)
        try:
            val = data['SP.POP.TOTL']['GB']['2010']
            assert True
        except KeyError:
            assert False

    def test_can_pass_own_cache_object(self):
        import urllib2
        def test_fetch(url):
            return urllib2.urlopen(url).read()

        wb = wbpy.Indicators(cache=test_fetch)
        data = wb.get_topics()
        self.assertTrue(data.values()[1].has_key('sourceNote'))

    def test_url_structure_changing_kwargs_work(self):
        wb = wbpy.Indicators()
        indicators = wb.get_indicators(topic=4, language="EN")
        # Check that every indicator belongs to topic 4. 
        matches = []
        for v in indicators.values():
                matches.append('4' in [topic['id'] for topic in v['topics']])
        self.assertTrue(all(matches))

    def test_no_print_exceptions_for_indicators_data_info(self):
        wb = wbpy.Indicators()
        data, info = wb.get_country_indicators(['SP.POP.TOTL'])
        wb.print_codes(info)
        assert True

if __name__ == '__main__':
    unittest.main()

