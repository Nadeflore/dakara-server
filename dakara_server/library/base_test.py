from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status
from .models import *

UserModel = get_user_model()
class BaseAPITestCase(APITestCase):

    def authenticate(self, user):
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_user(self, username, playlist_level=None, library_level=None, users_level=None):
        user = UserModel.objects.create_user(username, "", "password")
        user.playlist_permission_level = playlist_level
        user.library_permission_level = library_level
        user.users_permission_level = users_level
        user.save()
        return user

    def create_library_test_data(self):
        # Create work types
        wt1 = WorkType(name="WorkType1", query_name="wt1")
        wt1.save()
        wt2 = WorkType(name="WorkType2", query_name="wt2")
        wt2.save()

        # Create works
        work1 = Work(title="Work1", work_type=wt1)
        work1.save()
        work2 = Work(title="Work2", work_type=wt1)
        work2.save()
        work3 = Work(title="Work3", work_type=wt2)
        work3.save()

        # Create artists
        artist1 = Artist(name="Artist1")
        artist1.save()
        artist2 = Artist(name="Artist2")
        artist2.save()

        # Create song tags
        tag1 = SongTag(name="TAG1")
        tag1.save()
        tag2 = SongTag(name="TAG2")
        tag2.save()

        # Create songs

        # Song with no tag, artist or work
        self.song1 = Song(title="Song1", filename="file.mp4")
        self.song1.save()

        # Song associated with work, artist, and tag
        self.song2 = Song(title="Song2", filename="file.mp4")
        self.song2.save()
        self.song2.tags.add(tag1)
        self.song2.artists.add(artist1)
        SongWorkLink(
                song_id=self.song2.id,
                work_id=work1.id,
                link_type=SongWorkLink.OPENING
                ).save()

    def check_song_json(self, json, expected_song):
        """
        Method to test a song representation against the expected song
        """
        self.assertEqual(json['id'], expected_song.id)
        self.assertEqual(json['title'], expected_song.title)
        self.assertEqual(json['filename'], expected_song.filename)
        self.assertEqual(json['directory'], expected_song.directory)
        self.assertEqual(json['version'], expected_song.version)
        self.assertEqual(json['detail'], expected_song.detail)
        self.assertEqual(json['detail_video'], expected_song.detail_video)

    def song_query_test(self, query, expected_songs):
        """
        Method to test a song song request with a given query
        Returned songs should be the same as expected_songs,
        in the same order
        """
        # TODO This only works when there is only one page of songs
        response = self.client.get(self.url, {'query': query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], len(expected_songs))
        results = response.data['results']
        self.assertEqual(len(results), len(expected_songs))
        for song, expected_song in zip(results, expected_songs):
            self.assertEqual(song['id'], expected_song.id)
