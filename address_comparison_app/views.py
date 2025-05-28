# views.py: Django views for MongoDB querying and display, following OOP and clean code principles.
from django.shortcuts import render
from django.http import HttpResponse
from .data_handler import DataHandler, MongoDBSource
from .cds_config import CDSConfig
from .cds_client import CDSClient, CDSClientError
from .forms import CDSLookupForm, DataSourceChoiceForm
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Union
import logging

# Configuration for MongoDB connection (loaded from environment variables for security)
MONGO_CONFIG = {
    'uri': os.environ.get('MONGO_URI', ''),
    'database': os.environ.get('MONGO_DATABASE', ''),
    'collection': os.environ.get('MONGO_COLLECTION', '')
}

@dataclass
class Token:
    value: str
    expires_at: datetime
    @property
    def is_expired(self) -> bool:
        return datetime.now() >= (self.expires_at - timedelta(minutes=5))

class CDSClientError(Exception): pass
class AuthenticationError(CDSClientError): pass
class APIError(CDSClientError): pass
class InvalidIdentifierError(CDSClientError): pass

class IdentifierUtils:
    @staticmethod
    def is_bvd_id(identifier: Union[str, int]) -> bool:
        if isinstance(identifier, int): return False
        if not isinstance(identifier, str): return False
        return bool(any(c.isalpha() or c in ['*', '#', '&'] for c in str(identifier)))
    @staticmethod
    def is_entity_id(identifier: Union[str, int]) -> bool:
        try:
            int(identifier)
            return True
        except (ValueError, TypeError):
            return False
    @staticmethod
    def validate_identifier(identifier: Union[str, int]) -> str:
        if IdentifierUtils.is_entity_id(identifier):
            return "entity_id"
        elif IdentifierUtils.is_bvd_id(identifier):
            return "bvd_id"
        else:
            raise InvalidIdentifierError(f"Invalid identifier format: {identifier}")

class TokenService:
    def __init__(self, config: CDSConfig):
        self.config = config
        self._token: Optional[Token] = None
        self._session = requests.Session()
        self.logger = logging.getLogger(__name__)
    def get_token(self) -> str:
        if self._token is None or self._token.is_expired:
            self._refresh_token()
        return self._token.value
    def _refresh_token(self) -> None:
        try:
            payload = {"audience": self.config.api_name}
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {self.config.pe_token}',
                'Cookie': self.config.cookie_gt
            }
            response = self._session.post(
                self.config.token_service,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            response_data = response.json()
            if 'token' not in response_data:
                raise AuthenticationError("Token not found in response")
            expires_at = datetime.now() + timedelta(hours=1)
            self._token = Token(response_data['token'], expires_at)
            self.logger.info("Token refreshed successfully")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to generate token: {e}")
            raise AuthenticationError(f"Token generation failed: {e}")
        except (KeyError, ValueError) as e:
            self.logger.error(f"Invalid token response: {e}")
            raise AuthenticationError(f"Invalid token response: {e}")
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): self._session.close()

class CDSService:
    def __init__(self, config: CDSConfig, token_service: TokenService):
        self.config = config
        self.token_service = token_service
        self._session = requests.Session()
        self.logger = logging.getLogger(__name__)
    def lookup_by_entity_id(self, entity_id: int) -> Dict[str, Any]:
        if not isinstance(entity_id, int) or entity_id <= 0:
            raise ValueError("Entity ID must be a positive integer")
        try:
            token = self.token_service.get_token()
            url = f"{self.config.base_url_cds}legalentities/firmographics/locations"
            params = {"entityid": entity_id}
            headers = {
                'Authorization': f'Bearer {token}',
                'Cookie': self.config.cookie_cds,
                'Accept': 'application/json'
            }
            response = self._session.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()
            self.logger.info(f"Successfully retrieved data for entity ID: {entity_id}")
            return result
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired token")
            elif response.status_code == 404:
                raise APIError(f"Entity ID {entity_id} not found")
            else:
                raise APIError(f"HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for entity ID {entity_id}: {e}")
            raise APIError(f"Request failed: {e}")
        except ValueError as e:
            self.logger.error(f"Invalid response format: {e}")
            raise APIError(f"Invalid response format: {e}")
    def lookup_by_bvd_id(self, bvd_id: str) -> Dict[str, Any]:
        if not isinstance(bvd_id, str) or not bvd_id.strip():
            raise ValueError("BVD ID must be a non-empty string")
        try:
            token = self.token_service.get_token()
            url = f"{self.config.base_url_cds}legalentities/firmographics/locations"
            params = {"bvdid": bvd_id}
            headers = {
                'Authorization': f'Bearer {token}',
                'Cookie': self.config.cookie_cds,
                'Accept': 'application/json'
            }
            response = self._session.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()
            self.logger.info(f"Successfully retrieved data for BVD ID: {bvd_id}")
            return result
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired token")
            elif response.status_code == 404:
                raise APIError(f"BVD ID {bvd_id} not found")
            else:
                raise APIError(f"HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for BVD ID {bvd_id}: {e}")
            raise APIError(f"Request failed: {e}")
        except ValueError as e:
            self.logger.error(f"Invalid response format: {e}")
            raise APIError(f"Invalid response format: {e}")
    def lookup_value(self, identifier: Union[str, int]) -> Dict[str, Any]:
        identifier_type = IdentifierUtils.validate_identifier(identifier)
        if identifier_type == "entity_id":
            return self.lookup_by_entity_id(int(identifier))
        elif identifier_type == "bvd_id":
            return self.lookup_by_bvd_id(str(identifier))
        else:
            raise InvalidIdentifierError(f"Unsupported identifier type: {identifier_type}")
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): self._session.close()

def explode_location_data(api_response: Dict[str, Any]) -> pd.DataFrame:
    all_rows = []
    for entity in api_response.get('data', []):
        entity_id = entity.get('entityId')
        bvd_id = entity.get('bvdId')
        for location in entity.get('locations', []):
            categories = location.get('categories', [])
            category_code = categories[0].get('code') if categories else None
            category_label = categories[0].get('label') if categories else None
            for address in location.get('addresses', []):
                reported = address.get('reported', {})
                standardized = address.get('standardized', {})
                row = {
                    'entity_id': entity_id,
                    'bvd_id': bvd_id,
                    'location_category_code': category_code,
                    'location_category_label': category_label,
                    'reported_address_lines': ', '.join(reported.get('addressLines', [])),
                    'reported_city': reported.get('city'),
                    'reported_post_code': reported.get('postCode'),
                    'reported_country_code': reported.get('country', {}).get('code'),
                    'reported_country_label': reported.get('country', {}).get('label'),
                    'reported_phone_numbers': ', '.join(reported.get('phoneNumbers', [])),
                    'reported_fax_numbers': ', '.join(reported.get('faxNumbers', [])),
                    'standardized_address_lines': ', '.join(standardized.get('addressLines', [])),
                    'standardized_provider': standardized.get('provider'),
                    'standardized_verification_code': standardized.get('verificationCode'),
                    'standardized_quality_index': standardized.get('qualityIndex'),
                    'standardized_country_name': standardized.get('countryName'),
                    'standardized_iso31662': standardized.get('iso31662'),
                    'standardized_iso31663': standardized.get('iso31663'),
                    'standardized_iso3166n': standardized.get('iso3166N'),
                    'standardized_super_admin_area': standardized.get('superAdministrativeArea'),
                    'standardized_admin_area': standardized.get('administrativeArea'),
                    'standardized_sub_admin_area': standardized.get('subAdministrativeArea'),
                    'standardized_locality': standardized.get('locality'),
                    'standardized_thoroughfare': standardized.get('thoroughfare'),
                    'standardized_building': standardized.get('building'),
                    'standardized_premise': standardized.get('premise'),
                    'standardized_postal_code': standardized.get('postalCode'),
                    'standardized_postal_code_primary': standardized.get('postalCodePrimary'),
                    'standardized_post_box': standardized.get('postBox'),
                    'standardized_longitude': standardized.get('longitude'),
                    'standardized_latitude': standardized.get('latitude')
                }
                all_rows.append(row)
    return pd.DataFrame(all_rows)

def health_check(request):
    """
    Simple health check endpoint for the application.
    """
    return HttpResponse("OK")

def mongo_query_view(request):
    """
    Main view for querying MongoDB and displaying normalized address data in a table.
    Adds a checkbox filter for standardizedAddress_provider (LoqateAddress: only rows with 'L').
    """
    context = {'result': None, 'error': None}
    uri = MONGO_CONFIG['uri']
    database = MONGO_CONFIG['database']
    collection = MONGO_CONFIG['collection']
    filter_dict = {}
    projection_dict = {}
    columns = [
        '_id',
        'reportedAddress_addressLines', 'reportedAddress_city', 'reportedAddress_phoneNumbers', 'reportedAddress_faxNumbers', 'reportedAddress_postCode',
        'standardizedAddress_addressLines', 'standardizedAddress_provider', 'standardizedAddress_verificationCode', 'standardizedAddress_qualityIndex',
        'standardizedAddress_countryName', 'standardizedAddress_ISO31662', 'standardizedAddress_ISO31663', 'standardizedAddress_ISO3166N',
        'standardizedAddress_superAdministrativeArea', 'standardizedAddress_administrativeArea', 'standardizedAddress_locality',
        'standardizedAddress_dependentLocality', 'standardizedAddress_thoroughfare', 'standardizedAddress_building', 'standardizedAddress_premise',
        'standardizedAddress_subBuilding', 'standardizedAddress_longitude', 'standardizedAddress_latitude', 'standardizedAddress_postalCode',
        'standardizedAddress_postalCodePrimary', 'standardizedAddress_postBox'
    ]
    loqate_checked = False
    if request.method == 'POST':
        ids = request.POST.get('ids', '')
        values = [v.strip() for v in ids.split(',') if v.strip()]
        loqate_checked = request.POST.get('loqate_filter') == 'on'
        if values:
            filter_dict = {'_id': {'$in': values}}
        projection_dict = {
            'd.addresses.localizedAddresses.standardizedAddress': 1,
            'd.addresses.localizedAddresses.reportedAddress': 1
        }
        try:
            # Use OOP data access and normalization
            source = MongoDBSource(uri, database, collection)
            handler = DataHandler(source)
            data = handler.fetch_data(filter_dict, projection_dict)
            df = handler.normalize_addresses(data)
            # Apply LoqateAddress filter if checked
            if loqate_checked:
                df = df[df['standardizedAddress_provider'].astype(str).str.startswith('L', na=False)]
            # Ensure all columns exist in the DataFrame
            for col in columns:
                if col not in df.columns:
                    df[col] = ''
            # Always show all columns in the UI
            df = df[columns]
            result = df.to_dict(orient='records')
            context['result'] = result
            # Group by _id for address comparison
            grouped_result = []
            if result:
                from collections import defaultdict
                group_map = defaultdict(list)
                for row in result:
                    group_map[row.get('_id', 'N/A')].append(row)
                for _id, addresses in group_map.items():
                    grouped_result.append({'id': _id, 'addresses': addresses})
            context['grouped_result'] = grouped_result
        except Exception as e:
            context['error'] = str(e)
    context.update({
        'columns': columns,
        'selected_columns': columns,
        'loqate_checked': loqate_checked
    })
    # Address Comparison for MongoDB: group by _id and extract comparison fields
    address_comparison = []
    if context.get('result'):
        from collections import defaultdict
        group_map = defaultdict(list)
        for row in context['result']:
            group_map[row.get('_id', 'N/A')].append(row)
        for _id, addresses in group_map.items():
            comparison_rows = []
            for addr in addresses:
                comparison_rows.append({
                    # Map Mongo fields to the CDS-style keys for template compatibility
                    'reported_address_lines': addr.get('reportedAddress_addressLines', ''),
                    'standardized_address_lines': addr.get('standardizedAddress_addressLines', ''),
                    'reported_city': addr.get('reportedAddress_city', ''),
                    'standardized_locality': addr.get('standardizedAddress_locality', ''),
                    'reported_post_code': addr.get('reportedAddress_postCode', ''),
                    'standardized_postal_code': addr.get('standardizedAddress_postalCode', ''),
                    # Mongo does not have country fields in this context, but add empty for template compatibility
                    'reported_country_label': '',
                    'standardized_country_name': ''
                })
            address_comparison.append({'id': _id, 'addresses': comparison_rows})
    context['address_comparison'] = address_comparison
    return render(request, 'address_comparison_app/mongo_query.html', context)

def cds_lookup_view(request):
    """
    View for looking up CDS data by entity ID or BVD ID using a Django form.
    """
    result = None
    error = None
    if request.method == 'POST':
        form = CDSLookupForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['identifier']
            try:
                with CDSClient() as client:
                    result = client.lookup_entity_as_dataframe(identifier)
            except CDSClientError as e:
                error = str(e)
        else:
            error = 'Invalid input.'
    else:
        form = CDSLookupForm()
    return render(request, 'address_comparison_app/cds_lookup.html', {'form': form, 'result': result, 'error': error})

def unified_lookup_view(request):
    """
    Unified view for selecting data source (MongoDB or CDS API) and extracting data.
    Includes LoqateAddressOnly checkbox filter for standardized_provider.
    """
    result = None
    error = None
    columns = []
    loqate_checked = False
    if request.method == 'POST':
        form = DataSourceChoiceForm(request.POST)
        if form.is_valid():
            data_source = form.cleaned_data['data_source']
            identifier = form.cleaned_data['identifier']
            loqate_checked = form.cleaned_data.get('loqate_filter', False)
            try:
                if data_source == 'mongo':
                    from .data_handler import DataHandler, MongoDBSource
                    uri = MONGO_CONFIG['uri']
                    database = MONGO_CONFIG['database']
                    collection = MONGO_CONFIG['collection']
                    source = MongoDBSource(uri, database, collection)
                    handler = DataHandler(source)
                    filter_dict = {'_id': identifier}
                    projection_dict = {
                        'd.addresses.localizedAddresses.standardizedAddress': 1,
                        'd.addresses.localizedAddresses.reportedAddress': 1
                    }
                    data = handler.fetch_data(filter_dict, projection_dict)
                    df = handler.normalize_addresses(data)
                    if loqate_checked:
                        df = df[df['standardizedAddress_provider'].astype(str).str.startswith('L', na=False)]
                    # Only keep the columns needed for Mongo address comparison
                    columns = [
                        '_id',
                        'reportedAddress_addressLines',
                        'reportedAddress_city',
                        'reportedAddress_postCode',
                        'standardizedAddress_addressLines',
                        'standardizedAddress_locality',
                        'standardizedAddress_postalCode'
                    ]
                    for col in columns:
                        if col not in df.columns:
                            df[col] = ''
                    df = df[columns]
                    result = df.to_dict(orient='records')
                    # Address Comparison for MongoDB
                    from collections import defaultdict
                    group_map = defaultdict(list)
                    for row in result:
                        group_map[row.get('_id', 'N/A')].append(row)
                    address_comparison = []
                    for _id, addresses in group_map.items():
                        comparison_rows = []
                        for addr in addresses:
                            comparison_rows.append({
                                # Map Mongo fields to the CDS-style keys for template compatibility
                                'reported_address_lines': addr.get('reportedAddress_addressLines', ''),
                                'standardized_address_lines': addr.get('standardizedAddress_addressLines', ''),
                                'reported_city': addr.get('reportedAddress_city', ''),
                                'standardized_locality': addr.get('standardizedAddress_locality', ''),
                                'reported_post_code': addr.get('reportedAddress_postCode', ''),
                                'standardized_postal_code': addr.get('standardizedAddress_postalCode', ''),
                                # Mongo does not have country fields in this context, but add empty for template compatibility
                                'reported_country_label': '',
                                'standardized_country_name': ''
                            })
                        address_comparison.append({'id': _id, 'addresses': comparison_rows})
                elif data_source == 'cds':
                    from .cds_client import CDSClient, CDSClientError
                    with CDSClient() as client:
                        df = client.lookup_entity_as_dataframe(identifier)
                        if loqate_checked and 'standardized_provider' in df.columns:
                            df = df[df['standardized_provider'].astype(str).str.startswith('L', na=False)]
                        columns = df.columns.tolist()
                        result = df.to_dict(orient='records')
                        # Address Comparison for CDS API
                        address_comparison = []
                        if not df.empty:
                            comparison_rows = []
                            for _, addr in df.iterrows():
                                comparison_rows.append({
                                    'reported_address_lines': addr.get('reported_address_lines', ''),
                                    'standardized_address_lines': addr.get('standardized_address_lines', ''),
                                    'reported_city': addr.get('reported_city', ''),
                                    'standardized_locality': addr.get('standardized_locality', ''),
                                    'reported_post_code': addr.get('reported_post_code', ''),
                                    'standardized_postal_code': addr.get('standardized_postal_code', ''),
                                    'reported_country_label': addr.get('reported_country_label', ''),
                                    'standardized_country_name': addr.get('standardized_country_name', '')
                                })
                            address_comparison.append({'id': identifier, 'addresses': comparison_rows})
            except Exception as e:
                error = str(e)
        else:
            error = 'Invalid input.'
    else:
        form = DataSourceChoiceForm()
        address_comparison = []
    return render(request, 'address_comparison_app/unified_lookup.html', {'form': form, 'result': result, 'columns': columns, 'error': error, 'loqate_checked': loqate_checked, 'address_comparison': address_comparison})

# Example usage of CDSConfig in a Django view or utility:
# cds_config = CDSConfig.from_env()
# print(cds_config.token_service)
# You can now use cds_config to initialize your CDS API client logic.
