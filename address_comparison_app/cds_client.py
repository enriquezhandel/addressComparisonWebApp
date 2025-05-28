"""
CDS API client and service logic for Moody's Address Comparison WebApp
Handles authentication, token management, and entity/BVD lookups.
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Union
import logging
from .cds_config import CDSConfig

@dataclass
class Token:
    """Represents an authentication token with expiry."""
    value: str
    expires_at: datetime
    @property
    def is_expired(self) -> bool:
        """Check if the token is expired (with a 5-minute buffer)."""
        return datetime.now() >= (self.expires_at - timedelta(minutes=5))

class CDSClientError(Exception):
    """Base exception for CDS client errors."""
    pass
class AuthenticationError(CDSClientError):
    """Exception for authentication/token errors."""
    pass
class APIError(CDSClientError):
    """Exception for API errors (HTTP, data, etc)."""
    pass
class InvalidIdentifierError(CDSClientError):
    """Exception for invalid identifier formats."""
    pass

class IdentifierUtils:
    """Utility class for identifier validation and type detection."""
    @staticmethod
    def is_bvd_id(identifier: Union[str, int]) -> bool:
        """Check if identifier is a BVD ID format."""
        if isinstance(identifier, int): return False
        if not isinstance(identifier, str): return False
        return bool(any(c.isalpha() or c in ['*', '#', '&'] for c in str(identifier)))
    @staticmethod
    def is_entity_id(identifier: Union[str, int]) -> bool:
        """Check if identifier is a numeric entity ID."""
        try:
            int(identifier)
            return True
        except (ValueError, TypeError):
            return False
    @staticmethod
    def validate_identifier(identifier: Union[str, int]) -> str:
        """Return the identifier type or raise if invalid."""
        if IdentifierUtils.is_entity_id(identifier):
            return "entity_id"
        elif IdentifierUtils.is_bvd_id(identifier):
            return "bvd_id"
        else:
            raise InvalidIdentifierError(f"Invalid identifier format: {identifier}")

class TokenService:
    """Handles token generation, caching, and refresh for CDS API."""
    def __init__(self, config: CDSConfig):
        self.config = config
        self._token: Optional[Token] = None
        self._session = requests.Session()
        self.logger = logging.getLogger(__name__)
    def get_token(self) -> str:
        """Get a valid token, refreshing if needed."""
        if self._token is None or self._token.is_expired:
            self._refresh_token()
        return self._token.value
    def _refresh_token(self) -> None:
        """Request a new token from the CDS token service."""
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
    """Service for interacting with the CDS API for entity and BVD lookups."""
    def __init__(self, config: CDSConfig, token_service: TokenService):
        self.config = config
        self.token_service = token_service
        self._session = requests.Session()
        self.logger = logging.getLogger(__name__)
    def lookup_by_entity_id(self, entity_id: int) -> Dict[str, Any]:
        """Lookup entity data by numeric entity ID."""
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
        """Lookup entity data by BVD ID."""
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
        """Universal lookup by identifier (entity ID or BVD ID)."""
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
    """
    Flatten the nested CDS API response into a pandas DataFrame for tabular analysis.
    """
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

class CDSClient:
    """
    Main client for CDS operations with support for both Entity ID and BVD ID.
    Handles token management, API calls, and DataFrame conversion.
    """
    def __init__(self, config: Optional[CDSConfig] = None):
        self.config = config or CDSConfig.from_env()
        self.token_service = TokenService(self.config)
        self.cds_service = CDSService(self.config, self.token_service)
        self.logger = self._setup_logging()
    def lookup_entity(self, identifier: Union[str, int]) -> Dict[str, Any]:
        """Universal lookup for both entity ID and BVD ID."""
        return self.cds_service.lookup_value(identifier)
    def lookup_by_entity_id(self, entity_id: int) -> Dict[str, Any]:
        """Lookup by entity ID only."""
        return self.cds_service.lookup_by_entity_id(entity_id)
    def lookup_by_bvd_id(self, bvd_id: str) -> Dict[str, Any]:
        """Lookup by BVD ID only."""
        return self.cds_service.lookup_by_bvd_id(bvd_id)
    def lookup_entity_as_dataframe(self, identifier: Union[str, int]) -> pd.DataFrame:
        """Lookup and return results as a DataFrame."""
        result = self.lookup_entity(identifier)
        return explode_location_data(result)
    def lookup_multiple_entities(self, identifiers: List[Union[str, int]]) -> Dict[Union[str, int], Dict[str, Any]]:
        """Lookup multiple entities (mix of entity IDs and BVD IDs)."""
        results = {}
        for identifier in identifiers:
            try:
                results[identifier] = self.lookup_entity(identifier)
                self.logger.info(f"Successfully processed identifier: {identifier}")
            except Exception as e:
                self.logger.error(f"Failed to lookup identifier {identifier}: {e}")
                results[identifier] = {"error": str(e)}
        return results
    def lookup_multiple_entities_as_dataframe(self, identifiers: List[Union[str, int]]) -> pd.DataFrame:
        """Lookup multiple entities and return as a combined DataFrame."""
        all_dataframes = []
        for identifier in identifiers:
            try:
                result = self.lookup_entity(identifier)
                df = explode_location_data(result)
                identifier_type = IdentifierUtils.validate_identifier(identifier)
                df['lookup_identifier'] = str(identifier)
                df['lookup_type'] = identifier_type
                all_dataframes.append(df)
            except Exception as e:
                self.logger.error(f"Failed to lookup identifier {identifier}: {e}")
                error_df = pd.DataFrame([{
                    'lookup_identifier': str(identifier),
                    'lookup_type': 'error',
                    'error': str(e)
                }])
                all_dataframes.append(error_df)
        return pd.concat(all_dataframes, ignore_index=True) if all_dataframes else pd.DataFrame()
    @staticmethod
    def _setup_logging() -> logging.Logger:
        """Set up logging for the CDS client."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.token_service.__exit__(exc_type, exc_val, exc_tb)
        self.cds_service.__exit__(exc_type, exc_val, exc_tb)
    @staticmethod
    def split_list(lst, chunk_size):
        """Split a list into chunks of a specified size."""
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]
