from flask import Blueprint, flash, g, redirect, render_template, request, url_for, session
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint("blog", __name__)

def get_post(id, check_author=True):
    post = get_db().execute(
        "SELECT p.id, title, body, created, author_id, username,(SELECT count(author_id) FROM post_likes WHERE post_id = p.id AND author_id = ?) as 'liked' ,(SELECT count(author_id) FROM post_likes WHERE post_id = p.id) as 'likes'"
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (session['user_id'], id)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)
    
    return post


def get_post_comments(id):
    post_comments = get_db().execute(
        "SELECT u.username, pc.comment, pc.created"
        " FROM post_comments pc JOIN user u ON pc.author_id = u.id"        
        " WHERE pc.post_id = ?"
        " ORDER BY created DESC",
        (id,)
    ).fetchall()

    return post_comments

@bp.route("/")
def index():
    db = get_db()
    posts = db.execute(
        "SELECT p.id, title, body, created, author_id, username, (SELECT count(author_id) FROM post_likes WHERE post_id = p.id) as 'likes', (SELECT count (id) FROM post_comments WHERE post_id = p.id) as 'comments' "
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
    comments = get_post_comments(post['id'])    
    return render_template('blog/details.html', post=post, comments=comments)


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


@bp.route('/<int:post_id>/comments', methods=('POST',))
@login_required
def comment(post_id: int):
    get_post(post_id, check_author=False)
    comment = request.form['comment']

    if len(comment) == 0:
      return redirect(url_for('blog.details', id=post_id)), 400

    db = get_db()
    db.execute(
      'INSERT INTO post_comments(post_id, author_id, comment)'
      ' VALUES(?, ?, ?)',
      (post_id, session['user_id'], comment)
    )
    db.commit()
    return redirect(url_for('blog.details', id=post_id))
