import { Link } from 'react-router-dom';

const NotFoundPage = () => {
  return (
    <div style={styles.container}>
      <h1 style={styles.code}>404</h1>
      <p style={styles.text}>Страница не найдена</p>
      <Link to="/" style={styles.link}>
        Вернуться на главную
      </Link>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 'calc(100vh - 64px - 60px)',
    padding: '40px',
  },
  code: {
    fontSize: '96px',
    fontWeight: 'bold',
    color: '#667eea',
    margin: '0 0 16px 0',
  },
  text: {
    fontSize: '24px',
    color: '#718096',
    margin: '0 0 32px 0',
  },
  link: {
    padding: '12px 32px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff',
    textDecoration: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: '600',
  },
};

export default NotFoundPage;