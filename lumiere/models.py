from django.db import models


class OAuth2Clients(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    prod_client_id = models.CharField(max_length=36, null=True, blank=True)
    non_prod_client_id = models.CharField(max_length=36, null=True, blank=True)
    redirect_uri = models.URLField()
    active = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'lumiere_clients'
        verbose_name = "OAuth2 Client"

    def __str__(self):
        return "{} - {}".format(self.name, self.prod_client_id)