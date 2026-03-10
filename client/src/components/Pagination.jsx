export default function Pagination({ pagination, onPageChange }) {
  const { page, total_pages, total, page_size } = pagination

  if (total_pages <= 1) return null

  const start = (page - 1) * page_size + 1
  const end = Math.min(page * page_size, total)

  // Build visible page numbers: always show first, last, current ±1
  const pages = new Set([1, total_pages, page, page - 1, page + 1])
  const visiblePages = [...pages]
    .filter((p) => p >= 1 && p <= total_pages)
    .sort((a, b) => a - b)

  return (
    <div className="pagination">
      <span className="pagination-info">
        {start}–{end} of {total.toLocaleString()}
      </span>

      <div className="pagination-controls">
        <button
          className="page-btn"
          disabled={page === 1}
          onClick={() => onPageChange(page - 1)}
        >
          ‹
        </button>

        {visiblePages.map((p, i) => {
          const prev = visiblePages[i - 1]
          return (
            <span key={p} className="page-group">
              {prev && p - prev > 1 && <span className="page-ellipsis">…</span>}
              <button
                className={`page-btn ${p === page ? 'active' : ''}`}
                onClick={() => onPageChange(p)}
              >
                {p}
              </button>
            </span>
          )
        })}

        <button
          className="page-btn"
          disabled={page === total_pages}
          onClick={() => onPageChange(page + 1)}
        >
          ›
        </button>
      </div>
    </div>
  )
}
