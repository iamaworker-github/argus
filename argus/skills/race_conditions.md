---
name: race_conditions
description: TOCTOU, parallel request attacks, concurrency exploits
category: vulnerabilities
---

# Race Condition Testing

## Attack Surface
Race conditions occur when the timing of operations affects security guarantees.
- Coupon/redemption systems
- Balance transfers and financial operations
- Account creation (username squatting)
- File upload/processing pipelines
- Rate limit resets
- Like/vote/follow actions

## Methodology
1. **Detection**
   - Send N parallel identical requests simultaneously
   - Use HTTP pipelining or async IO for concurrent requests
   - Target: money transfers, coupon redemptions, inventory deductions

2. **TOCTOU Pattern**
   - Identify check-then-act patterns
   - Send verification request followed immediately by action
   - Exploit window between permission check and resource operation

3. **Exploitation Tools**
   - Python asyncio: gather() with many concurrent tasks
   - Burp Suite Turbo Intruder
   - Custom race condition scripts

## Validation
- Coupon applied N times instead of once
- Balance increased by more than expected amount
- Multiple accounts created with same username
- File uploaded before virus scan completes
- Race condition reliably reproducible >50% of attempts
