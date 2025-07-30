import axios from 'axios';

const API_BASE_URL = 'https://ludostock-backend-1015299081216.europe-west1.run.app/api/user_locations';

const locationService = {
  getAllLocations: (token) => {
    return axios.get(`${API_BASE_URL}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  getLocation: (id, token) => {
    return axios.get(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  createLocation: (locationData, token) => {
    return axios.post(`${API_BASE_URL}/`, locationData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  updateLocation: (id, locationData, token) => {
    return axios.put(`${API_BASE_URL}/${id}`, locationData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  deleteLocation: (id, token) => {
    return axios.delete(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },
};

export default locationService;