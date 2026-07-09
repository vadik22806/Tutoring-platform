import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const HomePage = () => {
  const { user } = useAuth();

  return (
    <div style={styles.container}>
      <div style={styles.hero}>
        <h1 style={styles.title}>StudyEasy</h1>
        <p style={styles.subtitle}>
          Платформа для поиска репетиторов и записи на занятия
        </p>

        {user ? (
          <div style={styles.buttons}>
            <Link
              to={user.role === 'tutor' ? '/dashboard/tutor' : '/dashboard/student'}
              style={styles.primaryBtn}
            >
              Перейти в кабинет
            </Link>
            <Link to="/lessons" style={styles.secondaryBtn}>
              Найти занятия
            </Link>
          </div>
        ) : (
          <div style={styles.buttons}>
            <Link to="/register" style={styles.primaryBtn}>
              Зарегистрироваться
            </Link>
            <Link to="/login" style={styles.secondaryBtn}>
              Войти
            </Link>
          </div>
        )}
      </div>

      <div style={styles.features}>
        <div style={styles.featureCard}>
          <h3 style={styles.featureTitle}>🎓 Для учеников</h3>
          <p style={styles.featureText}>
            Находите репетиторов по любым предметам, записывайтесь на занятия,
            откладывайте в избранное и управляйте расписанием.
          </p>
        </div>
        <div style={styles.featureCard}>
          <h3 style={styles.featureTitle}>👨‍🏫 Для репетиторов</h3>
          <p style={styles.featureText}>
            Создавайте занятия, управляйте расписанием, принимайте учеников
            и отслеживайте свою статистику.
          </p>
        </div>
        <div style={styles.featureCard}>
          <h3 style={styles.featureTitle}>⚡ Просто и быстро</h3>
          <p style={styles.featureText}>
            Мгновенная запись на занятия, удобные фильтры, атомарное бронирование
            — никаких двойных записей.
          </p>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '40px 20px',
  },
  hero: {
    textAlign: 'center',
    padding: '60px 20px',
  },
  title: {
    fontSize: '48px',
    fontWeight: 'bold',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    margin: '0 0 16px 0',
  },
  subtitle: {
    fontSize: '20px',
    color: '#718096',
    margin: '0 0 40px 0',
  },
  buttons: {
    display: 'flex',
    gap: '16px',
    justifyContent: 'center',
    flexWrap: 'wrap',
  },
  primaryBtn: {
    display: 'inline-block',
    padding: '14px 32px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff',
    textDecoration: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: '600',
  },
  secondaryBtn: {
    display: 'inline-block',
    padding: '14px 32px',
    background: '#fff',
    color: '#667eea',
    textDecoration: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: '600',
    border: '2px solid #667eea',
  },
  features: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '24px',
    marginTop: '40px',
  },
  featureCard: {
    background: '#fff',
    borderRadius: '12px',
    padding: '32px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
  },
  featureTitle: {
    color: '#2d3748',
    fontSize: '20px',
    margin: '0 0 12px 0',
  },
  featureText: {
    color: '#718096',
    fontSize: '15px',
    lineHeight: '1.6',
    margin: 0,
  },
};

export default HomePage;