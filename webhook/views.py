import json
import requests
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ProcessedMessage, Atendimento, Usuario
from .serializers import NovaMensagem

VERIFY_TOKEN = "12345"
WHATSAPP_API_TOKEN = "EAALsGcAB8xkBO470wWerIVeZBbcf8psL840DqMbYN4sVKZBV0St2tlJPotwGUEVOwBLXxz1mFDYmFxe5relcrN5lYsSzzJJhAxJZBJ72ASilrrchyexzIjqZC56MZBwIuRDqApPTSE81KV2xaHgRdtkQqiBODywjjJudEDDASvojcTJRa2oNyd1CVBiJUTiWFuhDgZAP6IBGD45ar7LV2x"
PHONE_NUMBER_ID = "315297828332138"


class WebhookView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.GET.get('hub.verify_token') == VERIFY_TOKEN:
            return HttpResponse(request.GET.get('hub.challenge'), content_type="text/plain")
        return HttpResponse("Verification token mismatch", status=403, content_type="text/plain")

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode('utf-8'))
            print(f"informação recebida: {data}")
            if 'entry' in data:
                for entry in data['entry']:
                    if 'changes' in entry:
                        for change in entry['changes']:
                            value = change['value']
                            if 'messages' in value:
                                for message in value['messages']:
                                    message_id = message['id']
                                    usuario_msg = message['text']['body']
                                    numero_usuario = message['from']
                                    numero_formatado = format_phone_number(phone_number=numero_usuario)

                                    if not Atendimento.objects.filter(numero_usuario=numero_usuario).exists():
                                        Atendimento.objects.create(numero_usuario=numero_usuario, status='emAndamento')

                                        send_message(to=numero_formatado,
                                                     text="Atendimento iniciado!\nPara continuar informe seu cpf:\n")
                                    try:
                                        atendimento = Atendimento.objects.get(numero_usuario=numero_usuario)
                                        if atendimento.usuario is not None:
                                            send_message(numero_formatado, "Vc ja tem um cpf valido salvo")
                                            send_message(numero_formatado,
                                                         f"Seu cpf: {atendimento.usuario.cpf}")
                                        else:
                                            atendimento.salvar_mensagem(usuario_msg)
                                            eh_um_cpf_valido = validar_cpf(usuario_msg)
                                            if eh_um_cpf_valido:
                                                send_message(numero_formatado, "cpf valido!!!")
                                                usuario = Usuario.objects.get(cpf=usuario_msg)
                                                atendimento.salvar_usuario(usuario)
                                                send_message(numero_formatado, f"Usuario encontrado: {usuario.cpf}")
                                            else:
                                                send_message(numero_formatado,
                                                             f"Mensagem inválida, informe um cpf válido!")
                                            print(f"Mensagem salva")
                                    except Atendimento.DoesNotExist:
                                        print("Atendimento não encontrado.")
                                    except Atendimento.MultipleObjectsReturned:
                                        print("Mais de um atendimento encontrado com esse número de usuário.")

            return JsonResponse({'status': 'success'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)


class SendMessage(APIView):
    serializer_class = NovaMensagem
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=NovaMensagem)
    def post(self, request, *args, **kwargs):
        serializer = NovaMensagem(data=request.data)
        if serializer.is_valid():
            response = send_message(serializer.validated_data["to"], serializer.validated_data["mensagem"])
            if response.status_code != 200 or response.status_code != 201:
                return Response(response.json(), status=status.HTTP_400_BAD_REQUEST)
            return Response(response.json(), status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def handle_button_reply(from_number, button_reply):
    if button_reply == 'pay_bill':
        send_message(from_number, "Você escolheu pagar a mensalidade. Aqui está o link para pagamento: [link]")
    elif button_reply == 'help_center':
        send_message(from_number,
                     "Você escolheu falar com a central de ajuda. Um de nossos atendentes falará com você em breve.")
    elif button_reply == 'payment_history':
        send_message(from_number, "Você escolheu ver o histórico de pagamentos. Aqui está seu histórico: [histórico]")
    else:
        send_message(from_number, "Opção inválida. Por favor, tente novamente.")


def send_message(to, text, buttons=None):
    url = f"https://graph.facebook.com/v12.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json"
    }

    if buttons:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": text
                },
                "action": {
                    "buttons": buttons
                }
            }
        }
    else:
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "text": {
                "body": text
            }
        }

    response = requests.post(url, json=data, headers=headers)
    print(response.json())
    return response.json()


def validar_cpf(cpf):
    # Verifica se o CPF tem 11 dígitos e se todos são números
    if not cpf.isdigit() or len(cpf) != 11:
        return False

    # Calcula o primeiro dígito verificador
    def calcular_digito(cpf, fator):
        soma = 0
        for i in range(fator - 1):
            soma += int(cpf[i]) * (fator - i)
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    # Calcula os dois dígitos verificadores
    primeiro_digito = calcular_digito(cpf, 10)
    segundo_digito = calcular_digito(cpf, 11)

    # Verifica se os dígitos verificadores são válidos
    return cpf[-2:] == f"{primeiro_digito}{segundo_digito}"


def format_phone_number(phone_number):
    if len(phone_number) > 13:
        raise ValueError("Número de telefone deve ter 12 dígitos.")

    country_code = phone_number[:2]
    area_code = phone_number[2:4]
    part1 = phone_number[4:8]
    part2 = phone_number[8:]
    part1 = '9' + part1
    formatted_number = f"+{country_code} ({area_code}) {part1}-{part2}"
    return formatted_number


""""
                                      # Envia opções de interação
                                            buttons = [
                                                {
                                                    "type": "reply",
                                                    "reply": {
                                                        "id": "pay_bill",
                                                        "title": "Pagar"
                                                    }
                                                },
                                                {
                                                    "type": "reply",
                                                    "reply": {
                                                        "id": "help_center",
                                                        "title": "Ajuda"
                                                    }
                                                },
                                                {
                                                    "type": "reply",
                                                    "reply": {
                                                        "id": "payment_history",
                                                        "title": "Histórico"
                                                    }
                                                }
                                            ]
                                            send_message(from_number,
                                                         "Olá! Como posso ajudar você hoje? Escolha uma das opções abaixo:",
                                                         )
"""
