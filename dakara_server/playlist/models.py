from datetime import timedelta, datetime

from django.db import models
from django.core.cache import cache
from django.utils import timezone

from users.models import DakaraUser


tz = timezone.get_default_timezone()


class PlaylistEntry(models.Model):
    """Song in playlist
    """
    song = models.ForeignKey('library.Song', null=False,
                             on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(DakaraUser, null=False,
                              on_delete=models.CASCADE)
    was_played = models.BooleanField(default=False, null=False)
    had_error = models.BooleanField(default=False, null=False)
    date_played = models.DateTimeField(null=True)

    def __str__(self):
        return "{} (for {})".format(
            self.song,
            self.owner.username
        )

    @classmethod
    def get_next(cls, entry_id=None):
        """Retrieve next playlist entry

        Returns the next playlist entry in playlist excluding entry with
        specified id and alredy played songs.
        """
        if entry_id is None:
            playlist = cls.objects.exclude(was_played=True)

        else:
            playlist = cls.objects.exclude(
                models.Q(pk=entry_id) | models.Q(was_played=True)
            )

        playlist.order_by('date_created')

        if not playlist:
            return None

        return playlist.first()

    @classmethod
    def get_playing(cls):
        playlist = cls.objects.filter(
            was_played=False, date_played__isnull=True
        ).order_by('date_created')

        if not playlist:
            return None

        if playlist.count() > 1:
            raise RuntimeError("It seems that two entries are playing at "
                               "the same time")

        return playlist.first()

    @classmethod
    def get_playlist(cls):
        queryset = cls.objects.exclude(
            models.Q(was_played=True) | models.Q(date_played__isnull=False)
        ).order_by('date_created')

        return queryset

    @classmethod
    def get_playlist_with_date(cls):
        # we have to transform the queryset to a list, otherwise the adjuction
        # of the play date will be lost by any queryset method
        playlist = list(cls.get_playlist())

        # it is not possible to add the timing of the player
        # for each entry, compute when it is supposed to play
        date = datetime.now(tz)
        for entry in playlist:
            entry.date_play = date
            date += entry.song.duration

        return playlist, date

    @classmethod
    def get_playlist_played(cls):
        playlist = cls.objects.filter(
            was_played=True, date_played__isnull=False
        ).order_by('date_created')

        return playlist


class KaraStatus(models.Model):
    """Current status of the kara

    The status is unique for now.
    """
    STOP = "stop"
    PLAY = "play"
    PAUSE = "pause"
    STATUSES = (
        (STOP, "Stop"),
        (PLAY, "Play"),
        (PAUSE, "Pause")
    )

    status = models.CharField(
        max_length=5,
        choices=STATUSES,
        default=PLAY,
        null=False,
    )

    def __str__(self):
        return str("in {} mode".format(self.status))

    @classmethod
    def get_object(cls):
        """Get the first instance of kara status
        """
        kara_status, _ = cls.objects.get_or_create(pk=1)
        return kara_status


class Player:
    """Player representation in the server

    This object is not stored in database, but lives within Django memory
    cache.
    """
    PLAYER_NAME = 'player'

    def __init__(
            self,
            playlist_entry_id=None,
            timing=timedelta(),
            paused=False
    ):
        self.playlist_entry_id = playlist_entry_id
        self.timing = timing
        self.paused = paused

    @classmethod
    def get_or_create(cls):
        """Retrieve the current player in cache or create one
        """
        player = cache.get(cls.PLAYER_NAME)

        if player is None:
            # create a new player object
            player = cls()

        return player

    def save(self):
        """Save player in cache
        """
        cache.set(self.PLAYER_NAME, self)

    def reset(self):
        """Reset the player to its initial state
        """
        self.playlist_entry_id = None
        self.timing = timedelta()
        self.paused = False

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, str(self))

    def __str__(self):
        return "in {} mode".format("pause" if self.paused else "play")


class PlayerCommand:
    """Commands to the player

    This object is not stored in database, but lives within Django memory
    cache.
    """
    PLAYER_COMMAND_NAME = 'player_command'

    def __init__(
            self,
            pause=False,
            skip=False
    ):
        self.pause = pause
        self.skip = skip

    @classmethod
    def get_or_create(cls):
        """Retrieve the current player commands in cache or create one
        """
        player_command = cache.get(cls.PLAYER_COMMAND_NAME)

        if player_command is None:
            # create a new player commands object
            player_command = cls()

        return player_command

    def save(self):
        """Save player commands in cache
        """
        cache.set(self.PLAYER_COMMAND_NAME, self)

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, str(self))

    def __str__(self):
        return "requesting {}, {}".format(
            "pause" if self.pause else "no pause",
            "skip" if self.skip else "no skip"
        )


class PlayerError:
    """Error encountered by the player

    Each error is stored in cache for `PLAYER_ERROR_TIME_OF_LIFE` seconds and
    will be then removed. Each of them has a distinct name made from the
    `PLAYER_ERROR_PATTERN` pattern with its `id` as a suffix.

    The error is not stored automatically in memory when created. The `save`
    method has to be called for this.

    This class should not be manipulated directly outside of this module.

    This object is not stored in database, but lives within Django memory
    cache.
    """
    PLAYER_ERROR_PATTERN = "player_error_{}"
    PLAYER_ERROR_TIME_OF_LIFE = 10

    def __init__(self, id, song, error_message):
        self.id = id
        self.song = song
        self.error_message = error_message

    @classmethod
    def get(cls, id):
        """Retrieve an error from the cache by its ID if still present
        """
        player_error_name = cls.PLAYER_ERROR_PATTERN.format(id)
        return cache.get(player_error_name)

    def save(self):
        """Save the object in cache for a certain amount of time
        """
        player_error_name = self.PLAYER_ERROR_PATTERN.format(self.id)
        cache.set(player_error_name, self, self.PLAYER_ERROR_TIME_OF_LIFE)

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, str(self))

    def __str__(self):
        return "error {}".format(self.id)


class PlayerErrorsPool:
    """Class to manage player errors

    The class manages the pool of errors and the errors themselve. Both of them
    are stored in cache.

    Each method should be followed by the `save` method, otherwize the cache is
    not updated.

    This object is not stored in database, it is not stored at all.
    """
    PLAYER_ERROR_POOL_NAME = 'player_error_pool'

    def __init__(self, ids_pool=[], count=0):
        self.ids_pool = ids_pool
        self.count = count

        # temporary pool for new errors
        self.temp_pool = []

    @classmethod
    def get_or_create(cls):
        """Retrieve the current player errors pool in cache or create one
        """
        pool = cache.get(cls.PLAYER_ERROR_POOL_NAME)

        if pool is None:
            # create a new pool
            pool = cls()

        else:
            # clean old errors
            pool.clean()
            pool.save()

        return pool

    def save(self):
        """Save player errors pool in cache
        """
        cache.set(self.PLAYER_ERROR_POOL_NAME, self)

        # save new errors
        for error in self.temp_pool:
            error.save()

        # purge new errors list
        self.temp_pool = []

    def add(self, song, error_message):
        """Add one error to the errors pool
        """
        error = PlayerError(self.count, song, error_message)
        self.temp_pool.append(error)
        self.ids_pool.append(self.count)
        self.count += 1

    def clean(self):
        """Remove old errors from pool
        """
        self.ids_pool = [
            id for id in self.ids_pool
            if PlayerError.get(id) is not None
        ]

    def dump(self):
        """Gives the pool as a list
        """
        return [PlayerError.get(id) for id in self.ids_pool]

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, str(self))

    def __str__(self):
        return "with {} error(s)".format(self.count)
