const Footer = () => {
  return (
    <footer style={styles.footer}>
      <div style={styles.container}>
        <p style={styles.text}>© 2026 StudyEasy — Платформа для поиска репетиторов</p>
      </div>
    </footer>
  );
};

const styles = {
  footer: {
    background: '#2d3748',
    padding: '20px 0',
    marginTop: 'auto',
  },
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 20px',
    textAlign: 'center',
  },
  text: {
    color: 'rgba(255,255,255,0.6)',
    fontSize: '14px',
    margin: 0,
  },
};

export default Footer;