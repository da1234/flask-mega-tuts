from app.main import bp
from app import db
from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import current_user, login_required
from werkzeug.urls import url_parse
from app.main.forms import EditProfileForm, PostForm, MessageForm
from app.models import User, Post, Message, Notification
from datetime import datetime

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@bp.route("/",methods=['GET', 'POST'])
@bp.route("/index",methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post has been added!")
        return redirect(url_for("main.index"))
    page = request.args.get('page',1,type=int)
    posts = current_user.followed_posts().paginate(page,current_app.config["POSTS_PER_PAGE"], False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html",title="Welcome Screen", form=form, posts=posts.items,
        next_url=next_url,prev_url=prev_url)

@bp.route('/user/<string:username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page',1,type=int)
    posts = user.posts.paginate(page,current_app.config["POSTS_PER_PAGE"], False)
    next_url = url_for('main.user',username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.user',username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("user.html",posts=posts.items,user=user,
    next_url=next_url,prev_url=prev_url)

@bp.route("/edit_profile",methods=["Get","Post"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved")
        return redirect(url_for("main.edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("edit_profile.html",form=form, title='Edit Profile')

@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('main.user', username=username))

@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('main.user', username=username))

@bp.route('/explore', methods=['GET'])
@login_required
def explore():
    page = request.args.get('page',1,type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page,
    current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html",title="Explore",posts=posts.items)

@bp.route('/send_message/<string:recipient>', methods=['GET','POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
          body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash("your message just sent")
        return redirect(url_for('main.send_message',recipient=recipient))
    return render_template("send_message.html",form=form,recipient=recipient)

@bp.route('/messages', methods=['Get'])
@login_required
def messages():
    current_user.last_read_mesage_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get("page",1,type=int)
    messages = current_user.messages_recieved.order_by(
    Message.timestamp.desc()).paginate(
        page, current_app.config["POSTS_PER_PAGE"], False)
    next_url = url_for("main.messages",page=mesages.next_num) if \
        messages.has_next else None
    prev_url = url_for("main.messages",page=messages.prev_num) if \
        messages.has_prev else None
    return render_template("message.html", messages=messages.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])
