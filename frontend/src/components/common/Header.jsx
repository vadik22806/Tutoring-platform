import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const getDashboardLink = () => {
    if (!user) return '/';
    return user.role === 'tutor' ? '/dashboard/tutor' : '/dashboard/student';
  };

  return (
    <header style={styles.header}>
      <div style={styles.container}>
        <Link to="/" style={styles.logo}>
          StudyEasy
        </Link>

        <nav style={styles.nav}>
          <Link to="/lessons" style={styles.navLink}>
            Занятия
          </Link>

          {user ? (
            <>
              <Link to={getDashboardLink()} style={styles.navLink}>
                {user.role === 'tutor' ? 'Кабинет' : 'Мой кабинет'}
              </Link>
              {user.role === 'student' && (
                <>
                  <Link to="/saved" style={styles.navLink}>
                    Избранное
                  </Link>
                  <Link to="/bookings" style={styles.navLink}>
                    Записи
                  </Link>
                </>
              )}
              <Link to="/profile/edit" style={styles.navLink}>
                Профиль
              </Link>
              <span style={styles.roleBadge}>
                {user.role === 'tutor' ? '👨‍🏫 Репетитор' : '🎓 Ученик'}
              </span>
              <span style={styles.userName}>{user.first_name || user.email}</span>
              <button onClick={handleLogout} style={styles.logoutBtn}>
                Выйти
              </button>
            </>
          ) : (
            <>
              <Link to="/login" style={styles.navLink}>
                Войти
              </Link>
              <Link to="/register" style={styles.registerBtn}>
                Регистрация
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
};

const styles = {
  header: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    padding: '0 20px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
  },
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    height: '64px',
  },
  logo: {
    color: '#fff',
    fontSize: '24px',
    fontWeight: 'bold',
    textDecoration: 'none',
  },
  nav: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  navLink: {
    color: 'rgba(255,255,255,0.9)',
    textDecoration: 'none',
    fontSize: '14px',
    fontWeight: '500',
    transition: 'color 0.2s',
  },
  roleBadge: {
    color: '#fff',
    fontSize: '13px',
    padding: '2px 8px',
    borderRadius: '12px',
    background: 'rgba(255,255,255,0.2)',
  },
  userName: {
    color: '#fff',
    fontSize: '14px',
    fontWeight: '500',
  },
  logoutBtn: {
    background: 'rgba(255,255,255,0.2)',
    color: '#fff',
    border: 'none',
    padding: '6px 16px',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  registerBtn: {
    background: '#fff',
    color: '#667eea',
    textDecoration: 'none',
    padding: '8px 20px',
    borderRadius: '6px',
    fontWeight: '600',
    fontSize: '14px',
  },
};

export default Header;