"""
MODELOS = as "tabelas" do banco de dados.

Cada classe vira uma tabela, e cada atributo vira uma coluna.
Depois de mudar este arquivo, sempre rode:
    python manage.py makemigrations
    python manage.py migrate
"""
import os

from django.conf import settings
from django.db import models
from django.utils import timezone


class Subsetor(models.Model):
    """Os subsetores do departamento: Reguladores, Vidros, Notas..."""

    nome = models.CharField(max_length=60, unique=True)

    class Meta:
        verbose_name_plural = "subsetores"
        ordering = ["nome"]

    def __str__(self):
        # É isso que aparece quando o Django precisa "mostrar" o objeto
        return self.nome


class Colaborador(models.Model):
    """
    Liga um usuário de login (que o Django já tem pronto: User)
    a um subsetor e a um papel. Isso se chama relação 1 para 1.
    """

    class Papel(models.TextChoices):
        COLABORADOR = "colaborador", "Colaborador(a)"
        LIDER = "lider", "Líder"
        SUPERVISOR = "supervisor", "Supervisão"

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subsetor = models.ForeignKey(Subsetor, on_delete=models.PROTECT, related_name="colaboradores")
    papel = models.CharField(max_length=20, choices=Papel.choices, default=Papel.COLABORADOR)

    # Usado pelas filas (próxima etapa): quem está indisponível é pulado
    disponivel = models.BooleanField(
        "disponível", default=True,
        help_text="Desmarque para férias, atestado ou folga: a pessoa sai das filas.",
    )
    motivo_indisponivel = models.CharField("motivo", max_length=100, blank=True)

    class Meta:
        verbose_name = "colaborador(a)"
        verbose_name_plural = "colaboradores"
        ordering = ["usuario__first_name"]

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username

    @property
    def gestor(self):
        """Líder ou supervisão: quem poderá transferir processos."""
        return self.papel in (self.Papel.LIDER, self.Papel.SUPERVISOR)


class Processo(models.Model):
    """Um sinistro, identificado pelo PROTOCOLO."""

    class Etapa(models.TextChoices):
        # O fluxo único: CADASTRO → ... → CONCLUSÃO
        CADASTRO = "cadastro", "Cadastro"
        REGULACAO = "regulacao", "Regulação"
        ANALISE = "analise", "Análise"
        AUTORIZACAO = "autorizacao", "Autorização"
        EXECUCAO = "execucao", "Execução"
        DOCUMENTACAO = "documentacao", "Documentação"
        CONCLUSAO = "conclusao", "Conclusão"

    class Tipo(models.TextChoices):
        COLISAO = "colisao", "Colisão"
        VIDROS = "vidros", "Vidros"
        ROUBO_FURTO = "roubo_furto", "Roubo/Furto"
        FENOMENO = "fenomeno", "Fenômeno natural"
        INCENDIO = "incendio", "Incêndio"
        TERCEIRO = "terceiro", "Terceiro"

    protocolo = models.CharField(max_length=30, unique=True)
    associado = models.CharField(max_length=120)
    placa = models.CharField(max_length=8)
    tipo = models.CharField("tipo de evento", max_length=20, choices=Tipo.choices)
    data_evento = models.DateField("data do evento", null=True, blank=True)
    etapa = models.CharField(max_length=20, choices=Etapa.choices, default=Etapa.CADASTRO)
    subsetor = models.ForeignKey(Subsetor, on_delete=models.PROTECT, related_name="processos")
    responsavel = models.ForeignKey(
        Colaborador, on_delete=models.SET_NULL, null=True, blank=True, related_name="processos"
    )
    descricao = models.TextField("descrição do evento", blank=True)
    pendencia = models.CharField("pendência", max_length=200, blank=True)
    prazo = models.DateField(null=True, blank=True)  # regras de prazo virão depois
    criado_por = models.ForeignKey(
        Colaborador, on_delete=models.SET_NULL, null=True, related_name="processos_cadastrados"
    )
    criado_em = models.DateTimeField("cadastrado em", default=timezone.now)
    concluido_em = models.DateTimeField("concluído em", null=True, blank=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.protocolo} – {self.placa}"

    def save(self, *args, **kwargs):
        # Padroniza antes de salvar: placa e protocolo sempre em maiúsculas, sem espaços
        self.placa = self.placa.upper().replace("-", "").replace(" ", "")
        self.protocolo = self.protocolo.upper().strip()
        super().save(*args, **kwargs)

    # ---- Regras de negócio ficam no modelo (assim todas as telas usam igual) ----

    @property
    def situacao_prazo(self):
        """Devolve 'concluido', 'sem_prazo', 'atrasado', 'vence_hoje' ou 'no_prazo'."""
        if self.etapa == self.Etapa.CONCLUSAO:
            return "concluido"
        if not self.prazo:
            return "sem_prazo"
        hoje = timezone.localdate()
        if self.prazo < hoje:
            return "atrasado"
        if self.prazo == hoje:
            return "vence_hoje"
        return "no_prazo"


class Movimentacao(models.Model):
    """
    Histórico: tudo o que acontece com o processo fica registrado aqui
    (cadastro, anotações, anexos, mudança de etapa, transferências...).
    É esta tabela que depois permite calcular "parado há 48h", SLA, tempo por etapa.
    """

    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, related_name="movimentacoes")
    etapa = models.CharField(max_length=20, choices=Processo.Etapa.choices)
    descricao = models.TextField("descrição")
    autor = models.ForeignKey(Colaborador, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "movimentação"
        verbose_name_plural = "movimentações"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.processo.protocolo}: {self.descricao[:40]}"


def caminho_anexo(instancia, nome_arquivo):
    """Guarda cada arquivo numa pasta com o protocolo: anexos/SIN-001/arquivo.pdf"""
    return f"anexos/{instancia.processo.protocolo}/{nome_arquivo}"


class Anexo(models.Model):
    """Documentos do processo: BO, CNH, fotos, orçamentos, notas..."""

    class TipoDocumento(models.TextChoices):
        BO = "bo", "Boletim de ocorrência"
        CNH = "cnh", "CNH"
        CRLV = "crlv", "CRLV / documento do veículo"
        FOTOS = "fotos", "Fotos"
        ORCAMENTO = "orcamento", "Orçamento"
        NOTA = "nota", "Nota fiscal"
        LAUDO = "laudo", "Laudo / regulação"
        OUTRO = "outro", "Outro"

    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, related_name="anexos")
    arquivo = models.FileField(upload_to=caminho_anexo)
    tipo_documento = models.CharField(
        "tipo de documento", max_length=20, choices=TipoDocumento.choices, default=TipoDocumento.OUTRO
    )
    observacao = models.CharField("observação", max_length=200, blank=True)
    enviado_por = models.ForeignKey(Colaborador, on_delete=models.SET_NULL, null=True)
    enviado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-enviado_em"]

    def __str__(self):
        return self.nome_arquivo

    @property
    def nome_arquivo(self):
        return os.path.basename(self.arquivo.name)

    @property
    def extensao(self):
        return os.path.splitext(self.arquivo.name)[1].lower().lstrip(".")
