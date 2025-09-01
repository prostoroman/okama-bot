## Compare/Portfolio Imports Fix Report

### Summary
Fixed NameError exceptions when handling `/compare` and portfolio creation flows:
- `name 'pd' is not defined`
- `name 'ok' is not defined`

### Root Cause
- `bot.py` used `pandas` (`pd`) utilities and `okama` (`ok`) symbols without importing them.
- `services/analysis_engine_enhanced.py` referenced `pd.DataFrame` without importing `pandas`.

### Changes
- Added imports to `bot.py`:
  - `import pandas as pd`
  - `import okama as ok`
- Added import to `services/analysis_engine_enhanced.py`:
  - `import pandas as pd`

### Files Updated
- `bot.py`
- `services/analysis_engine_enhanced.py`

### Impact
- `/compare` and portfolio-related commands no longer fail with NameError for `pd` or `ok`.
- No behavioral changes beyond resolving the exceptions.

### Validation
- Grepped the codebase for `pd.` and `ok.` usages to ensure corresponding imports are present.
- Confirmed `services/*` already import `okama` where needed.

### Follow-ups
- None required.

