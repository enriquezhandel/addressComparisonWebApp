# views.py: Django views for MongoDB querying and display, following OOP and clean code principles.
from django.shortcuts import render
from django.http import HttpResponse
from .data_handler import DataHandler, MongoDBSource
import os

# Configuration for MongoDB connection (loaded from environment variables for security)
MONGO_CONFIG = {
    'uri': os.environ.get('MONGO_URI', ''),
    'database': os.environ.get('MONGO_DATABASE', ''),
    'collection': os.environ.get('MONGO_COLLECTION', '')
}

def hello_world(request):
    """
    Simple hello world endpoint for health check or landing page.
    """
    return HttpResponse("Hello, world!")

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
    return render(request, 'hello/mongo_query.html', context)
