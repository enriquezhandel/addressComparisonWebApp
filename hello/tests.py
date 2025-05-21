from django.test import TestCase
import unittest
from unittest.mock import MagicMock, patch
from .data_handler import DataHandler, MongoDBSource
from django.test import RequestFactory, TestCase
from . import views

class DataHandlerTests(unittest.TestCase):
    def setUp(self):
        self.mock_source = MagicMock()
        self.handler = DataHandler(self.mock_source)

    def test_normalize_row_ascii(self):
        row = {'city': 'Málaga', 'list': ['niño', 'año'], 'num': 5}
        norm = self.handler._normalize_row(row)
        self.assertEqual(norm['city'], 'Malaga')
        self.assertEqual(norm['list'], ['nino', 'ano'])
        self.assertEqual(norm['num'], 5)

    def test_extract_reported_fields(self):
        reported = {'addressLines': 'A', 'city': 'B', 'phoneNumbers': 'C', 'faxNumbers': 'D', 'postCode': 'E'}
        out = self.handler._extract_reported_fields(reported)
        self.assertEqual(out['reportedAddress_city'], 'B')

    def test_extract_standardized_fields(self):
        standardized = {'addressLines': 'A', 'provider': 'L', 'locality': 'C', 'postalCode': 'D'}
        out = self.handler._extract_standardized_fields(standardized)
        self.assertEqual(out['standardizedAddress_provider'], 'L')
        self.assertEqual(out['standardizedAddress_locality'], 'C')

    def test_normalize_addresses_empty(self):
        df = self.handler.normalize_addresses([])
        self.assertTrue(df.empty)

class MongoDBSourceTests(unittest.TestCase):
    @patch('hello.data_handler.MongoClient')
    def test_fetch_data(self, mock_client):
        mock_collection = MagicMock()
        mock_collection.find.return_value = [{'_id': '1'}]
        mock_client.return_value.__getitem__.return_value.__getitem__.return_value = mock_collection
        source = MongoDBSource('uri', 'db', 'coll')
        docs = source.fetch_data({}, {})
        self.assertEqual(docs, [{'_id': '1'}])

class GetItemFilterTests(unittest.TestCase):
    def test_get_item(self):
        from .templatetags.custom_filters import get_item
        d = {'a': 1}
        self.assertEqual(get_item(d, 'a'), 1)
        self.assertEqual(get_item(d, 'b'), '')

class ViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch('hello.views.DataHandler')
    @patch('hello.views.MongoDBSource')
    def test_mongo_query_view_post(self, MockSource, MockHandler):
        mock_handler = MockHandler.return_value
        mock_handler.fetch_data.return_value = []
        mock_handler.normalize_addresses.return_value = MagicMock(to_dict=lambda orient: [])
        request = self.factory.post('/hello/mongo/', {'ids': '123', 'loqate_filter': 'on'})
        response = views.mongo_query_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Results', response.content)

    def test_hello_world(self):
        request = self.factory.get('/hello/')
        response = views.hello_world(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hello, world!', response.content)
