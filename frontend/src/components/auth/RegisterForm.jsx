import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { validateEmail, validatePhone, validatePassword, validatePasswordConfirm } from '../../utils/validation';
import toast from 'react-hot-toast';

const RegisterForm = () => {
  const [form, setForm] = useState({
    email: '',
    phone: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
    role: 'student',
  });
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.first_name) {
      toast.error('Введите имя');
      return;
    }
    if (!form.email && !form.phone) {
      toast.error('Укажите email или телефон');
      return;
    }
    if (form.email) {
      const emailCheck = validateEmail(form.email);
      if (!emailCheck.valid) {
        toast.error(emailCheck.message);
        return;
      }
    }
    if (form.phone) {
      const phoneCheck = validatePhone(form.phone);
      if (!phoneCheck.valid) {
        toast.error(phoneCheck.message);
        return;
      }
    }
    const passCheck = validatePassword(form.password);
    if (!passCheck.valid) {
      toast.error(passCheck.message);
      return;
    }
    const confirmCheck = validatePasswordConfirm(form.password, form.password_confirm);
    if (!confirmCheck.valid) {
      toast.error(confirmCheck.message);
      return;
    }

    setLoading(true);
    try {
      const data = { ...form };
      if (!data.email) delete data.email;
      if (!data.phone) delete data.phone;

      await register(data);
      toast.success('Регистрация успешна!');
      navigate('/');
    } catch (err) {
      const errors = err.response?.data?.errors || err.response?.data;
      if (typeof errors === 'object') {
        Object.values(errors).forEach((msg) => {
          if (Array.isArray(msg)) toast.error(msg[0]);
          else toast.error(msg);
        });
      } else {
        toast.error(errors?.error || 'Ошибка регистрации');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>Регистрация в StudyEasy</h2>
        <form onSubmit={handleSubmit}>
          <div style={styles.row}>
            <div style={styles.fieldHalf}>
              <label style={styles.label}>Имя *</label>
              <input
                type="text"
                name="first_name"
                value={form.first_name}
                onChange={handleChange}
                placeholder="Иван"
                style={styles.input}
              />
            </div>
            <div style={styles.fieldHalf}>
              <label style={styles.label}>Фамилия</label>
              <input
                type="text"
                name="last_name"
                value={form.last_name}
                onChange={handleChange}
                placeholder="Иванов"
                style={styles.input}
              />
            </div>
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Email</label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="user@example.com"
              style={styles.input}
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Телефон</label>
            <input
              type="text"
              name="phone"
              value={form.phone}
              onChange={handleChange}
              placeholder="+79991234567"
              style={styles.input}
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Пароль *</label>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Минимум 6 символов"
              style={styles.input}
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Подтверждение пароля *</label>
            <input
              type="password"
              name="password_confirm"
              value={form.password_confirm}
              onChange={handleChange}
              placeholder="Повторите пароль"
              style={styles.input}
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Кто вы?</label>
            <div style={styles.roleGroup}>
              <label style={styles.radioLabel}>
                <input
                  type="radio"
                  name="role"
                  value="student"
                  checked={form.role === 'student'}
                  onChange={handleChange}
                />
                🎓 Ученик
              </label>
              <label style={styles.radioLabel}>
                <input
                  type="radio"
                  name="role"
                  value="tutor"
                  checked={form.role === 'tutor'}
                  onChange={handleChange}
                />
                👨‍🏫 Репетитор
              </label>
            </div>
          </div>

          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? 'Регистрация...' : 'Зарегистрироваться'}
          </button>
        </form>
        <p style={styles.linkText}>
          Уже есть аккаунт?{' '}
          <Link to="/login" style={styles.link}>
            Войти
          </Link>
        </p>
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: 'calc(100vh - 64px - 60px)',
    background: '#f5f5f5',
    padding: '20px',
  },
  card: {
    background: '#fff',
    borderRadius: '12px',
    padding: '40px',
    width: '100%',
    maxWidth: '480px',
    boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
  },
  title: {
    textAlign: 'center',
    marginBottom: '32px',
    color: '#2d3748',
    fontSize: '24px',
  },
  row: {
    display: 'flex',
    gap: '12px',
  },
  field: {
    marginBottom: '20px',
  },
  fieldHalf: {
    flex: 1,
    marginBottom: '20px',
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
    padding: '12px 16px',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    fontSize: '16px',
    outline: 'none',
    boxSizing: 'border-box',
  },
  roleGroup: {
    display: 'flex',
    gap: '20px',
    marginTop: '8px',
  },
  radioLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '16px',
    cursor: 'pointer',
  },
  button: {
    width: '100%',
    padding: '12px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    marginTop: '8px',
  },
  linkText: {
    textAlign: 'center',
    marginTop: '20px',
    color: '#718096',
    fontSize: '14px',
  },
  link: {
    color: '#667eea',
    textDecoration: 'none',
    fontWeight: '500',
  },
};

export default RegisterForm;