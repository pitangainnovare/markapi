# Ordem dos grupos principais no menu admin
# Reflete o fluxo editorial: Upload → Processamento → Validação → Publicação
WAGTAIL_MENU_GROUPS_ORDER = [
    "markup_doc",      # Marcação (fluxo principal)
    "reference",       # Referências (insumo para validação)
    "xml_manager",     # Validação SPS e produtos finais
    "scielo",          # Journal Manager (configuração)
    "model_ai",        # IA (suporte)
    "tracker",         # Tracker (logs e eventos)
    "django_celery_beat",  # Tarefas agendadas (infra)
]


def get_menu_order(app_name):
    """
    Retorna a ordem do app no menu admin.
    
    Args:
        app_name: Nome do app (ex: 'markup_doc', 'reference')
    
    Returns:
        int: Ordem do menu (menor = aparece primeiro)
    """
    try:
        return WAGTAIL_MENU_GROUPS_ORDER.index(app_name) + 1
    except ValueError:
        return 9000


# Sub-ordem dentro do grupo markup_doc
MARKUP_DOC_SUBMENU_ORDER = {
    "upload": 1,           # Upload de DOCX (entrada)
    "processed": 2,        # DOCX processado (saída do processamento)
    "xml_editor": 3,       # Editor XML (edição manual)
    "issue": 4,            # Fascículos (vinculação)
}


def get_markup_doc_submenu_order(item_name):
    """
    Retorna a ordem de itens dentro do grupo markup_doc.
    
    Args:
        item_name: Nome do item (ex: 'upload', 'processed')
    
    Returns:
        int: Ordem do submenu
    """
    return MARKUP_DOC_SUBMENU_ORDER.get(item_name, 9000)
