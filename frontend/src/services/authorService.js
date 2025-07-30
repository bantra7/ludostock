import axios from 'axios';

const API_BASE_URL = 'https://ludostock-backend-1015299081216.europe-west1.run.app/api/authors';

const authorService = {
  getAllAuthors: (token) => {
    return axios.get(`${API_BASE_URL}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  getAuthor: (id, token) => {
    return axios.get(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  createAuthor: (authorData, token) => {
    return axios.post(`${API_BASE_URL}/`, authorData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  updateAuthor: (id, authorData, token) => {
    return axios.put(`${API_BASE_URL}/${id}`, authorData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  deleteAuthor: (id, token) => {
    return axios.delete(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },
};


export default authorService;