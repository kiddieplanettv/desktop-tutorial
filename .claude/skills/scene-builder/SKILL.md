---
name: scene-builder
description: Disko sahnesini kurar: parlayan zemin karoları, spot ışıkları, dönen disko topu, parallax arka plan. Hepsi beat ve enerjiye tepki verir. Arka plan, ışık veya sahne geçişi üzerinde çalışırken kullan.
---

# Scene Builder

Katmanlar (`src/scene/`), arkadan öne: `Backdrop` → `FloorTiles` → `Spotlights` → karakterler → `DiscoBall` → `Captions`.

- **Backdrop:** Mor tonlarda, yavaş kayan (parallax) yuvarlatılmış hap şekilleri. Hız beat'ten bağımsız ve çok yavaş, göz yormasın.
- **FloorTiles:** Yuvarlak köşeli karo ızgarası. Her downbeat'te deterministik rastgele (`random('tile'+bar)`) 3-6 karo parlar ve 10-15 karede söner. Nakaratta (enerji > 0.6) parlayan karo sayısını iki katına çıkar.
- **Spotlights:** Her karakterin üstünde yarı saydam bir ışık konisi ve yerde elips bir ışık havuzu. Vuruşta opaklık hafifçe artar.
- **DiscoBall:** Yavaş döner (karo deseni yatay kayar), beat'te küçük bir parıltı (✦) çıkar.
- **Intro:** Karakterler sırayla zıplayarak girer (her biri `spring`, 8 kare arayla). Başlık metni ortada belirir.
- **Outro:** Karakterler el sallar, ışıklar söner, logo/abone ol kartı gelir. Son kare temiz kalmalı.

## Renk ve güvenlik
- Doygun ama yumuşak bir palet kullan. Tam ekran beyaz flaş ve saniyede 3'ten fazla yüksek kontrastlı yanıp sönme yapma (ışığa duyarlı epilepsi kuralı).
- Logo ve alt yazı alanını (alt %15) karakterlerden boş tut.
