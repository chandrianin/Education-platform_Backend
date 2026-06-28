from django.db import models


class Indicator(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    # коэффициент модальности Km
    modality_coefficient = models.FloatField()

    def __str__(self):
        return self.name


from django.contrib.auth.models import User


class IndicatorValue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE)

    score = models.FloatField()
    comment = models.TextField(blank=True)

    period = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'indicator', 'period'],
                name='unique_user_indicator_per_period'
            )
        ]
        indexes = [
            models.Index(fields=['period']),
            models.Index(fields=['user', 'period']),
        ]


class MonthlyEnvironmentIndex(models.Model):
    period = models.DateField(unique=True)

    index_value = models.FloatField()

    calculated_at = models.DateTimeField(auto_now_add=True)
