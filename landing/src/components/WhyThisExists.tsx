import SectionLabel from "./SectionLabel";

export default function WhyThisExists() {
  return (
    <section className="px-6 md:px-12 lg:px-20 xl:px-28 py-24 md:py-32 lg:py-40 border-t border-hairline">
      <SectionLabel number="02" title="Why this exists" />
      <div className="grid grid-cols-12 gap-6 md:gap-8 lg:gap-12 max-w-[1280px]">
        <aside className="col-span-12 md:col-span-3 text-[10px] md:text-[11px] tracking-[0.22em] uppercase text-ink-soft font-body font-medium md:pt-3 leading-relaxed">
          <span className="block text-sage mb-2">In the margin</span>
          <span className="block normal-case tracking-normal font-body font-light italic text-ink/65 text-[13px] md:text-sm leading-snug">
            Trauma kills more children and working-age adults than any
            infectious disease.
          </span>
        </aside>
        <div className="col-span-12 md:col-span-9 space-y-7 md:space-y-9">
          <p className="font-display text-[24px] md:text-[34px] lg:text-[40px] leading-[1.2] tracking-[-0.005em] text-ink drop-cap">
            Trauma is the leading cause of death between the ages of 1 and 44
            worldwide. The Advanced Trauma Life Support primary survey — a
            structured walk through Airway, Breathing, Circulation, Disability,
            Exposure — works because someone trained walks it.
          </p>
          <p className="font-body font-light text-base md:text-lg text-ink/85 leading-[1.7] max-w-3xl">
            In rural emergency rooms and resource-limited casualty departments,
            that{" "}
            <span className="font-medium text-ink not-italic">
              someone trained
            </span>{" "}
            is often a junior clinician, a nurse on a phone link, or a referral
            chain that takes hours. ATLS — the project — is a structured,
            citation-backed triage assistant that walks the protocol on a chest
            X-ray and a brief clinical vignette, and produces a
            Pydantic-validated primary-survey JSON plus an SBAR handoff in the
            local language, in seconds.
          </p>
        </div>
      </div>
    </section>
  );
}
