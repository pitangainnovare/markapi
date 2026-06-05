"""
Views administrativas para a plataforma editorial MarkAPI.

Implementa a fila editorial, formulário de upload e hub central do artigo.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .new_models import Article, ArticleArtifact, ArticleProcessingLog, ProcessStatus
from .forms import ArticleUploadForm


@login_required
@staff_member_required
def editorial_queue(request):
    """
    View da fila editorial com lista de artigos, filtros e busca.
    
    Mostra todos os artigos com seus status, permite filtrar por:
    - Status (PENDING, PROCESSING, PROCESSED, FAILED)
    - Periódico (journal_acronym)
    - Busca por título
    """
    # Obter parâmetros de filtro
    status_filter = request.GET.get('status')
    journal_filter = request.GET.get('journal')
    search_query = request.GET.get('q', '')
    
    # Queryset base com prefetch de artifacts e logs
    queryset = Article.objects.select_related().prefetch_related(
        Prefetch('artifacts', queryset=ArticleArtifact.objects.filter(is_current=True)),
        Prefetch('processing_logs', queryset=ArticleProcessingLog.objects.order_by('-started_at')[:1])
    ).order_by('-created')
    
    # Aplicar filtros
    if status_filter:
        try:
            status_value = int(status_filter)
            queryset = queryset.filter(status=status_value)
        except (ValueError, TypeError):
            pass
    
    if journal_filter:
        queryset = queryset.filter(journal_acronym__icontains=journal_filter)
    
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(doi__icontains=search_query)
        )
    
    # Contagens por status para estatísticas
    stats = {
        'total': queryset.count(),
        'pending': queryset.filter(status=ProcessStatus.PENDING).count(),
        'processing': queryset.filter(status=ProcessStatus.PROCESSING).count(),
        'processed': queryset.filter(status=ProcessStatus.PROCESSED).count(),
        'failed': queryset.filter(status=ProcessStatus.FAILED).count(),
    }
    
    context = {
        'articles': queryset,
        'status_filter': status_filter,
        'journal_filter': journal_filter,
        'search_query': search_query,
        'stats': stats,
        'status_choices': ProcessStatus.choices,
        'upload_url': reverse('editorial_article_create'),
    }
    
    return render(request, 'markup_doc/editorial_queue.html', context)


@login_required
@staff_member_required
def article_create(request):
    """
    Formulário simplificado para upload de novo manuscrito.
    
    Permite upload de DOCX e título provisório.
    """
    if request.method == 'POST':
        form = ArticleUploadForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.status = ProcessStatus.PENDING
            article.save()
            
            # Criar artifact para o arquivo original
            if article.original_file:
                ArticleArtifact.objects.create(
                    article=article,
                    artifact_type='docx_original',
                    file=article.original_file,
                    language='pt',  # Default, pode ser atualizado depois
                    is_current=True,
                )
            
            messages.success(request, _('Manuscript created successfully!'))
            return redirect('editorial_article_detail', pk=article.pk)
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = ArticleUploadForm()
    
    context = {
        'form': form,
        'title': _('New Manuscript'),
        'cancel_url': reverse('editorial_queue'),
    }
    
    return render(request, 'markup_doc/article_form.html', context)


@login_required
@staff_member_required
def article_detail(request, pk):
    """
    Hub central do artigo com todas as informações e artefatos.
    
    Mostra:
    - Documento original
    - DOCX marcado
    - XML SPS
    - Referências validadas
    - Validação SPS
    - PDFs e HTMLs
    - Linha do tempo de processamento
    """
    article = get_object_or_404(
        Article.objects.prefetch_related(
            'artifacts',
            'processing_logs',
            'references',
            'sps_validations'
        ),
        pk=pk
    )
    
    # Organizar artifacts por tipo
    artifacts_by_type = {}
    for artifact in article.artifacts.all():
        if artifact.artifact_type not in artifacts_by_type:
            artifacts_by_type[artifact.artifact_type] = []
        artifacts_by_type[artifact.artifact_type].append(artifact)
    
    # Obter artifact atual de cada tipo
    current_artifacts = {}
    for artifact_type, artifacts in artifacts_by_type.items():
        current = next((a for a in artifacts if a.is_current), None)
        if current:
            current_artifacts[artifact_type] = current
    
    # Estatísticas de referências
    refs_stats = {
        'total': article.references.count(),
        'validated': article.references.filter(is_validated=True).count(),
        'with_doi': article.references.exclude(matched_doi__isnull=True).exclude(matched_doi='').count(),
    }
    
    # Último log de processamento
    last_log = article.processing_logs.order_by('-started_at').first()
    
    # Próximas ações sugeridas
    suggested_actions = []
    if article.status == ProcessStatus.PENDING:
        suggested_actions.append({
            'label': _('Start Processing'),
            'url': reverse('editorial_article_reprocess', kwargs={'pk': article.pk}),
            'icon': 'play',
            'primary': True,
        })
    elif article.status == ProcessStatus.FAILED:
        suggested_actions.append({
            'label': _('Reprocess'),
            'url': reverse('editorial_article_reprocess', kwargs={'pk': article.pk}),
            'icon': 'refresh',
            'primary': True,
        })
    
    if current_artifacts.get('docx_marked'):
        suggested_actions.append({
            'label': _('Download Marked DOCX'),
            'url': current_artifacts['docx_marked'].file.url,
            'icon': 'download',
            'primary': False,
        })
    
    if current_artifacts.get('xml_sps'):
        suggested_actions.append({
            'label': _('View XML'),
            'url': current_artifacts['xml_sps'].file.url,
            'icon': 'code',
            'primary': False,
        })
    
    context = {
        'article': article,
        'artifacts_by_type': artifacts_by_type,
        'current_artifacts': current_artifacts,
        'refs_stats': refs_stats,
        'last_log': last_log,
        'suggested_actions': suggested_actions,
        'status_choices': ProcessStatus.choices,
        'queue_url': reverse('editorial_queue'),
    }
    
    return render(request, 'markup_doc/article_detail.html', context)


@login_required
@staff_member_required
@require_POST
def article_reprocess(request, pk):
    """
    Reiniciar o processamento de um artigo.
    
    Limpa erro anterior, define status como PROCESSING e dispara task.
    """
    article = get_object_or_404(Article, pk=pk)
    
    # Resetar estado
    article.status = ProcessStatus.PROCESSING
    article.error_message = ''
    article.processing_started_at = None
    article.processed_at = None
    article.save()
    
    # Criar log de reprocessamento
    ArticleProcessingLog.objects.create(
        article=article,
        stage='upload',
        status='started',
        error_message=None,
    )
    
    # Disparar task de processamento (importar aqui para evitar circular import)
    from .tasks import task_process_article
    task = task_process_article.delay(article.pk, request.user.pk)
    
    # Atualizar log com task_id
    log = article.processing_logs.latest('started_at')
    log.task_id = task.id
    log.save()
    
    messages.success(request, _('Processing started successfully!'))
    
    # Se for AJAX, retornar JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': _('Processing started'),
            'task_id': task.id,
        })
    
    return redirect('editorial_article_detail', pk=article.pk)


@login_required
@staff_member_required
def article_download_artifact(request, pk, artifact_type):
    """
    Download de um artifact específico do artigo.
    """
    article = get_object_or_404(Article, pk=pk)
    artifact = get_object_or_404(
        ArticleArtifact.objects.filter(
            article=article,
            artifact_type=artifact_type,
            is_current=True
        ).first()
    )
    
    if not artifact.file:
        messages.error(request, _('File not available'))
        return redirect('editorial_article_detail', pk=article.pk)
    
    # Em produção, usar django-sendfile ou similar
    from django.http import FileResponse
    response = FileResponse(artifact.file)
    response['Content-Disposition'] = f'attachment; filename="{artifact.file.name}"'
    return response


@login_required
@staff_member_required
def article_references_detail(request, pk):
    """
    Detalhe das referências de um artigo com tabela interativa.
    """
    article = get_object_or_404(
        Article.objects.prefetch_related('references__element_citations'),
        pk=pk
    )
    
    references = article.references.all().order_by('ref_id')
    
    context = {
        'article': article,
        'references': references,
        'queue_url': reverse('editorial_queue'),
        'article_url': reverse('editorial_article_detail', kwargs={'pk': pk}),
    }
    
    return render(request, 'markup_doc/article_references.html', context)


@login_required
@staff_member_required
def article_timeline(request, pk):
    """
    Timeline completa de processamento do artigo.
    """
    article = get_object_or_404(
        Article.objects.prefetch_related('processing_logs'),
        pk=pk
    )
    
    logs = article.processing_logs.all().order_by('-started_at')
    
    context = {
        'article': article,
        'logs': logs,
        'queue_url': reverse('editorial_queue'),
        'article_url': reverse('editorial_article_detail', kwargs={'pk': pk}),
    }
    
    return render(request, 'markup_doc/article_timeline.html', context)
