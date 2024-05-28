# serializers.py
import re
from rest_framework import serializers


class NovaMensagem(serializers.Serializer):
    to = serializers.CharField(max_length=20, help_text='Formato exigido: +11 (11) 91111-1111')
    mensagem = serializers.CharField(max_length=255)

    def validate_to(self, value):
        phone_regex = re.compile(r'^\+\d{2} \(\d{2}\) \d{5}-\d{4}$')
        if not phone_regex.match(value):
            raise serializers.ValidationError(
                'Número de telefone inválido. O formato correto é "+55 (92) 99153-1689".'
            )
        return value
