import axios from 'axios';

const API_BASE_URL = 'https://ludostock-backend-1015299081216.europe-west1.run.app/api/collection_games';

const collection_gameService = {
  getAllCollectionGames: (token) => {
    return axios.get(`${API_BASE_URL}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  getCollectionGame: (id, token) => {
    return axios.get(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  createCollectionGame: (collection_gameData, token) => {
    return axios.post(`${API_BASE_URL}/`, collection_gameData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  updateCollectionGame: (id, collection_gameData, token) => {
    return axios.put(`${API_BASE_URL}/${id}`, collection_gameData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  deleteCollectionGame: (id, token) => {
    return axios.delete(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },
};

export default collection_gameService;