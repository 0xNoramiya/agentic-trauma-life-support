export default function CredibilityMoment() {
  return (
    <section className="px-6 md:px-12 lg:px-20 xl:px-28 py-32 md:py-44 lg:py-56 border-t border-hairline relative overflow-hidden">
      <div className="max-w-[1100px] mx-auto relative">
        <span
          aria-hidden
          className="absolute -top-20 md:-top-32 lg:-top-40 -left-3 md:-left-6 font-display font-semibold text-[260px] md:text-[420px] lg:text-[560px] leading-none text-terracotta select-none"
          style={{ fontFeatureSettings: "'liga'" }}
        >
          &ldquo;
        </span>
        <blockquote className="font-display italic font-normal text-[36px] sm:text-[48px] md:text-[68px] lg:text-[88px] leading-[1.04] tracking-[-0.015em] text-ink relative z-10 max-w-[18ch]">
          Imaging unremarkable. Recommend FAST and CT abdomen.
        </blockquote>

        <div className="mt-12 md:mt-16 lg:mt-20 flex items-center gap-5 max-w-[1100px]">
          <span aria-hidden className="h-px w-10 bg-terracotta flex-none" />
          <p className="text-[10px] md:text-[11px] tracking-[0.28em] uppercase text-ink/70 font-body font-medium leading-relaxed">
            Case 05 · Normal CXR with hypotension · Model declined to invent
          </p>
        </div>
      </div>
    </section>
  );
}
