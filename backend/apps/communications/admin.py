from django.contrib import admin

from .models import StoreAndForwardMessage, VideoSession

admin.site.register(VideoSession)
admin.site.register(StoreAndForwardMessage)
