import { useState, useEffect } from 'react';
import { getDashboard } from '../api/users';
import { getLessons, createLesson } from '../api/lessons';
import api from '../api/client';
import LessonCard from '../components/lessons/LessonCard';
import Loader from '../components/common/Loader';
import toast from 'react-hot-toast';

const TutorDashboard = () => {
  const [dashboard, setDashboard] = useState(null);
  const [myLessons, setMyLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [subjects, setSubjects] = useState([]);
  const [form, setForm] = useState({
    subject_id: '',
    date: '',
    time: '',
    duration: 60,
    price: 1000,
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashRes, lessonsRes] = await Promise.all([
        getDashboard(),
        getLessons(),
      ]);
      setDashboard(dashRes.data);
      setMyLessons(lessonsRes.data.results || lessonsRes.data);
    } catch (err) {
      console.error('Tutor dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSubjects = async () => {
    try {
      const res = await api.get('/subjects/');
      setSubjects(res.data.results || res.data);
    } catch (err) {
      console.error('Subjects load error:', err);
    }
  };

  useEffect(() => {
    fetchData();
    fetchSubjects();
  }, []);

  const handleCreateLesson = async (e) => {
    e.preventDefault();
    if (!form.subject_id || !form.date || !form.time) {
      toast.error('Заполните все поля');
      return;
    }
    setSubmitting(true);
    try {
      const dateTime = `${form.date}T${form.time}:00Z`;
      await createLesson({
        subject_id: form.subject_id,
        date: dateTime,
        duration: parseInt(form.duration),
        price: parseInt(form.price),
      });
      toast.success('Занятие создано!');
      setShowForm(false);
      setForm({ subject_id: '', date: '', time: '', duration: 60, price: 1000 });
      fetchData();
    } catch (err) {
      const msg = err.response?.data?.error || 'Ошибка при создании занятия';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <Loader />;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>👨‍🏫 Кабинет репетитора</h1>
        <button onClick={() => setShowForm(!showForm)} style={styles.addBtn}>
          {showForm ? 'Отмена' : '+ Создать занятие'}
        </button>
      </div>

      {dashboard && (
        <div style={styles.statsGrid}>
          <div style={styles.statCard}>
            <p style={styles.statNumber}>{dashboard.total_lessons || 0}</p>
            <p style={styles.statLabel}>Всего занятий</p>
          </div>
          <div style={styles.statCard}>
            <p style={styles.statNumber}>{dashboard.active_lessons || 0}</p>
            <p style={styles.statLabel}>Активных</p>
          </div>
          <div style={styles.statCard}>
            <p style={styles.statNumber}>{dashboard.completed_lessons || 0}</p>
            <p style={styles.statLabel}>Завершено</p>
          </div>
          <div style={styles.statCard}>
            <p style={styles.statNumber}>{dashboard.total_earned || 0} ₽</p>
            <p style={styles.statLabel}>Заработано</p>
          </div>
        </div>
      )}

      {showForm && (
        <div style={styles.formCard}>
          <h3 style={styles.formTitle}>Новое занятие</h3>
          <form onSubmit={handleCreateLesson}>
            <div style={styles.formRow}>
              <div style={styles.formField}>
                <label style={styles.label}>Предмет</label>
                <select
                  value={form.subject_id}
                  onChange={(e) => setForm({ ...form, subject_id: e.target.value })}
                  style={styles.input}
                >
                  <option value="">Выберите предмет</option>
                  {subjects.map((s) => (
                    <option key={s.id || s._id} value={s.id || s._id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <div style={styles.formField}>
                <label style={styles.label}>Длительность (мин)</label>
                <input
                  type="number"
                  value={form.duration}
                  onChange={(e) => setForm({ ...form, duration: e.target.value })}
                  style={styles.input}
                />
              </div>
            </div>
            <div style={styles.formRow}>
              <div style={styles.formField}>
                <label style={styles.label}>Дата</label>
                <input
                  type="date"
                  value={form.date}
                  onChange={(e) => setForm({ ...form, date: e.target.value })}
                  style={styles.input}
                />
              </div>
              <div style={styles.formField}>
                <label style={styles.label}>Время</label>
                <input
                  type="time"
                  value={form.time}
                  onChange={(e) => setForm({ ...form, time: e.target.value })}
                  style={styles.input}
                />
              </div>
            </div>
            <div style={styles.formField}>
              <label style={styles.label}>Цена (₽)</label>
              <input
                type="number"
                value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })}
                style={styles.input}
              />
            </div>
            <button type="submit" disabled={submitting} style={styles.submitBtn}>
              {submitting ? 'Создание...' : 'Создать занятие'}
            </button>
          </form>
        </div>
      )}

      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Мои занятия</h2>
        {myLessons.length === 0 ? (
          <p style={styles.empty}>У вас пока нет занятий</p>
        ) : (
          <div style={styles.grid}>
            {myLessons.map((lesson) => (
              <LessonCard key={lesson.id || lesson._id} lesson={lesson} onUpdate={fetchData} />
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
  addBtn: {
    padding: '12px 24px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    fontSize: '15px',
    fontWeight: '600',
    cursor: 'pointer',
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
  formCard: {
    background: '#fff',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '40px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
  },
  formTitle: {
    color: '#2d3748',
    fontSize: '18px',
    margin: '0 0 20px 0',
  },
  formRow: {
    display: 'flex',
    gap: '16px',
    marginBottom: '16px',
  },
  formField: {
    flex: 1,
    marginBottom: '16px',
  },
  label: {
    display: 'block',
    marginBottom: '6px',
    color: '#4a5568',
    fontSize: '14px',
    fontWeight: '500',
  },
  input: {
    width: '100%',
    padding: '10px 12px',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    fontSize: '14px',
    boxSizing: 'border-box',
  },
  submitBtn: {
    width: '100%',
    padding: '12px',
    background: '#28a745',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  section: {
    marginBottom: '40px',
  },
  sectionTitle: {
    color: '#2d3748',
    fontSize: '22px',
    marginBottom: '20px',
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

export default TutorDashboard;