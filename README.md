# Dans Eden Hayvanlar: Çocuk Şarkısı Videosu

Şarkıya senkron, dans eden hayvan figürlü video üretim hattı (Remotion + ses analizi).
Video süresi şarkının süresinden otomatik hesaplanır: intro + ölçülere hizalı dans blokları + outro.

## Kurulum
```bash
bash scripts/setup.sh
```

## Akış
```bash
# 1) Şarkıyı public/audio/ altına koy
.venv/bin/python scripts/analyze_audio.py public/audio/song.wav        # -> public/data/beats.json
.venv/bin/python scripts/plan_timeline.py public/data/beats.json       # -> public/data/timeline.json
.venv/bin/python scripts/lyrics_sync.py public/audio/song.wav --separate --lang en   # -> captions.json
# 2) Önizleme / render
npm run studio
npm run render
```
`src/Root.tsx` içindeki `defaultProps.audio` değerini kendi şarkı dosyanla değiştir. `public/audio/sample.mp3` sentetik bir test parçasıdır.

## Kullanılan repolar
| Repo | Kullanım |
|---|---|
| remotion-dev/remotion | Video motoru (`remotion`, `@remotion/*`) |
| FFmpeg/FFmpeg | Kodlama, loudnorm |
| CPJKU/madmom | Beat ve downbeat tespiti |
| librosa/librosa | Enerji ve bölüm analizi |
| rive-app/rive-react | Kemikli karakter animasyonu (`@rive-app/react-canvas`) |
| m-bain/whisperX | Söz zamanlaması |
| facebookresearch/demucs | Vokal ve davul ayırma |
| airbnb/lottie-web | Lottie efektleri (`@remotion/lottie`) |
| EsotericSoftware/spine-runtimes | Spine karakterleri (`@esotericsoftware/spine-webgl`) |
| facebookresearch/AnimatedDrawings | Çizimden animasyon, yedek seçenek (`vendor/`, git dışı) |

## Skill'ler (`.claude/skills/`)
Projeye özel: `audio-analyzer`, `timeline-planner`, `character-rig`, `dance-moves-library`, `lyrics-sync`,
`scene-builder`, `render-pipeline`, `visual-qa`, `thumbnail-and-metadata`.
Resmi Remotion skill'leri (remotion-dev/skills): `remotion-best-practices`, `remotion-markup`, `remotion-captions`,
`remotion-render`, `remotion-studio`, `remotion-create`, `remotion-multimedia`, `remotion-docs`.
