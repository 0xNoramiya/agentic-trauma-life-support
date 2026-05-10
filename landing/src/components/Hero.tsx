import Link from "next/link";

const HF_DEMO =
  "https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/atls";
const BLOG =
  "https://github.com/0xNoramiya/agentic-trauma-life-support/blob/main/docs/BLOG_POST.md";

export default function Hero() {
  return (
    <section className="min-h-screen flex flex-col px-6 md:px-12 lg:px-20 xl:px-28 py-8 md:py-10 lg:py-12 relative">
      {/* Mast */}
      <header className="flex items-baseline justify-between text-[10px] md:text-[11px] tracking-[0.32em] uppercase text-ink-soft font-body font-medium fade-up fade-up-1">
        <span className="flex items-baseline gap-3">
          <span className="font-display italic text-sage normal-case tracking-normal text-base leading-none">
            atls
          </span>
          <span aria-hidden className="h-px w-6 bg-hairline self-center" />
          <span className="hidden sm:inline">A field journal</span>
        </span>
        <span className="tabular-nums">№ 01 — May 2026</span>
      </header>

      {/* Center column */}
      <div className="flex-1 flex flex-col justify-center max-w-[1280px] mt-20 md:mt-24 lg:mt-12">
        <p className="text-[11px] md:text-[12px] tracking-[0.36em] uppercase text-sage font-body font-medium mb-8 md:mb-12 fade-up fade-up-2">
          Agentic Trauma Life Support
        </p>

        <h1 className="font-display italic font-normal leading-[0.96] tracking-[-0.02em] text-[40px] sm:text-[56px] md:text-[88px] lg:text-[120px] xl:text-[140px] text-ink fade-up fade-up-3 max-w-[16ch]">
          Qwen2.5-VL-72B
          <br />
          in full BF16,
          <br />
          on a single AMD MI300X.
        </h1>

        <div className="flex items-start gap-5 md:gap-7 mt-12 md:mt-16 max-w-2xl fade-up fade-up-4">
          <span
            aria-hidden
            className="h-px w-10 md:w-14 bg-sage flex-none mt-[14px] md:mt-[18px]"
          />
          <p className="font-body font-light text-base md:text-lg lg:text-xl text-ink/85 leading-[1.6]">
            Agentic trauma-triage decision-support, in{" "}
            <span className="font-medium text-ink">English</span> or{" "}
            <span className="font-medium text-ink">Bahasa Indonesia</span>. The
            agentic AI realization of the{" "}
            <em className="text-ink">Advanced Trauma Life Support</em> primary
            survey, served from a single AMD Instinct MI300X.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-6 sm:gap-12 mt-12 md:mt-16 fade-up fade-up-5">
          <Link
            href={HF_DEMO}
            target="_blank"
            rel="noreferrer"
            className="group inline-flex items-center gap-3 text-base md:text-lg font-body font-medium tracking-tight text-ink"
          >
            <span className="border-b-2 border-terracotta pb-[6px] group-hover:text-terracotta transition-colors duration-300">
              Try the live demo
            </span>
            <span
              aria-hidden
              className="text-terracotta transition-transform duration-300 group-hover:translate-x-1.5 group-hover:-translate-y-0.5"
            >
              ↗
            </span>
          </Link>
          <Link
            href={BLOG}
            target="_blank"
            rel="noreferrer"
            className="group inline-flex items-center gap-3 text-base md:text-lg font-body font-light tracking-tight text-ink/80"
          >
            <span className="border-b border-sage pb-[6px] group-hover:text-sage transition-colors duration-300">
              Read the engineering writeup
            </span>
            <span
              aria-hidden
              className="text-sage transition-transform duration-300 group-hover:translate-x-1.5"
            >
              →
            </span>
          </Link>
        </div>
      </div>

      {/* Colophon */}
      <footer className="mt-20 md:mt-12 fade-up fade-up-5">
        <div className="h-px w-full bg-hairline" aria-hidden />
        <div className="flex flex-col md:flex-row items-start md:items-baseline justify-between gap-2 md:gap-6 text-[10px] md:text-[11px] tracking-[0.28em] uppercase text-ink-soft font-body font-medium pt-4">
          <span>AMD Developer Hackathon</span>
          <span className="hidden md:inline">
            Decision support · not diagnosis
          </span>
          <span>Built by an emergency physician</span>
        </div>
      </footer>
    </section>
  );
}
