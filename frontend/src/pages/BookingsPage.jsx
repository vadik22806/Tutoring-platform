import { useState, useEffect } from 'react';
import { getMyBookings, cancelBooking } from '../api/bookings';
import LessonCard from '../components/lessons/LessonCard';
import Loader from '../components/common/Loader';
import toast from 'react-hot-toast';

const BookingsPage = () => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchBookings = async () => {
    setLoading(true);
    try {
      const res = await getMyBookings();
      const data = res.data.results || res.data.bookings || res.data;
      setBookings(data);
    } catch (err) {
      toast.error('Ошибка загрузки записей');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, []);

  const handleCancel = async (id) => {
    try {
      await cancelBooking(id);
      toast.success('Запись отменена');
      fetchBookings();
    } catch (err) {
      toast.error('Ошибка при отмене записи');
    }
  };

  if (loading) return <Loader />;

  const upcoming = bookings.filter(
    (b) => (b.status || b.lesson?.status) === 'booked'
  );
  const past = bookings.filter(
    (b) => (b.status || b.lesson?.status) !== 'booked'
  );

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>📋 Мои записи</h1>

      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Предстоящие</h2>
        {upcoming.length === 0 ? (
          <p style={styles.empty}>Нет предстоящих записей</p>
        ) : (
          <div style={styles.list}>
            {upcoming.map((b) => {
              const lesson = b.lesson || b;
              return (
                <div key={b.id || b._id} style={styles.bookingItem}>
                  <LessonCard lesson={lesson} showActions={false} />
                  <button
                    onClick={() => handleCancel(b.id || b._id)}
                    style={styles.cancelBtn}
                  >
                    Отменить запись
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>История</h2>
        {past.length === 0 ? (
          <p style={styles.empty}>История записей пуста</p>
        ) : (
          <div style={styles.list}>
            {past.map((b) => {
              const lesson = b.lesson || b;
              return (
                <div key={b.id || b._id} style={styles.bookingItem}>
                  <LessonCard lesson={lesson} showActions={false} />
                </div>
              );
            })}
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
  section: {
    marginBottom: '40px',
  },
  sectionTitle: {
    color: '#2d3748',
    fontSize: '22px',
    marginBottom: '20px',
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  bookingItem: {
    background: '#fff',
    borderRadius: '12px',
    padding: '20px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
  },
  cancelBtn: {
    marginTop: '12px',
    padding: '8px 20px',
    background: '#dc3545',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
  },
  empty: {
    color: '#718096',
    textAlign: 'center',
    padding: '40px',
    background: '#fff',
    borderRadius: '12px',
  },
};

export default BookingsPage;