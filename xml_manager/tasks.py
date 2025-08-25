import logging
import os
import tempfile

from packtools import data_checker

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from config import celery_app
from core.utils.utils import _get_user

from .models import XMLDocument


User = get_user_model()


@celery_app.task(bind=True, timelimit=-1)
def task_process_xml_document(self, xml_id, user_id=None, username=None):
    user = _get_user(self.request, username=username, user_id=user_id)

    try:
        xml_document = XMLDocument.objects.get(id=xml_id)
    except XMLDocument.DoesNotExist:
        logging.error(f'XML document with ID {xml_id} does not exist.')
        return False
    
    logging.info(f'Processing XML file {xml_document.xml_file.name}.')
    task_validate_xml_file.delay(xml_id, user_id=user_id, username=username)
    task_generate_pdf_file.delay(xml_id, user_id=user_id, username=username)
    task_generate_html_file.delay(xml_id, user_id=user_id, username=username)
    
    return True


@celery_app.task(bind=True, timelimit=-1)
def task_validate_xml_file(self, xml_id, user_id=None, username=None):
    user = _get_user(self.request, username=username, user_id=user_id)

    try:
        xml_file = XMLDocument.objects.get(id=xml_id)
    except XMLDocument.DoesNotExist:
        logging.error(f'XML file with ID {xml_id} does not exist.')
        return False
    
    logging.info(f'Starting XML validation for XML file {xml_file.xml_file.name}.')
    params = {}

    temp_dir = tempfile.gettempdir()
    base_filename = os.path.splitext(os.path.basename(xml_file.xml_file.name))[0]

    path_csv = os.path.join(temp_dir, f"{base_filename}.validation.csv")
    path_exceptions = os.path.join(temp_dir, f"{base_filename}.exceptions.json")

    try:
        validator = data_checker.XMLDataChecker(path_csv, path_exceptions, xml_file.xml_file.path)
        validator.validate(params=params, csv_per_xml=False)
    except Exception as e:
        logging.error(f'Error during XML validation: {e}')
        return False
    
    xml_file.validation_file = path_csv
    xml_file.exceptions_file = path_exceptions
    xml_file.save()
    logging.info(f'XML validation completed successfully for {xml_file.xml_file.name}.')


@celery_app.task(bind=True, timelimit=-1)
def task_generate_pdf_file(self, xml_id, user_id=None, username=None):
    user = _get_user(self.request, username=username, user_id=user_id)
    
    try:
        xml_file = XMLDocument.objects.get(id=xml_id)
    except XMLDocument.DoesNotExist:
        logging.error(f'XML file with ID {xml_id} does not exist.')
        return False
    
    logging.info(f'Starting PDF generation for XML file {xml_file.xml_file.name}.')
    # TODO: Implement PDF generation logic here


@celery_app.task(bind=True, timelimit=-1)
def task_generate_html_file(self, xml_id, user_id=None, username=None):
    user = _get_user(self.request, username=username, user_id=user_id)
    
    try:
        xml_file = XMLDocument.objects.get(id=xml_id)
    except XMLDocument.DoesNotExist:
        logging.error(f'XML file with ID {xml_id} does not exist.')
        return False
    
    logging.info(f'Starting HTML generation for XML file {xml_file.xml_file.name}.')
    # TODO: Implement HTML generation logic here
