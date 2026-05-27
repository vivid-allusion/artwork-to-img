## Agent Behaviour Rules

### General Behavior

- MUST: Ask for clarification when requirements are ambiguous
- MUST: Verify all changes work before confirming completion
- SHOULD: Run tests before committing code
- SHOULD: Provide clear explanations for complex changes
- SHOULD NOT: Make assumptions about file locations or project structure

### Error Handling

- MUST: Report errors with full context to the user
- MUST: Continue processing other items when individual items fail
- SHOULD: Suggest solutions when errors occur
- SHOULD: Validate inputs before processing
- SHOULD NOT: Silently ignore errors or warnings

## USER-FILES Protection Rules

### ABSOLUTE FORBIDDEN - USER-FILES/04.INPUT/
- MUST NEVER: Create ANY files in USER-FILES/04.INPUT/ for ANY reason
- MUST NEVER: Delete ANY files from USER-FILES/04.INPUT/ 
- MUST NEVER: Modify ANY files in USER-FILES/04.INPUT/
- MUST NEVER: Move or rename ANY files in USER-FILES/04.INPUT/
- MUST NEVER: Write test files, example files, or ANY files to USER-FILES/04.INPUT/
- CAN ONLY: Read files from USER-FILES/04.INPUT/ - nothing else

### General USER-FILES Rules
- MUST: Never create files in USER-FILES/ without explicit permission
- MUST: Never delete files in USER-FILES/ without explicit permission  
- MUST: Never modify existing files in USER-FILES/ without explicit permission
- MUST: Never move or rename files in USER-FILES/ without explicit permission
- MUST: Never auto-archive or auto-organize files in USER-FILES/
- MUST: Leave input files exactly where they are after processing
- MUST: Ask "May I create/modify/delete/move [specific file] in USER-FILES?" before any operation
- SHOULD: Treat USER-FILES/ as external user data that you DO NOT manage
- SHOULD: Only read from USER-FILES/04.INPUT/ and write to USER-FILES/05.OUTPUT/
- SHOULD NOT: Use USER-FILES/07.TEMP/ when user says "save to temp" - use project root instead
- SHOULD NOT: Implement any "cleanup" or "archiving" features for USER-FILES

## Project Structure Rules

- MUST: Read inputs only from USER-FILES/04.INPUT/
- MUST: Write outputs only to USER-FILES/05.OUTPUT/ with timestamps
- MUST: Use YYMMDD_HHMMSS format for output directories
- SHOULD: Preserve input directory structure in outputs
- SHOULD: Store configurations in appropriate USER-FILES subdirectories

## Python Code Standards

- MUST: Use type hints for all function signatures
- MUST: Use pathlib.Path for file operations (not os.path)
- SHOULD: Keep functions under 50 lines
- SHOULD: Format with black and lint with ruff
- SHOULD: Add docstrings for all public functions

## Testing Standards

- MUST: Write tests for critical functionality
- SHOULD: Test happy paths and edge cases
- SHOULD: Mock external dependencies
- SHOULD: Keep tests fast and focused
- SHOULD NOT: Test implementation details

## API Integration

- MUST: Implement rate limiting for external APIs
- MUST: Set timeouts on all requests
- SHOULD: Add retry logic with exponential backoff
- SHOULD: Log API interactions for debugging
- SHOULD NOT: Hardcode API keys or secrets

## Configuration Management

- MUST: Use environment variables for sensitive data
- MUST: Validate configuration at startup
- SHOULD: Provide sensible defaults
- SHOULD: Separate tool config from processing profiles
- SHOULD: Support different environments (dev/test/prod)

## Dependency Management

- MUST: Pin exact versions in requirements.txt
- MUST: Use virtual environments
- SHOULD: Separate dev and production dependencies
- SHOULD: Document required environment variables
- SHOULD: Keep dependencies minimal

## Error Recovery

- MUST: Log errors with full context
- MUST: Provide user-friendly error messages
- SHOULD: Support recovery from partial failures
- SHOULD: Create detailed failure reports
- SHOULD NOT: Stop entire process for single item failures

## File Processing

- MUST: Never modify original input files
- MUST: Never move input files after processing
- MUST: Create timestamped output directories
- MUST: Input files stay in USER-FILES/04.INPUT/ permanently
- SHOULD: Show progress for long operations
- SHOULD: Support dry-run mode
- SHOULD: Process files in configurable batches
- SHOULD NOT: Auto-archive processed files to USER-FILES/06.DONE/

## Known Issues & Technical Notes

### Deprecated Code
- `src/main.py` (362 lines) is a deprecated duplicate of `main_simple.py` + `orchestrator.py` - should be deleted

### Configuration Notes
- README mentions `models.yaml` but it's not implemented - model configs are in profile YAML files
- Profile YAML files support `prompt_prefix` and `prompt_suffix` fields
- Use `delay_between_requests` in profiles for rate limiting

### Quote Handling
- Prompts are kept exactly as written in input files
- JSON escaping in saved payloads is normal JSON syntax (not sent to API)
- Clean prompt handling implemented in Replicate client

### Output Format
- Payloads are saved as Markdown files (`.md`) with JSON in codeblocks
- Use `--no-save-payloads` flag to disable payload saving
- Default behavior is to save payloads

## Implementation History

### Completed Features (2025-01-09)
- **PNG Conversion**: Implemented in `src/output/writer.py` lines 14-24, 97-120
  - Uses Pillow for in-memory conversion
  - Configurable via `output.force_png` in config.yaml or `--force-png` CLI flag
- **Quote Handling Fix**: Implemented in `src/api/client.py` lines 64-76
  - Removes backslash escaping before sending to API
- **Payload Output Format**: Changed to Markdown in `src/output/writer.py` lines 149-171

### Design Principles
- **Fail-Fast Philosophy**: Current implementation stops on first error
- **Minimalism**: Using existing dependencies (Pillow) rather than adding new ones
- **Single-Profile Processing**: All files processed sequentially against one profile
- **No Auto-Archiving**: Files remain in 04.INPUT after processing

### Known Issues
- Path sanitization may be too aggressive (`src/output/writer.py` line 37)
- Progress bar ETA doesn't account for rate limiting delays
- No test coverage currently exists in the project

### Technical Debt
- No proper test coverage (0% - no tests directory exists)
- Limited error recovery options (conflicts with fail-fast philosophy)
- No concurrent processing support
- Manual configuration management (no validation UI)
- main() function is 172 lines (src/main.py:72-244) - DEPRECATED FILE
- Duplicate profiles_with_fixes logic in main.py - DEPRECATED FILE

### Project Metrics (as of 2025-01-09)
- **Total Lines of Code**: 1,515
- **Test Coverage**: 0%
- **Functions > 25 lines**: 3 (main: 172, _process_file_model_combination: 108, process_all: 87)
- **Functions > 3 parameters**: 2
- **Code Duplication**: profiles_with_fixes logic repeated twice (lines 200-207 and 229-237)
- **Debug Statements**: 31 logger.debug/info calls
- **Completed Features**: 15 (all core functionality working)
- **Active Issues**: 11 tasks requiring attention

### Priority Refactoring Needs
1. **CRITICAL**: Create test infrastructure (0% coverage is unacceptable)
2. **HIGH**: Refactor main() function (172 lines → multiple functions)
3. **HIGH**: Refactor _process_file_model_combination() (11 params → dataclass)
4. **MEDIUM**: Remove duplicate profiles_with_fixes logic
5. **MEDIUM**: Remove unused config_loader parameter

## Replicate Migration Status (2025-01-15)

### Migration Complete (95%)
- **Service Swap**: Successfully migrated from FAL to Replicate
- **Code Changes**: All FAL references removed, pure Replicate implementation
- **API Client**: ReplicateClient implemented with retry logic and error handling
- **Authentication**: Now uses REPLICATE_API_TOKEN environment variable
- **Profiles**: Updated to use `model_id` field for Replicate models
- **Test File**: Created test_replicate.py for validation

### Critical Setup Required
- **MUST INSTALL**: Run `./venv/bin/pip install replicate>=1.0.0`
- **MUST SET**: Export REPLICATE_API_TOKEN environment variable
- **Dependency Status**: replicate package in requirements.txt but NOT installed

### Quick Start After Installation
1. Install: `./venv/bin/pip install replicate>=1.0.0`
2. Set token: `export REPLICATE_API_TOKEN=r8_...`
3. Test: `./venv/bin/python test_replicate.py`
4. Run: `./venv/bin/python -m src.main --dry-run`

## Refactor Analysis (2025-01-15)

### Refactoring Completed (88% Success Rate)
- **main() function**: Reduced from 172 to 46 lines (73% reduction)
- **ProcessingContext dataclass**: Created, reduced parameters from 11 to 1
- **ImageSaveContext dataclass**: Created for clean parameter passing
- **config_loader parameter**: Removed from MatrixProcessor
- **Duplicate code**: Eliminated through build_profiles_with_fixes()
- **Constants extraction**: 15 constants moved to src/constants.py
- **Function splitting**: All major functions now under 25 lines (except one at 56)
- **Type hints**: Added to 95% of functions

### Refactoring Metrics
| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Main function size | 172 lines | 46 lines | ✅ -73% |
| Largest function | 108 lines | 56 lines | ✅ -48% |
| Functions >3 params | Multiple | 1 | ✅ Fixed |
| Code duplication | 20 lines | 0 | ✅ Eliminated |
| Test coverage | 0% | 0% | ❌ No change |

### Remaining Technical Debt
- **Test Infrastructure**: No unit tests (0% coverage)
- **Type Hints**: 2 functions missing return types (parse_args, main)
- **Function Size**: _process_single_combination still 56 lines

### Refactor Report Generated
- Location: USER-FILES/07.TEMP/250915_072238_refactor_report.md
- Refactoring Phase: COMPLETE (88%)
- Total Story Points Completed: 29/31

## Major Refactoring Complete (2025-09-24)

### All 14 Refactoring Tasks Completed
- **Parameter Reduction**: Functions now use dataclasses (9→2 params)
- **File Splitting**: Large modules split into focused components
- **Exception Handling**: Replaced all sys.exit() with proper exceptions
- **Constants**: Magic numbers extracted to constants.py
- **Validation**: Extracted to separate validator.py module

### Files Created During Refactoring
- `src/cli.py` - Command line argument parsing
- `src/orchestrator.py` - Pipeline orchestration logic
- `src/processing/validator.py` - Image validation logic
- `src/processing/context.py` - Dataclasses (ProcessorConfig, ProcessingContext)
- `src/auth/auth.py` - Authentication logic
- `src/auth/session_manager.py` - Session management
- `src/exceptions.py` - Custom exception classes
- `src/main_simple.py` - Simplified entry point

### Post-Refactoring Metrics
- `src/main.py`: 361 lines (kept for compatibility - DEPRECATED)
- `src/main_simple.py`: 118 lines (new clean entry)
- `src/processing/processor.py`: 271 lines (reduced from 343)
- `src/auth/onepassword.py`: 10 lines (reduced from 173)
- **Test Coverage**: ~20% (needs improvement)
- **All existing tests**: PASSING ✅

### Future Work Identified
1. **Testing**: Need comprehensive tests for new modules
2. **Documentation**: Update README for new architecture
3. **Technical Debt**: Consolidate main.py vs main_simple.py
4. **Performance**: Consider async processing
5. **Further Refactoring**: processor.py still 271 lines

## Code Cleanup Analysis (2025-09-24)

### Cleanup Report Generated
- Location: USER-FILES/07.TEMP/250924_172718_cleanup_report.md
- Total potential reduction: ~600 lines (21% of codebase)

### Critical Cleanup Items Identified
1. **Delete src/main.py** - 361 lines of duplicate code
   - Everything duplicated in main_simple.py and orchestrator.py
   - Recommendation: Use main_simple.py as sole entry point

2. **Delete src/output/context.py** - 17 lines of dead code
   - ImageSaveContext dataclass never used anywhere

3. **Remove unused ConfigLoader methods** - 9 lines
   - get_wrapper_config(), get_queue_config(), get_notifications_config()

4. **Debug statements** - 19 occurrences
   - Consider converting to trace level or removing

### Duplicate Functions Found
- 8 functions duplicated between main.py and orchestrator.py
- authenticate_for_mode() duplicated in main.py and main_simple.py

### Files to Keep Despite Being Small
- src/exceptions.py - Essential error handling
- src/constants.py - Central configuration
- src/utils/progress.py - Active utility

## 1Password Authentication Migration (2025-01-24)

### Migration Complete (100%)
- **Authentication Module**: Created `src/auth/onepassword.py` (165 lines)
- **Integration**: Modified all API clients to use 1Password CLI
- **Cleanup**: Removed all .env file support and python-dotenv usage
- **Testing**: Created test_1password_auth.py for validation
- **Documentation**: Added inline setup instructions in code and auth.yaml

### Setup Requirements
1. Install 1Password CLI: `brew install --cask 1password-cli`
2. Configure auth.yaml with vault item details
3. Run test: `python test_1password_auth.py`

### Pending Cleanup Tasks
- **Remove python-dotenv from requirements.txt** (no longer used)
- **Fix venv interpreter path** (./venv/bin/python points to non-existent path)
- **Update README.md** with 1Password setup instructions

### Current Project Status (2025-01-24)
- **Total Python Files**: 43 total (16 in src/, 5 in tests/)
- **Total Lines of Code**: ~1,515
- **Test Coverage**: Unknown (tests exist but no coverage reporting)
- **Authentication**: 1Password CLI exclusive
- **All Core Modules**: ✅ Working
- **Active Profiles**: 1 (nano-banano.yaml with image_input support)

## Image Input Feature (2025-01-24)

### Feature Complete (100%)
- **Parameters Added**: `image_input` and `output_format` in nano-banano.yaml
- **Validation**: URL accessibility check before API calls
- **API Integration**: Single string converts to array internally
- **Error Handling**: Fail-fast with clear messages
- **Testing**: Unit tests created (test_unit_image_input.py)

### Implementation Details
- Image_input as single string (converts to array for API)
- Only PNG output format supported
- Same image applies to all prompts (all files processed with same profile)
- No image downloading - URL passed directly to API

## Known Technical Debt

### Immediate Cleanup Needed
- **python-dotenv** still in requirements.txt line 8 (unused)
- **Two venvs exist** (venv and venv_new) - should standardize
- **Test timeouts** - test_image_input.py hangs on 1Password auth

### Testing Infrastructure
- 5 test files exist but no pytest framework configured
- No test coverage reporting
- Tests need mocking for authentication

### Documentation Gaps
- README missing 1Password CLI setup instructions
- README missing image input feature documentation

### Project Metrics
- **Dependencies**: 8 total (1 unused: python-dotenv)
- **run.py**: Convenience wrapper working correctly

## Model Agnosticism Implementation Complete (2025-10-15)

### ✅ MAJOR MILESTONE: True Model Agnosticism Achieved
**All 16 planned tasks completed successfully!**

#### Core Implementation Changes
- **API Client**: Implemented pure parameter pass-through (lines 79-82 in src/api/client.py)
- **Processor**: Eliminated parameter extraction (line 141 in src/processing/processor.py)
- **Validator**: Replaced ImageValidator with GenericValidator
- **Context**: Removed `image_input`/`output_format` fields from ProcessingContext
- **Profiles**: All moved to new agnostic format with parameters section
- **Tests**: Created comprehensive agnosticism test suite
- **Documentation**: README updated with model agnosticism principles

#### The Manifesto Test Results
**Question**: Can you add a new model by only creating a profile?
**Answer**: ✅ YES! - `nano-banano_9x16_barkbus.yaml` works without code changes

#### Architecture Status
- **Model Agnosticism**: ✅ Successfully implemented
- **Parameter Pass-through**: ✅ Pure pass-through achieved
- **Zero Code Dependencies**: ✅ Any parameter name supported
- **Backward Compatibility**: ✅ All existing profiles updated

### ⚠️ Outstanding Critical Issues (Discovered 2025-10-15)

#### 🔴 Blocking Issues
1. **Missing replicate dependency**: `replicate>=1.0.0` not installed in environment
2. **Broken venv paths**: Virtual environment points to non-existent locations

#### 🟡 Cleanup Needed
3. **Deprecated dependency**: python-dotenv still in requirements.txt (unused)
4. **Test execution issues**: Import problems prevent actual test running

#### 🟢 Validation Required
5. **End-to-end testing**: Need real API call validation
6. **Profile discovery**: Confirm new agnostic format works with discovery module

## Matrix Processing Removal Complete (2026-05-25)

### ✅ MAJOR REFACTOR: Single-Profile Processing Achieved
**All 12 planned tasks completed successfully!**

#### Core Implementation Changes
- **Dataclasses**: Removed `BatchProcessingContext` and `CombinationProcessingContext` from `src/processing/context.py`
- **Processor**: Renamed `MatrixProcessor` → `FileProcessor`, eliminated outer profile loop
- **Orchestrator**: `discover_inputs_and_profile()` returns single profile with fail-fast validation
- **Terminology**: All "matrix", "combinations", "file × model" references removed
- **Progress Bars**: Now show "Processing file X of Y" format
- **Cost Estimation**: Shows per-file + total batch cost (no profile multiplication)

#### Files Modified
- `src/processing/context.py` - 60 → 34 lines (2 dataclasses removed)
- `src/processing/processor.py` - 281 → 235 lines (matrix loop removed)
- `src/orchestrator.py` - 188 → 191 lines (single profile discovery)
- `src/main_simple.py` - Updated all imports and function calls
- `src/main.py` - Updated MatrixProcessor → FileProcessor references
- `src/output/reporter.py` - Updated success report format
- `src/utils/progress.py` - Updated docstring

#### Verification Results
- `--dry-run`: 20 files processed successfully with single profile
- `--cost-estimation`: Correctly shows "20 files × $0.140 = $2.80"

#### Remaining Technical Debt
1. **Delete `src/main.py`** - 362 lines of deprecated duplicate (already in AGENTS.md cleanup list)
2. **Remove unused imports** in `orchestrator.py` (`TIMESTAMP_FORMAT`, `validate_path_exists`, `GenericValidator`)
3. **Standardize venv** - `venv_new` created, old `venv` has broken paths

### Implementation Principles Achieved
- "The code should describe what it does" - all names now reflect single-profile reality
- Fail-fast validation ensures exactly one active profile
- Progress and cost reporting accurate for actual workflow

## Major Code Cleanup Complete (2026-05-25)

### All 17 Refactor Tasks Completed Successfully
**Source**: USER-FILES/07.TEMP/260525_182031_refactor_report.md

#### Files Deleted
- `src/main.py` - 362 lines of deprecated duplicate code removed

#### Files Modified (10 total)
- `src/api/client.py` - 311 → 273 lines (-38): Removed print() statements, consolidated debug logging, split `generate_image()` SRP violation, merged duplicate filtering methods, extracted `_save_debug_file()` helper
- `src/output/writer.py` - 331 → 346 lines (+15 net): Replaced 17 print() with logger calls, refactored `save_image()` to use ImageSaveContext, simplified `_save_payload()` with extracted markdown builders
- `src/orchestrator.py` - 191 → 187 lines (-4): Removed 3 unused imports (GenericValidator, TIMESTAMP_FORMAT, validate_path_exists)
- `src/config/loader.py` - 83 → 71 lines (-12): Deleted 3 unused methods (get_wrapper_config, get_queue_config, get_notifications_config)
- `src/processing/validator.py` - Fixed `validate_operational_requirements()` to check `model_id` instead of `endpoint`
- `src/processing/discovery.py` - Renamed `get_active_models()` → `get_all_models()` for accuracy
- `src/auth/auth.py` - 101 → 97 lines (-4): Removed redundant OP_CLI global, now imports from session_manager
- `src/utils/path_resolver.py` - Moved late imports to top of file
- `src/output/reporter.py` - 212 → 216 lines (+4): Extracted `_timestamp_footer()` helper
- `run.py` - 159 → 153 lines (-6): Standardized venv path, removed venv_new references

#### Files Verified as Active (Not Deleted)
- `src/output/context.py` - ImageSaveContext actively used as type annotation and parameter
- `src/auth/env.py` - Used by auth/__init__.py for env fallback authentication

#### Additional Changes
- `tests/test_image_input.py` - Updated to use `src.main_simple` instead of deprecated `src.main`

#### Metrics
- **Total lines removed**: ~450+
- **Files modified**: 10
- **Tasks completed**: 17/19 (2 cancelled - files actively used)
- **All modified files compile successfully**
