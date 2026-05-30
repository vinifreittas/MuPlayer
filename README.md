# 🎵 MuPlayer

O MuPlayer é um player de música para terminal super leve que transforma o YouTube em seu streaming pessoal. Ele utiliza o `yt-dlp` para buscar o áudio, o `FFmpeg` para processá-lo e o `PyAudio` para a reprodução direta no console.


## ✨ Funcionalidades

* **Leve e rápido:** Consome poucos recursos do sistema.
* **Busca direta:** Streaming de áudio sem necessidade de download prévio.
* **Interface via terminal:** Controle total direto da sua linha de comando.


## 🛠️ Pré-requisitos

Antes de instalar as dependências do Python, é necessário configurar as ferramentas de áudio, vídeo e engine JavaScript no seu sistema operacional.

### 🐧 Linux (Ubuntu/Debian)
```bash
sudo apt update && sudo apt install -y ffmpeg portaudio19-dev quickjs
```

### 🍏 macOS
```bash
brew install ffmpeg portaudio quickjs
```

### 🪟 Windows
1. **FFmpeg:** Baixe no site oficial, extraia os arquivos e adicione a pasta `bin` às **Variáveis de Ambiente (PATH)** do sistema.
2. **QuickJS:** Baixe o executável (ex: *quickjs-windows* no GitHub), renomeie o binário de `qjs.exe` para `quickjs.exe` e adicione o diretório dele ao seu **PATH**.


## 🚀 Como Instalar e Rodar

Siga os passos abaixo para configurar o ambiente Python e iniciar o player:

### 1. Clonar o repositório
```bash
git clone https://github.com
cd MuPlayer
```

### 2. Instalar as dependências do Python
```bash
pip install -r requirements.txt
```

### 3. Iniciar o player
```bash
python main.py
```


## 🛠️ Tecnologias Utilizadas

* **[yt-dlp](https://github.com):** Extração de áudio e busca de mídias.
* **[FFmpeg](https://ffmpeg.org):** Conversão e processamento de fluxo de áudio.
* **[PyAudio](https://mit.edu):** Reprodução de áudio baseada no PortAudio.
* **[QuickJS](https://bellard.org):** Engine JavaScript leve usada pelo yt-dlp para decodificar assinaturas de streaming.