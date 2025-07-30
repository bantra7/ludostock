import axios from 'axios';

const API_BASE_URL = 'https://ludostock-backend-1015299081216.europe-west1.run.app/api/distributors';

const distributorService = {
  getAllDistributors: (token) => {
    return axios.get(`${API_BASE_URL}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  getDistributor: (id, token) => {
    return axios.get(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  createDistributor: (distributorData, token) => {
    return axios.post(`${API_BASE_URL}/`, distributorData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  updateDistributor: (id, distributorData, token) => {
    return axios.put(`${API_BASE_URL}/${id}`, distributorData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  deleteDistributor: (id, token) => {
    return axios.delete(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },
};

export default distributorService;