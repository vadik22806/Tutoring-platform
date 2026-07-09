import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import * as authApi from '../api/auth';
import { setTokens, removeTokens } from '../utils/token';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    const refresh = localStorage.getItem('refresh_token');
    if (refresh) {
      authApi.logout(refresh).catch(() => {});
    }
    removeTokens();
    setUser(null);
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      authApi
        .getMe()
        .then((res) => setUser(res.data))
        .catch(() => {
          removeTokens();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username, password) => {
    const response = await authApi.login(username, password);
    const { access, refresh } = response.data.tokens;
    setTokens(access, refresh);
    try {
      const meRes = await authApi.getMe();
      setUser(meRes.data);
    } catch {
      setUser(response.data.user);
    }
    return response;
  };

  const register = async (data) => {
    const response = await authApi.register(data);
    const { access, refresh } = response.data.tokens;
    setTokens(access, refresh);
    setUser(response.data.user);
    return response;
  };

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;