# 📋 MuPlayer — Backlog v1.0.0

> Atualizado em: 2026-09-28  
> Base: Análise do `ROADMAP v1-0-0.md` × Código TUI × Alinhamento via `/grill-me`

---

## Legenda de Prioridade

| Prioridade | Descrição |
|------------|-----------|
| 🔴 **P0** | Bloqueador de v1.0.0 — funcionalidade essencial ausente ou incompleta |
| 🟡 **P1** | Importante para v1.0.0 — lacuna de UX/UI com especificação alinhada |
| 🟢 **P2** | Futuro / Postponed — movido para v1.1.0+ ou melhorias secundárias |

---

## 🎯 Épico 1 — Sistema de Playlists (UI)

### BL-01 — Exclusão de Playlist na Sidebar 🔴 P0
- **Contexto:** `LibraryService.delete_playlist()` existe no backend, mas não tem UI na `Sidebar`.
- **Decisão de UI/UX:**
  - Exibir botão de lixeira 🗑 inline ao passar o mouse (hover) sobre o item da playlist na `Sidebar`.
  - Ao clicar no 🗑, **excluir diretamente** a playlist e exibir uma notificação toast de confirmação informando a remoção.
- **Implementação:**
  - `widgets/sidebar.py`: Emitir mensagem `PlaylistDeleteRequested(name)`.
  - `controllers/navigation.py`: Manipular evento, chamar `library_service.delete_playlist(name)`, atualizar `Sidebar.playlist_names` e recarregar view.
  - `infrastructure/i18n.py`: Chaves de tradução da notificação toast.

---

### BL-02 — Remoção de Faixa da Playlist 🔴 P0
- **Contexto:** `LibraryService.remove_song_from_playlist()` existe no backend, mas não há ação de remoção no `SongList`.
- **Decisão de UI/UX:**
  - Adicionar botão 🗑 inline visível no hover sobre cada item do `SongList`.
  - O botão 🗑 de remoção deve ser visível **apenas quando o `SongList` estiver exibindo uma playlist** (não no histórico ou resultado de busca).
- **Implementação:**
  - `widgets/song_item.py`: Adicionar botão de remoção 🗑 condicional ao contexto de playlist.
  - `widgets/song_list.py`: Repassar evento `SongRemoveRequested(index)`.
  - `controllers/navigation.py`: Invocar `library_service.remove_song_from_playlist(current_playlist_name, song_index)` e recarregar faixas.

---

### BL-03 — Destaque de Playlist Ativa na Sidebar 🟡 P1
- **Decisão de UI/UX:**
  - Manter o estado `active_playlist_name: reactive[str]` no `NavigationMixin`.
  - Aplicar classe CSS `.active` no `ListItem` correspondente na `Sidebar`.
  - Esse estado garante o contexto necessário para BL-02 (saber qual playlist está sendo visualizada).

---

## 🎨 Épico 2 — Refinamento de UX/TUI

### BL-12 — Exibição Numérica do Volume 🟡 P1
- **Decisão de UI/UX:**
  - Adicionar um label numérico no `MiniPlayer` ao lado da barra de volume exibindo a porcentagem atual (ex.: `50%`).

---

## 🟢 Épico 3 — Roadmap Futuro (v1.1.0 e v1.2.0)

Os itens abaixo foram postergados ou mantidos no planejamento de versões futuras:

### v1.1.0
- **BL-13 / BL-14:** Keybindings de Atalho (Toggle Sidebar com `ctrl+b` e Foco na Busca com `/`).
- **BL-17:** Auditoria avançada de invalidação de cache de URLs viciadas em segundo nível.
- **BL-18:** Suíte de testes de integração end-to-end de UI com `textual.testing`.
- **BL-19:** Importação de playlist pública do YouTube via URL.

### v1.2.0
- **BL-20:** Modo offline opcional com download local de faixas.

---

## 📊 Matriz de Priorização v1.0.0

| ID | Item | Categoria | Escopo v1.0.0 |
|----|------|-----------|---------------|
| **BL-01** | Exclusão de Playlist (🗑 hover inline + toast) | Playlists | 🔴 P0 |
| **BL-02** | Remoção de Faixa de Playlist (🗑 hover inline no SongList) | Playlists | 🔴 P0 |
| **BL-03** | Highlight de playlist selecionada na Sidebar | UI/UX | 🟡 P1 |
| **BL-12** | Label de porcentagem numérica do Volume | UI/UX | 🟡 P1 |
| **BL-13/14** | Keybindings de busca e sidebar | UI/UX | 🟢 v1.1.0 |
| **BL-17/18** | Testes TUI e cache audit | QA | 🟢 v1.1.0 |
| **BL-19** | Importação de Playlist YouTube | Feature | 🟢 v1.1.0 |
| **BL-20** | Modo Offline / Download | Feature | 🟢 v1.2.0 |
