import { useState, useEffect, useCallback } from 'react';
import { getAvailableLessons } from '../api/lessons';
import LessonCard from '../components/lessons/LessonCard';
import LessonFilters from '../components/lessons/LessonFilters';
import Loader from '../components/common/Loader';

const LessonsListPage = () => {
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({});
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  const fetchLessons = useCallback(async (pageNum = 1, append = false) => {
    setLoading(true);
    setError(null);
    try {
      const params = { ...filters, page: pageNum };
      const res = await getAvailableLessons(params);
      const data = res.data.results || res.data;
      if (append) {
        setLessons((prev) => [...prev, ...data]);
      } else {
        setLessons(data);
      }
      setHasMore(!!res.data.next);
    } catch (err) {
      setError('Ошибка загрузки занятий');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    setPage(1);
    fetchLessons(1);
  }, [fetchLessons]);

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchLessons(nextPage, true);
  };

  const handleUpdate = () => {
    fetchLessons(1);
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Доступные занятия</h1>

      <LessonFilters filters={filters} onFilterChange={handleFilterChange} />

      {error && <p style={styles.error}>{error}</p>}

      {loading && lessons.length === 0 ? (
        <Loader />
      ) : lessons.length === 0 ? (
        <p style={styles.empty}>Пока нет доступных занятий</p>
      ) : (
        <>
          <div style={styles.grid}>
            {lessons.map((lesson) => (
              <LessonCard
                key={lesson.id || lesson._id}
                lesson={lesson}
                onUpdate={handleUpdate}
              />
            ))}
          </div>

          {hasMore && (
            <div style={styles.loadMoreContainer}>
              <button
                onClick={handleLoadMore}
                disabled={loading}
                style={styles.loadMoreBtn}
              >
                {loading ? 'Загрузка...' : 'Загрузить ещё'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

const styles = {
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '40px 20px',
  },
  title: {
    color: '#2d3748',
    fontSize: '28px',
    marginBottom: '24px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
    gap: '20px',
  },
  error: {
    color: '#dc3545',
    textAlign: 'center',
    padding: '20px',
  },
  empty: {
    textAlign: 'center',
    color: '#718096',
    fontSize: '18px',
    padding: '60px',
  },
  loadMoreContainer: {
    textAlign: 'center',
    marginTop: '32px',
  },
  loadMoreBtn: {
    padding: '12px 32px',
    background: '#667eea',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    cursor: 'pointer',
    fontWeight: '500',
  },
};

export default LessonsListPage;