export const validateEmail = (email) => {
  if (!email) return { valid: true }; // email is optional
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email) ? { valid: true } : { valid: false, message: 'Неверный формат email' };
};

export const validatePhone = (phone) => {
  if (!phone) return { valid: true }; // phone is optional
  const cleaned = phone.replace(/[\s\-\(\)]/g, '');
  const re = /^\+?7\d{10}$|^8\d{10}$/;
  return re.test(cleaned)
    ? { valid: true }
    : { valid: false, message: 'Телефон должен быть в формате +79991234567' };
};

export const validatePassword = (password) => {
  if (!password || password.length < 6) {
    return { valid: false, message: 'Пароль должен быть минимум 6 символов' };
  }
  return { valid: true };
};

export const validatePasswordConfirm = (password, confirm) => {
  if (password !== confirm) {
    return { valid: false, message: 'Пароли не совпадают' };
  }
  return { valid: true };
};