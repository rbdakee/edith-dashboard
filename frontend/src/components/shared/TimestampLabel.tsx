import { relativeTime, formatDateTime } from '@/lib/format';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip';

interface TimestampLabelProps {
  dateStr: string | null;
  className?: string;
}

export function TimestampLabel({ dateStr, className }: TimestampLabelProps) {
  if (!dateStr) return <span className={className ?? 'text-gray-500 text-xs'}>Never</span>;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className={className ?? 'text-gray-400 text-xs cursor-default'}>
            {relativeTime(dateStr)}
          </span>
        </TooltipTrigger>
        <TooltipContent>{formatDateTime(dateStr)}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
