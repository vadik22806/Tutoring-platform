import { useState, useEffect } from 'react';
import api from '../../api/client';

const LessonFilters = ({ filters, onFilterChange }) => {
  const [subjects, setSubjects] = useState([]);

  useEffect(() => {
    api.get('/subjects/').then((res) => {
      setSubjects(res.data.results || res.data);
    }).catch(() => {});
  }, []);

  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value });
  };

  return (
    <div style={styles.container}>
      <div style={styles.filterGroup}>
        <label style={styles.label}>Предмет</label>
        <select
          value={filters.subject_id || ''}
          onChange={(e) => handleChange('subject_id', e.target.value)}
          style={styles.select}
        >
          <option value="">Все предметы</option>
          {subjects.map((s) => (
            <option key={s.id || s._id} value={s.id || s._id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      <div style={styles.filterGroup}>
        <label style={styles.label}>Цена до</label>
        <input
          type="number"
          value={filters.price_max || ''}
          onChange={(e) => handleChange('price_max', e.target.value)}
          placeholder="Например, 2000"
          style={styles.input}
        />
      </div>

      <div style={styles.filterGroup}>
        <label style={styles.label}>Статус</label>
        <select
          value={filters.status || ''}
          onChange={(e) => handleChange('status', e.target.value)}
          style={styles.select}
        >
          <option value="">Все</option>
          <option value="available">Доступные</option>
          <option value="booked">Забронированные</option>
          <option value="completed">Завершённые</option>
          <option value="cancelled">Отменённые</option>
        </select>
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    gap: '16px',
    flexWrap: 'wrap',
    marginBottom: '24px',
    padding: '20px',
    background: '#fff',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
  },
  filterGroup: {
    flex: 1,
    minWidth: '180px',
  },
  label: {
    display: 'block',
    marginBottom: '6px',
    color: '#4a5568',
    fontSize: '13px',
    fontWeight: '500',
  },
  select: {
    width: '100%',
    padding: '10px 12px',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    fontSize: '14px',
    background: '#fff',
  },
  input: {
    width: '100%',
    padding: '10px 12px',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    fontSize: '14px',
    boxSizing: 'border-box',
  },
};

export default LessonFilters;