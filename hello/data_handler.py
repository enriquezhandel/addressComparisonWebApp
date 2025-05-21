import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import unicodedata

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

MONGO_URI = os.environ.get('MONGO_URI', '')
MONGO_DATABASE = os.environ.get('MONGO_DATABASE', '')
MONGO_COLLECTION = os.environ.get('MONGO_COLLECTION', '')

# DataHandler is responsible for fetching and normalizing MongoDB address data into a flat, tabular format.
class DataHandler:
    def __init__(self, data_source):
        """
        Initialize with a data source (e.g., MongoDBSource).
        """
        self.data_source = data_source

    def fetch_data(self, filter, projection):
        """
        Fetch data from the data source using the provided filter and projection.
        """
        return self.data_source.fetch_data(filter, projection)

    def normalize_addresses(self, data):
        """
        Normalize nested MongoDB address data into a flat pandas DataFrame.
        Applies ASCII normalization to all string fields for consistent encoding.
        """
        records = []
        for doc in data:
            _id = doc.get('_id')
            addresses = doc.get('d', {}).get('addresses', [])
            for address in addresses:
                localized = address.get('localizedAddresses', [])
                for loc in localized:
                    row = {'_id': _id}
                    reported = loc.get('reportedAddress', {})
                    standardized = loc.get('standardizedAddress', {})
                    # Extract and flatten reported and standardized address fields
                    row.update(self._extract_reported_fields(reported))
                    row.update(self._extract_standardized_fields(standardized))
                    # Normalize all string fields to ASCII
                    row = self._normalize_row(row)
                    records.append(row)
        return pd.DataFrame(records)

    def _extract_reported_fields(self, reported):
        """
        Extract and map reported address fields to flat keys.
        """
        return {
            'reportedAddress_addressLines': reported.get('addressLines'),
            'reportedAddress_city': reported.get('city'),
            'reportedAddress_phoneNumbers': reported.get('phoneNumbers'),
            'reportedAddress_faxNumbers': reported.get('faxNumbers'),
            'reportedAddress_postCode': reported.get('postCode'),
        }

    def _extract_standardized_fields(self, standardized):
        """
        Extract and map standardized address fields to flat keys.
        """
        return {
            'standardizedAddress_addressLines': standardized.get('addressLines'),
            'standardizedAddress_provider': standardized.get('provider'),
            'standardizedAddress_verificationCode': standardized.get('verificationCode'),
            'standardizedAddress_qualityIndex': standardized.get('qualityIndex'),
            'standardizedAddress_countryName': standardized.get('countryName'),
            'standardizedAddress_ISO31662': standardized.get('ISO31662'),
            'standardizedAddress_ISO31663': standardized.get('ISO31663'),
            'standardizedAddress_ISO3166N': standardized.get('ISO3166N'),
            'standardizedAddress_superAdministrativeArea': standardized.get('superAdministrativeArea'),
            'standardizedAddress_administrativeArea': standardized.get('administrativeArea'),
            'standardizedAddress_locality': standardized.get('locality'),
            'standardizedAddress_dependentLocality': standardized.get('dependentLocality'),
            'standardizedAddress_thoroughfare': standardized.get('thoroughfare'),
            'standardizedAddress_building': standardized.get('building'),
            'standardizedAddress_premise': standardized.get('premise'),
            'standardizedAddress_subBuilding': standardized.get('subBuilding'),
            'standardizedAddress_longitude': standardized.get('longitude'),
            'standardizedAddress_latitude': standardized.get('latitude'),
            'standardizedAddress_postalCode': standardized.get('postalCode'),
            'standardizedAddress_postalCodePrimary': standardized.get('postalCodePrimary'),
            'standardizedAddress_postBox': standardized.get('postBox'),
        }

    def _normalize_row(self, row):
        """
        Normalize all string and list-of-string fields in a row to closest English ASCII representation.
        Removes accents and special characters for consistent display (e.g., 'ç' -> 'c', 'ã' -> 'a', 'ú' -> 'u').
        Also removes or replaces any non-ASCII character with a close English equivalent.
        """
        normalized = {}
        for k, v in row.items():
            if isinstance(v, str):
                # Convert to closest ASCII representation
                ascii_str = unicodedata.normalize('NFKD', v).encode('ascii', 'ignore').decode('ascii')
                normalized[k] = ascii_str
            elif isinstance(v, list):
                norm_list = [unicodedata.normalize('NFKD', i).encode('ascii', 'ignore').decode('ascii') if isinstance(i, str) else i for i in v]
                normalized[k] = norm_list
            else:
                normalized[k] = v
        return normalized

# MongoDBSource abstracts MongoDB access and provides a fetch_data method for querying documents.
class MongoDBSource:
    def __init__(self, uri=None, database=None, collection=None):
        """
        Initialize MongoDB client and select database/collection.
        """
        self.client = MongoClient(uri or MONGO_URI)
        self.database = database or MONGO_DATABASE
        self.collection = collection or MONGO_COLLECTION

    def fetch_data(self, filter, projection):
        """
        Fetch documents from MongoDB using the given filter and projection.
        Returns a list of documents.
        """
        collection = self.client[self.database][self.collection]
        cursor = collection.find(filter=filter, projection=projection)
        return list(cursor)
