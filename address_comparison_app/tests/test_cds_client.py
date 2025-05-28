"""
Unit tests for the CDSClient class and CDS API integration.
"""

import unittest
from address_comparison_app.cds_client import CDSClient, CDSClientError
import os

class TestCDSClient(unittest.TestCase):
    """Test suite for CDSClient lookups and error handling."""
    def setUp(self):
        # Use test env variables or mock if needed
        self.client = CDSClient()

    def test_lookup_by_entity_id(self):
        """Test lookup by a valid entity ID."""
        # This test will only work if the test entity ID exists and credentials are valid
        entity_id = 105842360
        try:
            df = self.client.lookup_entity_as_dataframe(entity_id)
            self.assertIsNotNone(df)
        except CDSClientError as e:
            self.skipTest(f"CDS API not available or credentials missing: {e}")

    def test_lookup_by_bvd_id(self):
        """Test lookup by a valid BVD ID."""
        bvd_id = "CA*S00222833"
        try:
            df = self.client.lookup_entity_as_dataframe(bvd_id)
            self.assertIsNotNone(df)
        except CDSClientError as e:
            self.skipTest(f"CDS API not available or credentials missing: {e}")

    def test_invalid_identifier(self):
        """Test that an invalid identifier raises an error."""
        with self.assertRaises(CDSClientError):
            self.client.lookup_entity_as_dataframe("invalid_id!!")

if __name__ == "__main__":
    unittest.main()
