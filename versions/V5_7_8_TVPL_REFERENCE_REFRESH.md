# V5.7.8 – TVPL as third-party reference

- Added **Cập nhật TVPL / Update TVPL** in Pháp luật & tiêu chuẩn, with separate numbered table of unverified records.
- Source links: https://m.thuvienphapluat.vn/ and https://thuvienphapluat.vn/page/Tim-Van-Ban.aspx.
- The button downloads a JSON snapshot from **this app repository**, not directly from TVPL browser JavaScript (CORS/auth can block it). The GitHub Actions workflow `refresh-tvpl.yml` fetches only public link metadata on a schedule or manual trigger.
- Candidate records are **not** automatically imported into the verified official catalog, legal statistics, or 'current' status.
- When live TVPL access is blocked or produces no relevant public links, the workflow must preserve the old JSON and report an error. Do not bypass login/paywalls or republish full documents/TCVN.
- Previous app state, revision storage, 9 official source sites and QLDA_ver612_VPS are untouched.
