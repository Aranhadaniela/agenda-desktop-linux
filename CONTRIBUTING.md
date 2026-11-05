# Como contribuir

1. Descreva o problema com exemplos sintéticos.
2. Mantenha o Core independente dos desktops e preserve o contrato JSON.
3. Execute `/usr/bin/python3 -m unittest discover -s tests -v`.
4. Explique a alteração e os resultados dos testes no pull request.

Não inclua eventos reais, nomes de calendários pessoais, identificadores institucionais, credenciais, arquivos `.env`, JSON gerado ou qualquer conteúdo de `backup/`. Revise arquivos explicitamente antes de adicioná-los ao Git; o `.gitignore` não protege arquivos já rastreados. Não use `git add -f` para esses dados.

Não altere extensões instaladas no perfil do usuário nem calendários existentes para testar. Use mocks ou um calendário descartável criado e autorizado para integração manual.

A pasta de trabalho pode precisar ser inicializada como repositório Git pelo mantenedor. Publicação, configuração de remoto e escolha de licença são etapas separadas.
