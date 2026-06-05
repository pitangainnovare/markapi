# Reformulação Editorial do Admin MarkAPI (Plano Refinado)

## Resumo Executivo

Transformar o admin atual em uma **plataforma editorial centrada no Artigo**, onde cada manuscrito é o núcleo de um ecossistema de produtos derivados (DOCX marcado, XML, PDF, HTML, validações). O usuário poderá visualizar toda a trilha de processamento, identificar erros de validação com clareza e navegar entre todos os artefatos gerados a partir de um único ponto.

A navegação principal será simplificada:
1. **Artigos** (fila editorial - página inicial)
2. **Periódicos**
3. **Fascículos**
4. **Configurações**
5. **Ferramentas Avançadas** (visível somente para administradores/superusuários)

A raiz do admin (`/admin/`) redirecionará diretamente para a **Fila de Artigos**.

---

## 1. Área Artigos: O Coração do Sistema

### 1.1 Fila Editorial (ListView)

Uma view administrativa própria com:

- **Cartões de Artigos** (visual moderno, bordas arredondadas, estados coloridos):
  - Título do artigo (truncado se longo)
  - Periódico e fascículo (se vinculados)
  - Status com badge colorido:
    - 🟡 `PROCESSING` (amarelo)
    - 🟢 `PROCESSED` (verde)
    - 🔴 `FAILED` (vermelho)
    - ⚪ `PENDING` (cinza)
  - Etapa atual do fluxo (ex: "Validação SPS", "Geração de PDF")
  - Mensagem resumida de erro (se `FAILED`)
  - Data de upload e última atualização
  - Próxima ação sugerida (ex: "Reprocessar", "Validar XML", "Gerar PDF")

- **Filtros Inteligentes**:
  - Por status (multiseleção)
  - Por periódico (autocomplete)
  - Por fascículo (dependente do periódico)
  - Por etapa do fluxo
  - Por data (range)
  - Busca por: título, autor, DOI, PID, nome do arquivo

- **Ações em Lote** (seleção múltipla):
  - Reprocessar selecionados
  - Vincular a fascículo
  - Exportar lista (CSV/JSON)

- **Botão "Novo Manuscrito"**:
  - Destacado no canto superior direito
  - Abre formulário simplificado (modal ou página dedicada)

### 1.2 Formulário de Upload (CreateView)

Formulário editorial simplificado:

- **Campo DOCX** (obrigatório, drag-and-drop)
- **Título Provisório** (opcional, pode ser extraído automaticamente)
- **Periódico** (autocomplete, obrigatório)
- **Fascículo** (opcional, filtrado pelo periódico selecionado)
- **Metadados opcionais**:
  - Autor correspondente (email)
  - DOI (se já tiver)
  - Palavras-chave (tags)
- **Checksum automático** do arquivo enviado
- **Validação prévia**:
  - Tamanho máximo do arquivo
  - Formato DOCX válido
  - Verificação de duplicidade (hash do arquivo)

### 1.3 Detalhe do Artigo (DetailView) - **O Hub Central**

Esta é a interface mais importante. Deve mostrar **toda a trilha do artigo** em uma única página, com abas ou seções colapsáveis:

#### **Cabeçalho do Artigo**
- Título completo
- Status atual (badge grande)
- Periódico e fascículo (com links)
- Datas: upload, último processamento, conclusão
- Ações rápidas:
  - 🔄 **Reprocessar** (reinicia todo o fluxo)
  - ✏️ **Editar Metadados**
  - 🗑️ **Excluir** (com confirmação)
  - 📦 **Baixar Pacote Completo** (ZIP com todos os artefatos)

#### **Seção 1: Documento Original**
- Nome do arquivo DOCX original
- Data de upload
- Tamanho
- Hash (SHA256)
- Botão: **Baixar Original**
- Botão: **Substituir Documento** (mantém histórico)

#### **Seção 2: DOCX Marcado**
- Status da marcação (✅ Sucesso / ❌ Erro)
- Visualização prévia (se possível) ou link para download
- Botão: **Baixar DOCX Marcado**
- Botão: **Visualizar Citações Linkadas** (abre modal com lista de citações e suas refs)
- **Erros de Marcação** (se houver):
  - Lista de erros com descrição clara
  - Sugestão de correção
  - Link para seção específica do documento (se suportado)

#### **Seção 3: Validação de Referências**
- Total de citações no texto
- Total de referências na bibliografia
- Citações válidas vs. inválidas
- **Tabela Interativa de Citações**:
  | Citação no Texto | Status | Referência Correspondente | Ação |
  |------------------|--------|---------------------------|------|
  | (Silva, 2020) | ✅ Validada | Silva et al. 2020 | [Ver] |
  | (Santos, 2019) | ❌ Não encontrada | - | [Vincular Manualmente] |
  | (Oliveira, 2021) | ⚠️ Múltiplas | 3 opções | [Selecionar] |

- Botão: **Corrigir Vinculações** (abre interface de mapeamento manual)
- Botão: **Revalidar Referências**

#### **Seção 4: XML SPS**
- Status da geração (✅ Gerado / ❌ Erro)
- Versão do SPS utilizada
- Botão: **Baixar XML**
- Botão: **Editar XML** (abre editor técnico - só para admins)
- Botão: **Validar XML Agora**
- **Erros de Geração** (se houver):
  - Lista de erros com linha/coluna
  - Explicação em linguagem simples
  - Sugestão de correção

#### **Seção 5: Validação SPS**
- Status da validação (✅ Aprovado / ⚠️ Avisos / ❌ Erros Críticos)
- Nível de conformidade (ex: 95%)
- **Lista de Validações** (ordenadas por criticidade):
  - 🔴 Erro Crítico: "Elemento <title-group> ausente"
  - 🟡 Aviso: "Data de recebimento não informada"
  - 🟢 OK: "Estrutura de autores válida"
- Botão: **Revalidar**
- Botão: **Ver Relatório Completo** (PDF ou HTML)
- Botão: **Ignorar Avisos e Prosseguir** (se aplicável)

#### **Seção 6: Produtos Derivados**
Cards lado a lado para cada produto:

- **PDF**:
  - Status: ✅ Gerado / ❌ Erro / ⏳ Pendente
  - Versões disponíveis (prova, preprint, versão final)
  - Botão: **Gerar PDF** (se pendente)
  - Botão: **Baixar PDF**
  - Botão: **Visualizar** (abre em modal)
  - Logs de geração (se erro)

- **HTML**:
  - Status: ✅ Gerado / ❌ Erro / ⏳ Pendente
  - Botão: **Gerar HTML**
  - Botão: **Baixar HTML** (ZIP ou arquivo único)
  - Botão: **Visualizar** (abre em nova aba)
  - Logs de geração

- **Pacote ZIP**:
  - Contém: XML + PDF + HTML + assets
  - Botão: **Gerar Pacote**
  - Botão: **Baixar Pacote**
  - Histórico de pacotes gerados

#### **Seção 7: Linha do Tempo (Trilha de Eventos)**
Timeline vertical mostrando todo o histórico do artigo:

```
📅 2025-01-15 10:30 - Artigo criado (DOCX enviado)
📅 2025-01-15 10:31 - Início do processamento
📅 2025-01-15 10:32 - DOCX marcado com sucesso
📅 2025-01-15 10:33 - Validação de referências: 45/47 válidas
📅 2025-01-15 10:34 - XML SPS gerado
📅 2025-01-15 10:35 - Validação SPS: 2 erros críticos encontrados
🔴 2025-01-15 10:35 - Processamento falhou: Erro na validação SPS
📅 2025-01-15 11:00 - Usuário corrigiu metadados manualmente
📅 2025-01-15 11:01 - Reprocessamento iniciado
📅 2025-01-15 11:03 - Validação SPS: Aprovado com 3 avisos
📅 2025-01-15 11:04 - PDF gerado com sucesso
📅 2025-01-15 11:05 - HTML gerado com sucesso
🟢 2025-01-15 11:06 - Processamento concluído
```

- Cada evento clicável mostra detalhes completos
- Filtro por tipo de evento (erro, sucesso, ação do usuário)
- Botão: **Exportar Trilha** (JSON ou PDF)

#### **Seção 8: Vínculos e Relacionamentos**
- **Artigos Relacionados**:
  - Versões anteriores do mesmo artigo (se houve substituição)
  - Artigos que citam este (se disponível)
  - Artigos citados por este (lista)

- **Pacotes e Depósitos**:
  - Lista de pacotes SciELO gerados
  - Status de envio ao Journal Manager
  - Data de publicação online (se aplicável)

#### **Seção 9: Logs e Debug** (apenas para admins)
- Logs completos do processamento
- Stack traces de erros
- Variáveis de ambiente no momento do erro
- Botão: **Copiar Logs**
- Botão: **Reportar Problema** (abre issue no GitHub com contexto)

---

## 2. Estados e Retentativa (Modelo de Dados)

### 2.1 Novos Estados no `ProcessStatus`

```python
class ProcessStatus(models.TextChoices):
    PENDING = 'pending', 'Pendente'
    PROCESSING = 'processing', 'Processando'
    PROCESSED = 'processed', 'Processado'
    FAILED = 'failed', 'Falhou'
    PARTIAL = 'partial', 'Parcial (com avisos)'
```

### 2.2 Campo de Erro Estruturado

```python
class ArticleDocxMarkup(models.Model):
    # ... campos existentes ...
    
    error_message = models.TextField(
        blank=True, 
        null=True,
        help_text="Mensagem resumida do último erro"
    )
    
    error_details = models.JSONField(
        blank=True,
        null=True,
        help_text="Detalhes estruturados do erro"
        # Ex: {
        #   "stage": "sps_validation",
        #   "code": "MISSING_TITLE_GROUP",
        #   "message": "Elemento <title-group> ausente",
        #   "line": 45,
        #   "suggestion": "Adicionar título em <title-group><article-title>"
        # }
    )
    
    error_traceback = models.TextField(
        blank=True,
        null=True,
        help_text="Stack trace completo para debug"
    )
    
    retry_count = models.IntegerField(default=0)
    last_retry_at = models.DateTimeField(blank=True, null=True)
```

### 2.3 Fluxo de Estados

```
[Upload] → PENDING
   ↓
[Início da Task] → PROCESSING (limpa erro anterior)
   ↓
   ├─→ [Sucesso] → PROCESSED (limpa erro)
   ├─→ [Sucesso com Avisos] → PARTIAL
   └─→ [Exceção] → FAILED (persiste erro estruturado)
   
[FAILED] → [Botão Reprocessar] → PROCESSING (incrementa retry_count)
```

### 2.4 Migração de Dados Legados

- Identificar registros presos em `PROCESSING` por > 24h
- Marcar como `FAILED` com mensagem: "Processamento legado recuperável - timeout detectado"
- Permitir reprocessamento imediato

---

## 3. Menu e Cadastros Simplificados

### 3.1 Nova Estrutura do Menu

```
📰 Artigos (ícone de documento)
   └─→ Fila Editorial (página inicial)
   
📚 Periódicos (ícone de livro)
   └─→ Lista de Periódicos
       └─→ Busca por: título, título curto, acrônimo, ISSN-L, ISSN-P, ISSN-E
   
📖 Fascículos (ícone de pasta)
   └─→ Lista de Fascículos
       └─→ Filtros: periódico, volume, número, ano, status
       
⚙️ Configurações (ícone de engrenagem)
   └─→ Usuários e Permissões
   └─→ Preferências do Sistema
   └─→ Integrações (APIs externas)
   
🛠️ Ferramentas Avançadas (ícone de ferramenta, só para superusuários)
   ├─→ Editor Técnico de XML
   ├─→ Documentos XML (lista geral)
   ├─→ Validações SPS (histórico global)
   ├─→ PDFs Gerados (lista geral)
   ├─→ HTMLs Gerados (lista geral)
   ├─→ Referências (banco global)
   ├─→ Eventos (logs do sistema)
   ├─→ Relatórios Analíticos
   └─→ Conteúdo Wagtail (páginas estáticas)
```

### 3.2 Remoção de Grupos Antigos

- ❌ Remover grupo "Marcação"
- ❌ Remover grupo "Journal Manager"
- ✅ Periódicos e Fascículos expostos diretamente no menu principal

### 3.3 Sincronização Explícita

- **Botões de Ação** nas listas de Periódicos e Fascículos:
  - 🔄 **Sincronizar Periódicos** (executa `sync_journals_from_core` em background)
  - 🔄 **Sincronizar Fascículos** (executa `sync_issues_from_core` em background)
  - ➕ **Criar Fascículo por ISSN** (formulário rápido)

- **Remoção de Sincronização Automática**:
  - Abrir telas NÃO dispara sincronização
  - Criar/editar registros NÃO dispara sincronização
  - Usuário tem controle total sobre quando sincronizar

- **Feedback de Sincronização**:
  - Toast notification: "Sincronização iniciada em background"
  - Badge no botão mostra progresso (ex: "Sincronizando... 45%")
  - Ao concluir: "Sincronização concluída: 12 periódicos atualizados"

---

## 4. Remoção do Modelo de Coleções

### 4.1 O Que Será Removido

- ❌ Model: `CollectionModel`
- ❌ Model: `CollectionValuesModel`
- ❌ Campo: `ArticleDocxMarkup.collection`
- ❌ Telas de gestão de coleções
- ❌ Autocomplete de coleções em formulários
- ❌ Função: `sync_collection_from_api`
- ❌ Setting: `CORE_COLLECTION_API_ENDPOINT`
- ❌ Parâmetros de filtro por coleção em sincronizações

### 4.2 Nova Abordagem

- Sincronizar **todos os periódicos** diretamente do SciELO Core
- Filtrar por periódico individualmente, não por coleção
- Se necessário agrupar periódicos, usar **tags** ou **categorias** personalizadas

### 4.3 Migração

- Migrar dados de `collection` para tags no periódico (se relevante)
- Atualizar queries que filtravam por coleção para usar periódico diretamente
- Documentar mudança para usuários afetados

---

## 5. Ferramentas Avançadas (Área Restrita)

### 5.1 Controle de Acesso

- Visível **apenas** para usuários com `is_superuser=True`
- Ou grupo específico "Administradores Técnicos"
- Não aparece no menu para usuários editoriais comuns

### 5.2 Funcionalidades Incluídas

1. **Editor Técnico de XML**:
   - Editor de código com syntax highlighting
   - Validação em tempo real
   - Comparação de versões (diff)
   - Histórico de edições

2. **Documentos XML** (lista global):
   - Todos os XMLs gerados no sistema
   - Filtros avançados (periódico, data, versão SPS, status)
   - Busca por conteúdo do XML (XPath)

3. **Validações SPS** (histórico):
   - Todas as validações já executadas
   - Estatísticas de conformidade
   - Tendências de erros por período

4. **PDFs e HTMLs** (listas globais):
   - Assets gerados por todo o sistema
   - Uso de armazenamento, versões, etc.

5. **Referências** (banco global):
   - Todas as referências validadas
   - Deduplicação
   - Estatísticas de citação

6. **Eventos** (logs do sistema):
   - Logs de todas as tasks
   - Filtros por tipo, severidade, data
   - Exportação para SIEM externo

7. **Relatórios Analíticos**:
   - Dashboard com métricas:
     - Artigos processados por dia/semana/mês
     - Taxa de sucesso vs. falha
     - Tempo médio de processamento
     - Erros mais frequentes
     - Uso por periódico

8. **Conteúdo Wagtail**:
   - Páginas estáticas do admin
   - Customizações de interface
   - Textos de ajuda

---

## 6. Interface de Vínculo entre Artefatos

### 6.1 Modelo de Relacionamentos

```python
class ArticleArtifact(models.Model):
    """Modelo genérico para vincular todos os artefatos a um artigo"""
    
    article = models.ForeignKey(
        'ArticleDocxMarkup',
        on_delete=models.CASCADE,
        related_name='artifacts'
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
        ]
    )
    
    file = models.FileField(upload_to=artifact_upload_path)
    version = models.CharField(max_length=20, default='1.0')
    created_at = models.DateTimeField(auto_now_add=True)
    checksum = models.CharField(max_length=64)  # SHA256
    
    metadata = models.JSONField(
        blank=True,
        null=True,
        help_text="Metadados específicos do tipo de artefato"
        # Ex para PDF: {"pages": 15, "size_bytes": 2048576}
        # Ex para XML: {"sps_version": "1.9", "validation_status": "approved"}
    )
    
    is_current = models.BooleanField(
        default=True,
        help_text="Indica se esta é a versão vigente do artefato"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['article', 'artifact_type']),
            models.Index(fields=['artifact_type', 'created_at']),
        ]
```

### 6.2 Navegação Bidirecional

- **Do Artigo → Artefatos**: 
  - Detail view do artigo mostra todos os artifacts relacionados
  
- **Do Artefato → Artigo**:
  - Listas globais de PDFs/XMLs/HTMLs têm link "Voltar ao Artigo"
  - Breadcrumb: `Artigos > [Título] > PDFs > arquivo.pdf`

### 6.3 Visualização de Pacote Completo

- Botão **"Baixar Pacote"** no detail do artigo gera ZIP contendo:
  - `original.docx`
  - `marked.docx`
  - `article.xml`
  - `article.pdf`
  - `article.html/` (pasta)
  - `validation_report.pdf`
  - `manifest.json` (metadados do pacote)

---

## 7. Melhorias de UX/UI

### 7.1 Feedback Visual de Status

- **Badges Coloridos**:
  - 🟢 Verde: Sucesso/Concluído
  - 🟡 Amarelo: Processando/Avisos
  - 🔴 Vermelho: Erro/Falha
  - 🔵 Azul: Informação/Pendente
  - 🟣 Roxo: Ação Requerida

- **Barras de Progresso**:
  - Para tarefas longas (> 5s), mostrar progresso estimado
  - Ex: "Gerando PDF... 65%"

- **Toasts e Notificações**:
  - Ações bem-sucedidas: toast verde no topo
  - Erros: toast vermelho com opção "Ver Detalhes"
  - Tasks em background: notificação com link para monitorar

### 7.2 Responsividade

- Layout adaptativo para tablets (útil para editores em movimento)
- Menu lateral colapsável em telas pequenas
- Tabelas com scroll horizontal em mobile
- Modais responsivos

### 7.3 Acessibilidade

- Contraste de cores adequado (WCAG AA)
- Navegação por teclado
- Labels descritivos em formulários
- Textos alternativos em ícones
- Suporte a leitores de tela

### 7.4 Atalhos de Teclado

- `N`: Novo manuscrito
- `R`: Reprocessar artigo atual
- `F`: Focar na busca
- `Esc`: Fechar modal
- `Ctrl+Enter`: Salvar formulário

---

## 8. Interfaces e Rotas Alteradas

### 8.1 Novas Rotas Administrativas

```
/admin/                           → Redireciona para /admin/articles/queue/
/admin/articles/                  → Alias para /admin/articles/queue/
/admin/articles/queue/            → Fila editorial (nova view)
/admin/articles/create/           → Formulário de novo manuscrito
/admin/articles/<id>/             → Detail do artigo (hub central)
/admin/articles/<id>/edit/        → Editar metadados
/admin/articles/<id>/reprocess/   → Acionar reprocessamento
/admin/articles/<id>/xml/edit/    → Editor técnico de XML (só admin)
/admin/articles/<id>/validate/    → Forçar validação SPS
/admin/articles/<id>/download/    → Baixar pacote completo

/admin/journals/                  → Lista de periódicos (nova UI)
/admin/journals/sync/             → Acionar sincronização (background)
/admin/issues/                    → Lista de fascículos (nova UI)
/admin/issues/sync/               → Acionar sincronização (background)
/admin/issues/create-by-issn/     → Criar fascículo por ISSN

/admin/tools/                     → Landing page de ferramentas avançadas
/admin/tools/xml-editor/          → Editor técnico de XML
/admin/tools/xml-documents/       → Lista global de XMLs
/admin/tools/validations/         → Histórico de validações
/admin/tools/pdfs/                → Lista global de PDFs
/admin/tools/htmls/               → Lista global de HTMLs
/admin/tools/references/          → Banco de referências
/admin/tools/events/              → Logs de eventos
/admin/tools/reports/             → Relatórios analíticos
```

### 8.2 Mudanças no Modelo de Dados

```python
# Adições ao ArticleDocxMarkup
class ArticleDocxMarkup(models.Model):
    # ... campos existentes ...
    
    # Novo campo de erro estruturado
    error_message = models.TextField(blank=True, null=True)
    error_details = models.JSONField(blank=True, null=True)
    error_traceback = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    last_retry_at = models.DateTimeField(blank=True, null=True)
    
    # Remoção do campo collection
    # collection = models.ForeignKey(...)  ← REMOVER
    
    # Vínculo com artifacts (opcional, se usar modelo genérico)
    # artifacts = GenericRelation(ArticleArtifact)
```

```python
# Novo modelo (opcional, para vínculo explícito)
class ArticleArtifact(models.Model):
    article = models.ForeignKey('ArticleDocxMarkup', on_delete=models.CASCADE)
    artifact_type = models.CharField(max_length=50, choices=ARTIFACT_TYPES)
    file = models.FileField(upload_to=artifact_upload_path)
    version = models.CharField(max_length=20, default='1.0')
    created_at = models.DateTimeField(auto_now_add=True)
    checksum = models.CharField(max_length=64)
    metadata = models.JSONField(blank=True, null=True)
    is_current = models.BooleanField(default=True)
```

### 8.3 Mudanças nas Tasks

```python
# Assinatura alterada: remove collection_acron
@app.task
def sync_journals_from_api():
    # Antes: sync_journals_from_api(collection_acron=None)
    # Agora: sincroniza todos os periódicos sem filtro
    pass

@app.task
def sync_issues_from_api():
    # Mesma lógica: sem filtro por coleção
    pass

# Task de marcação com tratamento robusto de erro
@app.task
def process_article_markup(article_id):
    article = ArticleDocxMarkup.objects.get(id=article_id)
    
    try:
        article.status = ProcessStatus.PROCESSING
        article.error_message = None
        article.error_details = None
        article.error_traceback = None
        article.save()
        
        # ... lógica de processamento ...
        
        article.status = ProcessStatus.PROCESSED
        article.save()
        
    except Exception as e:
        article.status = ProcessStatus.FAILED
        article.error_message = str(e)[:500]  # Resumo
        article.error_details = {
            "type": type(e).__name__,
            "stage": detect_stage(),  # inferir etapa do erro
            "suggestion": get_suggestion_for_error(e),
        }
        article.error_traceback = traceback.format_exc()
        article.save()
        
        # Notificar usuário (email, webhook, etc.)
        notify_user_of_failure(article, e)
        
        raise  # Re-raise para o Celery registrar
```

---

## 9. Testes e Critérios de Aceitação

### 9.1 Testes Funcionais

- [ ] **Criação de Manuscrito**:
  - Upload de DOCX via novo formulário
  - Preenchimento de metadados opcionais
  - Validação de arquivo (tamanho, formato, duplicidade)
  - Redirecionamento para detail do artigo após criação

- [ ] **Fila Editorial**:
  - Visualização de artigos nos estados: PENDING, PROCESSING, PROCESSED, FAILED, PARTIAL
  - Filtros combinados (status + periódico + data)
  - Busca por título, autor, DOI, PID, nome do arquivo
  - Ações em lote (reprocessar, vincular, exportar)
  - Paginação e ordenação

- [ ] **Detail do Artigo**:
  - Todas as seções visíveis e funcionais
  - Links para baixar cada artefato
  - Timeline completa de eventos
  - Tabela interativa de citações
  - Validações SPS com níveis de criticidade
  - Botões de ação (reprocessar, editar, excluir)

- [ ] **Gestão de Erros**:
  - Simular falha na task de marcação
  - Verificar persistência de `error_message`, `error_details`, `error_traceback`
  - Verificar mudança de status para FAILED
  - Clicar em "Reprocessar" e confirmar:
    - Status volta para PROCESSING
    - Erros são limpos
    - `retry_count` incrementa
    - `last_retry_at` atualizado

- [ ] **Migração de Legados**:
  - Criar registros artificiais em PROCESSING com `updated_at` antigo (> 24h)
  - Rodar migração
  - Verificar que foram marcados como FAILED com mensagem apropriada
  - Verificar que podem ser reprocessados

- [ ] **Periódicos e Fascículos**:
  - Busca por todos os campos (título, acrônimo, ISSNs)
  - Filtros de fascículos (periódico, volume, número, ano)
  - Botão "Sincronizar Periódicos" executa em background
  - Botão "Sincronizar Fascículos" executa em background
  - Criar fascículo por ISSN funciona
  - Abrir telas NÃO dispara sincronização automática

- [ ] **Controle de Acesso**:
  - Usuário comum NÃO vê "Ferramentas Avançadas"
  - Superusuário VÊ "Ferramentas Avançadas"
  - Tentar acessar rota de ferramenta avançada sem permissão retorna 403

- [ ] **Vínculo de Artefatos**:
  - Do detail do artigo, baixar cada artefato individualmente
  - Do detail do artigo, baixar pacote completo (ZIP)
  - Da lista global de PDFs, clicar em "Voltar ao Artigo" e navegar corretamente
  - Verificar que `manifest.json` no pacote contém metadados corretos

### 9.2 Testes Visuais (Desktop e Mobile)

- [ ] Fila editorial com cartões responsivos
- [ ] Detail do artigo com abas/seções colapsáveis
- [ ] Formulário de upload com drag-and-drop
- [ ] Badges de status com cores adequadas
- [ ] Timeline vertical legível
- [ ] Tabelas interativas (citações, validações)
- [ ] Modais e toasts funcionais
- [ ] Menu lateral com nova estrutura
- [ ] Testar em Chrome, Firefox, Safari, Edge
- [ ] Testar em resoluções: 1920x1080, 1366x768, 1024x768, 768x1024 (tablet)

### 9.3 Testes de Integração

- [ ] Executar suíte completa de testes do MarkAPI
- [ ] Verificar que nenhuma funcionalidade existente foi quebrada
- [ ] Testar integração com SciELO Core (sincronização)
- [ ] Testar geração de PDF e HTML em cenário real
- [ ] Testar validação SPS com casos de teste conhecidos
- [ ] Testar tasks assíncronas com Celery (sucesso e falha)

### 9.4 Critérios de Aceitação

- ✅ Usuário consegue subir um DOCX e acompanhar todo o processamento em uma única tela
- ✅ Erros são claros, acionáveis e permitem retentativa fácil
- ✅ É possível navegar do artigo para qualquer artefato derivado e vice-versa
- ✅ A fila editorial dá visão geral imediata do status de todos os manuscritos
- ✅ Sincronizações são explícitas e não ocorrem automaticamente
- ✅ Ferramentas técnicas estão protegidas e acessíveis apenas a administradores
- ✅ O visual é moderno, consistente com o Wagtail e responsivo
- ✅ Todos os testes automatizados passam
- ✅ Documentação atualizada reflete as novas interfaces

---

## 10. Premissas e Escopo

### 10.1 Premissas Mantidas

- ✅ Entrada suportada: **apenas DOCX** nesta etapa
- ✅ **Wagtail** continua fornecendo:
  - Autenticação
  - Permissões
  - Estrutura da barra lateral
  - Base para views admin customizadas
- ✅ **Não haverá dashboard separado**: a fila de artigos É a página inicial
- ✅ **Não há associação por nome de arquivo**: o vínculo é feito via ID do artigo no banco

### 10.2 Fora do Escopo (Futuras Iterações)

- 📌 Upload de outros formatos (LaTeX, ODT, Markdown)
- 📌 Submissão por autores (portal externo)
- 📌 Revisão por pares integrada
- 📌 Versionamento avançado de artigos (controle de mudanças no conteúdo)
- 📌 Integração com ORCID, Crossref, DataCite
- 📌 Workflow de aprovação editorial (aceitar/rejeitar)
- 📌 Notificações por email automáticas em cada etapa
- 📌 API REST pública para integração externa

### 10.3 Dependências Técnicas

- Python 3.10+
- Django 4.2+
- Wagtail 5.2+
- Celery + Redis/RabbitMQ
- Banco de dados: PostgreSQL recomendado
- Armazenamento de arquivos: S3-compatible ou local

---

## 11. Plano de Implementação (Ordem Sugerida)

### Fase 1: Fundação (Semana 1-2)
1. **Modelo de Dados**:
   - Adicionar campos de erro ao `ArticleDocxMarkup`
   - Criar modelo `ArticleArtifact` (se optar por essa abordagem)
   - Criar migrações
   - Migrar registros legados em PROCESSING

2. **Remoção de Coleções**:
   - Remover modelos `CollectionModel`, `CollectionValuesModel`
   - Remover campo `collection` de `ArticleDocxMarkup`
   - Remover funções de sincronização de coleção
   - Atualizar tests afetados

### Fase 2: Views e Templates (Semana 3-4)
3. **Fila Editorial**:
   - Criar view `ArticleQueueView`
   - Criar template com cartões e filtros
   - Implementar busca e paginação
   - Testes de integração

4. **Formulário de Upload**:
   - Criar view `ArticleCreateView`
   - Template com drag-and-drop
   - Validações de arquivo
   - Testes de criação

5. **Detail do Artigo**:
   - Criar view `ArticleDetailView`
   - Template com todas as seções (abas ou colapsáveis)
   - Implementar timeline de eventos
   - Implementar tabela de citações
   - Implementar cards de artefatos
   - Testes de visualização

### Fase 3: Lógica de Processamento (Semana 5)
6. **Tasks com Tratamento de Erro**:
   - Atualizar task `process_article_markup` para capturar exceções
   - Persistir erro estruturado
   - Implementar lógica de retentativa
   - Testes de falha e recuperação

7. **Vínculo de Artefatos**:
   - Atualizar tasks de geração (XML, PDF, HTML) para criar `ArticleArtifact`
   - Implementar função de gerar pacote ZIP
   - Testes de vínculo

### Fase 4: Menu e Limpeza (Semana 6)
8. **Reestruturação do Menu**:
   - Atualizar `wagtail_hooks.py` de cada app
   - Remover grupos antigos
   - Adicionar novos grupos e itens
   - Implementar controle de acesso (Ferramentas Avançadas)

9. **Periódicos e Fascículos**:
   - Atualizar views para remover sincronização automática
   - Adicionar botões de sincronização explícita
   - Melhorar buscas e filtros
   - Testes de sincronização

### Fase 5: Polimento e Testes (Semana 7-8)
10. **UX/UI**:
    - Aplicar estilos consistentes (badges, cards, timeline)
    - Implementar toasts e notificações
    - Adicionar atalhos de teclado
    - Testes de responsividade

11. **Testes Completos**:
    - Executar suíte completa de testes
    - Corrigir bugs encontrados
    - Testes de aceitação manual
    - Documentação de usuário

12. **Deploy e Treinamento**:
    - Deploy em ambiente de staging
    - Testes de carga (opcional)
    - Treinar equipe editorial
    - Coletar feedback
    - Ajustes finais
    - Deploy em produção

---

## 12. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Perda de dados na migração de coleções | Alto | Backup completo antes de migrar; script de rollback testado |
| Tasks de processamento falharem silenciosamente | Médio | Implementar logging robusto; notificações de falha; monitoramento com Sentry |
| Performance da fila com muitos artigos | Médio | Paginação, lazy loading, índices no banco, cache de consultas frequentes |
| Resistência dos usuários à nova interface | Baixo | Treinamento, documentação clara, período de transição com tutorial in-app |
| Complexidade excessiva do detail do artigo | Médio | Testes de usabilidade; iterar com feedback real; manter abas colapsáveis |
| Integração com SciELO Core instável | Médio | Retry com backoff exponencial; fallback para dados em cache; notificação de falha |

---

## 13. Métricas de Sucesso

Após 30 dias em produção:

- ✅ **Taxa de Sucesso de Processamento**: > 90% dos artigos processados sem erro crítico
- ✅ **Tempo Médio de Resolução de Erros**: < 2 horas para reprocessar artigo falho
- ✅ **Satisfação do Usuário**: > 4/5 em pesquisa de UX
- ✅ **Redução de Tickets de Suporte**: -50% comparado ao sistema anterior
- ✅ **Adoção**: > 80% dos artigos novos usando o novo fluxo
- ✅ **Performance**: Carregamento da fila < 2s, detail do artigo < 3s

---

## Conclusão

Este plano refinado transforma o MarkAPI em uma plataforma editorial moderna, centrada no artigo, com visibilidade completa da trilha de processamento, gestão robusta de erros e navegação intuitiva entre todos os artefatos gerados. A remoção de complexidades desnecessárias (coleções) e a separação clara entre operações editoriais e ferramentas técnicas tornam o sistema mais fácil de usar e manter.

A implementação faseada permite entrega incremental de valor, com testes contínuos e oportunidade de ajustes baseados em feedback real. O resultado final será uma experiência editorial fluida, eficiente e profissional, alinhada com as melhores práticas de plataformas de publicação científica modernas.
