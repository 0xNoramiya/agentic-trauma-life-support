const REPO = "https://github.com/0xNoramiya/agentic-trauma-life-support";
const HF_DEMO =
  "https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/atls";

export default function Closing() {
  return (
    <footer className="px-6 md:px-12 lg:px-20 xl:px-28 py-32 md:py-44 lg:py-56 border-t border-hairline">
      <div className="max-w-[900px] mx-auto text-center">
        <div
          className="h-px w-32 md:w-48 bg-sage mx-auto mb-14 md:mb-20"
          aria-hidden
        />
        <h2 className="font-display font-semibold text-[88px] sm:text-[120px] md:text-[180px] lg:text-[220px] leading-[0.85] tracking-[-0.03em] text-ink">
          ATLS
        </h2>
        <div className="mt-12 md:mt-16 space-y-2 text-[10px] md:text-[11px] tracking-[0.28em] uppercase text-ink/70 font-body font-medium">
          <p>Agentic Trauma Life Support</p>
          <p className="tabular-nums">MIT · May 2026</p>
          <p>Built by an emergency physician for the AMD Developer Hackathon</p>
        </div>

        <div className="mt-14 md:mt-20 flex flex-col md:flex-row items-center justify-center gap-3 md:gap-8 text-sm md:text-[15px] font-body font-light">
          <a
            href={REPO}
            target="_blank"
            rel="noreferrer"
            className="border-b border-ink/25 hover:border-sage hover:text-sage transition-colors"
          >
            github.com/0xNoramiya/agentic-trauma-life-support
          </a>
          <span aria-hidden className="hidden md:inline text-ink/30">
            ·
          </span>
          <a
            href={HF_DEMO}
            target="_blank"
            rel="noreferrer"
            className="border-b border-terracotta/50 hover:text-terracotta transition-colors"
          >
            huggingface.co/spaces/lablab-ai-amd-developer-hackathon/atls
          </a>
        </div>

        <p className="mt-16 md:mt-24 max-w-2xl mx-auto text-[12px] md:text-[13px] text-ink/55 font-body font-light italic leading-[1.7]">
          Decision support, not diagnosis. Not a regulated device. Not for
          unsupervised clinical use. Every output ships with a disclaimer to
          that effect. The clinical content is reviewed by the author (a
          practicing emergency physician) but is no substitute for a trained
          trauma team.
        </p>
      </div>
    </footer>
  );
}
