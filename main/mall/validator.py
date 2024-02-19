from workshop.exceptions import ValidationError
import datetime

class YearValidator:
    def __init__(self, min_value=1900):
        self.min_value = min_value
        self.max_value = datetime.date.today().year

    def __call__(self, value):
        try:
            year = int(value.strftime("%Y"))
            if year < self.min_value or year > self.max_value:
                raise ValidationError(
                    f"Year must be between {self.min_value} and {self.max_value}.")
        except ValueError:
            raise ValidationError(
                "Invalid year format. Use a 4-digit year (e.g., '2023').")