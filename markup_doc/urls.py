"""
URLs para a plataforma editorial MarkAPI.
"""

from django.urls import path
from . import editorial_views

app_name = 'markup_doc'

urlpatterns = [
    # Fila editorial
    path(
        'editorial/queue/',
        editorial_views.editorial_queue,
        name='editorial_queue',
    ),
    
    # Criar novo artigo
    path(
        'editorial/article/create/',
        editorial_views.article_create,
        name='editorial_article_create',
    ),
    
    # Detalhe do artigo (hub central)
    path(
        'editorial/article/<int:pk>/',
        editorial_views.article_detail,
        name='editorial_article_detail',
    ),
    
    # Reprocessar artigo
    path(
        'editorial/article/<int:pk>/reprocess/',
        editorial_views.article_reprocess,
        name='editorial_article_reprocess',
    ),
    
    # Download de artifact
    path(
        'editorial/article/<int:pk>/artifact/<str:artifact_type>/',
        editorial_views.article_download_artifact,
        name='editorial_article_download_artifact',
    ),
    
    # Referências do artigo
    path(
        'editorial/article/<int:pk>/references/',
        editorial_views.article_references_detail,
        name='editorial_article_references',
    ),
    
    # Timeline do artigo
    path(
        'editorial/article/<int:pk>/timeline/',
        editorial_views.article_timeline,
        name='editorial_article_timeline',
    ),
]
