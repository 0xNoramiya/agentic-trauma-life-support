import SectionLabel from "./SectionLabel";

export default function DoubleMeaning() {
  return (
    <section className="px-6 md:px-12 lg:px-20 xl:px-28 py-24 md:py-32 lg:py-40 border-t border-hairline">
      <SectionLabel number="01" title="The double meaning" />
      <div className="grid grid-cols-12 gap-6 md:gap-8 lg:gap-12 max-w-[1280px]">
        <aside className="col-span-12 md:col-span-3 text-[10px] md:text-[11px] tracking-[0.22em] uppercase text-ink-soft font-body font-medium md:pt-3 leading-relaxed">
          <span className="block text-sage mb-2">In the margin</span>
          <span className="block normal-case tracking-normal font-body font-light italic text-ink/65 text-[13px] md:text-sm leading-snug">
            The acronym was deliberate — the project is named for what it does
            and what it follows.
          </span>
        </aside>
        <div className="col-span-12 md:col-span-9">
          <p className="font-display text-[26px] md:text-[36px] lg:text-[44px] leading-[1.16] tracking-[-0.005em] text-ink drop-cap">
            A double meaning was deliberate. ATLS is the global trauma protocol
            from the American College of Surgeons —{" "}
            <em>Advanced Trauma Life Support</em>. This project —{" "}
            <em>Agentic Trauma Life Support</em> — is the agentic AI
            realization of that protocol&rsquo;s primary survey.
          </p>
        </div>
      </div>
    </section>
  );
}
