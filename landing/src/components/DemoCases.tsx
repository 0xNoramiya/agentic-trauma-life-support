import SectionLabel from "./SectionLabel";

type Case = {
  id: string;
  pathology: string;
  lang: "EN" | "ID";
  tests: string;
  highlight?: boolean;
};

const cases: Case[] = [
  {
    id: "case_01_tension_ptx",
    pathology: "Tension pneumothorax",
    lang: "EN",
    tests: "Drafter calls the right action — drama case",
  },
  {
    id: "case_02_massive_htx",
    pathology: "Massive hemothorax + shock",
    lang: "EN",
    tests: "Verifier catches drafter laterality error",
  },
  {
    id: "case_03_flail_chest",
    pathology: "Flail chest",
    lang: "EN",
    tests: "Verifier downgrades drafter over-call",
  },
  {
    id: "case_04_pulm_contusion",
    pathology: "Bilateral pulmonary contusion",
    lang: "EN",
    tests: "Multi-panel image · ICU disposition",
  },
  {
    id: "case_05_normal_polytrauma",
    pathology: "Normal CXR · abdominal injury",
    lang: "EN",
    tests: "The credibility test — model declined to invent",
    highlight: true,
  },
  {
    id: "case_06_pediatric_id",
    pathology: "Pediatric blunt thoracic trauma",
    lang: "ID",
    tests: "Multilingual rendering · Bahasa Indonesia",
  },
];

export default function DemoCases() {
  return (
    <section className="px-6 md:px-12 lg:px-20 xl:px-28 py-24 md:py-32 lg:py-40 border-t border-hairline">
      <SectionLabel number="06" title="Six demo cases" />
      <div className="max-w-[1200px]">
        <h2 className="font-display text-[28px] md:text-[40px] lg:text-[52px] leading-[1.08] tracking-[-0.01em] mb-12 md:mb-16 max-w-[24ch]">
          Five English. One Indonesian. One that has to refuse to invent.
        </h2>

        <div
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-px bg-hairline border border-hairline"
          role="list"
        >
          {cases.map((c) => (
            <article
              key={c.id}
              role="listitem"
              className={`bg-paper p-7 md:p-9 flex flex-col min-h-[220px] relative transition-colors duration-300 hover:bg-paper-2/60`}
            >
              {c.highlight && (
                <span
                  aria-hidden
                  className="absolute top-0 left-0 right-0 h-[2px] bg-terracotta"
                />
              )}
              <div className="flex items-baseline justify-between mb-5 md:mb-6">
                <span className="font-mono text-[11px] tracking-tight text-ink/50">
                  {c.id}
                </span>
                <span
                  className={`text-[10px] tracking-[0.22em] uppercase font-body font-medium border px-1.5 py-[2px] ${
                    c.lang === "ID"
                      ? "text-terracotta border-terracotta/50"
                      : "text-sage border-sage/40"
                  }`}
                >
                  {c.lang}
                </span>
              </div>
              <h3 className="font-display text-[22px] md:text-[26px] leading-[1.15] tracking-[-0.005em] text-ink mb-5 md:mb-6 flex-1">
                {c.pathology}
              </h3>
              <p
                className={`text-sm md:text-[15px] font-body leading-snug ${
                  c.highlight
                    ? "text-terracotta italic font-normal"
                    : "text-ink/65 font-light"
                }`}
              >
                {c.tests}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
