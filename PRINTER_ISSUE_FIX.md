# Printer Issue Fix - Device Image Endpoint

## Problem
When calling `/device/<device_id>/image-raw`, the ESP32 receives the image data but the printer doesn't print. However, `/genai-image-raw/0?wrap=1` works fine.

## Root Cause
The difference is in the **printer command wrapping**:

- `/genai-image-raw/0?wrap=1` - The `?wrap=1` parameter wraps the raw image data with printer initialization commands
- `/device/<device_id>/image-raw` - Returns ONLY the raw image data without printer commands by default

## The Fix
Add `?wrap=1` to your device endpoint call:

### Before (Not Working)
```bash
curl --location 'https://tanmaymaloo.pythonanywhere.com/device/<device_id>/image-raw'
```

### After (Working)
```bash
curl --location 'https://tanmaymaloo.pythonanywhere.com/device/<device_id>/image-raw?wrap=1'
```

## What Does `wrap=1` Do?
When `wrap=1` is added, the endpoint wraps the raw image bytes with printer initialization commands:

1. `CMD_GET_DEV_STATE` - Get device state
2. `CMD_SET_QUALITY_200_DPI` - Set print quality to 200 DPI
3. `cmd_set_energy(energy)` - Set energy level (default 0xffff)
4. `cmd_apply_energy()` - Apply energy settings
5. `CMD_LATTICE_START` - Start lattice mode
6. Image row data (encoded)
7. `cmd_feed_paper(25)` - Feed paper
8. `CMD_SET_PAPER` (3x) - Set paper settings
9. `CMD_LATTICE_END` - End lattice mode
10. `CMD_GET_DEV_STATE` - Get final device state

Without these commands, the printer receives raw data but doesn't know what to do with it.

## Additional Parameters
Both endpoints support the same query parameters:

- `wrap=1` - Wrap with printer commands (REQUIRED for printing)
- `invert=1` - Invert bits (default is 1, set to 0 to disable)
  - `invert=1` (default): Black becomes white, white becomes black
  - `invert=0`: Normal colors (use this if image appears dark with white lines)
- `energy=0xffff` - Set printer energy level (default is 0xffff)

### Example with all parameters:
```bash
curl --location 'https://tanmaymaloo.pythonanywhere.com/device/<device_id>/image-raw?wrap=1&energy=0xffff&invert=0'
```

### Common Issue: Dark Image with White Lines
If your printed image appears mostly dark with white lines instead of white with black lines, use `invert=0`:
```bash
curl --location 'https://tanmaymaloo.pythonanywhere.com/device/<device_id>/image-raw?wrap=1&invert=0'
```

## Why Both Endpoints Exist
- `/genai-image-raw/<invert>` - Serves the most recent generated image (global)
- `/device/<device_id>/image-raw` - Serves device-specific images (per device)

Both use the same underlying data format and support the same parameters.

## Verification
To verify the fix is working:

1. Check the response headers:
   - `X-Printer-Wrapped: 1` should be present when `wrap=1` is used
   - `X-Device-ID: <device_id>` confirms the device

2. Check the response size:
   - Without wrap: ~43KB (raw image data only)
   - With wrap: ~44KB (includes printer commands)

## Code Reference
The wrapping logic is in `api/views.py`:
- Function: `wrap_raw_bytes_with_print_commands()`
- Used by both: `get_genai_image_raw()` and `get_device_image_raw()`
