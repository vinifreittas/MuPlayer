# 🎵 MuPlayer

O MuPlayer é um app de músicas super leve que roda direto no terminal e transforma o YouTube em seu streaming pessoal. Ele utiliza o `yt-dlp` para buscas, o `MPV` ou `VLC` player para processar e reproduzir o áudio, o framework `Textual` para interface e o `SQLite` para gerenciar suas playlists e músicas.


## ✨ Qualidades

* **Leve e rápido:** Consome poucos recursos do sistema.
* **Streaming direto:** Reprodução de áudio sem necessidade de download prévio.
* **Interface via terminal:** Controle total direto pelo terminal.
* **Banco de dados próprio:** Gerencia suas playlists e músicas localmente.


## 🛠️ Pré-requisitos

Antes de instalar o MuPlayer é necessário instalar o player de áudio de sua preferencia, se ainda não tiver, instale o `mpv` ou `vlc`.

### 🐧 Linux (Ubuntu/Debian)
```bash
sudo apt install -y [player]
```

### 🍏 macOS
```bash
brew install [player]
```

### 🪟 Windows
1. **MPV:** Baixe no site oficial, extraia os arquivos e adicione a pasta `bin` às **Variáveis de Ambiente (PATH)** do sistema.
2. **VLC:** Baixe no site oficial, extraia os arquivos e adicione a pasta `bin` às **Variáveis de Ambiente (PATH)** do sistema.


## 🚀 Como Instalar e Rodar

Siga os passos abaixo para instalar e iniciar o player:

### 1. Instalar o MuPlayer
```bash
pip install git+https://github.com/vinifreittas/MuPlayer.git
```

### 2. Iniciar o player
```bash
muplayer
```


## 🛠️ Tecnologias Utilizadas

* **[yt-dlp](https://github.com/yt-dlp/yt-dlp):** Extração de áudio e busca de mídias.
* **[Textual](https://textualize.io):** Interface via terminal.
* **[SQLite](https://www.sqlite.org):** Banco de dados próprio.
* **[MPV](https://mpv.io):** Player de áudio.
* **[VLC](https://www.videolan.org):** Player de áudio.