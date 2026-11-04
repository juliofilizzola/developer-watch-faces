# Testes

## Processo

| Etapa | Ferramenta | Automático | O que garante |
|---|---|---|---|
| 1. Geração + checagem de layout | `generator/*_face.py` (`LayoutCheck`) | sim | nenhum texto ultrapassa a área circular segura (avisos listados no build) |
| 2. Validação de esquema | `wff-validator` (Kotlin, XSD 1.1 oficial do WFF v2) | sim | só elementos/atributos que existem no WFF v2, tipos corretos |
| 3. Validação semântica | `wff-validator` | sim | ≤ 20 configurações, defaults válidos, Flavors apontando para opções/slots reais, cores `[CONFIGURATION.x.n]` dentro do número de cores, fontes/drawables existentes, todo `displayName` com string |
| 4. Build | Gradle (AGP 9) | sim | APK debug + AAB release compilam |
| 5. Verificação de pacote | `scripts/verify_package.py` (aapt2) | sim | package id, minSdk 34, `hasCode=false`, propriedade WFF, feature de relógio, `watchface.xml` presente, sem dex |
| 6. Renderização real | `scripts/capture.py` no emulador Wear OS 5 | sim (precisa de emulador/relógio) | cada cenário é gerado com seus defaults, instalado, ativado e capturado (modo ativo e AOD) |
| 7. Inspeção visual | contact sheets das capturas | manual | legibilidade, margens, cores, AOD |
| 8. Validação física | Galaxy Watch 6 | manual | itens da seção "Pendências" |

Execução:

```bash
./build-all.sh
```

```bash
./build-all.sh screenshots
```

As capturas ficam em `reports/screens/<face>/<cenário>.png` (e `-aod.png`). Os cenários de cada face estão em
`<face>/generator/scenarios.py`.

## Ambiente usado

- Emulador Wear OS 5 (`system-images;android-34;android-wear;x86_64`, perfil `wearos_large_round`, 480×480,
  tela redonda), runtime `com.google.wear.watchface.runtime`.
- JDK 17.0.21 (Temurin), AGP 9.0.0, Gradle 9.2.1.

## Resultados (emulador)

| Teste | JSON | Code | Matrix | Evidência |
|---|---|---|---|---|
| Instalação e ativação | ✅ | ✅ | ✅ | todos os cenários |
| Inicialização (flavors registrados no sistema) | ✅ 4/4 | ✅ 7/7 | ✅ 5/5 | logcat `DefaultWFFlavorsMgr ... Success count` |
| Renderização dos 5 layouts | ✅ | ✅ | ✅ | `developer`, `clean_json`, `amoled`, `bars_full`, `full_json` / `go_dev`, `terminal`, `minimal_code`, `vscode_dark`, `full_stats` / `classic`, `minimal`, `amoled_green`, `cyan_full_bars`, `full_digital` |
| 24 horas | ✅ | ✅ | ✅ | `h24_seconds`, `js_24h_seconds`, `amber_24h_sec` |
| 12 horas + AM/PM / padrão do sistema | ✅ | ✅ | ✅ | `h12_ampm_iso`, presets (emulador em 12h) |
| Segundos | ✅ | ✅ | ✅ | idem 24h |
| Formatos de data | ✅ DD/MM/AAAA, ISO, completa, dia + data, dia da semana, DD MMM | ✅ ISO, dia + data | ✅ completa, dia + data | cenários de cobertura |
| Bateria: percentual / barra / anel / ícone / oculto | ✅ todos | ✅ todos | ✅ percentual, barra, anel, ícone | `battery_hidden`, `t_bat_hidden`, `bars_full`, `icons`, `full_*` |
| Passos: número / meta / barra / anel / ícone | ✅ | ✅ | ✅ | idem |
| Frequência cardíaca (valor, ícone, compacto) | ✅ sem leitura → `null` | ✅ → `--` | ✅ → `--` | emulador não fornece BPM |
| Clima | ✅ sem dados → `null` | ✅ → `nil` / `null` | ✅ → `NO SIGNAL` | emulador sem provedor de clima |
| Complicações ext1/ext2 | ✅ renderizam texto do provedor | ✅ | ✅ | layouts Full/Informative |
| Cores / paletas / fundos | ✅ | ✅ | ✅ (matiz × intensidade, brilho) | cenários de cobertura |
| Tamanhos do relógio S/M/L/XL | ✅ S, XL | ✅ L | ✅ L | `size_s`, `size_xl`, `minimal_code`, `minimal` |
| Alternância Go ↔ JavaScript | ➖ | ✅ | ➖ | `go_dev` × `js_dev` |
| Linha de status real (charging/low_power/running) | ✅ "charging" (emulador carregando) | ✅ | ✅ SYS | — |
| Presets (Flavors) | ✅ | ✅ | ✅ | cenários com o mesmo nome dos flavors |
| Always-On Display | ✅ | ✅ | ✅ | `*-aod.png` |
| Opções que não renderizam nada (oculto / FALSE) | ✅ | ✅ | ✅ | `status_off`, `battery_hidden`, `t_nolines` |
| Sem dados disponíveis | ✅ | ✅ | ✅ | passos 0, meta 0 (barra vazia), BPM e clima ausentes |
| Consumo: tamanho do XML / parse | 0,55 MB | 0,89 MB | 0,74 MB | parse ~0,3 s (JSON) no emulador; faces maiores levam alguns segundos para a primeira exibição |
| Memória do processo do runtime | ~200 MB PSS (emulador, todos os mostradores do sistema) | — | — | `dumpsys meminfo` — não representa o limite do Play |

## Pendências no Galaxy Watch 6 (não validáveis no emulador)

1. **Frequência cardíaca real** (`HEART_RATE`): valor, atualização e comportamento sem permissão.
2. **Clima real** (`WEATHER.*`): temperatura, condição, ícones de condição (Matrix) e conversão °C/°F.
3. **Calorias e distância**: escolher os provedores do Samsung Health (ou outro) em `ext1`/`ext2` e conferir o texto.
4. **Meta de passos** (`STEP_GOAL`) vinda do Samsung Health.
5. **Tempo de carregamento** do Code Developer (~0,9 MB) ao selecionar o mostrador e após reiniciar.
6. **Consumo de bateria** com segundos ligados × desligados e chuva Matrix em densidade alta (monitorar 24 h).
7. **AOD em hardware**: brilho, burn-in protection (deslocamento de pixels do sistema) e legibilidade ao sol.
8. **Editor do relógio e app Galaxy Wearable**: navegação pelas 19 configurações, rótulos pt-BR e lista de Flavors.
9. **Tamanho 40 mm (432×432)**: escala automática do canvas 480 e margens.
10. **Memory footprint oficial** (`google/watchface/play-validations`): o Play executa no upload; para rodar
    localmente, compile a ferramenta do repositório oficial e aponte para os AABs em `dist/`.
