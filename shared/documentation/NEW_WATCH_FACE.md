# Criar uma nova watch face na coleção

1. Copie um módulo existente (ex.: `json-developer/`) para `<nome>-developer/`, apague `build/` e `src/main/res/raw`.
2. Em `<nome>-developer/build.gradle.kts`, troque `namespace` e `applicationId` (`dev.devtime.watchface.<nome>`).
3. Inclua o módulo em `settings.gradle.kts` e registre-o em `build-all.sh` (`MODULE`, `GENERATOR`, `PACKAGE`)
   e em `scripts/capture.py` (`FACES`).
4. Escreva `generator/<nome>_face.py` usando `wffgen.core`:
   - `user_configurations()` com no máximo 19 configurações + `Flavors` (limite de 20 do WFF v2);
   - cena com `group("active", …, variants=[ambient_hide()])` e um grupo `ambient` próprio;
   - `time_tree()` / `date_tree()` / `temperature()` / `text_bar()` / `arc_ring()` / `complication_slot()`.
5. Escreva `generator/scenarios.py` (cenários de teste e screenshots) incluindo `default`.
6. `./build-all.sh <nome>` até o validador passar; depois `./build-all.sh screenshots <nome>`.
7. Copie `reports/screens/<módulo>/default.png` para `res/drawable/preview.png`; rode `./build-all.sh assets`.
8. Crie `store-assets/<módulo>/listing.md` e adicione a face às tabelas em `docs/`.

Regras: não use atributos fora do XSD v2 (o validador barra), nunca exiba dados fictícios, mantenha o XML
abaixo de ~1 MB (cada configuração multiplica sub-árvores — prefira camadas independentes, cores por configuração
e máscaras) e valide no emulador cada combinação nova.
