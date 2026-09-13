# 🎵 MuPlayer

O **MuPlayer** é um player de áudio leve e eficiente feito sob medida para o terminal (TUI), transformando o YouTube no seu serviço de streaming pessoal. Projetado para desenvolvedores e entusiastas de linha de comando que buscam escutar música e podcasts sem distrações do navegador ou consumo excessivo de memória.

Ele utiliza `yt-dlp` para buscas e extração de URLs de stream, `mpv` ou `vlc` para reprodução contínua de áudio, o framework `Textual` para a interface rica em TUI e `SQLite` (via Tortoise ORM) para gerenciamento local de biblioteca e playlists.

---

## ✨ Principais Funcionalidades & Qualidades

* **Leve e Rápido:** Consumo mínimo de CPU e memória RAM (sem a sobrecarga de navegadores web).
* **Streaming Direto:** Reprodução instantânea de áudio via stream puramente em memória, sem necessidade de download prévio.
* **Interface TUI Moderna:** Interface responsiva construída com Textual, suporte a atalhos de teclado (Vim-style e media keys), temas visuais (Spotify Dark) e MiniPlayer.
* **Biblioteca Local Completa:** Gerenciamento de playlists personalizadas, faixas salvas/favoritas e histórico de reprodução via SQLite.
* **Importação Rápida:** Importação de playlists públicas do YouTube diretamente por link/URL.
* **Diagnóstico e Fallback Inteligente:** Auto-detecção de dependências na inicialização e alternância dinâmica entre motores de áudio (`mpv` e `vlc`).

---

## 📋 Requisitos do Sistema

Para rodar o MuPlayer perfeitamente, o sistema necessita dos seguintes pré-requisitos:

1. **Python & UV:** Python `>= 3.12` e gerenciador [uv](https://docs.astral.sh/uv/) instalado no sistema.
2. **Engine de Áudio:** `mpv` (*recomendado*, requer `libmpv`) ou `vlc` (`libvlc`).
3. **JavaScript Runtime:** `quickjs`, `node`, `deno` ou `bun` presente no `PATH` do sistema.
   > 💡 *O `yt-dlp` necessita de um runtime JS no ambiente para decifrar assinaturas e extrair as URLs de áudio do YouTube.*

---

## 🚀 Instalação e Uso via `uv`

O **MuPlayer** foi projetado para ser gerenciado e executado exclusivamente utilizando o `uv`.

### 1. Instalação (Ferramenta Global)

Instale o MuPlayer como uma ferramenta global no seu terminal via `uv tool`:

```bash
uv tool install git+https://github.com/vinifreittas/MuPlayer.git
```

> 💡 *Caso prefira rodar diretamente sem instalar globalmente, você pode utilizar `uvx`:*
> ```bash
> uvx git+https://github.com/vinifreittas/MuPlayer.git
> ```

### 2. Configuração Inicial (Assistente Interativo)

Execute o assistente de diagnóstico para verificar e orientar a instalação de dependências do sistema:

```bash
# Se instalado via uv tool:
muplayer setup

# Em ambiente de desenvolvimento local (clone do repositório):
uv run muplayer setup
```

### 3. Iniciar o Player

Após a configuração inicial, inicie o player TUI:

```bash
# Se instalado via uv tool:
muplayer

# Em desenvolvimento local:
uv run muplayer
```

#### Opções de Inicialização:
* `muplayer --debug` (ou `-d`): Ativa logs detalhados de depuração.
* `muplayer --force` (ou `-f`): Força a inicialização ignorando verificações prévias de ambiente.

---

## 🛠️ Comandos CLI

O MuPlayer disponibiliza um conjunto completo de comandos Typer (executáveis via `muplayer <comando>` ou `uv run muplayer <comando>`):

| Comando | Descrição |
| :--- | :--- |
| `muplayer` | Inicia a interface gráfica TUI principal do player. |
| `muplayer setup` | Executa o assistente interativo de instalação de motores de áudio e dependências do sistema. |
| `muplayer doctor` | Exibe diagnóstico completo do sistema (terminal, engines de áudio, runtime JS e diretórios XDG). |
| `muplayer update` | Verifica e atualiza a instalação do MuPlayer para a versão mais recente do repositório. |
| `muplayer version` | Exibe a versão atual do aplicativo. |

---

## 📁 Armazenamento e Configuração (Padrão XDG)

Os dados do MuPlayer são mantidos em diretórios padrão do sistema operacional gerenciados pelo `platformdirs`:

* **Banco de Dados e Configuração:** `~/.local/share/MuPlayer/` (`app_data.db`, `config.json`)
* **Cache de Buscas e URLs:** `~/.cache/MuPlayer/` (cache de buscas com 5 min TTL e URLs de stream com 1h TTL)
* **Logs do Sistema:** `~/.local/state/MuPlayer/logs/`

---

## 🗺️ Roteiro de Desenvolvimento (Roadmap Futuro)

- [ ] **Modo Offline Opcional:** Download de faixas selecionadas da biblioteca local para escuta offline sem dependência de conexão de rede.
- [ ] **Aprimoramento de Importação de Playlists:** Suporte avançado à sincronização periódica de playlists importadas via URL.

---

## 🛠️ Tecnologias Utilizadas

* **[Textual](https://textualize.io):** Framework gráfico para terminal (TUI).
* **[yt-dlp](https://github.com/yt-dlp/yt-dlp):** Busca e extração de streams de áudio do YouTube.
* **[mpv](https://mpv.io) / [VLC](https://www.videolan.org):** Motores de reprodução de áudio de alta fidelidade.
* **[Tortoise ORM](https://tortoise.github.io) & [SQLite](https://www.sqlite.org):** Persistência assíncrona para biblioteca local e playlists.
* **[Typer](https://typer.tiangolo.com) & [Rich](https://rich.readthedocs.io):** Framework de linha de comando (CLI) e formatação visual de relatórios.