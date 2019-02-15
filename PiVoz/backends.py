# backends.py


from Galeria.models import RegularUser


class RFIDAuthentication:
    def authenticate(self, rfid):
        try:
            usuario = RegularUser.objects.get(rfid=rfid)
            return usuario
        except RegularUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return RegularUser.objects.get(pk=user_id)
        except RegularUser.DoesNotExist:
            return None
