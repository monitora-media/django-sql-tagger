from django.db import models

import django_sql_tagger


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

    def save(self, *args, **kwargs):
        # Some overriden method - shouldn't show up in the output
        return super().save(*args, **kwargs)


@django_sql_tagger.ignore_below
def ignored_save(website):
    # some method calling save - shouldn't show up in the output
    return ignored_save_intermediary(website)


def ignored_save_intermediary(website):
    # some method calling save - shouldn't show up in the output
    return website.save()
