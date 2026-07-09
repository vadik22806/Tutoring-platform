import api from './client';

export const createBooking = (lessonId) =>
  api.post('/bookings/', { lesson_id: lessonId });

export const cancelBooking = (id) =>
  api.post(`/bookings/${id}/cancel/`);

export const getMyBookings = () =>
  api.get('/bookings/me/');