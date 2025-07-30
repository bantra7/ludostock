import axios from 'axios';

const API_BASE_URL = 'https://ludostock-backend-1015299081216.europe-west1.run.app/api/collection_shares';

const collection_shareService = {
  getAllCollectionShares: (token) => {
    return axios.get(`${API_BASE_URL}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  getCollectionShare: (id, token) => {
    return axios.get(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  createCollectionShare: (collection_shareData, token) => {
    return axios.post(`${API_BASE_URL}/`, collection_shareData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  updateCollectionShare: (id, collection_shareData, token) => {
    return axios.put(`${API_BASE_URL}/${id}`, collection_shareData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  deleteCollectionShare: (id, token) => {
    return axios.delete(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },
};

export default collection_shareService;