# Narration script — Bahasa Indonesia

> **Status:** placeholder. To be filled by you (the bilingual physician) — auto-translation of clinical Indonesian risks subtle errors that break credibility (`tubuh selang dada` vs `WSD`, `gawat darurat` vs `kritis`, etc.). Once you fill this in I'll generate the matching audio with ElevenLabs TTS using the same multilingual voice as the EN narration.

A draft auto-translation is provided below as a starting point — please correct in place. The clinical terms in particular (ATLS, SBAR, FAST, primary survey, BF16, MI300X) should stay either in English or use the Indonesian medical-school convention you'd actually use in handoff — your call.

---

## Scene 1 — Cold open (0:00–0:08)

_No narration. Text on screen, no voice._

> [teks di layar, muncul perlahan] *Kebanyakan kematian akibat trauma terjadi di tempat di mana tidak ada ahli bedah trauma yang siaga.*

---

## Scene 2 — Title (0:08–0:18)

> _DRAFT — please review:_
> Ini adalah **Agentic Trauma Life Support** — realisasi protokol ATLS dalam bentuk AI agentik.

---

## Scene 3 — What it does (0:18–0:30)

> _DRAFT — please review:_
> Klinisi mengunggah foto rontgen toraks, mengetik tanda vital, memilih bahasa — dan dalam hitungan detik, mendapatkan primary survey ATLS yang terstruktur.

---

## Scene 4 — Live demo (0:30–1:50)

_Live demo recording — see `docs/VIDEO_PLAN.md` Open Question 2 for whether the original audio is dubbed (Dubbing API) or replaced with TTS narration._

---

## Scene 5 — How it works (1:50–2:15)

> _DRAFT — please review:_
> Pipeline-nya terdiri dari tiga agen pada model yang sama. **Drafter** membaca rontgen dan menyusun primary survey dalam bentuk JSON terstruktur. **Verifier** memeriksa ulang gambar yang sama dan memperbaiki ketidakkonsistenan. **Renderer** mengubahnya menjadi handoff bergaya SBAR.

---

## Scene 6 — Hardware story (2:15–2:35)

> _DRAFT — please review:_
> Tujuh puluh dua miliar parameter dalam BF16 — sekitar seratus empat puluh lima gigabyte bobot. Model ini muat sepenuhnya dalam BF16 di sebuah AMD MI300X tunggal — satu-satunya GPU di bawah dua dolar per jam yang bisa menampungnya tanpa sharding atau kuantisasi.

---

## Scene 7 — Credibility (2:35–2:50)

> _DRAFT — please review:_
> Verifier ada untuk satu alasan: jangan mengarang temuan. Ada satu kasus uji di mana rontgen toraks normal tapi tanda vital memburuk. Model harus mengatakan "lihat ke abdomen." Dan model melakukannya.

---

## Scene 8 — Closing (2:50–3:00)

> _DRAFT — please review:_
> Repo dan live Space tersedia di tautan di bawah. Dibangun untuk AMD Developer Hackathon. Decision support — bukan diagnosis.

---

## Pronunciation notes for ElevenLabs (multilingual voice)

ElevenLabs `eleven_multilingual_v2` handles Indonesian natively, but specific tokens benefit from explicit hints:

- **"BF16"** → write as `B-F enam belas` if the voice mispronounces, otherwise leave `BF16`
- **"MI300X"** → write as `M-I tiga ratus X` if needed
- **"ATLS"** / **"SBAR"** / **"FAST"** — leave as English acronyms, the voice will pronounce letter-by-letter
- Numbers like "72 billion" — the script above writes them out (`tujuh puluh dua miliar`) which generally produces cleaner output than digits
