# 🎵 MuPlayer

O **MuPlayer** é um player de áudio leve e eficiente que roda direto no terminal (TUI) e transforma o YouTube no seu streaming pessoal. Ele utiliza o `yt-dlp` para buscas e extração de áudio, o `mpv` ou `vlc` para reprodução, o framework `Textual` para a interface e `SQLite` (via Tortoise ORM) para gerenciar sua biblioteca e playlists localmente.

---

## ✨ Qualidades

* **Leve e Rápido:** Consome pouquíssimos recursos de CPU e memória.
* **Streaming Direto:** Reprodução instantânea de áudio via stream, sem necessidade de download prévio.
* **Interface TUI Moderna:** Controles intuitivos por atalhos de teclado e estilo visual rico direto no terminal.
* **Biblioteca Local:** Gerencia playlists, histórico e faixas salvas em banco de dados SQLite local.
* **Fallback Inteligente:** Alterne dinamicamente entre os motores de áudio `mpv` e `vlc`.

---

## 📋 Requisitos do Sistema

Para rodar o MuPlayer perfeitamente, o sistema precisa atender a estes pré-requisitos:

1. **Python:** versão `>= 3.12`
2. **Engine de Áudio:** `mpv` (*recomendado*, requer `libmpv`) ou `vlc` (`libvlc`).
3. **JavaScript Runtime:** `quickjs`, `node`, `deno` ou `bun` no `PATH` do sistema.
   > 💡 *O `yt-dlp` necessita de um runtime JS para decifrar assinaturas e extrair as URLs de áudio do YouTube.*

---

## 🚀 Instalação e Uso

### 1. Instalação

Instale o MuPlayer utilizando `pip` ou `uv`:

```bash
pip install git+https://github.com/vinifreittas/MuPlayer.git
# ou via uv tool:
uv tool install git+https://github.com/vinifreittas/MuPlayer.git
```

### 2. Configuração Inicial (Assistente Interativo)

O MuPlayer possui um assistente próprio para verificar e instalar dependências do sistema se necessário:

```bash
muplayer setup
```

> 💡 *Se estiver rodando em ambiente de desenvolvimento local via `uv`, execute:*
> ```bash
> uv run muplayer setup
> ```

### 3. Iniciar o Player

Após a configuração, inicie a interface de terminal:

```bash
muplayer
```

#### Opções de Inicialização:
* `muplayer --debug` (ou `-d`): Ativa logs detalhados de depuração.
* `muplayer --force` (ou `-f`): Força a inicialização ignorando verificações prévias de ambiente.

---

## 🛠️ Comandos CLI

O MuPlayer disponibiliza um conjunto completo de comandos Typer para suporte e diagnóstico:

| Comando | Descrição |
| :--- | :--- |
| `muplayer` | Inicia a interface gráfica TUI principal do player. |
| `muplayer setup` | Executa o assistente de instalação de motores de áudio e dependências. |
| `muplayer doctor` | Exibe diagnóstico completo do sistema (terminal, engines de áudio, runtime JS e caminhos). |
| `muplayer update` | Verifica e atualiza o pacote do MuPlayer para a versão mais recente do repositório. |
| `muplayer version` | Exibe a versão atual do aplicativo. |

---

## 📁 Armazenamento e Configuração (Padrão XDG)

Os dados do MuPlayer são mantidos em diretórios padrão do sistema operacional gerenciados pelo `platformdirs`:

* **Banco de Dados e Configuração:** `~/.local/share/MuPlayer/` (`app_data.db`, `config.json`)
* **Cache de Buscas e URLs:** `~/.cache/MuPlayer/`
* **Logs do Sistema:** `~/.local/state/MuPlayer/logs/`

---

## 🛠️ Tecnologias Utilizadas

* **[Textual](https://textualize.io):** Interface gráfica para terminal (TUI).
* **[yt-dlp](https://github.com/yt-dlp/yt-dlp):** Busca e extração de áudio do YouTube.
* **[mpv](https://mpv.io) / [VLC](https://www.videolan.org):** Motores de reprodução de áudio.
* **[Tortoise ORM](https://tortoise.github.io) & [SQLite](https://www.sqlite.org):** Persistência e gerenciamento da biblioteca local.
* **[Typer](https://typer.tiangolo.com) & [Rich](https://rich.readthedocs.io):** Interface de linha de comando (CLI) e relatórios formatados.