from django.http import HttpResponse
from django.template import loader
from django.conf import settings


def home(request):
    template = loader.get_template('home.html')
    context = {
    }
    return HttpResponse(template.render(context, request))
