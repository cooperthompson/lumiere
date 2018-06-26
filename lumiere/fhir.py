import json

import requests

from lumiere.utils import discrete_url


def get_oauth2_urls(conformance):
    authorize_url = ''
    token_url = ''

    for extension in conformance['rest'][0]['security']['extension']:
        if extension['url'] == 'http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris':
            for oauth2_extension in extension['extension']:
                if oauth2_extension['url'] == 'authorize':
                    authorize_url = oauth2_extension['valueUri']
                if oauth2_extension['url'] == 'token':
                    token_url = oauth2_extension['valueUri']
    return authorize_url, token_url


def get_all_fhir_data(request, fhir_base, patient_id, access_token):

    fhir_content = []
    # Patient
    fhir_url = fhir_base + 'Patient/' + patient_id
    fhir_content.append(get_fhir_data(request, fhir_url, access_token, 'Patient'))

    # AllergyIntolerance
    fhir_url = fhir_base + 'AllergyIntolerance?patient=' + patient_id
    fhir_content.append(get_fhir_data(request, fhir_url, access_token, 'AllergyIntolerance'))

    # Condition
    fhir_url = fhir_base + 'Condition?patient=' + patient_id
    fhir_content.append(get_fhir_data(request, fhir_url, access_token, 'Condition'))

    # DiagnosticReport
    fhir_url = fhir_base + 'DiagnosticReport?patient=' + patient_id
    fhir_content.append(get_fhir_data(request, fhir_url, access_token, 'DiagnosticReport'))

    # Observation - labs
    fhir_url = fhir_base + 'Observation?patient=' + patient_id + '&category=laboratory'
    fhir_content.append(get_fhir_data(request, fhir_url, access_token, 'Observation'))

    # Immunization
    fhir_url = fhir_base + 'Immunization?patient=' + patient_id
    fhir_content.append(get_fhir_data(request, fhir_url, access_token, 'Immunization'))

    return fhir_content


def get_fhir_data(request, url, access_token, resource_name):
    request_session = requests.Session()
    fhir_resource = requests.Request(method='GET',
                                     url=url,
                                     headers={
                                         'Accept': 'application/json',
                                         'Authorization': 'Bearer {}'.format(access_token)
                                     }).prepare()
    fhir_response = request_session.send(
        fhir_resource,
        verify=False)

    resource_type = None
    response_json = None

    if fhir_response.status_code == 200 and fhir_response.text != "":
        response_json = json.loads(fhir_response.text)
        resource_type = response_json.get('resourceType')
    count = 1

    if resource_type == 'Bundle':
        resource_type = response_json.get('entry')[0].get('resource').get('resourceType')
        count = response_json.get('total')

    request.session['url_sequence'].append({
        'method': 'HTTP GET',
        'source': 'FHIR App',
        'target': 'Epic Interconnect',
        'tech': 'FHIR',
        'step': 'api',
        'url': discrete_url(url),
        'response': json.dumps(response_json, indent=4, sort_keys=True)
    })

    fhir_content = {
        'response': str(fhir_response),
        'name': resource_name,
        'body': json.dumps(response_json, indent=4, sort_keys=True),
        'count': count,
        'url': url
    }
    return fhir_content
