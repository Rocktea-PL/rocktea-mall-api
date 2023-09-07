from django.core.exceptions import ValidationError
import datetime

class YearValidator:
   def __init__(self):
      current_year = datetime.date.today().year
      self.min_value = 1900  # Change this to your desired minimum year
      self.max_value = current_year

   def __call__(self, value):
      try:
            year = int(value.strftime("%Y"))
            if year < self.min_value or year > self.max_value:
               raise ValidationError(
                  f"Year must be between {self.min_value} and {self.max_value}.")
      except ValueError:
            raise ValidationError(
               "Invalid year format. Use a 4-digit year (e.g., '2023').")