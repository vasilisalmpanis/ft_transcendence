/**
 * Represents an API client for making HTTP requests
 * to the backend server pong.
 * @class
 */
class ApiClient {
  constructor (baseUrl) {
    this.baseUrl = new URL(baseUrl);
    if (typeof localStorage === 'undefined') {
      this.headers = {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      };
      return ;
    }
    this.headers = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };
    if (localStorage.getItem('access_token')) {
      this.headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
    }
    if (localStorage.getItem('refresh_token')) {
      this.refresh_token = localStorage.getItem('refresh_token');
    }
      
    // dev only
  }

  async checkStatus (response) {
    if (!response.ok) {
      const errorData = await response;
      let errorMessage = `Error: ${response.status} ${response.statusText}`;
      if (errorData.message) {
        errorMessage += ` - ${errorData.message}`;
      }
      throw new Error(errorMessage);
    }
  }

  async proceedResponse(response) {
    if (response.ok)
    {
      let data = await response.json();
      if (data.message)
        return {error: data.message};
      return data;
    }
    else
      return {error: response.status}
  }

  async sendRequest (path, method, body, query) {
    /* Makes request and returns reponse object with all its fields */
    const url = new URL(path, this.baseUrl);
    const params = {
      method,
      headers: this.headers,
    };
    if (body) {
      params.body = JSON.stringify(body);
    }
    if (query) {
      Object.entries(query).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }
    try {
      const response = await fetch(url, params);
      return await this.proceedResponse(response);
    } catch (error) {
      return {error: "no connection"};
    }
  }

  async get (path, query) {
    const url = new URL(path, this.baseUrl);
    return await this.sendRequest(url, 'GET', null, query);
  }

  async post (path, body, query) {
    const url = new URL(path, this.baseUrl);
    return await this.sendRequest(url, 'POST', body, query);
  }

  async put (path, body, query) {
    const url = new URL(path, this.baseUrl);
    return await this.sendRequest(url, 'PUT', body, query);
  }

  async delete (path, body, query) {
    const url = new URL(path, this.baseUrl);
    return await this.sendRequest(url, 'DELETE', body, query);
  }

  async authorize (payload, query = null) {
    let response_body;
    if ("access_token" in payload)
      response_body = payload;
    else {
      response_body = await this.sendRequest('auth', 'POST', payload, query);
      console.log(response_body);
    }
    if (response_body.error)
      return response_body;
    const access_token = response_body.access_token;
    const refresh_token = response_body.refresh_token;
    this.headers['Authorization'] = `Bearer ${access_token}`;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    const me = await this.get("/users/me");
    if (me.error)
      return me;
    localStorage.setItem("me", JSON.stringify(me));
    return {"ok": true};
  }

  unauthorize () {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('me');
  }

  async logout () {
    const response = await this.sendRequest('logout', 'POST', null, null);
    this.unauthorize();
    return response;
  }

  async refresh ()
  {
    if (this.refresh_token === undefined) {
      return ;
    }
    this.headers['Authorization'] = `Bearer ${this.refresh_token}`;
    const response = await this.sendRequest('auth/refresh', 'POST', null, null);
    const response_body = await response.json();
    const access_token = response_body.access_token;
    // dev only
    if (typeof localStorage === 'undefined') {
      this.headers['Authorization'] = `Bearer ${access_token}`;
      return response;
    }
    localStorage.setItem('access_token', access_token);
    return response;
  }

  async second_factor (code) {
    const response = await this.sendRequest('auth/verify', 'POST', { "2fa_code" : code }, null);
    const response_body = await response.json();
    const access_token = response_body.access_token;
    const refresh_token = response_body.refresh_token;
    // dev only
    if (typeof localStorage === 'undefined') {
      this.headers['Authorization'] = `Bearer ${access_token}`;
      return response;
    }
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    return response;
  }
  authorized() {
    return localStorage.getItem('access_token') ? true : false;
  }
};

export const apiClient = new ApiClient(`http://${window.location.hostname}:8000`);

export default ApiClient;
