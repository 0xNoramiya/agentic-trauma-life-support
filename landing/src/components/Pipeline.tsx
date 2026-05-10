import SectionLabel from "./SectionLabel";

type Step = {
  number: string;
  name: string;
  asterisk?: boolean;
  lines: string[];
};

const steps: Step[] = [
  {
    number: "01",
    name: "Drafter",
    lines: [
      "Reads X-ray, vitals, retrieved excerpts",
      "Writes strict TriageOutput JSON",
      "vLLM guided JSON · no prose",
    ],
  },
  {
    number: "02",
    name: "Verifier",
    asterisk: true,
    lines: [
      "Re-sees the original X-ray",
      "Compares against the draft",
      "Returns notes + path-walker patches",
    ],
  },
  {
    number: "03",
    name: "Renderer",
    lines: [
      "Validated JSON in",
      "SBAR markdown out",
      "English or Bahasa Indonesia",
    ],
  },
];

export default function Pipeline() {
  return (
    <section className="px-6 md:px-12 lg:px-20 xl:px-28 py-24 md:py-32 lg:py-40 border-t border-hairline">
      <SectionLabel number="04" title="The agentic pipeline" />
      <div className="max-w-[1200px]">
        <h2 className="font-display text-[28px] md:text-[40px] lg:text-[52px] leading-[1.08] tracking-[-0.01em] mb-12 md:mb-20 max-w-[22ch]">
          Three agents on the same model, on the same vLLM server.
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-x-8 lg:gap-x-12 gap-y-14 relative">
          {steps.map((s, i) => (
            <article key={s.number} className="relative">
              <div className="flex items-start gap-2 mb-7">
                <span className="font-display italic text-sage text-2xl md:text-3xl leading-none">
                  {s.number}
                </span>
                {s.asterisk && (
                  <span
                    className="text-terracotta text-2xl md:text-3xl leading-none -mt-1 select-none"
                    aria-label="safety-critical step"
                  >
                    ∗
                  </span>
                )}
              </div>
              <h3 className="font-display text-3xl md:text-4xl lg:text-5xl tracking-[-0.01em] leading-[1.05] text-ink mb-6">
                {s.name}
              </h3>
              <div className="h-px w-12 bg-sage mb-6" aria-hidden />
              <ul className="space-y-3 font-body font-light text-[15px] md:text-base leading-[1.55] text-ink/85">
                {s.lines.map((line, li) => (
                  <li key={li} className="flex items-start gap-3">
                    <span
                      aria-hidden
                      className="inline-block h-px w-2.5 bg-sage flex-none mt-[12px]"
                    />
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
              {/* connector arrow on md+ */}
              {i < steps.length - 1 && (
                <span
                  aria-hidden
                  className="hidden md:flex absolute top-2 -right-5 lg:-right-7 text-sage/60 text-xl select-none"
                >
                  →
                </span>
              )}
            </article>
          ))}
        </div>

        <p className="mt-16 md:mt-24 max-w-3xl border-t border-hairline pt-5 font-display italic text-base md:text-lg lg:text-xl text-ink/75 leading-relaxed">
          Both model calls hit the same vLLM server. No model router. No second
          GPU.
        </p>
      </div>
    </section>
  );
}
