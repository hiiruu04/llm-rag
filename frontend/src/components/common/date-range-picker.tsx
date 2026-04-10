import { format } from "date-fns";

interface DateRangePickerProps {
  start: string;
  end: string;
  onStartChange: (v: string) => void;
  onEndChange: (v: string) => void;
}

export function DateRangePicker({ start, end, onStartChange, onEndChange }: DateRangePickerProps) {
  return (
    <div className="flex items-center gap-2">
      <input
        type="datetime-local"
        value={start ? format(new Date(start), "yyyy-MM-dd'T'HH:mm") : ""}
        onChange={(e) => onStartChange(e.target.value ? new Date(e.target.value).toISOString() : "")}
        className="h-9 rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
      />
      <span className="text-sm text-muted-foreground">to</span>
      <input
        type="datetime-local"
        value={end ? format(new Date(end), "yyyy-MM-dd'T'HH:mm") : ""}
        onChange={(e) => onEndChange(e.target.value ? new Date(e.target.value).toISOString() : "")}
        className="h-9 rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
      />
    </div>
  );
}
