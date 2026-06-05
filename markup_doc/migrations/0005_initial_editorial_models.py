# Generated migration for new editorial models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('markup_doc', '0004_articledocxmarkup_xref_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Last update date')),
                ('title', models.TextField(verbose_name='Title')),
                ('doi', models.CharField(blank=True, max_length=255, null=True, verbose_name='DOI')),
                ('original_file', models.FileField(blank=True, null=True, upload_to='articles/original/', verbose_name='Original Document')),
                ('journal_acronym', models.CharField(blank=True, max_length=50, null=True, verbose_name='Journal Acronym')),
                ('issue_identifier', models.CharField(blank=True, max_length=50, null=True, verbose_name='Issue Identifier')),
                ('fpage', models.CharField(blank=True, max_length=20, null=True, verbose_name='First Page')),
                ('lpage', models.CharField(blank=True, max_length=20, null=True, verbose_name='Last Page')),
                ('elocation_id', models.CharField(blank=True, max_length=50, null=True, verbose_name='E-location ID')),
                ('status', models.IntegerField(choices=[(0, 'Pending'), (1, 'Processing'), (2, 'Processed'), (3, 'Failed'), (4, 'Cancelled')], default=0, verbose_name='Process Status')),
                ('error_message', models.TextField(blank=True, null=True, verbose_name='Error Message')),
                ('processed_at', models.DateTimeField(blank=True, null=True, verbose_name='Processed At')),
                ('processing_started_at', models.DateTimeField(blank=True, null=True, verbose_name='Processing Started At')),
                ('creator', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='article_creator', to=settings.AUTH_USER_MODEL, verbose_name='Creator')),
                ('updated_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='article_last_mod_user', to=settings.AUTH_USER_MODEL, verbose_name='Updater')),
            ],
            options={
                'verbose_name': 'Article',
                'verbose_name_plural': 'Articles',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='ArticleArtifact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Last update date')),
                ('artifact_type', models.CharField(choices=[('docx_original', 'Original DOCX'), ('docx_marked', 'Marked DOCX'), ('xml_sps', 'XML SPS'), ('pdf', 'PDF'), ('html', 'HTML'), ('zip_package', 'ZIP Package'), ('validation_report', 'Validation Report'), ('exceptions_report', 'Exceptions Report')], max_length=50, verbose_name='Artifact Type')),
                ('file', models.FileField(blank=True, null=True, upload_to='articles/artifacts/%Y/%m/%d/', verbose_name='File')),
                ('language', models.CharField(default='pt', help_text='Language code (pt, en, es)', max_length=10, verbose_name='Language')),
                ('version', models.PositiveIntegerField(default=1, help_text='Version number of this artifact', verbose_name='Version')),
                ('is_current', models.BooleanField(default=True, help_text='Indicates if this is the current version of the artifact', verbose_name='Is Current Version')),
                ('file_size_bytes', models.PositiveBigIntegerField(default=0, verbose_name='File Size (bytes)')),
                ('checksum', models.CharField(blank=True, help_text='SHA256 checksum of the file', max_length=64, null=True, verbose_name='Checksum')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional metadata about this artifact', verbose_name='Metadata')),
                ('creator', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='articleartifact_creator', to=settings.AUTH_USER_MODEL, verbose_name='Creator')),
                ('updated_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='articleartifact_last_mod_user', to=settings.AUTH_USER_MODEL, verbose_name='Updater')),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='artifacts', to='markup_doc.article', verbose_name='Article')),
            ],
            options={
                'verbose_name': 'Article Artifact',
                'verbose_name_plural': 'Article Artifacts',
                'ordering': ['article', 'artifact_type', '-version'],
            },
        ),
        migrations.CreateModel(
            name='Reference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Last update date')),
                ('mixed_citation', models.TextField(verbose_name='Mixed Citation')),
                ('ref_id', models.CharField(blank=True, help_text='Internal reference identifier', max_length=50, null=True, verbose_name='Reference ID')),
                ('is_validated', models.BooleanField(default=False, help_text='Indicates if this reference has been validated', verbose_name='Is Validated')),
                ('validation_score', models.IntegerField(blank=True, help_text='Score from 1 to 10 indicating validation confidence', null=True, verbose_name='Validation Score')),
                ('matched_doi', models.CharField(blank=True, help_text='DOI found during validation', max_length=255, null=True, verbose_name='Matched DOI')),
                ('creator', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reference_creator', to=settings.AUTH_USER_MODEL, verbose_name='Creator')),
                ('updated_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reference_last_mod_user', to=settings.AUTH_USER_MODEL, verbose_name='Updater')),
                ('article', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='references', to='markup_doc.article', verbose_name='Article')),
            ],
            options={
                'verbose_name': 'Reference',
                'verbose_name_plural': 'References',
                'ordering': ['article', 'ref_id'],
            },
        ),
        migrations.CreateModel(
            name='ElementCitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False)),
                ('element_type', models.CharField(choices=[('person', 'Person'), ('title', 'Title'), ('source', 'Source'), ('date', 'Date'), ('volume', 'Volume'), ('issue', 'Issue'), ('pages', 'Pages'), ('doi', 'DOI'), ('url', 'URL'), ('publisher', 'Publisher'), ('organization', 'Organization')], default='person', max_length=50, verbose_name='Element Type')),
                ('content', models.JSONField(default=dict, help_text='Structured content of this element', verbose_name='Content')),
                ('marked_xml', models.TextField(blank=True, help_text='XML markup for this element', verbose_name='Marked XML')),
                ('reference', modelcluster.fields.ParentalKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='element_citations', to='markup_doc.reference')),
            ],
            options={
                'ordering': ['sort_order'],
            },
        ),
        migrations.CreateModel(
            name='ArticleProcessingLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Last update date')),
                ('stage', models.CharField(choices=[('upload', 'Upload'), ('markup', 'Markup'), ('xref_validation', 'XRef Validation'), ('xml_generation', 'XML Generation'), ('sps_validation', 'SPS Validation'), ('pdf_generation', 'PDF Generation'), ('html_generation', 'HTML Generation'), ('package_creation', 'Package Creation')], max_length=50, verbose_name='Processing Stage')),
                ('status', models.CharField(choices=[('started', 'Started'), ('completed', 'Completed'), ('failed', 'Failed')], default='started', max_length=20, verbose_name='Status')),
                ('error_message', models.TextField(blank=True, null=True, verbose_name='Error Message')),
                ('started_at', models.DateTimeField(auto_now_add=True, verbose_name='Started At')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Completed At')),
                ('duration_seconds', models.FloatField(blank=True, help_text='Processing duration in seconds', null=True, verbose_name='Duration (seconds)')),
                ('task_id', models.CharField(blank=True, help_text='Celery task ID', max_length=255, null=True, verbose_name='Task ID')),
                ('creator', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='articleprocessinglog_creator', to=settings.AUTH_USER_MODEL, verbose_name='Creator')),
                ('updated_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='articleprocessinglog_last_mod_user', to=settings.AUTH_USER_MODEL, verbose_name='Updater')),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='processing_logs', to='markup_doc.article', verbose_name='Article')),
            ],
            options={
                'verbose_name': 'Processing Log',
                'verbose_name_plural': 'Processing Logs',
                'ordering': ['article', '-started_at'],
            },
        ),
        migrations.CreateModel(
            name='SPSPackageValidation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Last update date')),
                ('package_file', models.FileField(blank=True, help_text='ZIP package file for validation', null=True, upload_to='articles/validations/packages/', verbose_name='Package File')),
                ('validation_report', models.FileField(blank=True, null=True, upload_to='articles/validations/reports/', verbose_name='Validation Report')),
                ('exceptions_report', models.FileField(blank=True, null=True, upload_to='articles/validations/exceptions/', verbose_name='Exceptions Report')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('done', 'Done'), ('error', 'Error')], default='pending', max_length=20, verbose_name='Status')),
                ('error_message', models.TextField(blank=True, null=True, verbose_name='Error Message')),
                ('validated_at', models.DateTimeField(blank=True, null=True, verbose_name='Validated At')),
                ('zip_size_bytes', models.PositiveBigIntegerField(default=0, verbose_name='ZIP Size (bytes)')),
                ('validation_level', models.CharField(choices=[('production', 'Production'), ('pre_production', 'Pre-production'), ('minimum', 'Minimum')], default='production', max_length=50, verbose_name='Validation Level')),
                ('creator', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='spspackagevalidation_creator', to=settings.AUTH_USER_MODEL, verbose_name='Creator')),
                ('updated_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='spspackagevalidation_last_mod_user', to=settings.AUTH_USER_MODEL, verbose_name='Updater')),
                ('article', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sps_validations', to='markup_doc.article', verbose_name='Article')),
            ],
            options={
                'verbose_name': 'SPS Package Validation',
                'verbose_name_plural': 'SPS Package Validations',
                'ordering': ['-created'],
            },
        ),
        migrations.AddIndex(
            model_name='articleartifact',
            index=models.Index(fields=['article', 'artifact_type', 'is_current'], name='markup_doc__article_95d857_idx'),
        ),
        migrations.AddIndex(
            model_name='articleprocessinglog',
            index=models.Index(fields=['article', '-started_at'], name='markup_doc__article_f2a3c1_idx'),
        ),
        migrations.AddIndex(
            model_name='articleprocessinglog',
            index=models.Index(fields=['status', 'stage'], name='markup_doc__article_4d8f2e_idx'),
        ),
    ]
