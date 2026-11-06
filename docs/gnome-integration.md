# Etapa 4.1 — extensão GNOME experimental

Para o roteiro atual de testes sintéticos sem EDS, consulte a [Etapa 4.2](gnome-validation.md).

Alvo inicial: GNOME Shell 46 / GJS 1.80. Implementação em `desktop/gnome/`; ainda requer validação visual em sessão isolada. KDE e Cinnamon continuam não implementados. Não há instalação ou ativação automática.

## Análise do backup

O backup usava gerador e JSON em caminhos locais no diretório de dados do usuário, sem contrato de instalação do Core, e o mesmo UUID da extensão local. Também usava `_backgroundGroup` (privado), leitura síncrona de arquivo, ordenação textual e ausência de bloqueio de subprocessos. Não foram copiados dados pessoais ou identificadores de calendário. O CSS roxo foi preservado; o código foi reorganizado com APIs ESM e St/Gio/GLib do GNOME 46.

## Arquitetura

`extension.js → Gio.Subprocess(argv) → update_events.py → Core Python → EDS → JSON atômico → events.js → St.Label`

- UUID público próprio: `agenda-desktop-linux@extensions.local`. Não conflita com o UUID da instalação anterior e não é um e-mail pessoal.
- O instalador copia uma lista fechada de fontes do mesmo Core para `python/core` e `python/providers` dentro do pacote. Não copia `main.py`, dados, configurações ou backups. Não mantém uma segunda implementação do Core. Mudanças posteriores no repositório exigem novo pacote.
- O entry point é relativo ao pacote (`this.path`), executado por `/usr/bin/python3` com argv fixo e sem shell. Python do sistema é usado para encontrar GI. O caminho não é concatenado em comando de shell.
- JSON: `${XDG_CACHE_HOME}/agenda-desktop-linux-gnome/eventos.json`; fallback padrão é `~/.cache`. O adapter rejeita cache que seja link simbólico, não pertença ao usuário ou permita acesso de grupo/outros. Criação com 0700; saída e lock com 0600. XDG deve ser absoluto; valores relativos usam o fallback XDG padrão.
- Uma atualização ao habilitar, uma a cada cinco minutos e botão manual. A extensão mantém um subprocesso por vez, encerra após 60 segundos e ao desabilitar. Um lock não bloqueante no adapter impede dois exports simultâneos usando este adapter/cache. CLI independente não usa esse lock: não apontar sua saída para este cache em paralelo.
- Nenhum diagnóstico do provider é escrito nos logs do Shell: stdout/stderr são descartados e mensagens ao usuário são genéricas. Em falhas, o writer preserva o JSON anterior e a interface indica dados anteriores; cache não tem garantia de atualidade. Timer recalcula hoje/amanhã.
- Leitura assíncrona e cancelável; `disable()` remove fontes GLib, sinais e atores, cancela leitura e termina o subprocesso. Callbacks de sessões anteriores não alteram uma sessão reabilitada.
- `events.js` interpreta datas de dia inteiro como datas civis locais, respeita fim exclusivo e ausência de fim como um dia. Eventos com hora exigem offset ou Z, são ordenados por instante e exibidos na hora local. Cada grupo mostra eventos que o intersectam; eventos de vários dias aparecem nos dois grupos. Eventos com hora já terminados são ocultados; sem fim é tratado como instante.
- Títulos são texto, nunca markup/HTML. Limites de parse: 2 MiB de texto, 5.000 eventos, 1.000 caracteres por título; até 100 linhas por dia com indicação de limite. A leitura assíncrona carrega o arquivo antes desses limites: não são um limite rígido de memória contra um cache local adulterado por outro processo do mesmo usuário.
- Widget roxo posicionado no monitor principal com `Main.layoutManager.addChrome`, sem reservar área de trabalho. Essa API o coloca na camada de interface do Shell, podendo sobrepor janelas; não garante posicionamento abaixo das janelas como o backup. Usa `trackFullscreen` e não declara modos de login/bloqueio. A experiência de desktop, múltiplos monitores, overview e redimensionamento requer validação visual.

## Requisitos e seleção de calendário

Além dos [requisitos do Core](dependencies.md): GNOME Shell 46, GJS 1.80, St e as bibliotecas do Shell/Mutter correspondentes. Nenhuma dependência GTK/Qt foi acrescentada ao Core. Instalar pacotes apenas pelo fluxo autorizado do sistema; scripts desta etapa não instalam dependências.

Por padrão, um único calendário habilitado é escolhido pelo Core. Com vários, prepare uma seleção privada em `${XDG_CONFIG_HOME}/agenda-desktop-linux/gnome.ini` (fallback `~/.config`) com permissão **0600**, em diretório privado:

```ini
[calendar]
uid = UID_OBTIDO_LOCALMENTE
```

Esse arquivo não é distribuído nem criado pelo instalador. Use a CLI existente com `--list-calendars` somente localmente para descobrir o UID. Não publique a saída. O adapter também aceita `CALENDAR_UID` se não houver INI; o ambiente do Shell pode diferir do terminal, portanto o INI é a opção previsível. INI com `uid` vazio solicita seleção automática. Não há UIDs fixos. Configuração inválida ou não privada provoca erro genérico, sem apagar o cache anterior.

Não há rede própria ou telemetria; o EDS pode sincronizar fontes configuradas ao ser consultado. Ativar a extensão inicia consultas. Para validar sem consultar contas reais, use outra sessão/VM com EDS e calendário sintético; não ative na sessão pessoal nesta etapa.

## Preparar sem instalar

Na pasta do projeto:

```bash
/usr/bin/python3 scripts/install_gnome.py --help
/usr/bin/python3 scripts/install_gnome.py
```

O segundo comando apenas gera `dist/gnome/agenda-desktop-linux@extensions.local`, ignorado pelo Git. Opcionalmente use `--output DIRETORIO_NOVO`. O destino deve ser novo: qualquer diretório ou link existente é recusado. Preparação dentro dos diretórios de extensões padrão é bloqueada; exige modo de instalação explícito. Se uma cópia falhar, pode restar um diretório incompleto; ele nunca é considerado automaticamente instalado/ativado pelo script. Não reutilizar esse destino sem revisão manual.

O pacote contém cinco arquivos da extensão, oito arquivos Python do Core/provider e a licença MIT. Somente `metadata.json` é JSON público, sem eventos; é a única exceção específica adicionada ao `.gitignore`.

## Validar sem substituir a instalação atual

1. Execute os testes abaixo no repositório; não carregam a interface nem consultam calendários reais.
2. Prepare o pacote em diretório novo de teste. Confira o conteúdo e as permissões.
3. Para validação visual, use preferencialmente uma VM ou conta de teste com GNOME 46 e calendários sintéticos. Transfira somente o pacote preparado, sem INI ou cache pessoal.
4. **Somente após autorização separada**, nessa sessão de teste, execute `python3 scripts/install_gnome.py --install` a partir dos fontes. O script exige terminal interativo e digitação do UUID. Ele nunca sobrescreve destino existente, não usa sudo e não ativa a extensão. O pacote preparado também pode ser inspecionado sem executar esse modo.
5. **Após autorização para ativar**, encerre/abra a sessão de teste se necessário e use `gnome-extensions enable agenda-desktop-linux@extensions.local`. Para desabilitar na sessão de teste, use `gnome-extensions disable agenda-desktop-linux@extensions.local`. Nenhum desses comandos foi executado nesta etapa.
6. Confira roxo, hoje/amanhã, eventos atravessando meia-noite, fim exclusivo, dias de DST, botão/timer, ausência de duplicação, cache inválido, offline, lock, disable/enable, overview, bloqueio de tela e monitor desconectado. Verifique que nenhum dado apareça em logs. Use dados sintéticos em toda evidência.

O UUID distinto evita substituir a extensão anterior. Não execute `--replace`, não edite a instalação anterior e não use o UUID antigo nos comandos de instalação/ativação. Atualizações de uma instalação desta nova extensão ainda exigem procedimento separado: o instalador recusa substituições mesmo com confirmação.

## Testes e resultados desta etapa

```bash
/usr/bin/python3 -m unittest discover -s tests -v
TZ=America/Fortaleza gjs -m tests/test_gnome_events.js
TZ=America/New_York gjs -m tests/test_gnome_dst.js
gjs -m scripts/check_gnome_js.js desktop/gnome/extension.js desktop/gnome/events.js tests/test_gnome_events.js tests/test_gnome_dst.js scripts/check_gnome_js.js
```

- 21 testes Python passaram (15 anteriores e 6 novos): pacote fechado, recusa de sobrescrita, cache privado, recusa de symlink, configuração privada, fallback XDG e lock.
- Testes GJS passaram para agrupamento, conversão, validação e dias de 23/25 horas em DST.
- Sintaxe ESM conferida por `Reflect.parse` com `target: 'module'`, usando SpiderMonkey do GJS 1.80.2. Não é um carregamento de extensão no Shell.
- API `St.ScrollView.set_child` conferida nos typelibs St/Mutter do GNOME 46 instalado, sem construir atores nem abrir sessão gráfica.
- Pacote e candidatos públicos revisados localmente para dados pessoais; metadados públicos não são dados de calendário. Nenhum JSON real ou backup integra o pacote. Sem instalação, ativação, commit ou push.

## Pendências

Validar ciclo visual real, sobreposição, teclado/acessibilidade e tamanhos de tela; adicionar teste de ciclo de vida dentro de Shell isolado e expansão real de recorrências; conferir privacidade durante bloqueio de tela. O timeout encerra o processo cliente, não promete cancelar trabalho que já tenha sido delegado ao EDS. Limites de consulta do Core e avisos de dependências da auditoria anterior continuam pendentes. Não há certificação extensions.gnome.org nem suporte anunciado para outras versões do Shell.

Referências: [ESM no GNOME 45+](https://gjs.guide/extensions/upgrading/gnome-shell-45.html), [portabilidade GNOME 46](https://gjs.guide/extensions/upgrading/gnome-shell-46.html), [ciclo de vida e revisão de extensões](https://gjs.guide/extensions/review-guidelines/review-guidelines.html).
