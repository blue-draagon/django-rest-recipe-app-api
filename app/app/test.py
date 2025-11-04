from django.test import SimpleTestCase

from . import calculator


class CalculatorTest(SimpleTestCase):
    def test_add_numbers(self):
        result = calculator.add(5, 6)
        self.assertEqual(result, 11)

    def test_subtract_numbers(self):
        result = calculator.subtract(10, 6)
        self.assertEqual(result, 4)
