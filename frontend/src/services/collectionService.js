import axios from 'axios';

const API_BASE_URL = 'https://ludostock-backend-1015299081216.europe-west1.run.app/api/collections';

const collectionService = {
  getAllCollections: (token) => {
    return axios.get(`${API_BASE_URL}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  getCollection: (id, token) => {
    return axios.get(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  createCollection: (collectionData, token) => {
    return axios.post(`${API_BASE_URL}/`, collectionData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  updateCollection: (id, collectionData, token) => {
    return axios.put(`${API_BASE_URL}/${id}`, collectionData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  deleteCollection: (id, token) => {
    return axios.delete(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },
};

export default collectionService;