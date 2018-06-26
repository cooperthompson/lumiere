from django import forms


class ManualTokenForm(forms.Form):
    iss = forms.URLField(
        label='FHIR Base URL',
        required=False
    )
    patient_fhir_id = forms.CharField(
        label='Patient FHIR ID',
        required=True
    )
    access_token = forms.CharField(
        label='Access Token',
        required=True
    )
