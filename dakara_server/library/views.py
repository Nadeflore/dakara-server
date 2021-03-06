from django.db.models.functions import Lower
from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
    ListCreateAPIView,
    ListAPIView,
)

from internal import permissions as internal_permissions
from library import models
from library import serializers
from library import permissions
from library.query_language import QueryLanguageParser
from library import views_feeder as feeder  # noqa F401


UserModel = get_user_model()


class ListCreateAPIViewWithQueryParsed(ListCreateAPIView):
    """API View with a parsed query attribute
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.query_parsed = None

    def list(self, request, *args, **kwargs):
        """Add the parsed query to the serialized response
        """
        response = super().list(request, *args, **kwargs)

        # pass the query words to highlight to the response
        # the words have been passed to the object in the get_queryset method
        # now, they have to be passed to the response
        # this is why this function in overloaded
        if self.query_parsed is not None:
            response.data["query"] = self.query_parsed

        return response


class SongListView(ListCreateAPIViewWithQueryParsed):
    """List of songs
    """

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    serializer_class = serializers.SongSerializer

    def get_queryset(self):
        """Search and filter the songs
        """
        query_set = models.Song.objects.all()

        # hide all songs with disabled tags for non-managers or non-superusers
        user = self.request.user
        if not (user.is_superuser or user.is_library_manager):
            query_set = query_set.exclude(tags__disabled=True)

        # if 'query' is in the query string then perform search otherwise
        # return all songs
        if "query" not in self.request.query_params:
            return query_set.order_by(Lower("title"))

        query = self.request.query_params.get("query", None)
        if query:
            # the query can use a syntax, the query language, to specify which
            # term to search and where
            # the language manages the simple search as well the parser is
            # provided from query_language.py
            language_parser = QueryLanguageParser()
            res = language_parser.parse(query)
            query_list = []
            query_list_many = []
            # specific terms of the research, i.e. artists, works and titles
            for artist in res["artist"]["contains"]:
                query_list_many.append(Q(artists__name__icontains=artist))

            for artist in res["artist"]["exact"]:
                query_list_many.append(Q(artists__name__iexact=artist))

            for title in res["title"]["contains"]:
                query_list.append(Q(title__icontains=title))

            for title in res["title"]["exact"]:
                query_list.append(Q(title__iexact=title))

            for work in res["work"]["contains"]:
                query_list.append(
                    Q(works__title__icontains=work)
                    | Q(works__alternative_title__title__icontains=work)
                )

            for work in res["work"]["exact"]:
                query_list.append(
                    Q(works__title__iexact=work)
                    | Q(works__alternative_title__title__iexact=work)
                )

            # specific terms of the research derivating from work
            for query_name, search_keywords in res["work_type"].items():
                for keyword in search_keywords["contains"]:
                    query_list.append(
                        (
                            Q(works__title__icontains=keyword)
                            | Q(
                                works__alternative_title__title__icontains=keyword
                            )  # noqa E501
                        )
                        & Q(works__work_type__query_name=query_name)
                    )

                for keyword in search_keywords["exact"]:
                    query_list.append(
                        (
                            Q(works__title__iexact=keyword)
                            | Q(works__alternative_title__title__iexact=keyword)
                        )
                        & Q(works__work_type__query_name=query_name)
                    )

                # one may want to factor the duplicated query on the work type
                # but it is very unlikely someone will define severals animes
                # (by instance) for a song at the same time
                # IMHO a factorization will make the code less clear and just
                # heavier, for no practical reason

            # unspecific terms of the research
            for remain in res["remaining"]:
                query_list.append(
                    Q(title__icontains=remain)
                    | Q(artists__name__icontains=remain)
                    | Q(works__title__icontains=remain)
                    | Q(works__alternative_title__title__icontains=remain)
                    | Q(version__icontains=remain)
                    | Q(detail__icontains=remain)
                    | Q(detail_video__icontains=remain)
                )

            # tags
            for tag in res["tag"]:
                query_list_many.append(Q(tags__name=tag))

            # now, gather the query objects
            filter_query = Q()
            for item in query_list:
                filter_query &= item

            query_set = query_set.filter(filter_query)
            # gather the query objects involving custom many to many relation
            for item in query_list_many:
                query_set = query_set.filter(item)

            # saving the parsed query to give it back to the client
            self.query_parsed = res

        return query_set.distinct().order_by(Lower("title"))

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        data = kwargs.get("data")
        many = kwargs.get("many")

        # check if the serializer is used to deserialize data
        # and check if the data is a list
        if data and isinstance(data, list) and many is None:
            return super().get_serializer(*args, many=True, **kwargs)

        # otherwise
        return super().get_serializer(*args, **kwargs)


class SongView(RetrieveUpdateDestroyAPIView):
    """Edition and display of a song
    """

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    queryset = models.Song.objects.all()
    serializer_class = serializers.SongSerializer


class ArtistListView(ListCreateAPIViewWithQueryParsed):
    """List of artists
    """

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    serializer_class = serializers.ArtistWithCountSerializer

    def get_queryset(self):
        """Search and filter the artists
        """
        query_set = models.Artist.objects.all()

        # if 'query' is in the query string then perform search return results
        # of the corresponding query
        if "query" not in self.request.query_params:
            return query_set.order_by(Lower("name"))

        query = self.request.query_params.get("query", None)
        if query:
            # there is no need for query language for artists
            # it is used to split terms and for uniformity
            res = QueryLanguageParser.split_remaining(query)
            query_list = []
            # only unspecific terms are used
            for remain in res:
                query_list.append(Q(name__icontains=remain))

            # gather the query objects
            filter_query = Q()
            for item in query_list:
                filter_query &= item

            query_set = query_set.filter(filter_query)
            # saving the parsed query to give it back to the client
            self.query_parsed = {"remaining": res}

        return query_set.order_by(Lower("name"))


class WorkListView(ListCreateAPIViewWithQueryParsed):
    """List of works
    """

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    serializer_class = serializers.WorkSerializer

    def get_queryset(self):
        """Search and filter the works
        """
        query_set = models.Work.objects.all()

        # if 'type' is in the query string
        # then filter work type
        if "type" in self.request.query_params:
            work_type = self.request.query_params.get("type", None)
            if work_type:
                query_set = query_set.filter(work_type__query_name=work_type)

        # if 'query' is in the query string then perform search return results
        # of the corresponding query and type filter
        if "query" not in self.request.query_params:
            return query_set.order_by(Lower("title"), Lower("subtitle"))

        query = self.request.query_params.get("query", None)
        if query:
            # there is no need for query language for works it is used to split
            # terms and for uniformity
            res = QueryLanguageParser.split_remaining(query)
            query_list = []
            # only unspecific terms are used
            for remain in res:
                query_list.append(
                    Q(title__icontains=remain)
                    | Q(subtitle__icontains=remain)
                    | Q(alternative_title__title__icontains=remain)
                )

            # gather the query objects
            filter_query = Q()
            for item in query_list:
                filter_query &= item

            query_set = query_set.filter(filter_query)
            # saving the parsed query to give it back to the client
            self.query_parsed = {"remaining": res}

        return query_set.distinct().order_by(Lower("title"), Lower("subtitle"))


class WorkTypeListView(ListCreateAPIView):
    """List of work types
    """

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    queryset = models.WorkType.objects.all().order_by(Lower("name"))
    serializer_class = serializers.WorkTypeSerializer


class SongTagListView(ListAPIView):
    """List of song tags
    """

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    queryset = models.SongTag.objects.all().order_by(Lower("name"))
    serializer_class = serializers.SongTagSerializer


class SongTagView(UpdateAPIView):
    """Update a song tag
    """

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    queryset = models.SongTag.objects.all()
    serializer_class = serializers.SongTagSerializer
