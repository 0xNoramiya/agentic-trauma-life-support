type Props = {
  number: string;
  title: string;
};

export default function SectionLabel({ number, title }: Props) {
  return (
    <div className="flex items-center gap-3 md:gap-4 text-[10px] md:text-[11px] tracking-[0.28em] uppercase text-sage font-body font-medium mb-12 md:mb-16">
      <span className="font-display italic font-normal text-base md:text-lg leading-none text-sage/80">
        §
      </span>
      <span className="tabular-nums">{number}</span>
      <span aria-hidden className="h-px w-8 md:w-12 bg-sage/40" />
      <span>{title}</span>
    </div>
  );
}
