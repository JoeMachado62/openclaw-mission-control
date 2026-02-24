export function BrandMark() {
  return (
    <div className="flex items-center gap-3">
      <div
        className="grid h-10 w-10 place-items-center rounded-lg text-xs font-semibold text-white shadow-sm"
        style={{ background: "linear-gradient(135deg, #59ab9d, #4061b6)" }}
      >
        <span className="font-heading tracking-[0.2em]">VC</span>
      </div>
      <div className="leading-tight">
        <div className="font-heading text-sm uppercase tracking-[0.26em] text-strong">
          Virtual CarHub
        </div>
        <div className="text-[11px] font-medium text-quiet">
          Mission Control
        </div>
      </div>
    </div>
  );
}
