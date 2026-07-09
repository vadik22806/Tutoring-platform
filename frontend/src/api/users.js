import api from './client';

export const getTutors = (params) =>
  api.get('/users/tutors/', { params });

export const getStudents = (params) =>
  api.get('/users/students/', { params });

export const getUser = (id) =>
  api.get(`/users/${id}/`);

export const updateUser = (id, data) =>
  api.post(`/users/${id}/update/`, data);

export const getDashboard = () =>
  api.get('/users/me/dashboard/');