import os
import threading
import logging
from contextlib import contextmanager

import av
import pyaudio

logger = logging.getLogger(__name__)

@contextmanager
def silenciar_stderr_nativo():
    """Silencia mensagens de erro de baixo nível (C/C++) do sistema operacional."""
    stderr_fd = 2
    try:
        # Salva o estado original do stderr e redireciona ele para o devnull
        copia_stderr = os.dup(stderr_fd)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, stderr_fd)
        os.close(devnull)
        yield
    finally:
        # Restaura o comportamento padrão do terminal
        os.dup2(copia_stderr, stderr_fd)
        os.close(copia_stderr)

class FFmpegPlayer:
    def __init__(self, out_channels: int = 2, out_rate: int = 44100, buffer_size: int = 4096):
        # Inicia o PyAudio de forma silenciosa, pra não sujar o terminal com mensagens inuteis
        with silenciar_stderr_nativo():
            self.pyaudio_instance = pyaudio.PyAudio()
        
        self.stream = None
        self.play_thread = None
        self._lock = threading.Lock()

        self.is_playing = threading.Event()
        
        self.out_channels = out_channels
        self.out_rate = out_rate
        self.buffer_size = buffer_size

    def play(self, source: str, mode: str) -> None:
        """Inicia a reprodução de um arquivo ou link de rede em uma nova thread."""
        if mode not in ['file', 'link']:
            raise ValueError("O modo deve ser 'file' ou 'link'")

        self.stop() 
        self.is_playing.set()
        
        self.play_thread = threading.Thread(
            target=self._play_worker, args=(source, mode), daemon=True
        )
        self.play_thread.start()
        logger.info(f"Reproduzindo (modo {mode}): {source}")

    def stop(self) -> None:
        """Para a reprodução atual"""
        if self.is_playing.is_set():
            self.is_playing.clear()
            logger.info("Player interrompido.")
        
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=1.0)
        
    def close(self) -> None:
        """Fecha o player e finaliza todas as dependências corretamente."""
        self.stop()
        with self._lock:
            if self.pyaudio_instance:
                self.pyaudio_instance.terminate()
        logger.info("Player finalizado.")

    def _play_worker(self, source: str, mode: str) -> None:
        """Método interno que roda na thread para decodificar e reproduzir o áudio."""
        options = {
            'timeout': '5000000',
            'rtsp_transport': 'tcp',
            'reconnect': '1'
        } if mode == 'link' else {}

        try:
            with av.open(source, options=options) as container:
                if not container.streams.audio:
                    logger.error(f"Nenhum fluxo de áudio encontrado em {source}")
                    return

                audio_stream = container.streams.audio[0]

                layout = "mono" if self.out_channels == 1 else "stereo"
                resampler = av.AudioResampler(
                    format='s16', layout=layout, rate=self.out_rate
                )
                
                # Inicializa o fluxo de saída do PyAudio de forma segura.
                with self._lock:
                    self.stream = self.pyaudio_instance.open(
                        format=pyaudio.paInt16,
                        channels=self.out_channels,
                        rate=self.out_rate,
                        output=True,
                        frames_per_buffer=self.buffer_size
                    )

                # Decodifica e manda pra reprodução
                for frame in container.decode(audio_stream):
                        if not self.is_playing.is_set():
                            break 

                        for resampled_frame in resampler.resample(frame):
                            self._write_audio(resampled_frame)
                
                # Envia o que restar no buffer
                if self.is_playing.is_set():
                    for resampled_frame in resampler.resample(None):
                        self._write_audio(resampled_frame)
                        
        except Exception as error:
            logger.error(f"Erro na reprodução (modo {mode}): {error}")
        finally:
            if self.is_playing.is_set():
                logger.info("Reprodução finalizada.")
            self._cleanup_stream()

    def _write_audio(self, frame):
        """Escreve os bytes de áudio diretamente no stream do PyAudio."""
        if self.stream and self.stream.is_active():
            raw_audio_bytes = frame.to_ndarray().tobytes()
            self.stream.write(raw_audio_bytes)

    def _cleanup_stream(self):
        """Fecha o stream do PyAudio com segurança."""
        with self._lock:
            self.is_playing.clear()
            if self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except Exception:
                    pass
                self.stream = None

    def __del__(self):
        self.close()