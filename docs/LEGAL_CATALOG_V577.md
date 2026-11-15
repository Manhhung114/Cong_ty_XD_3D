# V5.7.7 — Legal catalog sources and statistics

- The app has **9 official lookup sources** in `data/legal/MEP_XD_source_registry.json` (including Ministry of Public Security, National Legal Documents Database advanced search, and Ministry of Science & Technology). These are search sources, not nine new laws.
- Catalog counts derive solely from deduplicated entries `(discipline, document number)` in `legalStatistics`. Discovery candidates are excluded. Historical and consolidated text entries may still appear.
- The table displays sequential STT/No. after filtering, and breakdown by Laws, Decrees, Circulars, TCVN, QCVN, Consolidated texts and Other.
- Verify legal effect at each source; neither original QLDA source code nor its published data are modified.
