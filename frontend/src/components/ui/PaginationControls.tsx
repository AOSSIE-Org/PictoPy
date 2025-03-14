import { PaginationControlsProps } from '@/types/Media';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from './pagination';

export default function PaginationControls({
  currentPage,
  totalPages,
  onPageChange,
}: PaginationControlsProps) {
  const getPageNumbers = (): (number | string)[] => {
    const maxPages = 5;
    const pages: (number | string)[] = [];

    const startPage = Math.max(1, currentPage - Math.floor(maxPages / 2));
    const endPage = Math.min(totalPages, startPage + maxPages - 1);

    if (startPage > 1) {
      pages.push(1);
      if (startPage > 2) {
        pages.push('...');
      }
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        pages.push('...');
      }
      pages.push(totalPages);
    }

    return pages;
  };
  const handlePrevious = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };
  const handleNext = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  };
  return (
    <div className="mt-6 flex justify-center">
      <Pagination>
        {currentPage === 1 ? null : (
          <PaginationPrevious
            onClick={handlePrevious}
            className="mr-2 border border-white/20 hover:border-white/50 hover:bg-white/10 transition-all duration-200 hover:scale-105 active:scale-95"
          />
        )}
        {totalPages === 1 ? null : (
          <PaginationContent className="gap-1 md:gap-2">
            {getPageNumbers().map((page, index) =>
              page === '...' ? (
                <PaginationItem key={index}>
                  <PaginationLink className="cursor-default hover:no-underline">
                    {page}
                  </PaginationLink>
                </PaginationItem>
              ) : (
                <PaginationItem key={index}>
                  <PaginationLink
                    className="cursor-pointer transition-all duration-200 hover:scale-110 hover:bg-primary/90 active:scale-95"
                    isActive={page === currentPage}
                    onClick={() => onPageChange(Number(page))}
                  >
                    {page}
                  </PaginationLink>
                </PaginationItem>
              ),
            )}
          </PaginationContent>
        )}

        {currentPage === totalPages ? null : (
          <PaginationNext
            onClick={handleNext}
            className="ml-2 border border-white/20 hover:border-white/50 hover:bg-white/10 transition-all duration-200 hover:scale-105 active:scale-95"
          />
        )}
      </Pagination>
    </div>
  );
}
