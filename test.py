import unittest
from datetime import datetime, timedelta
from predictor import WorkingDayCroniter, DailyExecutionAnalyzer

class TestWorkingDayCroniter(unittest.TestCase):
    def setUp(self):
        self.holidays = [
            datetime(2024, 1, 1),  # New Year's Day
            datetime(2024, 12, 25),  # Christmas
            datetime(2024, 7, 4)  # Independence Day
        ]
        self.base_date = datetime(2024, 1, 1)

    def test_get_next_working_day(self):
        cron = WorkingDayCroniter("0 0 1W * *", self.base_date, holidays=self.holidays)
        results = []
        for _ in range(5):
            results.append(cron.get_next(datetime))
        self.assertEqual(len(results), 5)
        self.assertTrue(all(res.weekday() < 5 and res not in self.holidays for res in results))

    def test_get_next_normal_day(self):
        cron = WorkingDayCroniter("0 0 15 * *", self.base_date, holidays=self.holidays)
        results = []
        for _ in range(5):
            results.append(cron.get_next(datetime))
        self.assertEqual(len(results), 5)
        self.assertTrue(all(res.day == 15 for res in results))

    def test_combined_working_and_normal_days(self):
        cron = WorkingDayCroniter("0 0 15,1W * *", self.base_date, holidays=self.holidays)
        results = []
        for _ in range(10):
            results.append(cron.get_next(datetime))
        self.assertEqual(len(results), 10)
        self.assertTrue(all(
            (res.day == 15 or (res.weekday() < 5 and res not in self.holidays)) for res in results
        ))


class TestDailyExecutionAnalyzer(unittest.TestCase):
    def test_detect_working_day_pattern(self):
        historical_data = [
            datetime(2024, 1, 2), datetime(2024, 1, 3), datetime(2024, 1, 4), datetime(2024, 1, 5),
            datetime(2024, 2, 1), datetime(2024, 2, 2), datetime(2024, 2, 5), datetime(2024, 2, 6),
            datetime(2024, 3, 1), datetime(2024, 3, 4), datetime(2024, 3, 5), datetime(2024, 3, 6),
            datetime(2024, 4, 1), datetime(2024, 4, 2), datetime(2024, 4, 3), datetime(2024, 4, 4),
        ]
        holidays = [
            datetime(2024, 1, 1), datetime(2024, 12, 25), datetime(2024, 7, 4)
        ]

        analyzer = DailyExecutionAnalyzer(historical_data, holidays)
        pattern = analyzer.detect_pattern()
        self.assertEqual(pattern['best_cron_expression'], "0 0 1W,2W,3W,4W * *")
        self.assertEqual(pattern['includes_holidays'], True)

    def test_detect_working_day_pattern_with_noise(self):
        historical_data = [
            datetime(2024, 1, 2), datetime(2024, 1, 3), datetime(2024, 1, 4), datetime(2024, 1, 5),
            datetime(2024, 2, 1), datetime(2024, 2, 2), datetime(2024, 2, 5), datetime(2024, 2, 6),
            datetime(2024, 2, 22), # Added trash
            datetime(2024, 3, 1), datetime(2024, 3, 4), datetime(2024, 3, 5), # Removed entry so simulate failed execution
            datetime(2024, 3, 24), # Added trash
            datetime(2024, 4, 1), datetime(2024, 4, 2), datetime(2024, 4, 3), datetime(2024, 4, 4),
        ]
        holidays = [
            datetime(2024, 1, 1), datetime(2024, 12, 25), datetime(2024, 7, 4)
        ]

        analyzer = DailyExecutionAnalyzer(historical_data, holidays)
        pattern = analyzer.detect_pattern()
        self.assertEqual(pattern['best_cron_expression'], "0 0 1W,2W,3W,4W * *")
        self.assertEqual(pattern['includes_holidays'], True)


    def test_detect_week_day_pattern(self):
        historical_data = [
            datetime(2024, 1, 1), datetime(2024, 1, 8), datetime(2024, 1, 15), datetime(2024, 1, 22), datetime(2024, 1, 29),  # Mondays
            datetime(2024, 2, 5), datetime(2024, 2, 12), datetime(2024, 2, 19), datetime(2024, 2, 26),  # Mondays
            datetime(2024, 3, 4), datetime(2024, 3, 11), datetime(2024, 3, 18), datetime(2024, 3, 25),  # Mondays
        ]
        holidays = [
            datetime(2024, 12, 25), datetime(2024, 7, 4)  # No holidays affecting this pattern
        ]

        analyzer = DailyExecutionAnalyzer(historical_data, holidays)
        pattern = analyzer.detect_pattern()
        self.assertEqual(pattern['best_cron_expression'], "0 0 * * 1")  # Every Monday
        self.assertEqual(pattern['includes_holidays'], False)

    def test_detect_week_day_pattern_with_noise(self):
        historical_data = [
            datetime(2024, 1, 1), datetime(2024, 1, 8), datetime(2024, 1, 15), datetime(2024, 1, 22), datetime(2024, 1, 29),  # Mondays
            datetime(2024, 1, 23), # Added noise
            datetime(2024, 2, 5), datetime(2024, 2, 12), datetime(2024, 2, 19), datetime(2024, 2, 26),  # Mondays
            datetime(2024, 2, 23), # Added noise
            datetime(2024, 3, 4), datetime(2024, 3, 11), datetime(2024, 3, 18), datetime(2024, 3, 25),  # Mondays
        ]
        holidays = [
            datetime(2024, 12, 25), datetime(2024, 7, 4)  # No holidays affecting this pattern
        ]

        analyzer = DailyExecutionAnalyzer(historical_data, holidays)
        pattern = analyzer.detect_pattern()
        self.assertEqual(pattern['best_cron_expression'], "0 0 * * 1")  # Every Monday
        self.assertEqual(pattern['includes_holidays'], False)

    def test_detect_monthly_pattern(self):
        historical_data = [
            datetime(2024, 1, 1), datetime(2024, 2, 1), datetime(2024, 3, 1), datetime(2024, 4, 1),
            datetime(2024, 5, 1), datetime(2024, 6, 1), datetime(2024, 7, 1), datetime(2024, 8, 1),
            datetime(2024, 9, 1), datetime(2024, 10, 1), datetime(2024, 11, 1), datetime(2024, 12, 1),
        ]
        holidays = [
            datetime(2024, 7, 4), datetime(2024, 12, 25)  # Holidays not affecting the pattern
        ]

        analyzer = DailyExecutionAnalyzer(historical_data, holidays)
        pattern = analyzer.detect_pattern()
        self.assertEqual(pattern['best_cron_expression'], "0 0 1 * *")  # First day of every month
        self.assertEqual(pattern['includes_holidays'], False)

    def test_detect_weekend_pattern(self):
        historical_data = [
            datetime(2024, 1, 6), datetime(2024, 1, 7), datetime(2024, 1, 13), datetime(2024, 1, 14),  # Saturdays and Sundays
            datetime(2024, 1, 20), datetime(2024, 1, 21), datetime(2024, 1, 27), datetime(2024, 1, 28),  # Saturdays and Sundays
            datetime(2024, 2, 3), datetime(2024, 2, 4), datetime(2024, 2, 10), datetime(2024, 2, 11),
        ]
        holidays = [
            datetime(2024, 7, 4), datetime(2024, 12, 25)  # No holidays affecting this pattern
        ]

        analyzer = DailyExecutionAnalyzer(historical_data, holidays)
        pattern = analyzer.detect_pattern()
        self.assertEqual(pattern['best_cron_expression'], "0 0 * * 6,7")  # Every Saturday and Sunday
        self.assertEqual(pattern['includes_holidays'], False)

    def test_detect_irregular_pattern(self):
        historical_data = [
            datetime(2024, 1, 3), datetime(2024, 1, 10), datetime(2024, 1, 17), datetime(2024, 1, 24),  # Wednesdays
            datetime(2024, 1, 31), datetime(2024, 2, 7), datetime(2024, 2, 14), datetime(2024, 2, 28),  # Skipped 21st
            datetime(2024, 3, 6), datetime(2024, 3, 13), datetime(2024, 3, 20), datetime(2024, 3, 27),
        ]
        holidays = [
            datetime(2024, 2, 21),  # Holiday affecting the pattern
        ]

        analyzer = DailyExecutionAnalyzer(historical_data, holidays)
        pattern = analyzer.detect_pattern()
        self.assertEqual(pattern['best_cron_expression'], "0 0 * * 3")  # Every Wednesday
        self.assertEqual(pattern['includes_holidays'], False)

    def test_detect_pattern_with_large_noise(self):
        historical_data = [
            datetime(2024, 1, 1), datetime(2024, 1, 8), datetime(2024, 1, 15), datetime(2024, 1, 22), datetime(2024, 1, 29),  # Mondays
            datetime(2024, 1, 3), datetime(2024, 1, 12), datetime(2024, 1, 25),  # Noise
            datetime(2024, 2, 5), datetime(2024, 2, 12), datetime(2024, 2, 19), datetime(2024, 2, 26),  # Mondays
            datetime(2024, 2, 4), datetime(2024, 2, 13), datetime(2024, 2, 20),  # Noise
        ]
        holidays = [
            datetime(2024, 12, 25), datetime(2024, 7, 4)  # No holidays affecting this pattern
        ]

        analyzer = DailyExecutionAnalyzer(historical_data, holidays)
        pattern = analyzer.detect_pattern()
        self.assertEqual(pattern['best_cron_expression'], "0 0 * * 1")  # Every Monday
        self.assertEqual(pattern['includes_holidays'], False)


