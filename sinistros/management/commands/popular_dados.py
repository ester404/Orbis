"""
Comando personalizado: python manage.py popular_dados

Cria subsetores, usuários e processos FICTÍCIOS para você estudar
sem usar nenhum dado real da empresa.
Pode rodar de novo quando quiser: ele apaga os processos e recria.
"""
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from sinistros.models import Colaborador, Movimentacao, Processo, Subsetor

# Os 8 subsetores (confira e ajuste os nomes aqui ou pelo Admin)
SUBSETORES = [
    "Reguladores", "Atendimento/Negociação", "Autorização", "Vidros",
    "Notas", "Despachante", "Análise parcial", "Reembolso integral",
]

# (usuário, nome, sobrenome, subsetor, papel)
PESSOAS = [
    ("ana", "Ana", "Souza", "Atendimento/Negociação", "lider"),
    ("bruno", "Bruno", "Lima", "Reguladores", "colaborador"),
    ("carla", "Carla", "Dias", "Reguladores", "colaborador"),
    ("diego", "Diego", "Rocha", "Autorização", "colaborador"),
    ("elisa", "Elisa", "Prado", "Notas", "colaborador"),
    ("fabio", "Fábio", "Melo", "Vidros", "colaborador"),
    ("gabi", "Gabi", "Nunes", "Análise parcial", "colaborador"),
    ("hugo", "Hugo", "Alves", "Despachante", "colaborador"),
    ("iris", "Íris", "Costa", "Reembolso integral", "colaborador"),
    ("joao", "João", "Pires", "Atendimento/Negociação", "colaborador"),
]

ASSOCIADOS = ["Maria Fictícia", "José Exemplo", "Paula Teste", "Rafael Modelo",
              "Lúcia Demo", "Pedro Simulado", "Sônia Amostra", "Tiago Fantasia"]

LETRAS = "ABCDEFGHJKLMNPRSTUVWXYZ"


def placa_aleatoria():
    l = random.choice
    return f"{l(LETRAS)}{l(LETRAS)}{l(LETRAS)}{random.randint(0, 9)}{l(LETRAS)}{random.randint(10, 99)}"


class Command(BaseCommand):
    help = "Cria dados fictícios para estudo"

    def handle(self, *args, **opcoes):
        random.seed(42)  # mesma "sorte" toda vez → resultados repetíveis

        # 1) Subsetores
        subsetores = {nome: Subsetor.objects.get_or_create(nome=nome)[0] for nome in SUBSETORES}

        # 2) Supervisão (admin) — login: admin / senha: admin123
        admin, criado = User.objects.get_or_create(
            username="admin", defaults={"first_name": "Supervisão", "is_staff": True, "is_superuser": True}
        )
        if criado:
            admin.set_password("admin123")
            admin.save()
        Colaborador.objects.get_or_create(
            usuario=admin, defaults={"subsetor": subsetores["Notas"], "papel": "supervisor"}
        )

        # 3) Colaboradores fictícios — senha de todos: teste123
        colaboradores = []
        for usuario_nome, nome, sobrenome, subsetor, papel in PESSOAS:
            usuario, criado = User.objects.get_or_create(
                username=usuario_nome, defaults={"first_name": nome, "last_name": sobrenome}
            )
            if criado:
                usuario.set_password("teste123")
                usuario.save()
            colab, _ = Colaborador.objects.get_or_create(
                usuario=usuario, defaults={"subsetor": subsetores[subsetor], "papel": papel}
            )
            colaboradores.append(colab)

        # 4) Processos
        Processo.objects.all().delete()
        etapas = [valor for valor, _ in Processo.Etapa.choices]
        hoje = timezone.localdate()
        agora = timezone.now()

        for n in range(30):
            etapa_atual = random.choice(etapas)
            cadastrado = agora - timedelta(days=random.randint(1, 30), hours=random.randint(0, 8))
            responsavel = random.choice(colaboradores)
            processo = Processo.objects.create(
                protocolo=f"2026{10 + n // 20:02d}{n + 1:04d}",
                associado=random.choice(ASSOCIADOS),
                placa=placa_aleatoria(),
                tipo=random.choice(Processo.Tipo.values),
                data_evento=(cadastrado - timedelta(days=random.randint(0, 5))).date(),
                etapa=etapa_atual,
                subsetor=responsavel.subsetor,
                responsavel=responsavel,
                # alguns sem prazo, porque as regras de prazo ainda serão definidas
                prazo=None if n % 5 == 0 else hoje + timedelta(days=random.randint(-5, 10)),
                pendencia=random.choice(["", "", "Aguardando BO", "Aguardando orçamento"]),
                descricao="Evento fictício para testes do sistema.",
                criado_por=random.choice(colaboradores),
                criado_em=cadastrado,
                concluido_em=agora if etapa_atual == "conclusao" else None,
            )
            Movimentacao.objects.create(
                processo=processo, etapa="cadastro", autor=processo.criado_por,
                descricao="Processo cadastrado.", criado_em=cadastrado,
            )
            if etapa_atual != "cadastro":
                Movimentacao.objects.create(
                    processo=processo, etapa=etapa_atual, autor=responsavel,
                    descricao=f"Processo seguiu para {processo.get_etapa_display()}.",
                    criado_em=cadastrado + (agora - cadastrado) / 2,
                )

        # Deixa alguns processos com a supervisão, para a "Minha mesa" do admin ter conteúdo
        eu_admin = admin.colaborador
        for p in Processo.objects.exclude(etapa="conclusao")[:5]:
            p.responsavel = eu_admin
            p.save()

        self.stdout.write(self.style.SUCCESS("Pronto! 30 processos fictícios criados."))
        self.stdout.write("Supervisão: admin / admin123")
        self.stdout.write("Colaboradores: ana, bruno, carla... / senha teste123")
