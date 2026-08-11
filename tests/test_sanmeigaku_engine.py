import unittest
from datetime import date

from sanmeigaku_engine import calculate_chart


class SanmeigakuEngineTest(unittest.TestCase):
    def test_known_1977_08_20_chart(self):
        chart = calculate_chart(date(1977, 8, 20))
        self.assertEqual("丁巳", chart["year_pillar"])
        self.assertEqual("戊申", chart["month_pillar"])
        self.assertEqual("己酉", chart["day_pillar"])
        self.assertEqual("司禄星", chart["center_star"])
        self.assertEqual("龍高星", chart["north_star"])
        self.assertEqual("調舒星", chart["east_star"])
        self.assertEqual("石門星", chart["south_star"])
        self.assertEqual("鳳閣星", chart["west_star"])
        self.assertEqual("天将星", chart["early_star"])
        self.assertEqual("天恍星", chart["middle_star"])
        self.assertEqual("天貴星", chart["late_star"])


if __name__ == "__main__":
    unittest.main()
