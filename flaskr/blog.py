from flask import Blueprint, flash, g, redirect, render_template, request, url_for, session
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint("blog", __name__)

def get_post(id, check_author=True):
    post = get_db().execute(
        "SELECT p.id, title, body, created, author_id, username,(SELECT count(author_id) FROM post_likes WHERE post_id = ? AND author_id = ?) as 'liked' ,(SELECT count(author_id) FROM post_likes WHERE post_id = ?) as 'likes'"
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id, session['user_id'], id, id)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)
    
    return post


@bp.route("/")
def index():
    db = get_db()
    posts = db.execute(
        "SELECT p.id, title, body, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    return render_template("blog/index.html", posts=posts)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."
          
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))
        
    return render_template('blog/create.html')


@bp.route('/<int:id>', methods=('GET', 'POST'))
@login_required
def details(id: int):
    post = get_post(id, check_author=False)
    return render_template('blog/details.html', post=post)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))
    
    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id, ))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/<int:post_id>/like', methods=('GET',))
@login_required
def like(post_id: int):
    get_post(post_id, check_author=False)
    db = get_db()
    db.execute(
        'INSERT OR IGNORE INTO post_likes(post_id, author_id) VALUES (?, ?)', 
        (post_id, session['user_id'])
    )
    db.commit()
    return redirect(url_for('blog.details', id=post_id))


@bp.route('/<int:post_id>/dislike', methods=('GET',))
@login_required
def dislike(post_id: int):
    get_post(post_id, check_author=False)
    db = get_db()
    db.execute(
      'DELETE FROM post_likes WHERE post_id = ? AND author_id = ?',
      (post_id, session['user_id'])
    )
    db.commit()
    return redirect(url_for('blog.details', id=post_id))
