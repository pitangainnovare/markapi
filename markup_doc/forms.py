"""
Formulários para a plataforma editorial MarkAPI.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .new_models import Article


class ArticleUploadForm(forms.ModelForm):
    """
    Formulário simplificado para upload de novo manuscrito.
    
    Permite upload de DOCX e título provisório.
    """
    
    class Meta:
        model = Article
        fields = ['title', 'original_file', 'journal_acronym', 'issue_identifier']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'placeholder': _('Enter provisional title'),
            }),
            'original_file': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'accept': '.docx',
            }),
            'journal_acronym': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'placeholder': _('Journal acronym (e.g., rbp, spmj)'),
            }),
            'issue_identifier': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'placeholder': _('Issue identifier (e.g., v10n2s1)'),
            }),
        }
    
    def clean_original_file(self):
        """Validar que o arquivo é um DOCX."""
        file = self.cleaned_data.get('original_file')
        if file:
            # Verificar extensão
            if not file.name.endswith('.docx'):
                raise forms.ValidationError(
                    _('Only DOCX files are allowed.')
                )
            
            # Verificar tamanho máximo (100MB)
            max_size = 100 * 1024 * 1024  # 100MB
            if file.size > max_size:
                raise forms.ValidationError(
                    _('File size must not exceed 100MB.')
                )
        
        return file
    
    def clean_title(self):
        """Validar que o título não está vazio."""
        title = self.cleaned_data.get('title')
        if not title or not title.strip():
            raise forms.ValidationError(
                _('Title is required.')
            )
        return title.strip()
