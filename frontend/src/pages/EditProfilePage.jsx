import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { updateUser } from '../api/users';
import { validateEmail, validatePhone } from '../utils/validation';
import Loader from '../components/common/Loader';
import toast from 'react-hot-toast';

const EditProfilePage = () => {
  const { user, updateUser: updateUserContext } = useAuth();
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    bio: '',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setForm({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
        bio: user.bio || '',
      });
    }
  }, [user]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.first_name) {
      toast.error('Имя обязательно');
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

    setLoading(true);
    try {
      const data = { ...form };
      if (!data.email) delete data.email;
      if (!data.phone) delete data.phone;
      if (!data.bio) delete data.bio;

      const res = await updateUser(user.id || user._id, data);
      updateUserContext(res.data.user || res.data);
      toast.success('Профиль обновлён');
    } catch (err) {
      const errors = err.response?.data?.errors || err.response?.data;
      if (typeof errors === 'object') {
        Object.values(errors).forEach((msg) => {
          if (Array.isArray(msg)) toast.error(msg[0]);
          else toast.error(msg);
        });
      } else {
        toast.error('Ошибка обновления профиля');
      }
    } finally {
      setLoading(false);
    }
  };

  if (!user) return <Loader />;

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Редактирование профиля</h1>
        <form onSubmit={handleSubmit}>
          <div style={styles.row}>
            <div style={styles.fieldHalf}>
              <label style={styles.label}>Имя *</label>
              <input
                type="text"
                name="first_name"
                value={form.first_name}
                onChange={handleChange}
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
            <label style={styles.label}>О себе</label>
            <textarea
              name="bio"
              value={form.bio}
              onChange={handleChange}
              rows={4}
              style={styles.textarea}
            />
          </div>

          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? 'Сохранение...' : 'Сохранить'}
          </button>
        </form>
      </div>
    </div>
  );
};

const styles = {
  container: {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '40px 20px',
  },
  card: {
    background: '#fff',
    borderRadius: '12px',
    padding: '40px',
    boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
  },
  title: {
    color: '#2d3748',
    fontSize: '24px',
    marginBottom: '32px',
    textAlign: 'center',
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
  textarea: {
    width: '100%',
    padding: '12px 16px',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    fontSize: '16px',
    outline: 'none',
    resize: 'vertical',
    boxSizing: 'border-box',
    fontFamily: 'inherit',
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
  },
};

export default EditProfilePage;