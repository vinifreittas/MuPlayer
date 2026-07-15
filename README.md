# 🎵 MuPlayer

O MuPlayer é um app de músicas super leve que roda direto no terminal e transforma o YouTube em seu streaming pessoal. Ele utiliza o `yt-dlp` para buscas, o `MPV` ou `VLC` player para processar e reproduzir o áudio, o framework `Textual` para interface e o `SQLite` para gerenciar suas playlists e músicas.

## ✨ Qualidades

* **Leve e rápido:** Consome poucos recursos do sistema.
* **Streaming direto:** Reprodução de áudio sem necessidade de download prévio.
* **Interface via terminal:** Controle total direto pelo terminal.
* **Banco de dados próprio:** Gerencia suas playlists e músicas localmente.

## 🚀 Instalação e Configuração

Siga os passos abaixo para instalar, configurar as dependências e iniciar o player:

### 1. Instalar o MuPlayer

```bash
pip install git+https://github.com/vinifreittas/MuPlayer.git
```

### 2. Configurar os Players (mpv/vlc)

O MuPlayer depende de um player de áudio instalado, que pode ser o `mpv` ou `vlc`. Por isso, possui um **assistente de configuração (wizard) próprio** para auxiliar você nessa tarefa, caso ainda não possua nenhum dos dois instalado.

Para iniciar o assistente, execute:

```bash
python muplayer setup
```

> 💡 **Nota:** Se você preferir instalar os players manualmente, você ainda pode instalar o `mpv` ou `vlc` através do gerenciador de pacotes do seu sistema (como `apt` no Linux ou `brew` no macOS).

### 3. Iniciar o player

Após a configuração, basta rodar o comando abaixo para curtir suas músicas:

```bash
python muplayer
```

## 🛠️ Tecnologias Utilizadas

* **[yt-dlp](https://github.com/yt-dlp/yt-dlp):** Extração de áudio e busca de mídias.
* **[Textual](https://textualize.io):** Interface via terminal.
* **[SQLite](https://www.sqlite.org):** Banco de dados próprio.
* **[MPV](https://mpv.io):** Player de áudio.
* **[VLC](https://www.videolan.org):** Player de áudio.