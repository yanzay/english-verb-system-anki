# staging_img_cond_pass_rep.txt — Generation Report

## Summary
✓ **50 NEW Anki image-cue rows** created for English grammar — conditional/counterfactual, passive voice, and reported speech.

## File Details
- **Location**: `/Users/ograchov/projects/verbs/staging_img_cond_pass_rep.txt`
- **Format**: TSV with tab separator
- **Header**: 3 lines (#separator:tab, #html:true, #columns line)
- **Data Rows**: 50
- **Columns**: 6 (ImageQuery, Caption, Form, Function, Contrast, Tags)

## Validation Results

| Metric | Result | Status |
|--------|--------|--------|
| Total rows | 50 | ✓ |
| Columns per row | 6 (all uniform) | ✓ |
| Distinct ImageQuery values | 50/50 (100% unique) | ✓ |
| No overlap with existing 47 queries | Confirmed | ✓ |

## Category Breakdown

| Category | Rows | Distribution |
|----------|------|--------------|
| A. Conditional/Counterfactual | 15 | 30% |
| B. Passive Voice | 20 | 40% |
| C. Reported Speech/Indirect | 15 | 30% |
| **TOTAL** | **50** | **100%** |

### A. Conditional/Counterfactual (15 rows)
- **Forms**: Third Conditional, Mixed Conditional, "If Only" Conditional, Wish + Past Perfect
- **Imagery**: broken/spilled objects, empty chairs/rooms, missed moments, regret poses
- **Example**: "broken glass vase on floor" → "If I had been more careful, the glass vase wouldn't have broken."

### B. Passive Voice (20 rows)
- **Forms**: Present Perfect Passive, Present Continuous Passive, Past Simple Passive
- **Imagery**: finished/in-progress actions (painted walls, signed documents, repaired items, etc.), agent obscured or acknowledged
- **Example**: "broken window with glass shards" → "The window has been broken by the storm."

### C. Reported Speech/Indirect (15 rows)
- **Forms**: Reported Speech with tense backshift (present→past, will→would), Indirect Questions, Reported Thought
- **Imagery**: people on phones, in conversations, taking notes, interviewing, reading letters
- **Example**: "woman on phone looking serious" → "She said she was feeling tired after work."

## Tag Scheme Applied
All 50 rows include consistent tagging:
- **Module tags**: `image`, `module:image`, `card-type:image`
- **Category tags**: `conditional`, `passive`, `reported-speech`
- **Form-family tags**: `third-conditional`, `passive-present-perfect`, `passive-past-simple`, `present-continuous-passive`, `backshift`, `indirect-question`, `wish-past-perfect`, etc.
- **CEFR levels**: B1, B2 (appropriate for intermediate-advanced grammar)
- **Register**: `neutral` (or `formal` for news contexts)
- **Frequency**: `high`, `mid` (based on utility)
- **Domain**: `general`, `home`, `workplace`, `school`, `news`, `family`

## Key Features
1. **Photographable scenes**: All ImageQuery values describe real-world, observable situations (no proper nouns)
2. **Natural English**: Captions use authentic, idiomatic English sentences
3. **Clear contrasts**: Each Contrast column shows active voice, original tense, or alternative conditional form
4. **No overlap**: Verified against existing 47 rows (stative/dynamic, phrasal verbs)
5. **Distinct imagery**: Each scene targets a distinct linguistic pattern and real-world context

## File Location
```
/Users/ograchov/projects/verbs/staging_img_cond_pass_rep.txt
```

## Next Steps
- Integrate into main `conjugations_image.txt` or import directly into Anki
- Verify image URLs/queries if using external image generation
- Test in Anki desktop for HTML rendering and tag indexing
