import axios from 'axios';

const API_BASE_URL = 'https://ludostock-backend-1015299081216.europe-west1.run.app/api/artists';

const artistService = {
  getAllArtists: (token) => {
    return axios.get(`${API_BASE_URL}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  getArtist: (id, token) => {
    return axios.get(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  createArtist: (artistData, token) => {
    return axios.post(`${API_BASE_URL}/`, artistData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  updateArtist: (id, artistData, token) => {
    return axios.put(`${API_BASE_URL}/${id}`, artistData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  deleteArtist: (id, token) => {
    return axios.delete(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },
};

export default artistService;