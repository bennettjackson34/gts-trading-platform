from django.db import models
# python manage.py makemigrations server
# python manage.py migrate

class Trades(models.Model):
    asset = models.CharField(max_length=50)
    direction = models.IntegerField()
    entry_price = models.IntegerField()
    exit_price = models.IntegerField()
    risk_price = models.IntegerField()
    target_price = models.IntegerField()

    def __str__(self):
        direction = "long" if self.direction == 1 else "short"

        return self.asset + " " + direction
