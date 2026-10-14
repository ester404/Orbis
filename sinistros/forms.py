"""
FORMS = formulários.

Um ModelForm cria o formulário automaticamente a partir do modelo:
os campos, os tipos e até a validação (ex: protocolo repetido) vêm prontos.
"""
import os

from django import forms
from django.core.exceptions import ValidationError

from .models import Anexo, Processo

# Limites dos anexos — mudar aqui muda no sistema inteiro
EXTENSOES_PERMITIDAS = ["pdf", "jpg", "jpeg", "png", "webp", "doc", "docx", "xls", "xlsx", "txt"]
TAMANHO_MAXIMO_MB = 15


class ProcessoForm(forms.ModelForm):
    class Meta:
        model = Processo
        fields = [
            "protocolo", "associado", "placa", "tipo", "data_evento",
            "subsetor", "responsavel", "prazo", "pendencia", "descricao",
        ]
        widgets = {
            # type="date" faz o navegador mostrar um calendário
            "data_evento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "prazo": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "descricao": forms.Textarea(attrs={"rows": 4}),
            "protocolo": forms.TextInput(attrs={"placeholder": "Ex: 2026100001", "autofocus": True}),
            "placa": forms.TextInput(attrs={"placeholder": "ABC1D23"}),
        }
        labels = {"responsavel": "Responsável"}
        help_texts = {
            "responsavel": "Por enquanto é escolhido à mão. Na próxima etapa a fila escolhe sozinha.",
        }

    def __init__(self, *args, **kwargs):
        # __init__ roda quando o formulário é criado: aqui trocamos o texto das listas vazias
        super().__init__(*args, **kwargs)
        self.fields["tipo"].choices = [("", "Selecione…")] + list(Processo.Tipo.choices)
        self.fields["subsetor"].empty_label = "Selecione…"
        self.fields["responsavel"].empty_label = "Ninguém por enquanto"

    def clean_protocolo(self):
        # "clean_<campo>" é chamado automaticamente para validar aquele campo
        protocolo = self.cleaned_data["protocolo"].upper().strip()
        repetido = Processo.objects.filter(protocolo=protocolo).exclude(pk=self.instance.pk)
        if repetido.exists():
            raise ValidationError("Já existe um processo com esse protocolo.")
        return protocolo

    def clean_placa(self):
        placa = self.cleaned_data["placa"].upper().replace("-", "").replace(" ", "")
        if len(placa) != 7:
            raise ValidationError("A placa deve ter 7 caracteres (ex: ABC1D23).")
        return placa


class AnexoForm(forms.ModelForm):
    class Meta:
        model = Anexo
        fields = ["arquivo", "tipo_documento", "observacao"]
        widgets = {
            "observacao": forms.TextInput(attrs={"placeholder": "Opcional"}),
            "arquivo": forms.ClearableFileInput(attrs={
                "accept": ",".join("." + e for e in EXTENSOES_PERMITIDAS),
            }),
        }

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        extensao = os.path.splitext(arquivo.name)[1].lower().lstrip(".")
        if extensao not in EXTENSOES_PERMITIDAS:
            raise ValidationError(
                f"Tipo de arquivo não permitido. Use: {', '.join(EXTENSOES_PERMITIDAS)}."
            )
        if arquivo.size > TAMANHO_MAXIMO_MB * 1024 * 1024:
            raise ValidationError(f"Arquivo muito grande (máximo {TAMANHO_MAXIMO_MB} MB).")
        return arquivo


class AnotacaoForm(forms.Form):
    """Formulário simples (não ligado a modelo) para registrar uma anotação no histórico."""

    texto = forms.CharField(
        label="Nova anotação",
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Ex: Associado enviou o BO por e-mail."}),
    )
