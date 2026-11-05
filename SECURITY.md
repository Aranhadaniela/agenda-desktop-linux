# Segurança e privacidade

O projeto exporta dados privados de calendário. Não inclua eventos, UIDs reais, nomes pessoais, credenciais, logs privados ou cópias de calendários em issues, commits ou relatórios. Use exemplos sintéticos.

Para informar uma vulnerabilidade, use o canal privado de segurança do repositório, se habilitado pelo mantenedor. Se ele ainda não estiver disponível, não publique detalhes exploráveis nem dados pessoais em uma issue pública; solicite primeiro um canal privado ao mantenedor.

Mantenha Python, Evolution Data Server, PyGObject, libical e dependências transitivas atualizados por uma distribuição com suporte de segurança. Compatibilidade de sintaxe não garante suporte de segurança do runtime.

Grave a saída em diretório privado e controlado pelo usuário, fora de sincronização pública, e não execute o Core como root. O arquivo é gravado com permissão 0600, mas não é criptografado. O EDS pode sincronizar fontes remotas já configuradas quando consultado.

Todos os JSONs são ignorados por padrão. O `.gitignore` não impede uploads manuais, inclusão forçada ou publicação de arquivos já rastreados. Não distribua arquivos de backup ou a pasta de trabalho inteira.

Veja o [relatório de auditoria](docs/security-audit.md) para escopo, resultados e limitações. Integrações de desktop futuras exigirão nova revisão.
