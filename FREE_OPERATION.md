> **Implementation status — natural speech update:** Real Kokoro ONNX English
> preset speech is now available after explicit installation. Edge is optional
> and requires online permission. Paid/system/mock engines are not registered
> for normal generation. The legacy cloning tone generator is disabled; real
> cloning remains a future goal. Unsupported acting controls are disabled.
> See START_HERE.md for setup and current limitations; aspirational sections
> below are not claims that every planned feature is implemented.

# Free Operation Policy

## Absolute requirement

The application must have a normal operating cost of:

```txt
$0
```

Internet use is allowed.

Paying is not.

---

# Allowed

The application may use:

- free/open local models
- free open-source software
- locally downloaded model weights
- free model repositories
- genuinely free online services
- free online inference when it cannot create charges
- local CPU/GPU processing

---

# Forbidden as required dependencies

Do not require:

- paid APIs
- subscriptions
- credit purchases
- pay-per-character TTS
- paid voice cloning
- metered cloud compute that can charge money
- cloud storage fees
- payment methods
- billing accounts

---

# Local fallback

There must always be a free local path for core generation.

The application should still work if:

- Wi-Fi is off
- a free online service disappears
- a free quota is exhausted
- an online provider changes terms
- the provider is temporarily unavailable

---

# Online-free rule

An online integration may be added only after checking its current cost model.

At integration time, verify:

1. Does normal use cost money?
2. Can it automatically become paid?
3. Is a credit card required?
4. Is billing enrollment required?
5. Is the free allowance temporary?
6. Can the app stop safely before any charge?
7. What data is uploaded?
8. Can local generation replace it?

If there is any realistic risk of automatic charging, do not use it.

---

# Never auto-upgrade to paid

Forbidden:

```txt
free quota exhausted
→ continue as paid
```

Required behavior:

```txt
free quota exhausted
→ stop using online engine
→ use local engine or show message
```

---

# No hidden spending

The app must not contain:

- auto-purchase credits
- auto-upgrade subscription
- paid fallback
- background chargeable requests

A generation action must never unexpectedly create a monetary charge.

---

# Online privacy

If an online free engine is used, clearly show that data will leave the computer.

Example:

```txt
ONLINE • FREE

This engine will send the current dialogue to an external service.
Reference audio will be uploaded only if this engine requires it and you approve.
```

Nothing should be uploaded silently.

---

# Local labels

Clearly label engine types:

```txt
LOCAL • FREE
ONLINE • FREE
EXPERIMENTAL • LOCAL
```

Paid engines should not appear as normal supported choices.

---

# Model repositories

Downloading free/open model files from places such as official repositories is allowed.

Downloads must be explicit for large models.

Once downloaded, cache locally.

Do not re-download the same model every run.

---

# Licenses

"Free to download" does not automatically mean unrestricted.

Track model/software licenses.

Before making a model a default, verify whether it allows the intended use.

If a model is restricted to non-commercial/personal use, mark it clearly.

Example:

```txt
PERSONAL / NON-COMMERCIAL MODEL
```

Do not silently represent it as commercially unrestricted.

---

# Candidate-engine policy

Concrete model/service recommendations can become outdated.

Therefore engine metadata should include:

- local or online
- monetary cost category
- license
- source
- installed status
- hardware compatibility
- last verified date if useful

AI coding agents must re-check current terms before adding a new online service.

---

# Offline core

The following core actions must not require internet once local models are installed:

- open project
- parse Markdown
- detect speakers
- load voice profiles
- synthesize with installed local engine
- use reference audio
- cache audio
- assemble audio
- export audio

---

# Optional online enhancements

A genuinely free online engine may be used when it gives better quality or supports a feature the local machine cannot run well.

It must remain optional.

Example:

```txt
Preferred Engine: Free Online
Fallback Engine:  Local Reference Voice Engine
```

---

# No account requirement for the application

The desktop application itself must not require the user to create an account.

A third-party free online engine may require its own account only if:

- it remains genuinely free,
- there is no payment method requirement,
- the user explicitly chooses it,
- the local app still works without it.

---

# Telemetry

No telemetry by default.

No analytics by default.

No automatic crash-report upload.

The app should remain private by architecture.

---

# Final rule

When choosing between:

```txt
better but paid
```

and:

```txt
slightly less capable but free
```

choose the free option.

When no safe free online option exists, use local processing.

The product must never depend on payment to remain useful.
