# tests/__main__.py

import unittest

if __name__ == '__main__':
    # Define the pattern to match test files
    test_pattern = 'test_*.py'

    # Create a test loader
    loader = unittest.TestLoader()

    # Find all test cases in the current directory that match the pattern
    suite = loader.discover('.', pattern=test_pattern)

    # Create a test runner that will display the results to the console
    runner = unittest.TextTestRunner(verbosity=2)

    # Run the test suite
    runner.run(suite)