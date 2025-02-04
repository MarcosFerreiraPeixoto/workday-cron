from datetime import datetime, timedelta
import calendar
from typing import List, Dict, Optional, Any, Union
from collections import Counter
from croniter import croniter
from functools import lru_cache
from copy import deepcopy
import threading


class WorkingDayCroniter:
    def __init__(self, expr: Union[str, List[str]], base: datetime, holidays: Optional[List[datetime]] = None):
        if isinstance(expr, list):
            self.expressions = expr
        else:
            self.expressions = [expr]
        self.base = base
        self.holidays = set(holidays or [])
        self._state = threading.local()
        self._state.last_date = None

        # for expr in self.expressions:
        #     self._raise_if_invalid_expr(expr)

        self._has_working_day_expr = any("W" in expr for expr in self.expressions)

        if len(self.expressions) == 1:
            expr = self.expressions[0]
            self._is_working_day_expr = "W" in expr
            if self._is_working_day_expr:
                self._cron_iter = None
            else:
                self._cron_iter = croniter(expr, base)
        else:
            self._cron_iter = None

    def _raise_if_invalid_expr(self, expr: str):
        expr_parts = deepcopy(expr).split()
        if len(expr_parts) != 5:
            raise ValueError("Cron expression must have exactly 5 parts.")

        days_part = expr_parts[2]
        for day in days_part.split(","):
            if "W" in day:
                w_part = day.replace("W", "")
                if not w_part:
                    raise ValueError(f"Invalid working day number in expression: {day}")
                try:
                    int(w_part)
                except ValueError:
                    raise ValueError(f"Invalid working day number in expression: {day}")

        expr_to_validate = " ".join(expr_parts)
        if not croniter.is_valid(expr_to_validate):
            raise ValueError(f"Invalid cron expression: {expr}")

    def get_next(self, date_class=datetime) -> datetime:
        if len(self.expressions) == 1:
            return self._handle_single_expression(date_class)
        else:
            return self._handle_multiple_expressions(date_class)

    def _handle_single_expression(self, date_class):
        if not self._is_working_day_expr:
            return self._cron_iter.get_next(date_class)

        cron_expr = self._get_base_cron_expr()
        working_days = self._parse_working_days(self.expressions[0].split()[2])
        normal_days = self._parse_normal_days(self.expressions[0].split()[2])
        iter_base = croniter(cron_expr, self._state.last_date or self.base)

        max_iterations = 1500
        for _ in range(max_iterations):
            candidate_date = iter_base.get_next(date_class)
            if self._matches_working_day(candidate_date, working_days) or \
               self._matches_normal_day(candidate_date, normal_days):
                self._state.last_date = candidate_date
                return candidate_date
        raise RuntimeError("Exceeded maximum iterations while finding the next valid date.")

    def _handle_multiple_expressions(self, date_class):
        max_iterations = 1500
        start_date = self._state.last_date or self.base

        # Initialize iterators once and reuse them
        iterators = []
        for expr in self.expressions:
            iterator = WorkingDayCroniter(expr, start_date, self.holidays)
            iterators.append(iterator)

        # Get the first candidate dates from all iterators
        current_dates = [iterator.get_next(date_class) for iterator in iterators]
        candidate = max(current_dates)
        iterations = 0

        while iterations < max_iterations:
            
            # Check if all dates match the candidate
            if all(d == candidate for d in current_dates):
                self._state.last_date = candidate
                return candidate

            # Advance iterators that are behind the candidate
            for i in range(len(current_dates)):
                while current_dates[i] < candidate:
                    try:
                        current_dates[i] = iterators[i].get_next(date_class)
                    except RuntimeError:
                        break  # Handle potential errors from individual iterators

            # Update candidate to the new maximum
            new_candidate = max(current_dates)
            candidate = new_candidate
            iterations += 1


        raise RuntimeError("Exceeded maximum iterations while finding the next valid date.")

    def _get_base_cron_expr(self) -> str:
        parts = self.expressions[0].split()
        if "W" in parts[2]:
            parts[2] = "*"
        return " ".join(parts)

    def _parse_working_days(self, day_of_month: str) -> List[int]:
        return [int(part.replace("W", "")) for part in day_of_month.split(",") if "W" in part]

    def _parse_normal_days(self, day_of_month: str) -> List[int]:
        return [int(part) for part in day_of_month.split(",") if part.isdigit()]

    def _matches_working_day(self, date: datetime, working_days: List[int]) -> bool:
        if date.weekday() >= 5 or date in self.holidays:
            return False
        return self._get_nth_working_day(date) in working_days

    def _matches_normal_day(self, date: datetime, normal_days: List[int]) -> bool:
        return date.day in normal_days

    def _get_nth_working_day(self, date: datetime) -> int:
        month_start = date.replace(day=1)
        nth_working_day = 0
        for day in range(1, date.day + 1):
            try:
                candidate = month_start.replace(day=day)
            except ValueError:
                break
            if candidate.weekday() < 5 and candidate not in self.holidays:
                nth_working_day += 1
                if candidate == date:
                    return nth_working_day
        return 0


class MonthlyExecutionAnalyzer:
    def __init__(self, historical_data: List[datetime], threshold: float = 0.8, deviation: int = 3):
        """
        Initializes the analyzer with historical execution data.

        :param historical_data: List of datetime objects representing execution dates.
        :param threshold: Proportion of intervals required to determine a consistent pattern.
        :param deviation: Allowed deviation in days for interval matching.
        """
        if not historical_data:
            raise ValueError("Historical data cannot be empty.")
        
        self.historical_data = sorted(
            dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0) for dt in deepcopy(historical_data)
        )
        self.threshold = threshold
        self.deviation = deviation

    def detect_pattern(self) -> Dict[str, Any]:
        """
        Detects the frequency pattern from the historical data.

        :return: Dictionary containing the detected pattern and frequencies.
        """
        intervals = self._calculate_intervals_between_executions()
        frequencies = self._count_intervals_frequencies(intervals)
        starting_month = self._get_most_frequent_month()
        pattern = self._gerate_monthly_pattern(frequencies, starting_month)
        
        return {
            "pattern": pattern
        }

    def _count_by_month_and_filter_noise(self) -> Dict[int, int]:
        """
        Counts occurrences of dates by month.

        :return: Dictionary of months and their counts.
        """
        month_count = Counter(date.month for date in self.historical_data)
        max_count = max(month_count.values(), default=0)
        
        # Keep only months with counts close to the max count
        return {month: count for month, count in month_count.items() if count * 2 >= max_count}

    def _calculate_intervals_between_executions(self) -> List[int]:
        """
        Calculates the day intervals between consecutive dates, filtering by frequent months.

        :return: List of intervals in days.
        """
        filtered_months = set(self._count_by_month_and_filter_noise().keys())
        filtered_data = [date for date in self.historical_data if date.month in filtered_months]
        
        return [
            (filtered_data[i] - filtered_data[i - 1]).days
            for i in range(1, len(filtered_data))
        ]

    def _count_intervals_frequencies(self, intervals: List[int]) -> Counter:
        """
        Counts the occurrence of intervals that match predefined monthly patterns.

        :param intervals: List of day intervals.
        :return: Counter of matching interval frequencies.
        """
        monthly_intervals = [30, 60, 90, 120, 180]
        frequencies = Counter()

        for interval in intervals:
            for base in monthly_intervals:
                if abs(interval - base) <= self.deviation:  # Allow small deviation
                    frequencies[base] += 1
                    break

        return frequencies

    def _get_most_frequent_month(self) -> int:
        """
        Finds the most frequent month in the historical data.

        :return: The most frequent month as an integer (1 for January, 12 for December).
        """
        months = [dt.month for dt in self.historical_data]
        month_frequencies = Counter(months)
        return month_frequencies.most_common(1)[0][0]

    def _gerate_monthly_pattern(self, frequencies: Counter, starting_month: int) -> str:
        """
        Detects the most common frequency pattern.

        :param frequencies: Counter of interval frequencies.
        :param starting_month: The most frequent starting month.
        :return: A string representing the detected frequency pattern.
        """
        if not frequencies:
            return "*"
       
        most_common_interval = frequencies.most_common(1)[0][0]
        pattern = []

        if most_common_interval == 30:
            return "*"
        
        for i in range(0, 12, most_common_interval // 30):  # Convert interval to months
            pattern.append((starting_month + i - 1) % 12 + 1)

        return ",".join(map(str, sorted(set(pattern))))


class DailyExecutionAnalyzer:
    def __init__(self, historical_data: List[datetime], holidays: List[datetime] = None, monthly_pattern: str = "*"):
        self.historical_data = sorted(set(dt.replace(hour=0, minute=0, second=0, microsecond=0) for dt in deepcopy(historical_data)))

        if monthly_pattern != "*":
            self.historical_data = [date for date in self.historical_data if str(date.month) in monthly_pattern.split(",")]

        self.monthly_pattern = monthly_pattern
        self.holidays = set(dt.replace(hour=0, minute=0, second=0, microsecond=0) for dt in holidays) if holidays else set()

    def detect_pattern(self) -> Dict[str, any]:
        weekday_count = self._count_by_weekday_and_filter_noise()
        day_of_month_count = self._count_by_day_of_month_and_filter_noise()
        working_day_count = self._count_by_working_day_and_filter_noise()

        cron_expressions = self._generate_cron_expressions(weekday_count, day_of_month_count, working_day_count, self.monthly_pattern)

        best_cron = None
        highest_accuracy = 0
        includes_holidays = False

        for cron_expr in cron_expressions:
            accuracy = self._evaluate_cron_expr_accuracy(cron_expr, holiday=False)
            print(f"cron: {cron_expr}, accuracy: {accuracy}")
            if accuracy > highest_accuracy:
                best_cron = cron_expr
                highest_accuracy = accuracy

        for cron_expr in cron_expressions:
            accuracy = self._evaluate_cron_expr_accuracy(cron_expr, holiday=True)
            print(f"cron: {cron_expr}, accuracy: {accuracy}")
            if accuracy > highest_accuracy:
                best_cron = cron_expr
                highest_accuracy = accuracy
                includes_holidays = True

        return {
            "pattern": best_cron,
            "includes_holidays": includes_holidays,
        }

    def _count_by_weekday_and_filter_noise(self) -> Dict[int, int]:
        weekday_count = Counter(date.isoweekday() for date in self.historical_data)
        max_count = max(weekday_count.values(), default=0)
        return {day: count for day, count in weekday_count.items() if count * 1.5 >= max_count}

    def _count_by_day_of_month_and_filter_noise(self) -> Dict[int, int]:
        day_of_month_count = Counter(date.day for date in self.historical_data)
        max_count = max(day_of_month_count.values(), default=0)
        return {day: count for day, count in day_of_month_count.items() if count * 1.5 >= max_count}

    def _count_by_working_day_and_filter_noise(self) -> Dict[int, int]:
        working_day_count = Counter()
        for date in self.historical_data:
            year, month = date.year, date.month
            working_days = self._get_working_days(year, month)
            if date in working_days:
                index = working_days.index(date) + 1
                working_day_count[index] += 1

        max_count = max(working_day_count.values(), default=0)
        return {day: count for day, count in working_day_count.items() if count * 1.5 >= max_count}

    def _generate_cron_expressions(self, weekday_count: Dict[int, int], day_of_month_count: Dict[int, int], working_day_count: Dict[int, int], monthly_pattern: str) -> List[str]:
        crons = []

        crons.append(f"0 0 * {monthly_pattern} *")  # Daily execution

        weekdays = [str(day) for day, count in weekday_count.items() if count > 0]
        if weekdays:
            crons.append(f"0 0 * {monthly_pattern} {','.join(weekdays)}")

        days = [str(day) for day, count in day_of_month_count.items() if count > 0]
        if days:
            crons.append(f"0 0 {','.join(days)} {monthly_pattern} *")

        working_days = [f"{day}W" for day, count in working_day_count.items() if count > 0]
        if working_days:
            crons.append(f"0 0 {','.join(working_days)} {monthly_pattern} *")

        return crons

    def _evaluate_cron_expr_accuracy(self, cron_expr: str, holiday: bool) -> float:
        try:
            cron = WorkingDayCroniter(
                cron_expr, base=self.historical_data[0] - timedelta(hours=1), holidays=self.holidays if holiday else None
            )
            
            predicted_dates = set()
            for _ in range(len(self.historical_data)):
                next_date = cron.get_next(datetime)
                predicted_dates.add(next_date)

            return len(predicted_dates.intersection(self.historical_data)) / len(self.historical_data)
        except Exception as e:
            return 0.0

    @lru_cache(None)
    def _get_working_days(self, year: int, month: int) -> List[datetime]:
        working_days = []
        _, last_day = calendar.monthrange(year, month)
        for day in range(1, last_day + 1):
            try:
                date = datetime(year, month, day)
                if date.weekday() < 5 and date not in self.holidays:
                    working_days.append(date)
            except ValueError:
                continue
        return working_days
    
class HourlyExecutionAnalyzer:
    def __init__(self, historical_data: List[datetime]):
        self.historical_data = sorted(historical_data)
    
    def detect_pattern(self) -> Dict[str, any]:
        hours_count = self._count_by_hour_and_filter_noise()

        total_hours_count_sum = sum(hours_count)
        hour_with_max_count = max(hours_count, key=hours_count.get)

        cumulative_sum = hours_count[hour_with_max_count]

        counter = 0

        while cumulative_sum < total_hours_count_sum * 0.9:
            counter += 1
            lower_range = str(int(hour_with_max_count) - counter).zfill(2)
            upper_range = str(int(hour_with_max_count) + counter).zfill(2)

            cumulative_sum += hours_count.get(lower_range, 0) + hours_count.get(upper_range, 0)

        return {
            "pattern": int(hour_with_max_count),
            "tolerance": 1 if counter == 0 else counter
        }
    
    def _count_by_hour_and_filter_noise(self) -> Dict[int, int]:
        print(self.historical_data)
        hour_count = Counter(date.hour for date in self.historical_data)
        max_count = max(hour_count.values(), default=0)

        return {hour: count for hour, count in hour_count.items() if count * 1.5 >= max_count}
    
class ExecutionAnalyzer:
    def __init__(self, historical_data: datetime, holidays: List[datetime] = None):
        self.historical_data = historical_data
        self.holidays = holidays

    def detect_pattern(self):
        mea = MonthlyExecutionAnalyzer(self.historical_data)
        monthly_pattern = mea.detect_pattern()

        dea = DailyExecutionAnalyzer(self.historical_data, self.holidays, monthly_pattern['pattern'])
        daily_pattern = dea.detect_pattern()

        hea = HourlyExecutionAnalyzer(self.historical_data)
        hourly_pattern = hea.detect_pattern()

        most_common_hour = hourly_pattern['pattern']
        tolerance = hourly_pattern['tolerance']

        daily_cron_list_format = daily_pattern['pattern'].split(" ")
        includes_holidays = daily_pattern['includes_holidays']
        daily_cron_list_format[1] = str(most_common_hour)
        final_cron = " ".join(daily_cron_list_format)

        return {
            "pattern": final_cron,
            "hour_tolerance": tolerance,
            "includes_holidays": includes_holidays 
        }
        