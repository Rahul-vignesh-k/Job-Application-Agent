# Simulations are not applications

The current application adapter does not implement a real submission. It returns:

```json
{
  "success": false,
  "submission_status": "not_submitted",
  "simulated": true,
  "confirmation": null,
  "screenshot": null
}
```

The specialist `ApplicationAgent` and legacy `JobAgent` check the adapter's explicit submission capability before collecting form data or creating an application. The placeholder logs `application_not_submitted`, preserves the existing job status, and creates no application record. A real adapter must be implemented and reviewed before enabling its `supports_submission` capability. A page visit or screenshot is not proof of submission.

This patch does not repair or delete historical records. Existing entries with a `stub_confirm_` confirmation came from the old simulation and must not be counted as real submissions without external evidence.

## Focused verification

```text
python -m unittest discover -s tests -v
```

Four tests cover the placeholder, both orchestration paths and an adapter with no declared submission capability. The test harness loads real project methods and Pydantic schemas while substituting optional external imports and persistence functions. No Playwright browser, external API, production database, candidate data or real application is used. These checks are focused regression coverage, not a full integration suite.

Validated locally on 8 September 2026: four tests passed; `git diff --check` passed. The change is proposed for review; it has not been merged or deployed.
