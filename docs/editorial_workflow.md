# Fluxo Editorial - Documentação do Sistema MarkAPI

## Visão Geral

O sistema MarkAPI foi reorganizado para refletir o fluxo editorial de processamento de artigos científicos. O menu admin agora segue uma lógica sequencial que guia o usuário desde o upload do documento original até a geração dos produtos finais.

## Estrutura do Menu

### Ordem dos Grupos Principais

1. **Fluxo Editorial** (`markup_doc`) - Processo principal de marcação
2. **Referências (Validação)** (`reference`) - Base de referências validadas/invalidadas
3. **xml_manager** - Validação SPS e produtos finais (XML, PDF, HTML)
4. **Journal Manager** (`scielo`) - Configuração de coleções, periódicos e fascículos
5. **Modelos de IA** (`model_ai`) - Suporte de inteligência artificial
6. **Rastreio de eventos** (`tracker`) - Logs e auditoria
7. **Tarefas agendadas** (`django_celery_beat`) - Infraestrutura de background

---

## Fluxo Editorial Detalhado

### Grupo: Fluxo Editorial

Este grupo contém todas as etapas do processamento de um artigo científico.

#### 1. Upload de DOCX
- **Objetivo**: Receber o arquivo original do autor
- **Modelo**: `UploadDocx`
- **Ações**:
  - Upload do arquivo DOCX
  - Preenchimento do título do documento
  - Início automático do processamento via Celery
- **Próxima etapa**: Aguardar processamento → DOCX processado

#### 2. DOCX processado
- **Objetivo**: Exibir resultado do processamento inicial
- **Modelo**: `ProcessedDocx`
- **Informações exibidas**:
  - Status do processamento
  - Link para download do DOCX marcado
  - Status das citações (xref_status):
    - Total de referências
    - Total de citações linkadas
    - Citações sem referência (orphaned hyperlinks)
    - Referências sem citação (orphaned bookmarks)
- **Ações**:
  - Download do DOCX marcado (com citações linkadas)
  - Reprocessar documento (se necessário)
- **Próxima etapa**: Editor XML SPS

#### 3. Produtos Finais (sub-grupo)

##### 2. Editor XML SPS
- **Objetivo**: Editar manualmente o XML gerado
- **Modelo**: `MarkupXML`
- **Funcionalidades**:
  - Visualização do XML gerado
  - Edição manual dos campos:
    - Front (metadados, autores, afiliações)
    - Body (conteúdo principal)
    - Back (referências)
  - Campos detalhados do artigo (páginas, datas, DOI, etc.)
  - Botão de reprocessamento (descarta edições manuais)
- **Próxima etapa**: Validação SPS

##### 0. Validar SPS
- **Objetivo**: Validar pacotes SPS (ZIP com XML + arquivos relacionados)
- **Modelo**: `SPSPackageValidation`
- **Ações**:
  - Upload de pacote ZIP
  - Validação automática via tarefa Celery
  - Download do relatório de validação
  - Download do relatório de exceções
- **Status**: PENDING, VALID, INVALID

##### 1. Documentos XML
- **Objetivo**: Gerenciar documentos XML individuais
- **Modelo**: `XMLDocument`
- **Informações**:
  - Arquivo XML
  - Arquivo de validação
  - Arquivo de exceções
  - Data de upload
- **Ações**: Processar XML

##### 2. PDFs
- **Objetivo**: Armazenar PDFs gerados a partir do XML
- **Modelo**: `XMLDocumentPDF`
- **Informações**:
  - Documento XML de origem
  - Arquivo PDF
  - Arquivo DOCX de origem
  - Idioma
  - Data de upload

##### 3. HTMLs
- **Objetivo**: Armazenar HTMLs gerados a partir do XML
- **Modelo**: `XMLDocumentHTML`
- **Informações**:
  - Documento XML de origem
  - Arquivo HTML
  - Idioma
  - Data de upload

#### 4. Fascículos
- **Objetivo**: Vincular artigos a fascículos
- **Modelo**: `Issue`
- **Informações**:
  - Periódico (journal)
  - Volume, número, ano, mês
  - Suplemento (se aplicável)
- **Uso**: Selecionado durante o markup do artigo

---

### Grupo: Referências (Validação)

- **Objetivo**: Manter base de referências validadas para conferência
- **Modelo**: `Reference`
- **Funcionalidades**:
  - Inserção de referências em lote (uma por linha)
  - Validação automática via IA/API
  - Status: válido/inválido
  - Dados estruturados da referência (autores, título, DOI, etc.)
- **Integração**: Usado para validar citações no texto vs. referências no final

---

### Grupo: Journal Manager

Configuração necessária antes de iniciar o fluxo editorial.

#### Coleção
- **Modelo**: `CollectionModel`
- **Ação**: Sincroniza coleções da API SciELO

#### Periódicos
- **Modelo**: `JournalModel`
- **Ação**: Sincroniza journals da API SciELO
- **Campos**: título, ISSN, acrônimo, etc.

#### Fascículos
- **Modelo**: `Issue`
- **Nota**: Também acessível via Fluxo Editorial

---

## Processo de Validação de Citações

O sistema realiza a seguinte validação:

1. **Extração de citações**: Identifica marcadores como `[1]`, `(Smith, 2020)` no texto
2. **Extração de referências**: Lê a seção "References" no final do documento
3. **Linkagem**: Tenta vincular cada citação à referência correspondente
4. **Relatório de status**:
   - ✅ Válido: Todas as citações têm referência e vice-versa
   - ❌ Inválido: Existem citações órfãs ou referências não citadas
5. **DOCX marcado**: Gera documento com hiperlinks clicáveis entre citações e referências

---

## Produtos Gerados

Ao final do processo, o sistema gera:

1. **DOCX Marcado**: Documento original com citações linkadas às referências
2. **XML SPS**: XML no padrão SciELO Publishing Schema
3. **PDF**: Versão formatada para publicação
4. **HTML**: Versão web do artigo
5. **Pacote ZIP**: Contém todos os arquivos acima + metadados

---

## Tarefas em Background (Celery)

- `get_labels`: Processa DOCX e extrai estrutura
- `update_xml`: Atualiza XML a partir de edições manuais
- `task_validate_sps_package`: Valida pacote SPS
- `get_reference`: Valida referência via IA/API
- `download_model`: Baixa modelos de IA

---

## Boas Práticas

1. **Antes de começar**: Configure Coleção e Periódico em Journal Manager
2. **Upload**: Use títulos descritivos para facilitar busca
3. **Validação**: Sempre valide o pacote SPS antes de publicar
4. **Reprocessamento**: Evite reprocessar após edições manuais (perde as edições)
5. **Referências**: Mantenha a base de referências atualizada para validação cruzada
