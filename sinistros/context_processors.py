"""
CONTEXT PROCESSOR = uma função que entrega dados para TODAS as páginas.

Usamos para o contador do topo (o "sininho"): quantos processos abertos
a pessoa tem e quantos estão atrasados. Ele aparece em qualquer tela.
Está ligado em config/settings.py → TEMPLATES → context_processors.
"""
from .models import Processo


def minha_mesa(request):
    if not request.user.is_authenticated:
        return {}
    eu = getattr(request.user, "colaborador", None)
    if not eu:
        return {"eu": None}
    abertos = list(Processo.objects.filter(responsavel=eu).exclude(etapa=Processo.Etapa.CONCLUSAO))
    return {
        "eu": eu,
        "mesa_total": len(abertos),
        "mesa_atrasados": sum(p.situacao_prazo == "atrasado" for p in abertos),
    }
