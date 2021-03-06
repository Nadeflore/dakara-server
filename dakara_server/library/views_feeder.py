from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from library import models
from library import serializers
from library import permissions


class FeederListView(ListAPIView):

    permission_classes = [IsAuthenticated, permissions.IsLibraryManager]
    queryset = models.Song.objects.all()
    serializer_class = serializers.SongOnlyFilePathSerializer
    pagination_class = None
