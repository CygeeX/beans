import axios from 'axios'

export function registerApi(data) {
  return axios.post('http://localhost:8000/api/register', data)
}

export function loginApi(data) {
  return axios.post('http://localhost:8000/api/login', data)
}