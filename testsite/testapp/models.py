from django.db import models


class CustomQuerySet(models.QuerySet):
    def first(self):
        # Some overriden method - shouldn't show up in the output
        objs = list(self.all())
        if objs:
            return objs[0]


class Website(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()

    objects = models.Manager.from_queryset(CustomQuerySet)()

    def __str__(self):
        return self.name
