import SectionLabel from "./SectionLabel";

type Stat = {
  label: string;
  value: string;
  unit: string;
  suffix?: string;
  caption: string;
};

const stats: Stat[] = [
  {
    label: "TTFT (median)",
    value: "1981",
    unit: "ms",
    caption: "Single image · short prompt",
  },
  {
    label: "Throughput",
    value: "21.5",
    unit: "tok / s",
    caption: "Single image · 3 k-token retrieved context",
  },
  {
    label: "Peak VRAM",
    value: "183.95",
    unit: "GiB",
    suffix: "/ 191.69",
    caption: "Concurrent batch of four · 96 % of budget",
  },
];

export default function Benchmarks() {
  return (
    <section className="px-6 md:px-12 lg:px-20 xl:px-28 py-24 md:py-32 lg:py-40 border-t border-hairline bg-paper-2/40">
      <SectionLabel number="05" title="Real benchmarks" />
      <div className="max-w-[1200px]">
        <h2 className="font-display text-[28px] md:text-[40px] lg:text-[52px] leading-[1.08] tracking-[-0.01em] mb-12 md:mb-16 max-w-[26ch]">
          Numbers from a real chest X-ray, against the live vLLM server.
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-y-14 md:gap-x-10 lg:gap-x-16 border-t border-ink/15 pt-12 md:pt-16">
          {stats.map((s, i) => (
            <div
              key={i}
              className="flex flex-col md:border-l md:border-hairline md:first:border-l-0 md:pl-10 lg:md:pl-16 md:first:pl-0"
            >
              <span className="text-[10px] md:text-[11px] tracking-[0.28em] uppercase text-sage font-body font-medium mb-7">
                {s.label}
              </span>
              <div className="flex items-baseline gap-2 flex-wrap">
                <span className="font-display font-normal text-[64px] md:text-[80px] lg:text-[96px] leading-none text-ink tabular-nums tracking-[-0.02em]">
                  {s.value}
                </span>
                {s.suffix && (
                  <span className="font-display text-2xl md:text-3xl text-ink/55 tabular-nums">
                    {s.suffix}
                  </span>
                )}
                <span className="font-body font-light text-base md:text-lg text-ink/60">
                  {s.unit}
                </span>
              </div>
              <p className="mt-5 text-sm md:text-base text-ink/70 font-body font-light leading-snug max-w-xs">
                {s.caption}
              </p>
            </div>
          ))}
        </div>

        <p className="mt-16 md:mt-20 text-[10px] md:text-[11px] tracking-[0.28em] uppercase text-ink/55 font-body font-medium border-t border-hairline pt-4">
          n = 5 per scenario · real chest X-ray (case_01_tension_ptx) · vLLM
          0.17.1 ROCm · single MI300X
        </p>
      </div>
    </section>
  );
}
