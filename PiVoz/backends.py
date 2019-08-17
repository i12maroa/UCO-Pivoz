# backends.py


from Galeria.models import RegularUser


class RFIDAuthentication:
    """ Clase que permite autenticar a un usuario mediante código RFID. Retorna un objeto RegularUser """
    def authenticate(self, request,  rfid):
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
