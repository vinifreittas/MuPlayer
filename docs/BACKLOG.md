# 📋 Backlog pra versão 1.0.0

## 🐛 Terminal e Logs
- [ ] Corrigir vazamento de log no terminal.
- [X] Definir tamanho mínimo do terminal (com ajuste automático, se possível).
- [X] Refatorar sistema de histórico:
  - Corrigir bugs no histórico e migrar para registro real de execução baseado no modelo `SongTable`.
  - Filtrar retornos por última ocorrência.
- [X] Ajustar flags CLI:
  - Remover `--force`.
  - Integrar `--debug` ao comando de `log` (preservar log total em nível *debug* e aplicar filtros na visualização).

## 🎵 Playlists
- [ ] Implementar remoção de faixa de uma playlist.
- [ ] Implementar exclusão de playlist.

## 🛠️ Qualidade e Manutenção
- [ ] Analisar e melhorar a estrutura e a documentação do projeto.
- [ ] Garantir suporte e funcionamento ideal multiplataforma.
- [ ] Realizar testes completos em todas as funcionalidades (*features*).