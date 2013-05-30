from django.db import models

class WatcherMetadata(models.Model):
    class Meta:
        app_label = "assetpipe"
    watcher_id = models.CharField(max_length=255, primary_key=True)
    last_run_at = models.DateTimeField(null=True)
