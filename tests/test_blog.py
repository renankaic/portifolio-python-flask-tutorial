import pytest
from flask import Flask
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


# pytest.mark.parametrize tells Pytest to run the same test function with different arguments
# You use it here to test different inputs
@pytest.mark.parametrize('path', (
  '/create',
  '/1/update',
  '/1/delete'
))
def test_login_required(client, path):
  response = client.post(path)
  assert response.header['Location'] == '/auth/login'


def test_author_required(app: Flask, client, auth):
  # change the post author to another user
  with app.app_context():
    db = get_db()
    db.execute('UPDATE post SET author_id = 2 WHERE id = 1')
    db.commit()

  auth.login()
  # current user can't modify other user's post
  assert client.post('/1/update').status_code == 403
  assert client.post('/1/delete').status_code == 403
  # current user doesn't see edit link
  assert b'href="/1/update"' not in client.get('/').data

