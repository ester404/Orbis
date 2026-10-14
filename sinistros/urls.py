"""
URLS do app: liga cada endereço a uma view.
O "name" serve para usar {% url 'nome' %} nos templates sem escrever o caminho na mão.
"""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("buscar/", views.buscar, name="buscar"),
    path("processos/", views.lista_processos, name="lista_processos"),
    path("processos/novo/", views.novo_processo, name="novo_processo"),
    path("processo/<int:pk>/", views.detalhe_processo, name="detalhe_processo"),
    path("processo/<int:pk>/editar/", views.editar_processo, name="editar_processo"),
    path("anexo/<int:pk>/", views.baixar_anexo, name="baixar_anexo"),
    path("anexo/<int:pk>/excluir/", views.excluir_anexo, name="excluir_anexo"),
]
