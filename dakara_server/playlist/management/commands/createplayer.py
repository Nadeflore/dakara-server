from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from getpass import getpass
from django.db.utils import IntegrityError


UserModel = get_user_model()


class Command(BaseCommand):
    help = 'Create player account.'

    def handle(self, *args, **options):
        # get player name
        username = input("Enter player account name (default: 'player'): ")
        if not username:
            username = 'player'

        # get password
        password = getpass()

        try:
            player = UserModel.objects.create_user(username, password=password)

        except IntegrityError:
            self.stdout.write("Account '{}' already exists".format(username))
            return

        player.playlist_permission_level = 'p'
        player.save()
        self.stdout.write("Player created with name '{}'!".format(username))