import api from './client';

export const getSavedLessons = () =>
  api.get('/saved/');

export const saveLesson = (id) =>
  api.post(`/saved/${id}/save/`);

export const unsaveLesson = (id) =>
  api.delete(`/saved/${id}/unsave/`);

export const bookAllSaved = () =>
  api.post('/saved/book-all/');