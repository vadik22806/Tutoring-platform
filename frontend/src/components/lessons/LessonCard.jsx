import { useState } from 'react';
import { formatShortDate, isFutureDate } from '../../utils/date';
import { useAuth } from '../../context/AuthContext';
import { createBooking } from '../../api/bookings';
import { saveLesson, unsaveLesson } from '../../api/saved';
import toast from 'react-hot-toast';

const LessonCard = ({ lesson, onUpdate, showActions = true }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);

  const isAvailable = lesson.status === 'available' && isFutureDate(lesson.date);
  const isBooked = lesson.status === 'booked';
  const isCompleted = lesson.status === 'completed';
  const isCancelled = lesson.status === 'cancelled';

  const getStatusLabel = () => {
    if (isAvailable) return { text: 'Доступно', color: '#28a745' };
    if (isBooked) return { text: 'Забронировано', color: '#007bff' };
    if (isCompleted) return { text: 'Завершено', color: '#6c757d' };
    if (isCancelled) return { text: 'Отменено', color: '#dc3545' };
    return { text: lesson.status, color: '#6c757d' };
  };

  const status = getStatusLabel();

  const handleBook = async () => {
    setLoading(true);
    try {
      await createBooking(lesson.id || lesson._id);
      toast.success('Вы записаны на занятие!');
      if (onUpdate) onUpdate();
    } catch (err) {
      const msg = err.response?.data?.error || 'Ошибка при записи';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await saveLesson(lesson.id || lesson._id);
      toast.success('Добавлено в избранное');
      if (onUpdate) onUpdate();
    } catch (err) {
      toast.error('Ошибка при добавлении в избранное');
    } finally {
      setLoading(false);
    }
  };

  const handleUnsave = async () => {
    setLoading(true);
    try {
      await unsaveLesson(lesson.id || lesson._id);
      toast.success('Удалено из избранного');
      if (onUpdate) onUpdate();
    } catch (err) {
      toast.error('Ошибка при удалении из избранного');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <h3 style={styles.subject}>{lesson.subject_name || 'Предмет'}</h3>
        <span style={{ ...styles.statusBadge, background: status.color }}>
          {status.text}
        </span>
      </div>

      {lesson.tutor_name && (
        <p style={styles.tutor}>👨‍🏫 {lesson.tutor_name}</p>
      )}

      <div style={styles.details}>
        <p style={styles.detailItem}>📅 {formatShortDate(lesson.date)}</p>
        <p style={styles.detailItem}>⏱ {lesson.duration} мин</p>
        <p style={styles.detailItem}>💰 {lesson.price} ₽</p>
      </div>

      {showActions && user && isAvailable && user.role === 'student' && (
        <div style={styles.actions}>
          <button onClick={handleBook} disabled={loading} style={styles.bookBtn}>
            {loading ? '...' : 'Записаться'}
          </button>
          <button onClick={handleSave} disabled={loading} style={styles.saveBtn}>
            {loading ? '...' : '⭐ Отложить'}
          </button>
        </div>
      )}

      {showActions && user && lesson.is_saved && (
        <div style={styles.actions}>
          <button onClick={handleUnsave} disabled={loading} style={styles.unsaveBtn}>
            {loading ? '...' : 'Удалить из избранного'}
          </button>
        </div>
      )}
    </div>
  );
};

const styles = {
  card: {
    background: '#fff',
    borderRadius: '12px',
    padding: '20px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
    transition: 'box-shadow 0.2s',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
  },
  subject: {
    margin: 0,
    fontSize: '18px',
    color: '#2d3748',
  },
  statusBadge: {
    padding: '4px 12px',
    borderRadius: '12px',
    color: '#fff',
    fontSize: '12px',
    fontWeight: '600',
  },
  tutor: {
    color: '#4a5568',
    fontSize: '14px',
    margin: '0 0 12px 0',
  },
  details: {
    display: 'flex',
    gap: '16px',
    flexWrap: 'wrap',
  },
  detailItem: {
    color: '#718096',
    fontSize: '14px',
    margin: 0,
  },
  actions: {
    display: 'flex',
    gap: '10px',
    marginTop: '16px',
  },
  bookBtn: {
    flex: 1,
    padding: '10px',
    background: '#28a745',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '600',
    fontSize: '14px',
  },
  saveBtn: {
    flex: 1,
    padding: '10px',
    background: '#ffc107',
    color: '#333',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '600',
    fontSize: '14px',
  },
  unsaveBtn: {
    width: '100%',
    padding: '10px',
    background: '#dc3545',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '600',
    fontSize: '14px',
  },
};

export default LessonCard;