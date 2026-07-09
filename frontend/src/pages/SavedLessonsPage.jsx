import { useState, useEffect } from 'react';
import { getSavedLessons, bookAllSaved } from '../api/saved';
import LessonCard from '../components/lessons/LessonCard';
import Loader from '../components/common/Loader';
import toast from 'react-hot-toast';

const SavedLessonsPage = () => {
  const [savedLessons, setSavedLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [bookingAll, setBookingAll] = useState(false);

  const fetchSaved = async () => {
    setLoading(true);
    try {
      const res = await getSavedLessons();
      const data = res.data.results || res.data;
      const lessons = data.map((item) => ({
        ...item.lesson,
        is_saved: true,
        tutor_name: item.lesson?.tutor_name,
        subject_name: item.lesson?.subject_name,
      }));
      setSavedLessons(lessons);
    } catch (err) {
      toast.error('Ошибка загрузки избранного');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSaved();
  }, []);

  const handleBookAll = async () => {
    setBookingAll(true);
    try {
      const res = await bookAllSaved();
      const data = res.data;
      toast.success(`Забронировано: ${data.booked || 0}, ошибок: ${data.failed || 0}`);
      fetchSaved();
    } catch (err) {
      toast.error('Ошибка при массовой записи');
    } finally {
      setBookingAll(false);
    }
  };

  if (loading) return <Loader />;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>⭐ Избранное</h1>
        {savedLessons.length > 0 && (
          <button
            onClick={handleBookAll}
            disabled={bookingAll}
            style={styles.bookAllBtn}
          >
            {bookingAll ? 'Бронирование...' : 'Записаться на все'}
          </button>
        )}
      </div>

      {savedLessons.length === 0 ? (
        <p style={styles.empty}>В избранном пока нет занятий</p>
      ) : (
        <div style={styles.grid}>
          {savedLessons.map((lesson) => (
            <LessonCard
              key={lesson.id || lesson._id}
              lesson={lesson}
              onUpdate={fetchSaved}
            />
          ))}
        </div>
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
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '32px',
  },
  title: {
    color: '#2d3748',
    fontSize: '28px',
    margin: 0,
  },
  bookAllBtn: {
    padding: '12px 24px',
    background: '#28a745',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    fontSize: '15px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
    gap: '20px',
  },
  empty: {
    textAlign: 'center',
    color: '#718096',
    fontSize: '18px',
    padding: '60px',
  },
};

export default SavedLessonsPage;