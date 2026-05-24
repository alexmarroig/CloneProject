# Psychology Instagram Reels Content Design
**Date:** 2026-03-18
**Project:** Generate psychology-focused Instagram Reels content with voice cloning
**Status:** Design Approved

---

## Overview

Create a short (40-45 second) Instagram Reels video about healthy relationship boundaries, specifically designed to deconstruct the myth that "establishing limits means you don't love."

The content will be delivered in Portuguese (pt-BR) with audio generated using XTTS text-to-speech and converted to the user's wife's voice using the trained RVC model `api_probe4`.

---

## Content Strategy

**Theme:** Relationships - Healthy Boundaries
**Tone:** Direct and provocative
**Objective:** Deconstruct the myth that limit-setting equals selfishness/lack of love
**Target Audience:** People in relationships, particularly those struggling with boundary-setting

---

## Video Structure

### Duration: 40 seconds

**Moment 1: Provocative Opening (0-10s)**
- Question the limiting belief directly
- Hook: "Você acha que cuidar de você mesma é egoísmo?"

**Moment 2: Core Content - Education (10-30s)**
- Distinguish between healthy limits (protection) vs toxic behavior (punishment)
- Define what a healthy boundary actually is
- Provide reassurance that self-care is not selfishness

**Moment 3: Closing Reflection (30-40s)**
- Strong call to reflection
- Reframe the belief about love and self-care
- Final impact statement

---

## Script Content

```
"Você acha que cuidar de você mesma é egoísmo?

Escuta só: limite não é punição. Limite é proteção.

Quando você estabelece um limite, você não está machucando ninguém.
Você está dizendo 'isso não é aceitável para mim'.

Não confunda estabelecer limite com vingança ou frieza.
Limite saudável é amar a si mesma primeiro.

Se você só é feliz quando desaparece pelo outro, o problema não é você.
É a crença errada que te ensinaram sobre amor.

Amar alguém não significa aceitar tudo. Significa respeitar a si mesma."
```

**Characteristics:**
- Conversational tone suitable for audio delivery
- Direct, provocative language matching user intent
- Educational content embedded within emotional appeal
- ~45 seconds in natural speech pace
- Portuguese (pt-BR)

---

## Technical Execution

### Audio Generation Pipeline

1. **Text-to-Speech Generation (XTTS)**
   - Service: Running on port 8001
   - Model: xtts_v2
   - Device: CPU
   - Input: Portuguese script above
   - Output: Neutral speech WAV file

2. **Voice Conversion (RVC)**
   - Service: FastAPI backend on port 3000
   - Model: `api_probe4` (trained on wife's voice)
   - Input: Generated XTTS audio
   - Process: Voice conversion to apply wife's voice characteristics
   - Output: Final audio file with wife's voice

### File Locations
- **Model:** `app/models/voices/api_probe4/model.pth`
- **Index:** `app/models/voices/api_probe4/model.index`
- **Output:** Generated audio file (WAV format)

---

## Success Criteria

✅ Audio generated successfully with XTTS
✅ Voice conversion applied using api_probe4 model
✅ Output file contains intelligible speech in wife's voice
✅ Audio duration approximately 40-45 seconds
✅ Clear, professional audio quality suitable for Instagram Reels

---

## Implementation Next Steps

1. Generate speech from Portuguese script via XTTS
2. Convert generated audio to wife's voice using RVC model
3. Export final audio file
4. Ready for Instagram Reels video creation

