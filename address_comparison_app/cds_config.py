"""
CDS API client integration for Django app
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

@dataclass
class CDSConfig:
    token_service: str
    api_name: str
    pe_token: str
    cookie_gt: str
    cookie_cds: str
    base_url_cds: str

    @classmethod
    def from_env(cls) -> 'CDSConfig':
        return cls(
            token_service=os.environ.get('MAPTokenService', ''),
            api_name=os.environ.get('ApiName', ''),
            pe_token=os.environ.get('PEToken', ''),
            cookie_gt=os.environ.get('CookieGT', ''),
            cookie_cds=os.environ.get('CookieCDS', ''),
            base_url_cds=os.environ.get('BasedURLCDS', '')
        )

# You can now use CDSConfig.from_env() to get all CDS API settings from .env
