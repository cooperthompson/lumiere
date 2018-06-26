from django.contrib import admin

from lumiere.models import *


class OAuth2ClientAdmin(admin.ModelAdmin):
    list_display = [field.name for field in OAuth2Clients._meta.fields if field.name != "id"]
    list_editable = ('active',)


admin.site.register(OAuth2Clients, OAuth2ClientAdmin)

admin.site.site_title = 'Lumiere admin'
admin.site.site_header = 'Lumiere admin'
