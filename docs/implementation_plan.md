# Plano de Implementação — Refatoração da Infraestrutura & Migrações com Aerich

Plano detalhado para simplificar o módulo `src/muplayer/infrastructure`, remover wrappers redundantes,
achatar subpastas desnecessárias, resolver conflitos de nomes de modelos ORM e integrar o **Aerich**
para gerenciamento seguro de migrações no Tortoise ORM com SQLite.

---

## Visão Geral e Objetivos

1. **Manutenção do Tortoise ORM + Integração do Aerich** — Preservar o Tortoise ORM como motor de persistência assíncrono, adicionando a ferramenta oficial `aerich` para suportar migrações contínuas de esquema sem perda de dados do usuário.
2. **Resolução de Conflito de Nomes no ORM** — Renomear os modelos em `tables.py` (`Song` -> `SongTable`, `Playlist` -> `PlaylistTable`, `PlaylistSong` -> `PlaylistSongTable`), eliminando importações com aliases confusos no `manager.py`.
3. **Aplicação do Princípio KISS no Cache** — Remover o arquivo wrapper de 90 linhas (`cache.py`) e utilizar a biblioteca `diskcache.Cache` diretamente no `bootstrap.py` e nos serviços de aplicação.
4. **Achatamento da Estrutura de Diretórios** — Mover `search/search.py` para `infrastructure/search.py` e remover a subpasta `search/`, eliminando aninhamento redundante de arquivo único.
5. **Limpeza em Audio Backends** — Simplificar verificações de bibliotecas compartilhadas em `audio/backends.py`.

---

## Decisões Técnicas Importantes

**Fluxo de Migração com Aerich**

O `aerich` será adicionado às dependências do projeto no `pyproject.toml`.
Será criado o dicionário `TORTOISE_ORM` em `src/muplayer/infrastructure/database/config.py`
para que a CLI do Aerich consiga rastrear o esquema atual das tabelas.

O fluxo de migração deve seguir esta ordem obrigatória:

1. Inicializar o Aerich apontando para o estado **atual** das tabelas (`aerich init` e `aerich init-db`).
2. Aplicar a renomeação das classes em `tables.py`.
3. Gerar a migração via `aerich migrate --name "rename_table_models"`.
4. Aplicar a migração via `aerich upgrade`.

**Remoção do Wrapper de Cache**

O arquivo `src/muplayer/infrastructure/cache.py` será completamente excluído.
A instância do `diskcache.Cache` será gerenciada diretamente no `bootstrap.py`,
com fechamento limpo garantido no bloco `finally`.

---

## Mudanças Propostas por Componente

### 1. Dependências & Configuração do Aerich

**[MODIFY] `pyproject.toml`**

- Adicionar `"aerich"` à lista de `dependencies` do projeto.

**[NEW] `src/muplayer/infrastructure/database/config.py`**

- Criar o dicionário de configuração `TORTOISE_ORM` exigido pela CLI do Aerich.

```python
TORTOISE_ORM = {
    "connections": {"default": "sqlite://~/.local/share/MuPlayer/app_data.db"},
    "apps": {
        "models": {
            "models": ["muplayer.infrastructure.database.tables", "aerich.models"],
            "default_connection": "default",
        }
    },
}
```

---

### 2. Banco de Dados — Modelos e Manager

**[MODIFY] `src/muplayer/infrastructure/database/tables.py`**

Renomear as classes dos modelos ORM para evitar colisão com os schemas Pydantic do domínio:

- `Song` -> `SongTable`
- `Playlist` -> `PlaylistTable`
- `PlaylistSong` -> `PlaylistSongTable`

**[MODIFY] `src/muplayer/infrastructure/database/manager.py`**

- Atualizar as importações para utilizar os novos nomes diretamente, sem aliases.
- Substituir `_build_config()` pelo `TORTOISE_ORM` importado de `database/config.py`.

**[NEW] `migrations/`**

- Diretório gerado e mantido pelo `aerich` contendo o histórico de scripts de migração.

---

### 3. Cache — Simplificação (KISS)

**[DELETE] `src/muplayer/infrastructure/cache.py`**

- Remover o arquivo wrapper redundante.

**[MODIFY] `src/muplayer/application/bootstrap.py`**

- Importar `diskcache` diretamente.
- Instanciar `cache = diskcache.Cache(str(get_cache_dir()))` e injetá-lo nos serviços.
- Garantir `cache.close()` no bloco `finally`.

**[MODIFY] `src/muplayer/application/search_service.py` e `playback_service.py`**

- Atualizar hints de tipo de `Cache` (do wrapper) para `diskcache.Cache`.

---

### 4. Módulo de Busca — Achatamento de Subpasta

**[NEW] `src/muplayer/infrastructure/search.py`**

- Mover a classe `SearchAPI` e a função `validate_stream_url` para a raiz da camada `infrastructure`.

**[DELETE] `src/muplayer/infrastructure/search/`**

- Remover o diretório e o arquivo `search/search.py`.

**[MODIFY] `src/muplayer/infrastructure/__init__.py`**

- Atualizar a re-exportação de `SearchAPI` para `muplayer.infrastructure.search`.

---

### 5. Audio Backends — Limpeza

**[MODIFY] `src/muplayer/infrastructure/audio/backends.py`**

- Simplificar os métodos `is_available()` em `MpvBackend` e `VlcBackend` para evitar
  duplicação de chamadas de inspeção de bibliotecas do sistema.

---

## Passo a Passo de Execução

| Passo | Acao                         | Descricao                                                                                      |
|-------|------------------------------|-----------------------------------------------------------------------------------------------|
| 1     | Adicionar dependencia        | Adicionar `"aerich"` em `pyproject.toml` e executar `uv sync`.                                |
| 2     | Criar config do Aerich       | Criar `database/config.py` com o dicionario `TORTOISE_ORM`.                                   |
| 3     | Inicializar Aerich           | Executar `aerich init -t ...` e `aerich init-db` no esquema atual.                            |
| 4     | Renomear modelos ORM         | Alterar nomes das classes em `tables.py` e ajustar imports em `manager.py`.                   |
| 5     | Gerar e aplicar migração     | Executar `aerich migrate --name "rename_table_models"` e depois `aerich upgrade`.              |
| 6     | Refatorar cache              | Excluir `cache.py` e atualizar `bootstrap.py`, `search_service.py`, `playback_service.py`.    |
| 7     | Achatar módulo de busca      | Mover `search/search.py` -> `infrastructure/search.py` e deletar a subpasta `search/`.        |
| 8     | Atualizar exports e backends | Atualizar `infrastructure/__init__.py` e simplificar `backends.py`.                           |
| 9     | Qualidade e testes           | Executar linter, formatador e suíte de testes.                                                |

---

## Verificação e Validação

### Validação Automatizada

```bash
# Sincronizar ambiente com as novas dependências
uv sync

# Linter com auto-correção
uv run ruff check --fix src/

# Formatador
uv run ruff format src/

# Suíte de testes
uv run pytest

# Verificação de código morto
uv run deadcode
```

### Validação Manual

1. Executar `uv run muplayer` e confirmar que o player inicia sem erros.
2. Realizar uma busca de faixa e confirmar reprodução de áudio.
3. Adicionar uma faixa a uma playlist e encerrar o app.
4. Reabrir o app e confirmar que a playlist foi persistida corretamente no banco de dados migrado.
