"""
VIEWS = o "cérebro" de cada página.

Fluxo de uma requisição no Django:
  navegador pede /processo/7/  →  urls.py descobre qual view chamar
  →  a view busca dados no banco (models)  →  entrega para um template (HTML)
  →  o HTML pronto volta para o navegador.

GET  = só ler/mostrar uma página
POST = enviar um formulário (salvar algo)
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AnexoForm, AnotacaoForm, ProcessoForm
from .models import Anexo, Movimentacao, Processo, Subsetor


def colaborador_de(request):
    """Devolve o Colaborador ligado ao usuário logado (ou None se não tiver)."""
    return getattr(request.user, "colaborador", None)


def contar_situacoes(processos):
    """Conta quantos processos há em cada situação de prazo."""
    contagem = {"atrasado": 0, "vence_hoje": 0, "no_prazo": 0, "sem_prazo": 0, "concluido": 0}
    for p in processos:
        contagem[p.situacao_prazo] += 1
    return contagem


# ---------------------------------------------------------------- Início

@login_required  # só entra quem fez login
def inicio(request):
    """'Minha mesa': o que é meu, separado por situação de prazo."""
    eu = colaborador_de(request)
    meus = []
    if eu:
        meus = list(
            Processo.objects.filter(responsavel=eu)
            .exclude(etapa=Processo.Etapa.CONCLUSAO)
            .select_related("subsetor")
            .order_by("prazo")
        )
    return render(request, "sinistros/inicio.html", {
        "meus": meus,
        "contagem": contar_situacoes(meus),
        "ultimos": Processo.objects.select_related("subsetor", "responsavel__usuario")[:6],
    })


# ---------------------------------------------------------------- Busca

@login_required
def buscar(request):
    termo = request.GET.get("q", "").strip()
    if not termo:
        return redirect("inicio")

    # 1) Se o protocolo bate exatamente, vai direto para o processo
    exato = Processo.objects.filter(protocolo__iexact=termo).first()
    if exato:
        return redirect("detalhe_processo", pk=exato.pk)

    # 2) Senão, mostra todos que "contêm" o termo (protocolo, placa ou associado)
    placa = termo.upper().replace("-", "").replace(" ", "")
    resultados = Processo.objects.filter(
        Q(protocolo__icontains=termo) | Q(placa__icontains=placa) | Q(associado__icontains=termo)
    ).select_related("subsetor", "responsavel__usuario")

    if resultados.count() == 1:
        return redirect("detalhe_processo", pk=resultados.first().pk)

    return render(request, "sinistros/busca.html", {"termo": termo, "resultados": resultados})


# ---------------------------------------------------------------- Lista geral

@login_required
def lista_processos(request):
    processos = Processo.objects.select_related("subsetor", "responsavel__usuario")

    # Lê os filtros que vieram na URL, ex: /processos/?etapa=analise
    etapa = request.GET.get("etapa", "")
    subsetor = request.GET.get("subsetor", "")
    situacao = request.GET.get("situacao", "")
    if etapa:
        processos = processos.filter(etapa=etapa)
    if subsetor:
        processos = processos.filter(subsetor_id=subsetor)

    processos = list(processos)
    if situacao:
        # situacao_prazo é calculada em Python (não é coluna do banco), por isso filtramos na lista
        processos = [p for p in processos if p.situacao_prazo == situacao]

    return render(request, "sinistros/lista.html", {
        "processos": processos,
        "contagem": contar_situacoes(Processo.objects.all()),
        "etapas": Processo.Etapa.choices,
        "subsetores": Subsetor.objects.all(),
        "filtros": {"etapa": etapa, "subsetor": subsetor, "situacao": situacao},
    })


# ---------------------------------------------------------------- Cadastro / edição

@login_required
def novo_processo(request):
    if request.method == "POST":
        form = ProcessoForm(request.POST)
        if form.is_valid():
            # commit=False: monta o objeto mas ainda não salva, para completarmos campos
            processo = form.save(commit=False)
            processo.criado_por = colaborador_de(request)
            processo.save()
            Movimentacao.objects.create(
                processo=processo, etapa=processo.etapa, autor=colaborador_de(request),
                descricao="Processo cadastrado.",
            )
            messages.success(request, f"Processo {processo.protocolo} cadastrado! Agora anexe os documentos.")
            return redirect("detalhe_processo", pk=processo.pk)
    else:
        # Já sugere o subsetor de quem está cadastrando
        eu = colaborador_de(request)
        form = ProcessoForm(initial={"subsetor": eu.subsetor if eu else None})

    return render(request, "sinistros/form_processo.html", {"form": form, "titulo": "Cadastrar processo"})


@login_required
def editar_processo(request, pk):
    processo = get_object_or_404(Processo, pk=pk)
    if request.method == "POST":
        form = ProcessoForm(request.POST, instance=processo)
        if form.is_valid():
            # changed_data lista os campos que a pessoa alterou → vai pro histórico
            alterados = [form.fields[c].label or c for c in form.changed_data]
            form.save()
            if alterados:
                Movimentacao.objects.create(
                    processo=processo, etapa=processo.etapa, autor=colaborador_de(request),
                    descricao="Dados alterados: " + ", ".join(str(a).lower() for a in alterados) + ".",
                )
            messages.success(request, "Alterações salvas.")
            return redirect("detalhe_processo", pk=processo.pk)
    else:
        form = ProcessoForm(instance=processo)

    return render(request, "sinistros/form_processo.html", {
        "form": form, "titulo": f"Editar {processo.protocolo}", "processo": processo,
    })


# ---------------------------------------------------------------- Detalhe (+ anexos e anotações)

@login_required
def detalhe_processo(request, pk):
    processo = get_object_or_404(Processo.objects.select_related("subsetor", "responsavel__usuario"), pk=pk)
    eu = colaborador_de(request)
    form_anexo = AnexoForm()
    form_anotacao = AnotacaoForm()

    if request.method == "POST":
        # A mesma página tem dois formulários; o campo escondido "acao" diz qual foi enviado
        acao = request.POST.get("acao")

        if acao == "anexo":
            # Arquivos chegam em request.FILES, não em request.POST
            form_anexo = AnexoForm(request.POST, request.FILES)
            if form_anexo.is_valid():
                anexo = form_anexo.save(commit=False)
                anexo.processo = processo
                anexo.enviado_por = eu
                anexo.save()
                Movimentacao.objects.create(
                    processo=processo, etapa=processo.etapa, autor=eu,
                    descricao=f"Anexou {anexo.get_tipo_documento_display().lower()}: {anexo.nome_arquivo}.",
                )
                messages.success(request, "Documento anexado.")
                return redirect("detalhe_processo", pk=pk)

        elif acao == "anotacao":
            form_anotacao = AnotacaoForm(request.POST)
            if form_anotacao.is_valid():
                Movimentacao.objects.create(
                    processo=processo, etapa=processo.etapa, autor=eu,
                    descricao=form_anotacao.cleaned_data["texto"],
                )
                messages.success(request, "Anotação registrada.")
                return redirect("detalhe_processo", pk=pk)

    return render(request, "sinistros/detalhe.html", {
        "processo": processo,
        "anexos": processo.anexos.select_related("enviado_por__usuario"),
        "movimentacoes": processo.movimentacoes.select_related("autor__usuario"),
        "form_anexo": form_anexo,
        "form_anotacao": form_anotacao,
        "pode_excluir_anexo": bool(eu and eu.gestor) or request.user.is_superuser,
    })


@login_required
def baixar_anexo(request, pk):
    """
    Entrega o arquivo SÓ para quem está logado.
    (Se os arquivos ficassem numa pasta pública, qualquer um com o link baixaria.)
    """
    anexo = get_object_or_404(Anexo, pk=pk)
    baixar = request.GET.get("baixar") == "1"  # 1 = baixar; senão abre no navegador
    return FileResponse(anexo.arquivo.open("rb"), as_attachment=baixar, filename=anexo.nome_arquivo)


@login_required
def excluir_anexo(request, pk):
    anexo = get_object_or_404(Anexo, pk=pk)
    eu = colaborador_de(request)
    if not ((eu and eu.gestor) or request.user.is_superuser):
        raise PermissionDenied("Só líderes e supervisão podem excluir documentos.")
    if request.method == "POST":
        processo = anexo.processo
        nome = anexo.nome_arquivo
        anexo.arquivo.delete(save=False)  # apaga o arquivo do disco
        anexo.delete()                    # apaga o registro do banco
        Movimentacao.objects.create(
            processo=processo, etapa=processo.etapa, autor=eu,
            descricao=f"Excluiu o documento {nome}.",
        )
        messages.success(request, "Documento excluído.")
        return redirect("detalhe_processo", pk=processo.pk)
    return redirect("detalhe_processo", pk=anexo.processo.pk)
