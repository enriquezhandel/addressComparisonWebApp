"""
Django form for validating CDS lookup input (entity ID or BVD ID).
"""

from django import forms

class CDSLookupForm(forms.Form):
    """Form for CDS lookups by entity ID or BVD ID."""
    identifier = forms.CharField(
        label="Entity ID or BVD ID",
        max_length=64,
        required=True,
        help_text="Enter a numeric entity ID or a BVD ID (e.g. USFEI1018186, CA*S00222833)"
    )
    # Add more fields as needed for your CDS lookups

class DataSourceChoiceForm(forms.Form):
    DATA_SOURCE_CHOICES = [
        ("mongo", "MongoDB"),
        ("cds", "CDS API")
    ]
    data_source = forms.ChoiceField(
        choices=DATA_SOURCE_CHOICES,
        label="Select Data Source",
        required=True
    )
    identifier = forms.CharField(
        label="Entity ID or BVD ID (_id for MongoDB)",
        max_length=64,
        required=True,
        help_text="Enter a MongoDB _id, numeric entity ID, or a BVD ID."
    )
    loqate_filter = forms.BooleanField(
        label="LoqateAddressOnly (standardized_provider starts with 'L')",
        required=False,
        initial=False
    )
