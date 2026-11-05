# Contrato JSON

Exemplo inteiramente sintético:

```json
{
  "eventos": [
    {
      "titulo": "Evento de exemplo",
      "inicio": "2026-11-05T09:00:00-03:00",
      "fim": "2026-11-05T10:00:00-03:00",
      "dia_inteiro": false
    },
    {
      "titulo": "Dia inteiro de exemplo",
      "inicio": "2026-11-06",
      "fim": "2026-11-08",
      "dia_inteiro": true
    }
  ]
}
```

As cinco chaves existentes são preservadas. `fim` pode ser `null`. Eventos com hora usam ISO 8601 com deslocamento UTC; datas de dia inteiro usam `YYYY-MM-DD` e não são convertidas de fuso. O fim de dia inteiro é exclusivo: o segundo exemplo cobre os dias 6 e 7. Uma lista vazia é `{"eventos": []}`.

O serviço ordena por instante UTC; datas e horários sem fuso são interpretados no fuso local. Empates preservam a ordem do provider. Não modifica os textos do modelo. O provider converte horários UTC ou com fuso libical para o fuso local e interpreta horários flutuantes como locais.

O fuso local usa `TZ` (nome IANA ou caminho de arquivo TZif), ou `/etc/localtime`; isso preserva transições sazonais. Se o arquivo de sistema não estiver disponível, há fallback para o deslocamento local do processo. Uma variável `TZ` inválida gera erro em vez de deslocar eventos silenciosamente.

O writer cria um temporário no mesmo diretório, grava UTF-8, executa `fsync` no arquivo e o substitui com `os.replace`. Falhas anteriores à substituição preservam a versão anterior. O arquivo resultante tem permissão 0600. Não há garantia de persistência da entrada de diretório após queda de energia, pois o diretório não recebe `fsync`.
