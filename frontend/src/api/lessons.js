import api from './client';

export const getAvailableLessons = (params) =>
  api.get('/lessons/available/', { params });

export const getLessons = (params) =>
  api.get('/lessons/', { params });

export const getLesson = (id) =>
  api.get(`/lessons/${id}/`);

export const createLesson = (data) =>
  api.post('/lessons/', data);

export const updateLesson = (id, data) =>
  api.put(`/lessons/${id}/`, data);

export const deleteLesson = (id) =>
  api.delete(`/lessons/${id}/`);

export const completeLesson = (id) =>
  api.post(`/lessons/${id}/complete/`);

export const cancelLesson = (id) =>
  api.post(`/lessons/${id}/cancel/`);