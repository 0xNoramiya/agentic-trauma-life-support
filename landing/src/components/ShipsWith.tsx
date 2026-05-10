import SectionLabel from "./SectionLabel";

const REPO = "https://github.com/0xNoramiya/agentic-trauma-life-support";

type Item = {
  label: string;
  value: string;
  href?: string;
};

const items: Item[] = [
  {
    label: "Live demo",
    value: "huggingface.co/spaces/lablab-ai-amd-developer-hackathon/atls",
    href: "https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/atls",
  },
  {
    label: "Public repository",
    value: "github.com/0xNoramiya/agentic-trauma-life-support",
    href: REPO,
  },
  {
    label: "Engineering writeup",
    value:
      "BLOG_POST.md — 2,400 words on the bring-up and the cost-accessibility argument",
    href: `${REPO}/blob/main/docs/BLOG_POST.md`,
  },
  {
    label: "ROCm feedback",
    value:
      "ROCM_FEEDBACK.md — seven numbered findings, with repro steps, for AMD",
    href: `${REPO}/blob/main/docs/ROCM_FEEDBACK.md`,
  },
  {
    label: "Real benchmarks",
    value:
      "BENCHMARKS.md — TTFT, throughput, peak VRAM, cold-start, with operational logs",
    href: `${REPO}/blob/main/docs/BENCHMARKS.md`,
  },
  {
    label: "Six demo cases",
    value:
      "DEMO_CASES.md — five English, one in Bahasa Indonesia, one credibility test",
    href: `${REPO}/blob/main/docs/DEMO_CASES.md`,
  },
  {
    label: "License & tests",
    value: "MIT · 27 passing tests · mock-mode UI verified end-to-end",
  },
];

export default function ShipsWith() {
  return (
    <section className="px-6 md:px-12 lg:px-20 xl:px-28 py-24 md:py-32 lg:py-40 border-t border-hairline">
      <SectionLabel number="07" title="What this ships with" />
      <div className="max-w-[1100px]">
        <h2 className="font-display text-[28px] md:text-[40px] lg:text-[52px] leading-[1.08] tracking-[-0.01em] mb-12 md:mb-16 max-w-[20ch]">
          Seven artifacts. One repository. MIT.
        </h2>

        <ul className="border-t border-hairline">
          {items.map((s, i) => (
            <li
              key={i}
              className="grid grid-cols-12 items-baseline gap-3 md:gap-8 lg:gap-12 py-5 md:py-7 border-b border-hairline group"
            >
              <span className="col-span-12 md:col-span-3 text-[10px] md:text-[11px] tracking-[0.22em] uppercase text-sage font-body font-medium md:pt-[6px]">
                {s.label}
              </span>
              <span className="col-span-12 md:col-span-9 font-display text-[18px] md:text-[22px] lg:text-[26px] text-ink leading-[1.3] tracking-[-0.005em]">
                {s.href ? (
                  <a
                    href={s.href}
                    target="_blank"
                    rel="noreferrer"
                    className="border-b border-ink/15 hover:border-sage hover:text-sage transition-colors decoration-from-font"
                  >
                    {s.value}
                  </a>
                ) : (
                  s.value
                )}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
