import json

import requests
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

from lumiere.utils import discrete_url


def redeem_launch_token(request, authorize_url, launch_token, client_id, redirect_uri, state):
    query_params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'launch': launch_token,
        'scope': 'launch',
        'state': state,
        'aud': request.GET.get('iss')
    }
    authorize_request = requests.Request(url=authorize_url, params=query_params).prepare()

    request.session['auth_redirect'] = authorize_request.url

    request.session['url_sequence'].append({
        'method': '302-Redirect',
        'source': 'FHIR App',
        'target': 'Epic Interconnect',
        'tech': 'SMART',
        'step': 'authorize',
        'url': discrete_url(authorize_request.url),
    })

    if request.GET.get("debug"):
        context = {
            'authorize_url': authorize_request.url,
            'iss': request.GET.get('iss'),
            'launch_token': launch_token
        }
        template = loader.get_template('manual_redirect.html')
        return HttpResponse(template.render(context, request))
    return HttpResponseRedirect(authorize_request.url)


def redeem_auth_code(request, token_url, client_id, redirect_uri, auth_code):
    query_params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
        'code': auth_code
    }

    token_request = requests.Request(method='POST',
                                     url=token_url,
                                     headers={
                                         'Accept': 'application/json',
                                     },
                                     data=query_params)
    prepared_request = token_request.prepare()
    request_session = requests.Session()
    token_response = request_session.send(prepared_request,
                                          verify=False)

    response_json = json.loads(token_response.text)

    request.session['url_sequence'].append({
        'method': 'HTTP POST',
        'source': 'FHIR App',
        'target': 'Epic Interconnect',
        'tech': 'SMART',
        'step': 'token',
        'url': discrete_url(token_url),
        'request': query_params,
        'response': json.dumps(response_json, indent=4, sort_keys=True)
    })

    return token_response

