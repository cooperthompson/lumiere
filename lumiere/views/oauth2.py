import json

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
import urllib.parse
import urllib.request
import requests
from django.views.decorators.clickjacking import xframe_options_exempt

from lumiere import oauth2
from lumiere import fhir
from lumiere.fhir import get_all_fhir_data
from lumiere.forms.token_form import ManualTokenForm
from lumiere.models import *
from lumiere.utils import discrete_url


def start(request):
    """
    Test URL:
     http://127.0.0.1:8000/start?iss=https%3A%2F%2Fvs-icx18-25%2FInterconnect-FHIR-CDE-Unsecured%2Fapi%2FFHIR%2FDSTU2%2F&launch=token
    """
    launch_token = request.GET.get('launch')
    iss = request.GET.get('iss')

    request.session['url_sequence'] = []
    request.session['url_sequence'].append({
        'method': 'HTTP GET',
        'source': 'Epic Hyperspace',
        'target': 'FHIR App',
        'tech': 'SMART',
        'step': 'launch',
        'url': discrete_url(request.build_absolute_uri())
    })

    if iss is None or launch_token is None:
        return parameter_error(request, iss, launch_token)

    if not iss.endswith('/'):
        iss = "{}/".format(iss)

    # ==> Retrieve the OAuth2 authorize and token endpoints from the Conformance statement
    fhir_metadata_url = urllib.parse.urljoin(iss, "metadata")
    conformance_request = requests.get(url=fhir_metadata_url,
                                       headers={
                                           'Accept': 'application/json',
                                       },
                                       verify=False)
    conformance = json.loads(conformance_request.text)
    authorize_url, token_url = fhir.get_oauth2_urls(conformance)

    client = OAuth2Clients.objects.filter(active=True)[0]
    client_id = client.non_prod_client_id
    redirect_uri = request.build_absolute_uri(reverse('oauth2-redirect-return'))

    # save interesting information into the session for later
    request.session['iss'] = iss
    request.session['client_id'] = client_id
    request.session['launch_token'] = launch_token
    request.session['redirect_uri'] = redirect_uri
    request.session['metadata'] = fhir_metadata_url
    request.session['authorize_url'] = authorize_url
    request.session['token_url'] = token_url

    # ==> Exchange the launch token for an access code using the authorize endpoint
    return oauth2.redeem_launch_token(request,
                                      authorize_url,
                                      launch_token,
                                      client_id,
                                      redirect_uri,
                                      state=request.COOKIES.get('sessionid'))


def parameter_error(request, iss, launch_token):
    template = loader.get_template('oauth2_launch_error.html')
    context = {
        'iss': iss,
        'launch_token': launch_token
    }
    return HttpResponse(template.render(context, request), status=400)


def home(request):
    request.session = SessionStore(session_key=request.GET.get('state'))
    request.session['auth_code'] = request.GET.get('code')
    if request.session.get('access_token'):
        del request.session['access_token']

    request.session['url_sequence'].append({
        'method': '302-Redirect',
        'source': 'Epic Interconnect',
        'target': 'FHIR App',
        'tech': 'SMART',
        'step': 'auth',
        'url': discrete_url(request.build_absolute_uri())
    })

    request.session['state'] = request.GET.get('state')
    return HttpResponseRedirect(reverse('landing'))


@xframe_options_exempt
def landing(request):
    token_url = request.session.get('token_url')
    fhir_base = request.session.get('iss')

    if not token_url:
        template = loader.get_template('home.html')
        return HttpResponse(template.render({}, request))

    if request.session.get('access_token') is None:
        token_response = oauth2.redeem_auth_code(request,
                                                 token_url,
                                                 request.session.get('client_id'),
                                                 request.session.get('redirect_uri'),
                                                 request.session.get('auth_code'))

        token_response = json.loads(token_response.text)
        request.session['access_token'] = token_response.get('access_token')
        request.session['patient_id'] = token_response.get('patient')
        request.session['token_json'] = json.dumps(token_response, indent=4, sort_keys=True)

    if request.session['patient_id'] is None:
        # Hard coded default for now because RIS_PACS_REDIRECTOR is busted in CDE.
        request.session['patient_id'] = settings.DEFAULT_FHIR_PATIENT

    fhir_content = get_all_fhir_data(request, fhir_base, request.session.get('patient_id'), request.session['access_token'])

    template = loader.get_template('home.html')
    context = {
        'oauth2_info': request.session,
        'session': request.session,
        'payload': fhir_content,
        'fhir_content': fhir_content
    }
    return HttpResponse(template.render(context, request))


def manual_auth(request):
    if request.method == 'POST':
        manual_token_form = ManualTokenForm(request.POST)
        if manual_token_form.is_valid():
            request.session['iss'] = manual_token_form.cleaned_data['iss']
            request.session['patient_fhir_id'] = manual_token_form.cleaned_data['patient_fhir_id']
            request.session['access_token'] = manual_token_form.cleaned_data['access_token']

            url = manual_token_form.cleaned_data['iss'] + 'Patient/' + manual_token_form.cleaned_data['patient_fhir_id']
            fhir_content = fhir.get_all_fhir_data(url, manual_token_form.cleaned_data['access_token'])
            return fhir_response(request, fhir_content)
    else:
        manual_token_form = ManualTokenForm(initial={
            'iss': request.session.get('iss'),
            'patient_fhir_id': request.session.get('patient_fhir_id'),
            'access_token': request.session.get('access_token')
        })


    template = loader.get_template('manual_token_form.html')
    context = {
        'manual_token_form': manual_token_form
    }
    return HttpResponse(template.render(context, request))


def fhir_response(request, fhir_content):
    template = loader.get_template('fhir_browser.html')
    context = {
        'oauth2_info': request.session,
        'session': request.session,
        'fhir_content': fhir_content
    }
    return HttpResponse(template.render(context, request))