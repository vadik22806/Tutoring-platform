import { useState, useEffect } from 'react';
import { getDashboard } from '../api/users';
import { getMyBookings } from '../api/bookings';
import { getAvailableLessons } from '../api/lessons';
import { getSavedLessons } from '../api/saved';
import LessonCard from '../components/lessons/LessonCard';
import Loader from '../components/common/Loader';
import { Link } from 'react-router-dom';

const StudentDashboard = () => {
  const [dashboard, setDashboard] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [availableLessons, setAvailableLessons] = useState([]);
  const [savedCount, setSavedCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dashRes, bookingsRes, lessonsRes, savedRes] = await Promise.all([
          getDashboard(),
          getMyBookings(),
          getAvailableLessons({ limit: 3 }),
          getSavedLessons(),
        ]);
        setDashboard(dashRes.data);
        setBookings(bookingsRes.data.results || bookingsRes.data.bookings || []);
        setAvailableLessons(lessonsRes.data.results || lessonsRes.data);
        setSavedCount(savedRes.data.results?.length || savedRes.data.length || 0);
      } catch (err) {
        console.error('Dashboard load error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <Loader />;

  const upcomingBookings = (bookings || []).filter(
    (b) => b.status === 'booked' || b.lesson_status === 'booked'
  );

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>🎓 Кабинет ученика</h1>

      {dashboard && (
        <div style={styles.statsGrid}>
          <div style={styles.statCard}>
            <p style={styles.statNumber}>{dashboard.total_bookings || 0}</p>
            <p style={styles.statLabel}>Всего записей</p>
          </div>
          <div style={styles.statCard}>
            <p style={styles.statNumber}>{dashboard.completed_lessons || 0}</p>
            <p style={styles.statLabel}>Завершено</p>
          </div>
          <div style={styles.statCard}>
            <p style={styles.statNumber}>{savedCount}</p>
            <p style={styles.statLabel}>В избранном</p>
          </div>
          <div style={styles.statCard}>
            <p style={styles.statNumber}>{dashboard.total_spent || 0} ₽</p>
            <p style={styles.statLabel}>Потрачено</p>
          </div>
        </div>
      )}

      <section style={styles.section}>
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>Предстоящие занятия</h2>
          <Link to="/bookings" style={styles.sectionLink}>Все записи →</Link>
        </div>
        {upcomingBookings.length === 0 ? (
          <p style={styles.empty}>Нет предстоящих занятий</p>
        ) : (
          <div style={styles.grid}>
            {upcomingBookings.slice(0, 3).map((b) => (
              <LessonCard key={b.id || b._id} lesson={b.lesson || b} showActions={false} />
            ))}
          </div>
        )}
      </section>

      <section style={styles.section}>
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>Доступные занятия</h2>
          <Link to="/lessons" style={styles.sectionLink}>Все занятия →</Link>
        </div>
        {availableLessons.length === 0 ? (
          <p style={styles.empty}>Пока нет доступных занятий</p>
        ) : (
          <div style={styles.grid}>
            {availableLessons.slice(0, 3).map((lesson) => (
              <LessonCard key={lesson.id || lesson._id} lesson={lesson} />
            ))}
          </div>
        )}
      </section>
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
    marginBottom: '32px',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginBottom: '40px',
  },
  statCard: {
    background: '#fff',
    borderRadius: '12px',
    padding: '24px',
    textAlign: 'center',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
  },
  statNumber: {
    fontSize: '32px',
    fontWeight: 'bold',
    color: '#667eea',
    margin: '0 0 4px 0',
  },
  statLabel: {
    color: '#718096',
    fontSize: '14px',
    margin: 0,
  },
  section: {
    marginBottom: '40px',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  sectionTitle: {
    color: '#2d3748',
    fontSize: '22px',
    margin: 0,
  },
  sectionLink: {
    color: '#667eea',
    textDecoration: 'none',
    fontSize: '14px',
    fontWeight: '500',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
    gap: '20px',
  },
  empty: {
    color: '#718096',
    textAlign: 'center',
    padding: '40px',
    background: '#fff',
    borderRadius: '12px',
  },
};

export default StudentDashboard;