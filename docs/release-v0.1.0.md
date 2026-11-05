# Prontidão para publicação — v0.1.0

Data da preparação: 2026-11-05. Estado: fontes e documentação preparados; publicação não realizada. A versão está registrada em `VERSION`, sem mudança no comportamento do Core ou criação de pacote instalável.

## Entregas

- Licença MIT em `LICENSE`, com o ano 2026 e titular `agenda-desktop-linux`, confirmado explicitamente pelo usuário antes da finalização.
- README com instruções de instalação via pacotes do sistema, todos os argumentos CLI existentes e limites de suporte por desktop.
- Notas de versão em `CHANGELOG.md` e revisão de dependências, mínimos identificáveis, baseline e avisos em [dependencies.md](dependencies.md).
- [Lista explícita de 24 arquivos para o primeiro commit](first-commit-files.txt), sem JSONs, dados pessoais, backups, credenciais ou extensão instalada. A lista é uma autorização de escopo documental para revisão, não executa staging.
- `.gitignore` revisado: não há regras duplicadas; todos os JSONs, backups, configurações pessoais, credenciais comuns, ambientes, caches, logs e temporários continuam protegidos. Nenhuma exceção para JSON foi adicionada. Não houve necessidade de alterar as regras nesta etapa.

## Validação

- `/usr/bin/python3 -m unittest discover -s tests -v`: **15 testes passaram, sem testes ignorados**.
- `/usr/bin/python3 main.py --help`: executado sem acesso ao EDS; argumentos conferidos com o README. Não foram acrescentados argumentos como `--version` que o CLI ainda não implementa.
- Imports dos bindings e assinaturas EDS conferidos no Python do sistema; nenhuma consulta a calendário real executada.
- Lista de publicação conferida quanto à existência, cobertura das regras de exclusão e ausência de padrões óbvios de segredos e caminhos pessoais. A varredura não imprime valores.
- Não há repositório Git válido nesta pasta. Não foram executados `git init`, `git add`, `git commit` ou `git push`. Sem índice ou histórico acessível para auditar.

A lista representa os arquivos atuais, não garante a segurança de alterações futuras. `.gitignore` não protege conteúdo previamente rastreado, inclusão forçada ou arquivos enviados manualmente.

## Parecer

**A preparação documental e a licença estão concluídas. O conjunto selecionado de fontes pode ser revisado para uma futura publicação experimental do Core; não há liberação incondicional de segurança do ambiente ou certificação dos desktops.** Antes de promover a v0.1.0 como release pronta para uso, resolver ou documentar formalmente a avaliação dos avisos libical3 e a revisão das dependências transitivas. Não distribuir a pasta inteira.

## Pendências antes da publicação

| Prioridade | Pendência | Critério de conclusão |
| --- | --- | --- |
| Alta | Avaliar CVE-2026-111269 e CVE-2026-88383 para libical3 Ubuntu e revisar pacotes transitivos. | Confirmar aplicabilidade e patches pela distribuição; aplicar atualizações pelo fluxo autorizado e repetir testes. Detalhes e fontes em `dependencies.md`. |
| Alta | Revisar o conjunto final selecionado quando houver Git. | Conferir índice e eventual histórico restaurado, mantendo somente a lista explícita e verificando alterações posteriores. Inicialização e publicação exigem autorização futura. |
| Média | Confirmar integração real em ambiente descartável. | Consultar calendário sintético autorizado, incluindo recorrências, exceções, fusos e dia inteiro, sem usar dados pessoais em evidências públicas. |
| Média | Delimitar suporte a outras distribuições e versões. | Criar matriz testada antes de reduzir baseline ou anunciar suporte amplo. |
| Baixa | Configurar canal privado de segurança no futuro repositório. | Conferir que `SECURITY.md` aponta para um mecanismo disponível, sem inventar contato ou URL. |

## Recomendações e limites conhecidos

O aviso EDS CVE-2026-2604 foi verificado como corrigido na revisão Ubuntu instalada; isso não certifica todas as dependências. Versões de namespace GI não são mínimos de segurança. Python 3.10 é apenas mínimo sintático e não é recomendação de runtime upstream em novembro de 2026.

Permanecem as propostas da auditoria inicial: limite superior de dias/volume, cancelamento, política de sobrescrita e mensagens de erro com menos metadados. Não foram implementadas por alterarem comportamento; devem ser decididas separadamente. A escrita atual substitui o destino escolhido, mantém permissão 0600 e pode deixar temporário privado após interrupção abrupta. Usar diretório privado e não executar com privilégios elevados.

A extensão GNOME instalada não integra esta lista de publicação nem foi revisada nesta etapa. KDE e Cinnamon são planos futuros. O EDS pode sincronizar fontes remotas configuradas ao ser consultado, embora o projeto não implemente upload ou telemetria.

Nenhuma alteração foi feita em calendários, eventos, arquivos JSON privados, backups ou extensão instalada. Nenhum arquivo foi publicado.
