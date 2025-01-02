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
            className="mr-2 border border-white"
          />
        )}
        {totalPages === 1 ? null : (
          <PaginationContent>
            {getPageNumbers().map((page, index) =>
              page === '...' ? (
                <PaginationItem key={index}>
                  <PaginationLink className='cursor-pointer'>{page}</PaginationLink>
                </PaginationItem>
              ) : (
                <PaginationItem key={index}>
                  <PaginationLink className='cursor-pointer'
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
            className="ml-2 border border-white"
          />
        )}
      </Pagination>
    </div>
  );
}
