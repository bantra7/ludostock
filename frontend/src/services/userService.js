import axios from 'axios';

const API_BASE_URL = 'https://ludostock-backend-1015299081216.europe-west1.run.app/api/users';

const userService = {
  getAllUsers: (token) => {
    return axios.get(`${API_BASE_URL}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  getUser: (id, token) => {
    return axios.get(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  createUser: (userData, token) => {
    return axios.post(`${API_BASE_URL}/`, userData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  updateUser: (id, userData, token) => {
    return axios.put(`${API_BASE_URL}/${id}`, userData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  deleteUser: (id, token) => {
    return axios.delete(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },
};

export default userService;