from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.core.exceptions import ObjectDoesNotExist


class DakaraUserManager(UserManager):
    """Custom user manager to handle case insensitive usernames
    """

    def get_by_natural_key(self, username):
        """Search a username case insensitively
        """
        return self.get(username__iexact=username)

    def _create_user(self, username, *args, **kwargs):
        """Generic method to create new users

        Check if the username is free, otherwise raise a `ValueError`.
        """
        # check if username is free before creating user with this username
        if self.is_username_taken(username):
            raise ValueError("The username must be case insensitively unique")

        return super()._create_user(username, *args, **kwargs)

    def is_username_taken(self, username):
        """Check if a similar username exists with the natural method

        Since we've set the search to be case insensitive, it will find it case
        insensitively.
        """
        try:
            if self.get_by_natural_key(username):
                return True

        except ObjectDoesNotExist:
            pass

        return False


class DakaraUser(AbstractUser):
    """Custom user
    """

    objects = DakaraUserManager()

    # permission levels per application
    USER = "u"
    MANAGER = "m"
    PLAYER = "p"

    # role for Users app
    LEVELS_USERS = [(USER, "User"), (MANAGER, "Manager")]

    users_permission_level = models.CharField(
        max_length=1, choices=LEVELS_USERS, null=True
    )

    # role for Libraryapp
    LEVELS_LIBRARY = [(USER, "User"), (MANAGER, "Manager")]
    library_permission_level = models.CharField(
        max_length=1, choices=LEVELS_LIBRARY, null=True
    )

    # role for Playlist app
    LEVELS_PLAYLIST = [(PLAYER, "Player"), (USER, "User"), (MANAGER, "Manager")]

    playlist_permission_level = models.CharField(
        max_length=1, choices=LEVELS_PLAYLIST, null=True
    )

    @property
    def is_users_user(self):
        return self.users_permission_level == self.USER

    @property
    def is_users_manager(self):
        return self.users_permission_level == self.MANAGER

    @property
    def is_library_user(self):
        return self.library_permission_level == self.USER

    @property
    def is_library_manager(self):
        return self.library_permission_level == self.MANAGER

    @property
    def is_playlist_user(self):
        return self.playlist_permission_level == self.USER

    @property
    def is_playlist_manager(self):
        return self.playlist_permission_level == self.MANAGER

    @property
    def is_player(self):
        return self.playlist_permission_level == self.PLAYER
