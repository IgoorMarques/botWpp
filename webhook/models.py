from django.db import models


class Usuario(models.Model):
    cpf = models.CharField(max_length=100, unique=True, null=False)


class ProcessedMessage(models.Model):
    message_id = models.CharField(max_length=100, unique=True)
    processed_at = models.DateTimeField(auto_now_add=True)


class StepAtendimento(models.Model):
    mensagem = models.TextField()
    resposta_valida_usuario = models.CharField(null=True, max_length=255)
    operacao = models.CharField(max_length=20, choices=[
        ('start', 'Start'),
        ('pagar', 'Pagar'),
        ('fim', 'Fim'),
    ])


class Atendimento(models.Model):
    numero_usuario = models.CharField(max_length=255, null=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('emAndamento', 'EmAndamento'),
        ('finalizado', 'Finalizado')
    ])

    def __str__(self):
        return f"Atendimento {self.id} - {self.numero_usuario}"

    @property
    def mensagens_lista(self):
        return list(self.mensagens.values_list('mensagem', flat=True))

    def salvar_mensagem(self, conteudo_mensagem):
        mensagem = MensagemAtendimento(atendimento=self, mensagem=conteudo_mensagem)
        mensagem.save()
        return mensagem

    def salvar_usuario(self, usuario):
        self.usuario = usuario
        self.save()


class MensagemAtendimento(models.Model):
    atendimento = models.ForeignKey(Atendimento, related_name='mensagens', on_delete=models.CASCADE)
    mensagem = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return f"Mensagem {self.id} para Atendimento {self.atendimento.id}"
