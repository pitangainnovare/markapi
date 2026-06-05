"""
Novos modelos para a plataforma editorial MarkAPI.

Esta refatoração cria uma estrutura limpa e integrada centrada no artigo,
com rastreabilidade completa de todos os artefatos gerados.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey
from wagtail.models import Orderable

from core.models import CommonControlField
from core.forms import CoreAdminModelForm


class ProcessStatus(models.IntegerChoices):
    """Estados possíveis no ciclo de processamento de um artigo."""
    PENDING = 0, _("Pending")
    PROCESSING = 1, _("Processing")
    PROCESSED = 2, _("Processed")
    FAILED = 3, _("Failed")
    CANCELLED = 4, _("Cancelled")


class Article(CommonControlField, ClusterableModel):
    """
    Modelo central que representa um manuscrito no ciclo editorial.
    
    Este modelo consolida informações do artigo e serve como ponto de vínculo
    para todos os artefatos derivados (DOCX marcado, XML, PDF, HTML, validações).
    """
    
    # Identificação básica
    title = models.TextField(_("Title"), null=False, blank=False)
    doi = models.CharField(_("DOI"), max_length=255, null=True, blank=True)
    
    # Documento original
    original_file = models.FileField(
        _("Original Document"),
        upload_to="articles/original/",
        null=True,
        blank=True,
        help_text=_("Original DOCX file uploaded by the author")
    )
    
    # Vínculos com periódico e fascículo
    journal_acronym = models.CharField(
        _("Journal Acronym"),
        max_length=50,
        null=True,
        blank=True,
        help_text=_("Journal acronym (e.g., rbp, spmj)")
    )
    issue_identifier = models.CharField(
        _("Issue Identifier"),
        max_length=50,
        null=True,
        blank=True,
        help_text=_("Issue identifier in format vXnYsZ")
    )
    
    # Informações de paginação
    fpage = models.CharField(_("First Page"), max_length=20, null=True, blank=True)
    lpage = models.CharField(_("Last Page"), max_length=20, null=True, blank=True)
    elocation_id = models.CharField(_("E-location ID"), max_length=50, null=True, blank=True)
    
    # Estado do processamento
    status = models.IntegerField(
        _("Process Status"),
        choices=ProcessStatus.choices,
        default=ProcessStatus.PENDING,
    )
    error_message = models.TextField(
        _("Error Message"),
        blank=True,
        null=True,
        help_text=_("Last error message from processing")
    )
    
    # Metadados de processamento
    processed_at = models.DateTimeField(_("Processed At"), null=True, blank=True)
    processing_started_at = models.DateTimeField(_("Processing Started At"), null=True, blank=True)
    
    panels = [
        MultiFieldPanel(
            [
                FieldPanel("title"),
                FieldPanel("doi"),
            ],
            heading=_("Identification")
        ),
        MultiFieldPanel(
            [
                FieldPanel("original_file"),
            ],
            heading=_("Original Document")
        ),
        MultiFieldPanel(
            [
                FieldPanel("journal_acronym"),
                FieldPanel("issue_identifier"),
                FieldPanel("fpage"),
                FieldPanel("lpage"),
                FieldPanel("elocation_id"),
            ],
            heading=_("Journal Information")
        ),
        MultiFieldPanel(
            [
                FieldPanel("status"),
                FieldPanel("error_message", read_only=True),
                FieldPanel("processed_at", read_only=True),
            ],
            heading=_("Processing Status")
        ),
        InlinePanel("artifacts", label=_("Artifacts")),
        InlinePanel("processing_logs", label=_("Processing Logs")),
    ]
    
    base_form_class = CoreAdminModelForm
    
    def __str__(self):
        return self.title or f"Article {self.pk}"
    
    def get_status_display(self):
        return self.get_status_display()
    
    @property
    def has_error(self):
        return bool(self.error_message)
    
    @property
    def is_processed(self):
        return self.status == ProcessStatus.PROCESSED
    
    @property
    def is_failed(self):
        return self.status == ProcessStatus.FAILED
    
    @property
    def is_processing(self):
        return self.status == ProcessStatus.PROCESSING
    
    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
        ordering = ["-created"]


class ArticleArtifact(CommonControlField):
    """
    Modelo que representa qualquer produto derivado de um artigo.
    
    Este modelo unifica o gerenciamento de todos os arquivos gerados
    a partir de um artigo: DOCX marcado, XML SPS, PDF, HTML, ZIP, etc.
    """
    
    ARTICLE_ARTIFACT_TYPES = [
        ("docx_original", _("Original DOCX")),
        ("docx_marked", _("Marked DOCX")),
        ("xml_sps", _("XML SPS")),
        ("pdf", _("PDF")),
        ("html", _("HTML")),
        ("zip_package", _("ZIP Package")),
        ("validation_report", _("Validation Report")),
        ("exceptions_report", _("Exceptions Report")),
    ]
    
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="artifacts",
        verbose_name=_("Article")
    )
    
    artifact_type = models.CharField(
        _("Artifact Type"),
        max_length=50,
        choices=ARTICLE_ARTIFACT_TYPES,
    )
    
    file = models.FileField(
        _("File"),
        upload_to="articles/artifacts/%Y/%m/%d/",
        null=True,
        blank=True
    )
    
    language = models.CharField(
        _("Language"),
        max_length=10,
        default="pt",
        help_text=_("Language code (pt, en, es)")
    )
    
    version = models.PositiveIntegerField(
        _("Version"),
        default=1,
        help_text=_("Version number of this artifact")
    )
    
    is_current = models.BooleanField(
        _("Is Current Version"),
        default=True,
        help_text=_("Indicates if this is the current version of the artifact")
    )
    
    file_size_bytes = models.PositiveBigIntegerField(
        _("File Size (bytes)"),
        default=0
    )
    
    checksum = models.CharField(
        _("Checksum"),
        max_length=64,
        blank=True,
        null=True,
        help_text=_("SHA256 checksum of the file")
    )
    
    metadata = models.JSONField(
        _("Metadata"),
        default=dict,
        blank=True,
        help_text=_("Additional metadata about this artifact")
    )
    
    panels = [
        FieldPanel("article"),
        FieldPanel("artifact_type"),
        FieldPanel("file"),
        FieldPanel("language"),
        FieldPanel("version"),
        FieldPanel("is_current"),
        FieldPanel("file_size_bytes"),
        FieldPanel("checksum"),
        FieldPanel("metadata"),
    ]
    
    def __str__(self):
        return f"{self.article.title[:30]} - {self.get_artifact_type_display()} (v{self.version})"
    
    def save(self, *args, **kwargs):
        # Atualizar tamanho do arquivo se existir
        if self.file and not self.file_size_bytes:
            try:
                self.file_size_bytes = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _("Article Artifact")
        verbose_name_plural = _("Article Artifacts")
        ordering = ["article", "artifact_type", "-version"]
        indexes = [
            models.Index(fields=["article", "artifact_type", "is_current"]),
        ]


class ArticleProcessingLog(CommonControlField):
    """
    Modelo para rastrear tentativas de processamento de um artigo.
    
    Registra cada tentativa de processamento, incluindo erros,
    duração e etapas concluídas.
    """
    
    PROCESSING_STAGES = [
        ("upload", _("Upload")),
        ("markup", _("Markup")),
        ("xref_validation", _("XRef Validation")),
        ("xml_generation", _("XML Generation")),
        ("sps_validation", _("SPS Validation")),
        ("pdf_generation", _("PDF Generation")),
        ("html_generation", _("HTML Generation")),
        ("package_creation", _("Package Creation")),
    ]
    
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="processing_logs",
        verbose_name=_("Article")
    )
    
    stage = models.CharField(
        _("Processing Stage"),
        max_length=50,
        choices=PROCESSING_STAGES,
    )
    
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=[
            ("started", _("Started")),
            ("completed", _("Completed")),
            ("failed", _("Failed")),
        ],
        default="started"
    )
    
    error_message = models.TextField(
        _("Error Message"),
        blank=True,
        null=True
    )
    
    started_at = models.DateTimeField(_("Started At"), auto_now_add=True)
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)
    
    duration_seconds = models.FloatField(
        _("Duration (seconds)"),
        null=True,
        blank=True,
        help_text=_("Processing duration in seconds")
    )
    
    task_id = models.CharField(
        _("Task ID"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Celery task ID")
    )
    
    panels = [
        FieldPanel("article"),
        FieldPanel("stage"),
        FieldPanel("status"),
        FieldPanel("error_message"),
        FieldPanel("started_at"),
        FieldPanel("completed_at"),
        FieldPanel("duration_seconds"),
        FieldPanel("task_id"),
    ]
    
    def __str__(self):
        return f"{self.article.title[:30]} - {self.get_stage_display()} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Calcular duração se completado
        if self.status == "completed" and self.started_at and self.completed_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _("Processing Log")
        verbose_name_plural = _("Processing Logs")
        ordering = ["article", "-started_at"]
        indexes = [
            models.Index(fields=["article", "-started_at"]),
            models.Index(fields=["status", "stage"]),
        ]


class Reference(CommonControlField, ClusterableModel):
    """
    Modelo de referência bibliográfica vinculado a um artigo.
    
    Armazena as referências extraídas do artigo e seus status de validação.
    """
    
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="references",
        verbose_name=_("Article"),
        null=True,
        blank=True
    )
    
    mixed_citation = models.TextField(
        _("Mixed Citation"),
        null=False,
        blank=False,
        help_text=_("Full citation text as it appears in the document")
    )
    
    ref_id = models.CharField(
        _("Reference ID"),
        max_length=50,
        null=True,
        blank=True,
        help_text=_("Internal reference identifier")
    )
    
    is_validated = models.BooleanField(
        _("Is Validated"),
        default=False,
        help_text=_("Indicates if this reference has been validated")
    )
    
    validation_score = models.IntegerField(
        _("Validation Score"),
        null=True,
        blank=True,
        help_text=_("Score from 1 to 10 indicating validation confidence")
    )
    
    matched_doi = models.CharField(
        _("Matched DOI"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("DOI found during validation")
    )
    
    panels = [
        FieldPanel("article"),
        FieldPanel("mixed_citation"),
        FieldPanel("ref_id"),
        FieldPanel("is_validated"),
        FieldPanel("validation_score"),
        FieldPanel("matched_doi"),
        InlinePanel("element_citations", label=_("Element Citations")),
    ]
    
    base_form_class = CoreAdminModelForm
    
    def __str__(self):
        return self.mixed_citation[:100] or f"Reference {self.pk}"
    
    class Meta:
        verbose_name = _("Reference")
        verbose_name_plural = _("References")
        ordering = ["article", "ref_id"]


class ElementCitation(Orderable):
    """
    Elementos estruturados de uma citação bibliográfica.
    """
    
    reference = ParentalKey(
        Reference,
        on_delete=models.CASCADE,
        related_name="element_citations",
        null=True
    )
    
    element_type = models.CharField(
        _("Element Type"),
        max_length=50,
        choices=[
            ("person", _("Person")),
            ("title", _("Title")),
            ("source", _("Source")),
            ("date", _("Date")),
            ("volume", _("Volume")),
            ("issue", _("Issue")),
            ("pages", _("Pages")),
            ("doi", _("DOI")),
            ("url", _("URL")),
            ("publisher", _("Publisher")),
            ("organization", _("Organization")),
        ],
        default="person"
    )
    
    content = models.JSONField(
        _("Content"),
        default=dict,
        help_text=_("Structured content of this element")
    )
    
    marked_xml = models.TextField(
        _("Marked XML"),
        blank=True,
        help_text=_("XML markup for this element")
    )
    
    panels = [
        FieldPanel("element_type"),
        FieldPanel("content"),
        FieldPanel("marked_xml"),
    ]
    
    def __str__(self):
        return f"{self.element_type}: {str(self.content)[:50]}"
    
    class Meta:
        ordering = ["sort_order"]


class SPSPackageValidation(CommonControlField):
    """
    Validação de pacote SPS vinculada a um artigo.
    """
    
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="sps_validations",
        verbose_name=_("Article"),
        null=True,
        blank=True
    )
    
    package_file = models.FileField(
        _("Package File"),
        upload_to="articles/validations/packages/",
        null=True,
        blank=True,
        help_text=_("ZIP package file for validation")
    )
    
    validation_report = models.FileField(
        _("Validation Report"),
        upload_to="articles/validations/reports/",
        null=True,
        blank=True
    )
    
    exceptions_report = models.FileField(
        _("Exceptions Report"),
        upload_to="articles/validations/exceptions/",
        null=True,
        blank=True
    )
    
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=[
            ("pending", _("Pending")),
            ("running", _("Running")),
            ("done", _("Done")),
            ("error", _("Error")),
        ],
        default="pending"
    )
    
    error_message = models.TextField(
        _("Error Message"),
        blank=True,
        null=True
    )
    
    validated_at = models.DateTimeField(_("Validated At"), null=True, blank=True)
    
    zip_size_bytes = models.PositiveBigIntegerField(
        _("ZIP Size (bytes)"),
        default=0
    )
    
    validation_level = models.CharField(
        _("Validation Level"),
        max_length=50,
        default="production",
        choices=[
            ("production", _("Production")),
            ("pre_production", _("Pre-production")),
            ("minimum", _("Minimum")),
        ]
    )
    
    panels = [
        FieldPanel("article"),
        FieldPanel("package_file"),
        FieldPanel("validation_report"),
        FieldPanel("exceptions_report"),
        FieldPanel("status"),
        FieldPanel("error_message"),
        FieldPanel("validated_at"),
        FieldPanel("zip_size_bytes"),
        FieldPanel("validation_level"),
    ]
    
    def __str__(self):
        return f"{self.article.title[:30]} - {self.status}" if self.article else f"Validation {self.pk}"
    
    class Meta:
        verbose_name = _("SPS Package Validation")
        verbose_name_plural = _("SPS Package Validations")
        ordering = ["-created"]
