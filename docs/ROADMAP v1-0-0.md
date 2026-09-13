# 🚀 Primeira versão oficial (v1.0.0) - Em Desenvolvimento

## 🎯 Funcionalidades Principais
- [X] Checagem de compatibilidade do terminal (TTY, cores, dimensões)
- [X] Internacionalização / i18n (`pt-BR`, `en-US` via `i18n.py` e seletor na TUI)
- [X] CLI & Diagnóstico (`muplayer setup`, `doctor`, `update`, `version`)
- [X] Validação de Pre-flight & Composition Root (`main.py`, detecção de JS runtime para `yt-dlp`)
- [X] Suporte a XDG Standard (`platformdirs`) e Cache em disco (`diskcache`)
- [X] Suíte de testes (`pytest` e `pytest-asyncio`)
- [/] Sistema de playlists (Backend/ORM completo; criação e adição na UI prontos, exclusão pendente)
- [ ] Modo Eficiência (Economia de recursos no terminal)
- [ ] Histórico de reprodução (Registro de faixas tocadas)

## 🔧 Otimizações
- [ ] Otimização do uso de memória e CPU
- [ ] Refinamento da experiência de uso (UX/TUI)

## 📚 Documentação & Futuro
- [X] Documentação do projeto (`README.md` e `AGENTS.md`)
- [ ] Importação de playlists públicas do YouTube via URL (Futuro v1.1.0)
- [ ] Modo offline opcional com download de faixas (Futuro v1.2.0)
