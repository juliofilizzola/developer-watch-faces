# DevTime design system

Fonte da verdade em código: `shared/scripts/wffgen/palettes.py` (paletas) e as constantes de layout em cada
`generator/*_face.py`. Este documento descreve as regras.

## Grade e área segura

- Canvas de referência **480 × 480** (Galaxy Watch 6 44 mm); o runtime escala para 432 × 432 (40 mm) e outros.
- `clipShape="CIRCLE"`. Toda linha de texto é verificada contra a corda do círculo com margem de 10–14 px
  (`LayoutCheck`, `circle_half_width`). Linhas de valor variável usam `ellipsis` com largura limitada à corda.
- Relógio sempre o elemento dominante: 50–112 px conforme layout; ajuste automático de largura com segundos/AM-PM.
- Coluna de código: gutter alinhado à direita em x≈80–92, código em x≈104–114, indentação de 2 espaços.

## Tipografia

| Uso | Fonte | Pesos |
|---|---|---|
| JSON e Code | JetBrains Mono (OFL) | Light 300 (AOD, gutter), Regular 400, Bold 700 (relógio) |
| Matrix | Share Tech Mono (OFL) + JetBrains Mono (chuva e barras) | Regular |

As fontes são instâncias estáticas geradas do JetBrains Mono variável (`fontTools.varLib.instancer`),
~115 KB cada, copiadas para `res/font` de cada pacote. Licenças em `fonts/`.

## Cor

- Fundo preto AMOLED por padrão; fundos alternativos escuros (#101010, #1E1E1E, #0D1117, #00110A).
- 11 paletas de editor (VS Code Dark+, Dracula, Monokai, One Dark, GitHub Dark, Nord, Solarized, Gruvbox,
  Terminal, Âmbar CRT, Mono), cada uma com papéis: chave, string, número, keyword, função, comentário,
  pontuação, relógio.
- Matrix: cor principal em 2 tons (principal + dim), destaque para "cabeças" da chuva, intensidade em cinza
  multiplicada pelo tint, brilho opcional (OutGlow).

## AMOLED e AOD

- Nenhum preenchimento grande claro; painéis Matrix são pretos semitransparentes.
- AOD: grupo separado, sempre sobre preto, fonte Light, opacidade 78–82 %, sem segundos, sem chuva, sem anéis,
  sem decoração e sem complicações. Mantém a identidade (aspas do JSON, `Time:` do Code, fonte do Matrix).

## Ícones

Gerados por `shared/scripts/make_icons.py` (glifos brancos tingidos em runtime): bateria, passos, coração, clima
genérico, chama, pino e 16 ícones de condição de clima (`wx_0..wx_15`, indexados por `[WEATHER.CONDITION]`).
