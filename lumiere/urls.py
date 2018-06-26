from django.urls import path
from django.views.generic import RedirectView
from lumiere.views import oauth2


urlpatterns = [
    path('', RedirectView.as_view(pattern_name='oauth2-start', permanent=False)),
    path('start/', oauth2.start, name='oauth2-start'),
    path('home/', oauth2.home, name='oauth2-redirect-return'),
    path('landing/', oauth2.landing, name='landing'),
    path('manual-token/', oauth2.manual_auth, name='manual-token'),

]
