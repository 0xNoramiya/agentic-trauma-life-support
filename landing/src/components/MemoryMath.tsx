import SectionLabel from "./SectionLabel";

type Row = {
  label: string;
  vram: number;
  fits: boolean;
  cost: string;
  highlight?: boolean;
  note?: string;
};

const SCALE = 220;
const THRESHOLD = 145;
const thresholdPct = (THRESHOLD / SCALE) * 100;

const rows: Row[] = [
  { label: "1 × NVIDIA H100", vram: 80, fits: false, cost: "—" },
  { label: "1 × NVIDIA H200", vram: 141, fits: false, cost: "—" },
  {
    label: "2 × NVIDIA H100 NVLink",
    vram: 160,
    fits: true,
    cost: "≈ $4–5 / hr",
    note: "tensor-parallel",
  },
  { label: "1 × NVIDIA B200", vram: 192, fits: true, cost: "≈ $5–8 / hr" },
  {
    label: "1 × AMD MI300X",
    vram: 192,
    fits: true,
    cost: "≈ $1.99 / hr",
    highlight: true,
  },
];

function BarRow({ row, showThresholdLabel }: { row: Row; showThresholdLabel?: boolean }) {
  const fillBg = row.highlight
    ? "bg-sage"
    : row.fits
      ? "bg-ink/35"
      : "bg-ink/15";

  return (
    <div className="relative h-7 w-full">
      <div className="absolute inset-0 bg-hairline/35" aria-hidden />
      <div
        className={`absolute inset-y-0 left-0 ${fillBg}`}
        style={{ width: `${(row.vram / SCALE) * 100}%` }}
        aria-hidden
      />
      <div
        className="absolute top-0 bottom-0 border-l border-dashed border-ink/40 pointer-events-none"
        style={{ left: `${thresholdPct}%` }}
        aria-hidden
      >
        {showThresholdLabel && (
          <span className="absolute -top-9 left-2 text-[10px] tracking-[0.2em] uppercase text-ink/65 font-medium whitespace-nowrap">
            Qwen2.5-VL-72B BF16 · 145 GB
          </span>
        )}
      </div>
      {row.highlight && (
        <span className="absolute -right-2 top-1/2 -translate-y-1/2 translate-x-full text-[10px] tracking-[0.2em] uppercase text-sage font-semibold whitespace-nowrap">
          ← chosen
        </span>
      )}
    </div>
  );
}

export default function MemoryMath() {
  return (
    <section className="px-6 md:px-12 lg:px-20 xl:px-28 py-24 md:py-32 lg:py-40 border-t border-hairline">
      <SectionLabel number="03" title="Why a single MI300X" />
      <div className="max-w-[1200px]">
        <h2 className="font-display text-[28px] md:text-[40px] lg:text-[52px] leading-[1.08] tracking-[-0.01em] mb-5 max-w-[20ch]">
          The 192 GB-class shortlist, drawn to scale.
        </h2>
        <p className="font-body font-light text-base md:text-lg text-ink/80 leading-relaxed max-w-2xl mb-16 md:mb-20">
          Qwen2.5-VL-72B in full BF16 occupies roughly{" "}
          <span className="font-medium text-ink">145 GB</span> of weights — the
          dashed line. Anything to the left of it does not fit on a single
          device.
        </p>

        {/* Desktop layout */}
        <div className="hidden md:block max-w-[940px]">
          <div
            className="grid items-center gap-x-6 gap-y-6"
            style={{ gridTemplateColumns: "minmax(180px, 220px) 1fr 70px 110px" }}
          >
            {rows.map((row, i) => (
              <RowDesktop key={i} row={row} showThresholdLabel={i === 0} />
            ))}
          </div>
        </div>

        {/* Mobile layout */}
        <div className="md:hidden space-y-7 max-w-md">
          {rows.map((row, i) => (
            <div key={i} className="space-y-2">
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-[12px] tracking-[0.06em] uppercase font-body font-medium text-ink/85">
                  {row.label}
                </span>
                <span className="font-display text-base tabular-nums text-ink leading-none">
                  {row.vram}
                  <span className="text-ink/50 text-xs ml-1">GB</span>
                </span>
              </div>
              <BarRow row={row} />
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-[10px] tracking-[0.18em] uppercase font-body text-ink/60">
                  {row.fits ? "fits" : "does not fit"}
                  {row.note && ` · ${row.note}`}
                </span>
                <span className="text-[11px] tracking-[0.06em] uppercase font-body text-ink/70 tabular-nums">
                  {row.cost}
                </span>
              </div>
            </div>
          ))}
        </div>

        <p className="mt-16 md:mt-20 max-w-[940px] text-[11px] md:text-[12px] tracking-[0.22em] uppercase text-sage font-medium border-t border-sage/40 pt-4">
          The only sub-$2/hr option that fits 72B in BF16 on a single GPU.
        </p>
      </div>
    </section>
  );
}

function RowDesktop({
  row,
  showThresholdLabel,
}: {
  row: Row;
  showThresholdLabel: boolean;
}) {
  return (
    <>
      <div
        className={`text-[12px] tracking-[0.06em] uppercase font-body font-medium ${
          row.highlight ? "text-ink" : "text-ink/85"
        }`}
      >
        {row.label}
      </div>
      <BarRow row={row} showThresholdLabel={showThresholdLabel} />
      <div className="font-display text-base tabular-nums text-right text-ink leading-none">
        {row.vram}
        <span className="text-ink/50 text-xs ml-1">GB</span>
      </div>
      <div className="text-right font-body text-[11px] tracking-[0.06em] uppercase text-ink/60 whitespace-nowrap tabular-nums">
        {row.cost}
      </div>
    </>
  );
}
