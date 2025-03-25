import pytest
from flaskr.db import get_db


def test_index(client, auth):
  # before logging in, should display Log In and Register
  response = client.get('/')
  assert b'Log In' in response.data
  assert b'Register' in response.data

  auth.login()
  response = client.get('/')
  
  # after logging in, the following should pass
  assert b'Log Out' in response.data
  assert b'test title' in response.data
  assert b'by test on 2018-01-01' in response.data
  assert b'test\nbody' in response.data
  assert b'href="/1/update"' in response.data