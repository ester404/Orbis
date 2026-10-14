"""
O ADMIN é um painel pronto que o Django gera sozinho a partir dos modelos.
Acesse em http://127.0.0.1:8000/admin/ — é por aqui que a supervisão
cadastra subsetores e colaboradores, e marca quem está indisponível.
"""
from django.contrib import admin

from .models import Anexo, Colaborador, Movimentacao, Processo, Subsetor

admin.site.site_header = "Orbis · Administração"
admin.site.site_title = "Orbis"


@admin.register(Subsetor)
class SubsetorAdmin(admin.ModelAdmin):
    list_display = ["nome"]


@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ["__str__", "subsetor", "papel", "disponivel", "motivo_indisponivel"]
    list_filter = ["subsetor", "papel", "disponivel"]
    list_editable = ["disponivel", "motivo_indisponivel"]  # edita direto na lista


class MovimentacaoInline(admin.TabularInline):
    # Mostra as movimentações DENTRO da página do processo
    model = Movimentacao
    extra = 0


class AnexoInline(admin.TabularInline):
    model = Anexo
    extra = 0


@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ["protocolo", "associado", "placa", "tipo", "etapa", "subsetor", "responsavel", "prazo"]
    list_filter = ["etapa", "tipo", "subsetor"]
    search_fields = ["protocolo", "associado", "placa"]
    inlines = [AnexoInline, MovimentacaoInline]
