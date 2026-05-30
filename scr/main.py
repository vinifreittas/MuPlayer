from player import FFmpegPlayer
import yt_dlp
import logging

logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")

# Configs base do yt_dlp pra busca e extração do audio.
YTDL_BASE_OPTS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "js_runtimes": {"quickjs": {}},
}

def pesquisar_no_youtube(termo_busca: str, max_resultados: int = 8) -> list:
    """Pesquisa no youtube e retorna uma lista com os principais resultados"""
    search_opts = {
        **YTDL_BASE_OPTS, 
        "default_search": f"ytsearch{max_resultados}", 
        "extract_flat": "in_playlist"
    }

    try:
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            info = ydl.extract_info(termo_busca, download=False)
    except Exception as e:
        print(f"Erro ao conectar com o YouTube: {e}")
        return None

    # Retorna só as entradas válidas
    return list(filter(None, info.get("entries", [])))

def extrair_audio_url(video_url: str) -> str | None:
    """Extrai o URL de reprodução de áudio direto de um URL de vídeo do YouTube."""
    try:
        with yt_dlp.YoutubeDL(YTDL_BASE_OPTS) as ydl_final:
            info_final = ydl_final.extract_info(video_url, download=False)
    except Exception as e:
        print(f"Erro na extração do URL de audio: {e}")
        return None
    
    return info_final.get("url")

def selecionar_video(videos: list) -> str | None:
    """Imprime os resultados da pesquisa e pede para o usuário escolher um."""
    if not videos:
        print("Nenhum resultado encontrado.")
        return None

    print("\n--- Resultados Encontrados ---")
    for i, video in enumerate(videos, start=1):
        titulo = video.get("title", "Título desconhecido")
        duracao = video.get("duration_string", "Live/Desconhecido")
        print(f"[{i}] {titulo} ({duracao})")

    # Loop de escolha
    while True:
        escolha = input("\nDigite o número da música (ou 'q' para uma nova busca): ").strip().lower()
        if escolha == 'q':
            return None
        
        try:
            index = int(escolha) - 1
            if 0 <= index < len(videos):
                video_escolhido = videos[index]
                break

            print(f"Número inválido. Escolha entre 1 e {len(videos)}.")
        except ValueError:
            print("Por favor, digite um número válido ou 'q' para uma nova busca.")

    return video_escolhido["url"]

def main():
    audio_url = None
    player = None

    try:
        player = FFmpegPlayer()

        while not audio_url:
            termo = input("O que você quer ouvir? ")
            if not termo:
                print("O termo de busca não pode estar vazio.")
                continue

            resultados = pesquisar_no_youtube(termo)
            video_url_selecionado = selecionar_video(resultados)

            if video_url_selecionado:
                audio_url = extrair_audio_url(video_url_selecionado)

        print("\n▶️ Iniciando a reprodução...")
        player.play(audio_url, mode="link")

        input("\n🛑 Pressione ENTER a qualquer momento para parar a música...\n")
        player.stop()

    except KeyboardInterrupt:
        print("\n👋 Programa interrompido pelo usuário.")
        raise SystemExit(0)
    
    except Exception as e:
        print(f"\n❌ Ocorreu um erro: {e}")
    
    finally:
        if player is not None:
            player.close()
        

# ------ Execução --------
if __name__ == "__main__":
    main()