# Especificação Técnica: Plataforma Editorial MarkAPI

**Versão:** 2.0  
**Status:** Aprovado para Implementação  
**Data:** 2025-01-15  
**Tipo:** Spec-Driven Development  

---

## 1. Visão Geral

### 1.1 Objetivo

Transformar o MarkAPI em uma plataforma editorial centrada no **ciclo de vida do artigo**, onde cada manuscrito é o núcleo de um ecossistema de produtos derivados (DOCX marcado, XML SPS, PDF, HTML, validações), com rastreabilidade completa, gestão robusta de erros e interface intuitiva.

### 1.2 Princípios de Design

1. **Single Source of Truth**: Cada artefato tem um dono claro e vínculos explícitos
2. **Fail Fast, Fail Clearly**: Erros são detectados cedo e apresentados de forma acionável
3. **Audit Trail Completo**: Toda ação é registrada e recuperável
4. **UX Centrada no Editor**: Fluxo linear, feedback visual claro, mínimo de cliques
5. **Separação de Responsabilidades**: Operacional vs. Técnico (Ferramentas Avançadas)

### 1.3 Escopo

- ✅ Novos modelos Django limpos e integrados
- ✅ Interface administrativa unificada para artigos
- ✅ Gestão de estados e retentativas
- ✅ Vínculo explícito entre artigo e todos os artefatos
- ✅ Validação de referências integrada
- ✅ Remoção de legado (coleções, campos obsoletos)
- ❌ Compatibilidade com versões anteriores (breaking changes permitidos)
- ❌ Dashboards separados (fila de artigos é a home)

---

## 2. Arquitetura de Dados

### 2.1 Diagrama Entidade-Relacionamento

```
┌─────────────────┐       ┌──────────────────┐
│    Journal      │───────│     Issue        │
└─────────────────┘       └──────────────────┘
         │                        │
         │                        │
         ▼                        ▼
┌────────────────────────────────────────────────┐
│                  Article                       │
│  (novo modelo central, substitui ArticleDocxMarkup) │
└────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌────────────────────────────────────────────────┐
│              ArticleArtifact                   │
│  (DOCX original, DOCX marcado, XML, PDF, HTML) │
└────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌────────────────────────────────────────────────┐
│            ArticleProcessingLog                │
│  (histórico de tentativas, erros, eventos)     │
└────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌────────────────────────────────────────────────┐
│             Reference                          │
│  (citações do texto + bibliografia)            │
└────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌────────────────────────────────────────────────┐
│          SPSPackageValidation                  │
│  (validações formais do XML)                   │
└────────────────────────────────────────────────┘
```

### 2.2 Modelos Django

#### 2.2.1 Modelo Central: `Article`

```python
class Article(models.Model):
    """
    Representa um manuscrito no ciclo editorial.
    Substitui ArticleDocxMarkup como modelo central.
    """
    
    # Identificadores
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500, help_text="Título do artigo")
    doi = models.CharField(max_length=100, blank=True, null=True, unique=True)
    pid = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    # Vínculos
    journal = models.ForeignKey(
        'core.Journal',
        on_delete=models.PROTECT,
        related_name='articles',
        help_text="Periódico vinculado"
    )
    issue = models.ForeignKey(
        'core.Issue',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='articles',
        help_text="Fascículo vinculado (opcional)"
    )
    
    # Estado do Processamento
    status = models.CharField(
        max_length=20,
        choices=ProcessStatus.choices,
        default=ProcessStatus.PENDING,
        db_index=True,
        help_text="Estado atual do processamento"
    )
    current_stage = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Etapa atual do fluxo (ex: 'markup', 'xml_generation', 'pdf')"
    )
    
    # Gestão de Erros
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Mensagem resumida do último erro"
    )
    error_details = models.JSONField(
        blank=True,
        null=True,
        help_text="Detalhes estruturados do erro"
    )
    error_traceback = models.TextField(
        blank=True,
        null=True,
        help_text="Stack trace completo para debug"
    )
    
    # Controle de Retentativas
    retry_count = models.IntegerField(default=0)
    last_retry_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    # Metadados Opcionais
    corresponding_author_email = models.EmailField(blank=True, null=True)
    keywords = models.JSONField(blank=True, null=True, help_text="Lista de palavras-chave")
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    original_checksum = models.CharField(max_length=64, blank=True, null=True, help_text="SHA256")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['journal', 'status']),
            models.Index(fields=['pid']),
            models.Index(fields=['doi']),
        ]
    
    def __str__(self):
        return f"{self.title[:50]} ({self.get_status_display()})"
    
    @property
    def can_retry(self):
        """Verifica se o artigo pode ser reprocessado"""
        return self.status in [ProcessStatus.FAILED, ProcessStatus.PARTIAL]
    
    @property
    def artifacts_summary(self):
        """Retorna resumo dos artefatos gerados"""
        return {
            'docx_original': self.artifacts.filter(artifact_type='docx_original', is_current=True).exists(),
            'docx_marked': self.artifacts.filter(artifact_type='docx_marked', is_current=True).exists(),
            'xml_sps': self.artifacts.filter(artifact_type='xml_sps', is_current=True).exists(),
            'pdf': self.artifacts.filter(artifact_type='pdf', is_current=True).exists(),
            'html': self.artifacts.filter(artifact_type='html', is_current=True).exists(),
        }
```

#### 2.2.2 Gerenciador de Artefatos: `ArticleArtifact`

```python
class ArticleArtifact(models.Model):
    """
    Modelo genérico para todos os produtos derivados de um artigo.
    Substitui campos duplicados e cria vínculo explícito.
    """
    
    article = models.ForeignKey(
        'Article',
        on_delete=models.CASCADE,
        related_name='artifacts',
        help_text="Artigo proprietário deste artefato"
    )
    
    artifact_type = models.CharField(
        max_length=50,
        choices=[
            ('docx_original', 'DOCX Original'),
            ('docx_marked', 'DOCX Marcado'),
            ('xml_sps', 'XML SPS'),
            ('pdf', 'PDF'),
            ('html', 'HTML'),
            ('package', 'Pacote ZIP'),
            ('validation_report', 'Relatório de Validação'),
        ],
        db_index=True,
        help_text="Tipo do artefato"
    )
    
    file = models.FileField(
        upload_to=artifact_upload_path,
        help_text="Arquivo do artefato"
    )
    
    version = models.CharField(
        max_length=20,
        default='1.0',
        help_text="Versão do artefato"
    )
    
    checksum = models.CharField(
        max_length=64,
        help_text="SHA256 do arquivo"
    )
    
    size_bytes = models.BigIntegerField(help_text="Tamanho em bytes")
    
    metadata = models.JSONField(
        blank=True,
        null=True,
        help_text="Metadados específicos do tipo"
    )
    # Exemplos:
    # PDF: {"pages": 15, "pdf_version": "1.7"}
    # XML: {"sps_version": "1.9", "validation_status": "approved"}
    # DOCX Marcado: {"citations_count": 45, "references_count": 47}
    
    is_current = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indica se esta é a versão vigente"
    )
    
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Usuário ou sistema que gerou este artefato"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['article', 'artifact_type', 'is_current']),
            models.Index(fields=['artifact_type', 'created_at']),
        ]
        constraints = [
            # Garante apenas um artefato corrente por tipo por artigo
            models.UniqueConstraint(
                fields=['article', 'artifact_type'],
                condition=models.Q(is_current=True),
                name='unique_current_artifact_per_type'
            )
        ]
    
    def __str__(self):
        return f"{self.article.title[:30]} - {self.get_artifact_type_display()} (v{self.version})"
    
    def save(self, *args, **kwargs):
        # Se este é marcado como current, marcar outros como não-current
        if self.is_current:
            ArticleArtifact.objects.filter(
                article=self.article,
                artifact_type=self.artifact_type,
                is_current=True
            ).exclude(id=self.id).update(is_current=False)
        super().save(*args, **kwargs)
```

#### 2.2.3 Log de Processamento: `ArticleProcessingLog`

```python
class ArticleProcessingLog(models.Model):
    """
    Auditoria completa de todas as tentativas de processamento.
    Substitui tracker genérico para foco no artigo.
    """
    
    article = models.ForeignKey(
        'Article',
        on_delete=models.CASCADE,
        related_name='processing_logs',
        help_text="Artigo relacionado"
    )
    
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('created', 'Artigo Criado'),
            ('upload', 'Upload de Documento'),
            ('processing_started', 'Início do Processamento'),
            ('stage_completed', 'Etapa Concluída'),
            ('validation_passed', 'Validação Aprovada'),
            ('validation_failed', 'Validação Falhou'),
            ('artifact_generated', 'Artefato Gerado'),
            ('error_occurred', 'Erro Ocorrido'),
            ('retry_initiated', 'Retentativa Iniciada'),
            ('processing_completed', 'Processamento Concluído'),
            ('metadata_updated', 'Metadados Atualizados'),
            ('manual_action', 'Ação Manual'),
        ],
        db_index=True,
        help_text="Tipo do evento"
    )
    
    stage = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Etapa do fluxo (ex: 'markup', 'xml_generation')"
    )
    
    status = models.CharField(
        max_length=20,
        choices=ProcessStatus.choices,
        help_text="Status resultante"
    )
    
    message = models.TextField(
        help_text="Mensagem descritiva do evento"
    )
    
    error_details = models.JSONField(
        blank=True,
        null=True,
        help_text="Detalhes do erro (se aplicável)"
    )
    
    duration_seconds = models.FloatField(
        blank=True,
        null=True,
        help_text="Duração da operação em segundos"
    )
    
    task_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="ID da task Celery"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['article', 'event_type']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"[{self.created_at}] {self.article.title[:30]} - {self.get_event_type_display()}"
```

#### 2.2.4 Estados de Processamento: `ProcessStatus`

```python
class ProcessStatus(models.TextChoices):
    """Estados possíveis do ciclo de processamento"""
    
    PENDING = 'pending', 'Pendente'
    PROCESSING = 'processing', 'Processando'
    PROCESSED = 'processed', 'Processado com Sucesso'
    PARTIAL = 'partial', 'Parcial (com avisos)'
    FAILED = 'failed', 'Falhou'
    CANCELLED = 'cancelled', 'Cancelado'
```

#### 2.2.5 Referências: `Reference` (Refatorado)

```python
class Reference(models.Model):
    """
    Referências bibliográficas vinculadas a um artigo.
    Inclui citações no texto e entradas da bibliografia.
    """
    
    article = models.ForeignKey(
        'Article',
        on_delete=models.CASCADE,
        related_name='references',
        help_text="Artigo proprietário desta referência"
    )
    
    reference_type = models.CharField(
        max_length=20,
        choices=[
            ('citation', 'Citação no Texto'),
            ('bibliography', 'Entrada na Bibliografia'),
        ],
        db_index=True,
        help_text="Tipo de referência"
    )
    
    # Para citações no texto
    citation_text = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Texto da citação (ex: 'Silva et al., 2020')"
    )
    
    citation_position = models.JSONField(
        blank=True,
        null=True,
        help_text="Posição no documento: {'paragraph': 5, 'offset': 120}"
    )
    
    # Para entradas na bibliografia
    bibliography_entry = models.TextField(
        blank=True,
        null=True,
        help_text="Texto completo da entrada bibliográfica"
    )
    
    # Vinculação entre citação e entrada
    linked_reference = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='citations',
        help_text="Entrada na bibliografia vinculada (para citações)"
    )
    
    # Validação
    validation_status = models.CharField(
        max_length=20,
        choices=[
            ('valid', 'Válida'),
            ('invalid', 'Inválida'),
            ('ambiguous', 'Ambígua (múltiplas opções)'),
            ('unmatched', 'Não encontrada'),
            ('pending', 'Pendente'),
        ],
        default='pending',
        db_index=True,
        help_text="Status da validação"
    )
    
    validation_details = models.JSONField(
        blank=True,
        null=True,
        help_text="Detalhes da validação"
    )
    # Ex: {"matched_confidence": 0.95, "alternatives": [...]}
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['reference_type', 'citation_position']
        indexes = [
            models.Index(fields=['article', 'reference_type']),
            models.Index(fields=['validation_status']),
        ]
    
    def __str__(self):
        text = self.citation_text or self.bibliography_entry[:50]
        return f"{text} ({self.get_validation_status_display()})"
```

#### 2.2.6 Validação SPS: `SPSPackageValidation` (Vinculado)

```python
class SPSPackageValidation(models.Model):
    """
    Validações formais de pacotes XML SPS.
    Agora vinculado explicitamente ao Article.
    """
    
    article = models.ForeignKey(
        'Article',
        on_delete=models.CASCADE,
        related_name='sps_validations',
        help_text="Artigo validado"
    )
    
    xml_artifact = models.OneToOneField(
        'ArticleArtifact',
        on_delete=models.CASCADE,
        related_name='sps_validation',
        limit_choices_to={'artifact_type': 'xml_sps'},
        help_text="Artefato XML validado"
    )
    
    sps_version = models.CharField(
        max_length=20,
        help_text="Versão do SPS utilizada"
    )
    
    validation_status = models.CharField(
        max_length=20,
        choices=[
            ('approved', 'Aprovado'),
            ('approved_with_warnings', 'Aprovado com Avisos'),
            ('rejected', 'Rejeitado'),
        ],
        db_index=True,
        help_text="Status da validação"
    )
    
    compliance_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentagem de conformidade (0-100)"
    )
    
    critical_errors = models.JSONField(
        default=list,
        help_text="Lista de erros críticos"
    )
    
    warnings = models.JSONField(
        default=list,
        help_text="Lista de avisos"
    )
    
    report_file = models.FileField(
        upload_to=validation_report_path,
        blank=True,
        null=True,
        help_text="Relatório completo em PDF/HTML"
    )
    
    validated_at = models.DateTimeField(auto_now_add=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Usuário ou sistema que executou a validação"
    )
    
    class Meta:
        ordering = ['-validated_at']
        indexes = [
            models.Index(fields=['article', 'validation_status']),
        ]
    
    def __str__(self):
        return f"{self.article.title[:30]} - SPS {self.sps_version} ({self.get_validation_status_display()})"
```

### 2.3 Migração de Dados

#### 2.3.1 Estratégia de Migração

```python
# migration_001_create_new_models.py

def migrate_articles(apps, schema_editor):
    """Migra ArticleDocxMarkup para Article"""
    ArticleDocxMarkup = apps.get_model('markup_doc', 'ArticleDocxMarkup')
    Article = apps.get_model('markup_doc', 'Article')
    ArticleArtifact = apps.get_model('markup_doc', 'ArticleArtifact')
    
    for old_article in ArticleDocxMarkup.objects.all():
        # Criar novo Article
        new_article = Article.objects.create(
            title=old_article.title or old_article.original_file.name,
            doi=old_article.doi,
            pid=old_article.pid,
            journal=old_article.journal,
            issue=old_article.issue,
            status=migrate_status(old_article.status),
            current_stage='migrated',
            original_filename=old_article.original_file.name if old_article.original_file else None,
            created_at=old_article.created_at,
        )
        
        # Migrar DOCX original como Artifact
        if old_article.original_file:
            create_artifact(
                article=new_article,
                artifact_type='docx_original',
                file=old_article.original_file,
                version='1.0',
            )
        
        # Migrar DOCX marcado como Artifact
        if old_article.marked_file:
            create_artifact(
                article=new_article,
                artifact_type='docx_marked',
                file=old_article.marked_file,
                version='1.0',
                metadata={'citations_count': old_article.citations_count or 0}
            )
        
        # Criar log de migração
        ArticleProcessingLog.objects.create(
            article=new_article,
            event_type='created',
            stage='migration',
            status=new_article.status,
            message=f'Migrado de ArticleDocxMarkup (ID: {old_article.id})',
        )

def migrate_stuck_processing(apps, schema_editor):
    """Marca registros presos em PROCESSING como FAILED"""
    Article = apps.get_model('markup_doc', 'Article')
    from datetime import timedelta
    from django.utils import timezone
    
    stuck_threshold = timezone.now() - timedelta(hours=24)
    
    Article.objects.filter(
        status='processing',
        updated_at__lt=stuck_threshold
    ).update(
        status='failed',
        error_message='Processamento legado recuperável - timeout detectado (>24h)',
        error_details={
            'stage': 'legacy_migration',
            'code': 'TIMEOUT_DETECTED',
            'suggestion': 'Reprocessar o artigo'
        }
    )
```

#### 2.3.2 Remoção de Legado

```python
# migration_002_remove_legacy.py

def remove_collections(apps, schema_editor):
    """Remove modelos de coleção"""
    # Deletar dados
    CollectionValuesModel = apps.get_model('markup_doc', 'CollectionValuesModel')
    CollectionValuesModel.objects.all().delete()
    
    CollectionModel = apps.get_model('markup_doc', 'CollectionModel')
    CollectionModel.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('markup_doc', '0001_create_new_models'),
    ]
    
    operations = [
        migrations.DeleteModel(name='CollectionModel'),
        migrations.DeleteModel(name='CollectionValuesModel'),
        migrations.RemoveField(
            model_name='articledocxmarkup',
            name='collection',
        ),
        # ... remover outros campos obsoletos
    ]
```

---

## 3. Interfaces Administrativas

### 3.1 Fila Editorial (ListView)

**Rota:** `/admin/articles/`  
**Template:** `markup_doc/admin/article_queue.html`

#### 3.1.1 Componentes

```
┌────────────────────────────────────────────────────────────┐
│  📰 Fila Editorial                    [+ Novo Manuscrito]  │
├────────────────────────────────────────────────────────────┤
│  Filtros: [Status ▼] [Periódico ▼] [Fascículo ▼] [🔍 Busca]│
├────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🟡 Artigo em Processamento                           │  │
│  │ Título: Impact of AI on Scientific Publishing        │  │
│  │ Periódico: SciELO Brazil | Fascículo: v.25 n.1 2025 │  │
│  │ Etapa: Validação SPS                                 │  │
│  │ Upload: 2025-01-15 10:30 | Atualização: 10:35       │  │
│  │ Próxima ação: Aguardando conclusão                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🔴 Artigo com Falha                                  │  │
│  │ Título: Climate Change Effects...                    │  │
│  │ Periódico: Rev Saúde Pública                         │  │
│  │ Erro: Elemento <title-group> ausente                 │  │
│  │ Upload: 2025-01-15 09:00                             │  │
│  │ [🔄 Reprocessar] [✏️ Editar]                         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

#### 3.1.2 Funcionalidades

- **Busca**: título, autor, DOI, PID, nome do arquivo
- **Filtros múltiplos**: status, periódico, fascículo, etapa, data range
- **Ordenação**: por data (padrão), título, status
- **Ações em lote**: reprocessar, vincular fascículo, exportar CSV
- **Paginação**: 25 itens por página (configurável)

### 3.2 Formulário de Upload (CreateView)

**Rota:** `/admin/articles/new/`  
**Template:** `markup_doc/admin/article_upload.html`

#### 3.2.1 Campos

```yaml
documento_docx:
  type: FileField
  required: true
  accept: .docx
  features: [drag-and-drop, progress-bar, virus-scan]
  validation:
    max_size: 50MB
    format: DOCX válido (OOXML)
    duplicate_check: SHA256 hash

titulo_provisorio:
  type: CharField
  required: false
  max_length: 500
  help: "Será extraído automaticamente se não informado"

periodico:
  type: ForeignKey (Journal)
  required: true
  widget: AutocompleteSelect
  search_fields: [title, short_title, acronym, issn_l, issn_p, issn_e]

fasciculo:
  type: ForeignKey (Issue)
  required: false
  widget: Select (filtrado pelo periódico)
  dependent_on: periodico

autor_correspondente:
  type: EmailField
  required: false

doi:
  type: CharField
  required: false
  validation: formato DOI válido

palavras_chave:
  type: TagField
  required: false
  widget: TagAutocomplete
```

#### 3.2.2 Fluxo Pós-Upload

1. Validar arquivo (tamanho, formato, duplicidade)
2. Calcular checksum SHA256
3. Criar registro `Article` com status `PENDING`
4. Salvar DOCX como `ArticleArtifact` (tipo `docx_original`)
5. Registrar log `ArticleProcessingLog` (evento `upload`)
6. Disparar task Celery `process_article_task(article_id)`
7. Redirecionar para Detail View do artigo
8. Mostrar toast: "Processamento iniciado em background"

### 3.3 Detalhe do Artigo (DetailView) - Hub Central

**Rota:** `/admin/articles/<uuid:pk>/`  
**Template:** `markup_doc/admin/article_detail.html`

#### 3.3.1 Estrutura da Página

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Voltar para Fila                                             │
├─────────────────────────────────────────────────────────────────┤
│  📄 Impact of AI on Scientific Publishing                       │
│  🟢 Processado com Sucesso                                      │
│  SciELO Brazil | v.25 n.1 2025                                  │
│  Upload: 2025-01-15 10:30 | Conclusão: 11:06                    │
│  [🔄 Reprocessar] [✏️ Editar] [📦 Baixar Pacote] [🗑️ Excluir]   │
├─────────────────────────────────────────────────────────────────┤
│  ABAS:                                                          │
│  [📄 Original] [🏷️ Marcado] [📚 Referências] [📄 XML]           │
│  [✅ Validação] [📊 Produtos] [⏱️ Linha do Tempo]               │
├─────────────────────────────────────────────────────────────────┤
│  CONTEÚDO DA ABA SELECIONADA                                    │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.3.2 Abas e Conteúdo

**Aba 1: Documento Original**
- Nome do arquivo, tamanho, checksum
- Botões: Baixar, Substituir (mantém histórico)
- Metadados: data upload, usuário

**Aba 2: DOCX Marcado**
- Status da marcação (sucesso/erro)
- Preview ou download
- Botão: Visualizar Citações Linkadas (modal)
- Lista de erros de marcação (se houver)

**Aba 3: Validação de Referências**
- Resumo: 45/47 citações válidas
- Tabela interativa:
  ```
  | Citação        | Status  | Referência       | Ação              |
  |----------------|---------|------------------|-------------------|
  | (Silva, 2020)  | ✅ Válida | Silva et al.    | [Ver]             |
  | (Santos, 2019) | ❌ Não enc. | -              | [Vincular Manual] |
  | (Oliveira,2021)| ⚠️ Múltiplas | 3 opções     | [Selecionar]      |
  ```
- Botões: Corrigir Vinculações, Revalidar

**Aba 4: XML SPS**
- Status de geração
- Versão SPS utilizada
- Botões: Baixar, Editar (admin), Validar Agora
- Erros de geração com linha/coluna

**Aba 5: Validação SPS**
- Status: Aprovado com 3 avisos
- Score de conformidade: 95%
- Lista ordenada por criticidade:
  - 🔴 Erro Crítico: "Elemento <title-group> ausente"
  - 🟡 Aviso: "Data de recebimento não informada"
  - 🟢 OK: "Estrutura de autores válida"
- Botões: Revalidar, Ver Relatório, Ignorar Avisos

**Aba 6: Produtos Derivados**
- Cards lado a lado:
  - **PDF**: Status, versões, baixar, visualizar
  - **HTML**: Status, baixar, visualizar
  - **Pacote ZIP**: Conteúdo, gerar, baixar
- Logs de geração (em caso de erro)

**Aba 7: Linha do Tempo**
- Timeline vertical com todos os eventos
- Filtro por tipo (erro, sucesso, ação manual)
- Expansão de detalhes por clique
- Exportar trilha (JSON/PDF)

#### 3.3.3 Componentes Visuais

- **Badges de Status**:
  - 🟢 Verde: `PROCESSED`
  - 🟡 Amarelo: `PROCESSING`, `PARTIAL`
  - 🔴 Vermelho: `FAILED`
  - 🔵 Azul: `PENDING`
  - 🟣 Roxo: `CANCELLED`

- **Barras de Progresso**: Para operações > 5s
- **Toasts**: Feedback imediato de ações
- **Modais**: Para ações secundárias (visualizar, editar)

---

## 4. Fluxo de Processamento

### 4.1 Máquina de Estados

```
┌─────────┐
│ PENDING │
└────┬────┘
     │ Upload
     ▼
┌────────────┐
│ PROCESSING │◄──────┐
└─────┬──────┘       │
      │              │ Retry
      ├─→ Sucesso ───┼──→ PROCESSED
      │              │
      ├─→ Avisos ────┼──→ PARTIAL
      │              │
      └─→ Erro ──────┴──→ FAILED
```

### 4.2 Task de Processamento

```python
@app.task(bind=True, max_retries=3)
def process_article_task(self, article_id):
    """Task principal de processamento de artigo"""
    
    article = Article.objects.get(id=article_id)
    
    # Iniciar processamento
    article.status = ProcessStatus.PROCESSING
    article.current_stage = 'markup'
    article.error_message = None
    article.error_details = None
    article.error_traceback = None
    article.save()
    
    log = ArticleProcessingLog.objects.create(
        article=article,
        event_type='processing_started',
        stage='markup',
        status=ProcessStatus.PROCESSING,
        message='Início do processamento',
        task_id=self.request.id,
    )
    
    try:
        # Etapa 1: Marcação DOCX
        marked_docx = run_markup(article)
        create_artifact(article, 'docx_marked', marked_docx)
        log_event(article, 'stage_completed', 'markup', ProcessStatus.PROCESSED)
        
        # Etapa 2: Validação de Referências
        references = validate_references(article)
        log_event(article, 'validation_passed', 'references', ProcessStatus.PROCESSED)
        
        # Etapa 3: Geração XML SPS
        xml = generate_sps_xml(article)
        xml_artifact = create_artifact(article, 'xml_sps', xml)
        log_event(article, 'artifact_generated', 'xml', ProcessStatus.PROCESSED)
        
        # Etapa 4: Validação SPS
        validation = validate_sps(xml_artifact)
        if validation.validation_status == 'rejected':
            raise SPSValidationError(validation.critical_errors)
        
        # Etapa 5: Geração PDF/HTML
        pdf = generate_pdf(article)
        create_artifact(article, 'pdf', pdf)
        
        html = generate_html(article)
        create_artifact(article, 'html', html)
        
        # Conclusão
        if validation.warnings:
            article.status = ProcessStatus.PARTIAL
            article.error_message = f'{len(validation.warnings)} avisos'
        else:
            article.status = ProcessStatus.PROCESSED
        
        article.processed_at = timezone.now()
        article.save()
        
        log_event(article, 'processing_completed', None, article.status)
        
    except Exception as exc:
        # Falha
        article.status = ProcessStatus.FAILED
        article.error_message = str(exc)[:200]
        article.error_details = {
            'stage': article.current_stage,
            'code': get_error_code(exc),
            'message': str(exc),
        }
        article.error_traceback = traceback.format_exc()
        article.retry_count += 1
        article.last_retry_at = timezone.now()
        article.save()
        
        log_event(
            article, 
            'error_occurred', 
            article.current_stage, 
            ProcessStatus.FAILED,
            error_details=article.error_details,
        )
        
        # Retry automático para erros transitórios
        if should_retry(exc):
            raise self.retry(exc=exc, countdown=60)
```

### 4.3 Tratamento de Erros

```python
ERROR_CODES = {
    'MISSING_TITLE_GROUP': 'Adicionar <title-group> no XML',
    'INVALID_DOI_FORMAT': 'Verificar formato do DOI',
    'CITATION_NOT_FOUND': 'Vincular citação manualmente',
    'FILE_CORRUPTED': 'Substituir arquivo DOCX',
    'TIMEOUT': 'Reprocessar ou contatar suporte',
}

def get_error_code(exc):
    """Mapeia exceção para código de erro"""
    if isinstance(exc, SPSValidationError):
        return 'SPS_VALIDATION_FAILED'
    if isinstance(exc, DOCXMarkingError):
        return 'DOCX_MARKING_FAILED'
    if isinstance(exc, TimeoutError):
        return 'TIMEOUT'
    return 'UNKNOWN_ERROR'
```

---

## 5. Menu e Navegação

### 5.1 Estrutura do Menu Admin

```python
MENU_STRUCTURE = [
    {
        'label': 'Artigos',
        'icon': 'doc-empty',
        'url': '/admin/articles/',
        'order': 1,
        'is_home': True,  # Redireciona /admin/ para cá
    },
    {
        'label': 'Periódicos',
        'icon': 'book',
        'url': '/admin/core/journal/',
        'order': 2,
        'search_fields': ['title', 'short_title', 'acronym', 'issn_l', 'issn_p', 'issn_e'],
    },
    {
        'label': 'Fascículos',
        'icon': 'folder',
        'url': '/admin/core/issue/',
        'order': 3,
        'filters': ['journal', 'volume', 'number', 'year'],
    },
    {
        'label': 'Configurações',
        'icon': 'cog',
        'url': '/admin/settings/',
        'order': 4,
        'children': [
            {'label': 'Usuários', 'url': '/admin/users/'},
            {'label': 'Preferências', 'url': '/admin/preferences/'},
            {'label': 'Integrações', 'url': '/admin/integrations/'},
        ],
    },
    {
        'label': 'Ferramentas Avançadas',
        'icon': 'wagtail',
        'url': '/admin/advanced/',
        'order': 5,
        'permission': 'is_superuser',  # Só aparece para superusuários
        'children': [
            {'label': 'Editor XML', 'url': '/admin/advanced/xml-editor/'},
            {'label': 'Documentos XML', 'url': '/admin/xml_manager/xmldocument/'},
            {'label': 'Validações SPS', 'url': '/admin/xml_manager/spsvalidation/'},
            {'label': 'PDFs', 'url': '/admin/xml_manager/pdf/'},
            {'label': 'HTMLs', 'url': '/admin/xml_manager/html/'},
            {'label': 'Referências', 'url': '/admin/reference/reference/'},
            {'label': 'Eventos', 'url': '/admin/tracker/event/'},
            {'label': 'Relatórios', 'url': '/admin/reports/'},
        ],
    },
]
```

### 5.2 Remoção de Grupos Antigos

- ❌ Remover: "Marcação"
- ❌ Remover: "Journal Manager"
- ✅ Manter: Periódicos e Fascículos como itens de menu principais

### 5.3 Sincronização Explícita

```python
# views.py

@login_required
@require_http_methods(["POST"])
def sync_journals_view(request):
    """Aciona sincronização de periódicos em background"""
    task = sync_journals_from_core.delay()
    messages.success(
        request,
        f"Sincronização iniciada (Task ID: {task.id}). Atualize a página em alguns minutos."
    )
    return redirect('admin:core_journal_changelist')

@login_required
@require_http_methods(["POST"])
def sync_issues_view(request):
    """Aciona sincronização de fascículos em background"""
    task = sync_issues_from_core.delay()
    messages.success(
        request,
        f"Sincronização iniciada (Task ID: {task.id})."
    )
    return redirect('admin:core_issue_changelist')
```

**Templates**: Adicionar botões nas listas:
```html
<form method="post" action="{% url 'admin:sync_journals' %}">
  {% csrf_token %}
  <button type="submit" class="button button-small">
    🔄 Sincronizar Periódicos
  </button>
</form>
```

---

## 6. Critérios de Aceitação

### 6.1 Funcionais

- [ ] Criar artigo via formulário de upload
- [ ] Visualizar fila com filtros e busca
- [ ] Acessar detalhe completo do artigo (todas as abas)
- [ ] Reprocessar artigo com status FAILED
- [ ] Vincular citações manualmente
- [ ] Baixar pacote ZIP completo
- [ ] Visualizar linha do tempo de eventos
- [ ] Sincronizar periódicos/fascículos explicitamente
- [ ] Ferramentas Avançadas visíveis apenas para superusuários

### 6.2 Não-Funcionais

- [ ] Tempo de carregamento da fila < 2s (com 1000 artigos)
- [ ] Upload de arquivos até 50MB
- [ ] Tasks em background não bloqueiam interface
- [ ] Layout responsivo (desktop e tablet)
- [ ] Acessibilidade WCAG 2.1 nível AA

### 6.3 Testes Obrigatórios

```python
# tests/test_article_workflow.py

def test_create_article_via_upload():
    """Testa criação de artigo pelo formulário"""
    pass

def test_article_status_transitions():
    """Testa transições de estado (PENDING → PROCESSING → PROCESSED/FAILED)"""
    pass

def test_error_persistence_on_failure():
    """Testa persistência de erro quando task falha"""
    pass

def test_error_cleanup_on_retry():
    """Testa limpeza de erro ao reprocessar"""
    pass

def test_migration_of_stuck_processing():
    """Testa migração de registros PROCESSING legados"""
    pass

def test_queue_filters_and_search():
    """Testa filtros e busca da fila"""
    pass

def test_explicit_sync_buttons():
    """Testa botões de sincronização explícita"""
    pass

def test_no_auto_sync_on_page_load():
    """Testa que abrir telas não dispara sincronização"""
    pass

def test_advanced_tools_permission():
    """Testa que Ferramentas Avançadas só aparece para admins"""
    pass

def test_artifact_linkage():
    """Testa vínculo entre artigo e artefatos"""
    pass

def test_reference_validation_table():
    """Testa tabela interativa de referências"""
    pass

def test_full_package_download():
    """Testa geração e download de pacote ZIP"""
    pass
```

---

## 7. Plano de Implementação

### Fase 1: Modelos e Migrações (Semana 1)

1. Criar novos modelos (`Article`, `ArticleArtifact`, `ArticleProcessingLog`)
2. Escrever migrações de dados
3. Implementar remoção de legado (coleções)
4. Testes unitários de modelos

### Fase 2: Views e Templates (Semana 2)

1. Implementar Fila Editorial (ListView)
2. Implementar Formulário de Upload (CreateView)
3. Implementar Detalhe do Artigo (DetailView)
4. Componentes UI (badges, timeline, tabelas)
5. Testes de integração

### Fase 3: Processamento e Tasks (Semana 3)

1. Refatorar task `process_article_task`
2. Implementar máquina de estados
3. Tratamento estruturado de erros
4. Logs de processamento
5. Testes end-to-end

### Fase 4: Menu e Permissões (Semana 4)

1. Reestruturar menu admin
2. Implementar controle de acesso (Ferramentas Avançadas)
3. Botões de sincronização explícita
4. Redirecionamento da home admin
5. Testes de UX

### Fase 5: Polimento e Documentação (Semana 5)

1. Testes de carga e performance
2. Ajustes de responsividade
3. Documentação de usuário
4. Treinamento da equipe
5. Deploy em staging

---

## 8. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Perda de dados na migração | Alto | Backup prévio, migração em etapas, rollback plan |
| Performance da fila com muitos artigos | Médio | Paginação, índices DB, cache |
| Resistência dos usuários à mudança | Médio | Treinamento, documentação, feedback loop |
| Bugs na task de processamento | Alto | Testes abrangentes, monitoramento, alertas |
| Dependência de APIs externas (Core) | Médio | Timeout, retry, fallback manual |

---

## 9. Glossário

- **Artigo**: Manuscrito científico em processamento
- **Artefato**: Produto derivado (DOCX, XML, PDF, HTML)
- **Trilha Editorial**: Sequência de etapas do processamento
- **SPS**: SciELO Publishing Schema (padrão XML)
- **Fallback**: Mecanismo de contingência (não implementado nesta fase)

---

## 10. Aprovações

- [ ] Product Owner
- [ ] Tech Lead
- [ ] Equipe de Desenvolvimento
- [ ] QA/Testing

---

**Documento vivo**: Esta especificação será atualizada conforme descobertas durante a implementação. Mudanças significativas devem ser registradas no changelog do projeto.
