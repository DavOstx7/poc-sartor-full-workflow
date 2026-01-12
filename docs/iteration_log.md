# Iteration Log - Phase 7

> **Date:** 2026-01-12
> **Test Run Parameters:** MAX_ICPS=1, LLM_RATE_LIMIT_RPM=4

---

## Baseline Test Results

| Test Case | Product | Copy Limit Issue | Font Issue | Logo Issue |
|-----------|---------|------------------|------------|------------|
| TC-01 | Electronics | ✅ Within limits | ⚠️ Default font | ⚠️ 404 error |
| TC-02 | Skincare | ❌ 161/125 (+29%) | ⚠️ Default font | ⚠️ 404 error |
| TC-03 | Fashion | ❌ 142/125 (+14%) | ⚠️ Default font | ⚠️ 404 error |

---

## Issue #1: Body Copy Exceeds Character Limits

**Root Cause:** Copy Agent prompt lacked explicit character counting guidance.

**Fix Applied:** Enhanced `agents/copy/prompts.py` Step 6 with:
- Explicit counting methodology (count every character including spaces)
- Concrete example showing character counting
- Clear SAFE/RISKY/FAIL thresholds
- Stronger emphasis on rewriting if over limit

**Files Modified:**
- [agents/copy/prompts.py](file:///C:/Users/DELL/Documents/poc-sartor-full-workflow/agents/copy/prompts.py)

---

## Issue #2: Missing Fonts Causing Tiny Text

**Root Cause:** `assets/fonts/` directory contained only README.md, no font files.

**Fix Applied:**
1. Downloaded DejaVu Sans font family (TTF files)
2. Updated `text_renderer.py` with fallback chain: DejaVu → Inter → System → Default

**Files Modified:**
- [src/composition/text_renderer.py](file:///C:/Users/DELL/Documents/poc-sartor-full-workflow/src/composition/text_renderer.py)

**Assets Added:**
- `assets/fonts/DejaVuSans.ttf`
- `assets/fonts/DejaVuSans-Bold.ttf`
- (+ additional DejaVu variants)

---

## Issue #3: Logo URLs Returning 404

**Root Cause:** Sample data uses placeholder `example.com` URLs.

**Fix Applied:**
1. Added detection for placeholder URLs (`example.com`, `placeholder`)
2. Implemented text-based fallback logo rendering
3. Brand name displayed as styled text when logo unavailable

**Files Modified:**
- [src/composition/compositor.py](file:///C:/Users/DELL/Documents/poc-sartor-full-workflow/src/composition/compositor.py)

---

## Validation Results

### Before (TC-01 baseline)
- Text nearly illegible (default bitmap font)
- No logo visible (404 warning logged)
- Body copy within limits (1/3 passed)

### After (TC-01 fix)
- Text clearly legible (DejaVu Sans loaded)
- Brand name "NovaTech Audio" displayed as text fallback
- No font warnings in logs
- Pipeline completed with 0 errors

---

## Remaining Considerations

1. **Real logos:** Update sample data with valid logo URLs or embed logo images
2. **Inter fonts:** Can download Inter font files for better typography if desired
3. **Copy limits:** Monitor future runs to confirm LLM respects stricter character limits
