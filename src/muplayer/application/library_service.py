import logging

from muplayer.application.ports import StoragePort
from muplayer.domain import Playlist, Song

logger = logging.getLogger(__name__)


class LibraryService:
    """Orquestra casos de uso da biblioteca musical e persistência de dados."""

    def __init__(self, db: StoragePort) -> None:
        self.db = db

    async def connect(self) -> None:
        await self.db.connect()

    async def disconnect(self) -> None:
        await self.db.disconnect()

    async def get_playlists(self, limit: int = 50, offset: int = 0) -> list[Playlist]:
        """Obtém todas as playlists com paginação."""
        return await self.db.get_playlists(limit=limit, offset=offset)

    async def get_playlist_by_name(self, name: str) -> Playlist | None:
        """Busca uma playlist específica pelo nome."""
        if not name or not name.strip():
            return None
        return await self.db.get_playlist_by_name(name.strip())

    async def create_playlist(self, name: str) -> tuple[bool, str, Playlist | None]:
        """Cria uma nova playlist se o nome for válido e não existente."""
        clean_name = name.strip() if name else ""
        if not clean_name:
            return False, "Nome da playlist não pode ser vazio.", None

        existing = await self.db.get_playlist_by_name(clean_name)
        if existing:
            return False, f"Playlist '{clean_name}' já existe.", existing

        playlist = await self.db.create_playlist(clean_name)
        if playlist:
            return True, f"Playlist '{clean_name}' criada com sucesso.", playlist
        return False, f"Falha ao criar playlist '{clean_name}'.", None

    async def delete_playlist(self, name: str) -> tuple[bool, str]:
        """Remove uma playlist e suas associações."""
        clean_name = name.strip() if name else ""
        if not clean_name:
            return False, "Nome da playlist inválido."

        success = await self.db.delete_playlist(clean_name)
        if success:
            return True, f"Playlist '{clean_name}' removida com sucesso."
        return False, f"Playlist '{clean_name}' não encontrada ou falha ao remover."

    async def add_song_to_playlist(self, playlist_name: str, song: Song) -> tuple[bool, str]:
        """
        Adiciona uma música a uma playlist existente ou cria uma nova se não existir.

        Retorna (sucesso: bool, mensagem_ou_status: str).
        """
        clean_name = playlist_name.strip() if playlist_name else ""
        if not clean_name:
            return False, "Nome de playlist inválido."

        existing = await self.db.get_playlist_by_name(clean_name)
        if not existing:
            created = await self.db.create_playlist(clean_name)
            if not created:
                return False, f"Falha ao criar playlist '{clean_name}'."

        success = await self.db.add_song_to_playlist(clean_name, song)
        if success:
            return True, f"Música '{song.title}' adicionada à playlist '{clean_name}'."
        return False, f"Falha ao adicionar à playlist '{clean_name}'."

    async def remove_song_from_playlist(self, playlist_name: str, song_index: int) -> tuple[bool, str]:
        """
        Remove a música de determinado índice da playlist.

        Retorna (sucesso: bool, mensagem_ou_status: str).
        """
        clean_name = playlist_name.strip() if playlist_name else ""
        if not clean_name:
            return False, "Nome de playlist inválido."

        success = await self.db.remove_song_from_playlist(clean_name, song_index)
        if success:
            return True, f"Música removida da playlist '{clean_name}'."
        return False, f"Falha ao remover música no índice {song_index} da playlist '{clean_name}'."
