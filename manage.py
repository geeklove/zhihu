#!/usr/bin/env python
# encoding=utf-8
import os
from app import create_app, db

from app.models import User,  Role, Permission, Items, Answer,  Follow, Upvote, FocusTagQues, PostTag, Comment,  Thank,Question,Article
from app.email import send_email
from app.decorators import admin_required, permission_required

from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from flask import Flask, url_for, flash,abort,render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

from flask_migrate import Migrate, MigrateCommand
from flask_moment import Moment

from flask_login import login_user, logout_user, login_required, \
    current_user
import jieba
from threading import Thread
from app.forms import AnswerForm,LoginForm,CommentForm,PostForm,QuestionForm,RegistrationForm,EditProfileForm,ChangeEmailForm, \
	ChangePasswordForm,PasswordResetRequestForm,PasswordResetForm

app = create_app('heroku')
manager = Manager(app)
migrate = Migrate(app, db)



def make_shell_context():
	return dict(app=app, db=db, User=User,  Role=Role,
	Permission=Permission, Post=Post)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

@app.route('/about/')
def about():
	return render_template('about.html')

@app.route('/manage/<int:types>/<int:id>')
def delete(types,id):
	if types == 0 and id == 0:
		page = request.args.get('page', 1, type=int)
		pagination = Items.query.order_by(Items.id.asc()).filter(Items.types == 0).paginate(
             		page, per_page=10, error_out=False)
		posts = pagination.items
		return render_template('manage.html', tag = 0, posts = posts, pagination = pagination)
	elif types == 1 and id == 0:
		page = request.args.get('page', 1, type=int)
		pagination = Items.query.order_by(Items.id.asc()).filter(Items.types == 1).paginate(
             		page, per_page=10, error_out=False)
		posts = pagination.items
		return render_template('manage.html', tag = 1, posts = posts, pagination = pagination)
	elif types == 2 and id == 0:
		page = request.args.get('page', 1, type=int)
		pagination = Items.query.order_by(Items.id.asc()).filter(Items.types == 2).paginate(
             		page, per_page=10, error_out=False)
		posts = pagination.items
		return render_template('manage.html', tag = 2, posts = posts, pagination = pagination)
	elif types == 3 and id == 0:
		page = request.args.get('page', 1, type=int)
		pagination = Comment.query.order_by(Comment.itemid.asc()).paginate(
             		page, per_page=10, error_out=False)
		posts = pagination.items
		return render_template('manage.html', tag = 3, posts = posts, pagination = pagination)
	p = Items.query.get(id)
	if types == 0 and p.types == 0:
		 p.deleted = 1^p.deleted
		 allans = Answer.query.filter(Answer.belongtoques == p.id).all()
		 for a in allans:
		 	dans = Items.query.filter(Items.ans_id == a.id).first()
		 	dans.deleted = 1^dans.deleted 
		 	db.session.add(dans)
		 	db.session.commit()
		 allcom = Comment.query.filter(Comment.itemid == p.id).all()
		 for a in allcom:
		 	a.deleted = 1^a.deleted
		 	db.session.add(a)
		 	db.session.commit()
		 if p.deleted == 1:
		 	flash(u'问题['+bytes(p.id)+u']及其相关的答案,评论都已删除')
		 else:
		 	flash(u'问题['+bytes(p.id)+u']及其相关的答案,评论都已恢复')
		 return redirect(url_for('delete',types =0,  id = 0))
	elif types == 1 and p.types == 1:
		 p = Items.query.get(id)
		 p.deleted = 1^p.deleted
		 allcom = Comment.query.filter(Comment.itemid == p.id).all()
		 for a in allcom:
		 	a.deleted = 1^a.deleted
		 	db.session.add(a)
		 	db.session.commit()
		 if p.deleted == 1:
		 	flash(u'文章['+bytes(p.id)+u']及其相关的评论都已删除')
		 else:
		 	flash(u'文章['+bytes(p.id)+u']及其相关的评论都已恢复')
		 return redirect(url_for('delete', types =1, id = 0))
	elif types == 2 and p.types == 2:
		p.deleted = 1^p.deleted
		allcom = Comment.query.filter(Comment.itemid == p.id).all()
		for a in allcom:
		 	a.deleted = 1^a.deleted 
		 	db.session.add(a)
		 	db.session.commit()
		if p.deleted == 1:
		 	flash(u'答案['+bytes(p.id)+u']及其相关的评论都已删除')
		else:
		 	flash(u'答案['+bytes(p.id)+u']及其相关的评论都已恢复')
		return redirect(url_for('delete', types =2,id = 0))	
	else :
		p = Comment.query.get(id)
		p.deleted = 1^p.deleted
		db.session.add(p)
		db.session.commit()
		if p.deleted == 1:
		 	flash(u'评论['+bytes(p.id)+u']已删除')
		else:
		 	flash(u'评论['+bytes(p.id)+u']已恢复')
		return redirect(url_for('delete', types =3, id = 0))






@app.route('/write_articles/',  methods=['GET', 'POST'])
def write_articles():
    if current_user.is_anony():
    	return render_template('403.html')
    form = PostForm()
    if request.method == 'POST' :
    	title = request.form.get('title')
    	body = request.form.get('body')
    	ar = Article(content = body) 
    	db.session.add(ar)
	db.session.commit()      
	ar = Article.query.filter_by(content = body).first()
	it = Items(title_or_ans = title,author_id = current_user.id, types=1, art_id = ar.id)         
	db.session.add(it)
	db.session.commit()   
       	return redirect(url_for('index'))         
    return render_template('write_articles.html', form=form)
	
@app.route('/followers/<int:id>')
def followers(id):
	f_all = Follow.query.filter_by(followed_id = id).all()
	f = []
	for ff in f_all:
		f.append(ff.follower_id)
	u = User.query.get(id)
	page = request.args.get('page', 1, type=int)
	pagination = User.query.filter(User.id.in_( f )).paginate(page, 3,error_out=False)
	u_all = pagination.items
	return render_template('followers.html', u = u, u_all = u_all, pagination = pagination)

@app.route('/follow_whom/<int:id>')
def follow_whom(id):
	f_all = Follow.query.filter_by(follower_id = id).all()
	f = []
	for ff in f_all:
		f.append(ff.followed_id)
	u = User.query.get(id)
	page = request.args.get('page', 1, type=int)
	pagination = User.query.filter(User.id.in_( f )).paginate(page, 3,error_out=False)
	u_all = pagination.items
	return render_template('follow_whom.html', u = u, u_all = u_all, pagination = pagination)

@app.route('/post_upvotes/<int:ansid>')
def post_upvotes(ansid):
	all_up = Upvote.query.filter_by(answerid = ansid).all()
	all_u = []
	for a in all_up:
		all_u.append(a.upvoter)
	page = request.args.get('page', 1, type=int)
	pagination = User.query.filter(User.id.in_( all_u )).paginate(page, 3,error_out=False)
	u = pagination.items
	ansid = ansid
	return render_template('post_upvotes.html', u = u, ansid = ansid, pagination = pagination)

@app.route('/thanks/<int:userid>/<int:postid>')
def thanks(userid, postid):
	if current_user.id == Items.query.get( postid).author_id:
		return render_template('not.html', text = u'您不能感谢自己的回答')
	t = Thank( personid = userid, postid = postid)
	db.session.add(t)
	db.session.commit()
	au = Items.query.get( postid).author
	au.thanks = au.thanks + 1
	db.session.add( au )
	db.session.commit()
	quesid = Items.query.get(postid).answer.belongtoques
	return redirect(url_for('question', id = quesid ))

@app.route('/cancel_thanks/<int:userid>/<int:postid>')
def cancel_thanks(userid, postid):
	t = Thank.query.filter( Thank.personid == userid).filter(Thank.postid == postid).first()
	db.session.delete(t)
	db.session.commit()
	au = Items.query.get(postid).author
	au.thanks = au.thanks -1
	db.session.add( au )
	db.session.commit()
	quesid = Items.query.get(postid).answer.belongtoques
	return redirect(url_for('question', id =quesid ))

@app.route('/raise_question/',  methods=['GET', 'POST'])
def raise_question():
    if current_user.is_anony():
    	return render_template('403.html')
    form = QuestionForm()   
    if request.method == 'POST' :
        	title = request.form.get('title')
        	body = request.form.get('body')
        	ques = Question(description = body)
        	db.session.add(ques)
        	db.session.commit()
        	q = Question.query.filter_by(description = body).first()
        	it = Items(title_or_ans = title,author_id = current_user.id, types=0, ques_id = q.id)                  	       
        	db.session.add(it)
        	db.session.commit() 
        	return redirect(url_for('index'))         
    return render_template('raise_question.html', form=form)

@app.route('/comment_on_article/<int:id>' ,  methods=['GET', 'POST'])
def comment_on_article(id):
	if current_user.is_anony():
    		return render_template('403.html')
	art = Items.query.get(id)	
	page = request.args.get('page', 1, type=int)
	pagination = Comment.query.filter(Comment.itemid == id,Comment.deleted==0 ).order_by(Comment.timestamp.desc()).paginate(page, 3,error_out=False)
	c = pagination.items
	cform = CommentForm()	
	if cform.validate_on_submit():
		co = Comment(content = cform.body.data, userid=current_user.id, itemid =id )		    
		db.session.add(co)
		db.session.commit()
		return redirect(url_for('comment_on_article',  id =id ))
	return render_template('comment_on_article.html', art = art, Permission = Permission, comments = c, \
		cform = cform, pagination = pagination )
	
@app.route('/comment_on_question/<int:id>' ,  methods=['GET', 'POST'])
def comment_on_question(id):
	if current_user.is_anony():
    		return render_template('403.html')
	ques = Items.query.get(id)	
	pc = Comment.query.filter_by(itemid = id).all()
	page = request.args.get('page', 1, type=int)
	pagination = Comment.query.filter(Comment.itemid == id, Comment.deleted==0).order_by(Comment.timestamp.desc()).paginate(page, 3,error_out=False)
	c = pagination.items
	cform = CommentForm()	
	if cform.validate_on_submit():
		co = Comment(content = cform.body.data, userid=current_user.id, itemid =id )		    
		db.session.add(co)
		db.session.commit()
		return redirect(url_for('comment_on_question',  id =id ))
	return render_template('comment_on_question.html', ques = ques, Permission = Permission, comments = c, \
		cform = cform, pagination = pagination )

@app.route('/comment_on_answer/<int:quesid>/<int:id>' ,  methods=['GET', 'POST'])
def comment_on_answer(quesid, id):
	if current_user.is_anony():
    		return render_template('403.html')
	ques = Items.query.filter_by(id = quesid).first()
	ans = Items.query.filter_by(id = id).first()
	page = request.args.get('page', 1, type=int)
	pagination = Comment.query.filter(Comment.itemid == id, Comment.deleted==0).order_by(Comment.timestamp.desc()).paginate(page, 3,error_out=False)
	c = pagination.items
	cform = CommentForm()
	if cform.validate_on_submit():
		co = Comment(content = cform.body.data, itemid = id, userid =current_user.id )		    
		db.session.add(co)
		db.session.commit()
		return redirect(url_for('comment_on_answer', quesid = quesid, id =id ))
	return render_template('comment_on_answer.html', ques = ques, Permission = Permission, \
		comments = c, cform = cform, pagination = pagination, a =ans)
	
@app.route('/user/<int:id>')
def user(id):
	u = User.query.filter_by(id = id).first()
	follow = Follow.query.all()
	l = 0
	r = 0
	for f in follow:
		if f.follower_id == u.id:
			l = l+1
		elif f.followed_id == u.id:
			r = r+1
	page = request.args.get('page', 1, type=int)
	pagination = Items.query.order_by(Items.timestamp.desc()).filter(Items.types == 2, Items.author_id == id, Items.deleted ==0).paginate(
             	page, per_page=10, error_out=False)
	allans = pagination.items
	ques = Items.query.filter(Items.types == 0, Items.deleted ==0).all()
	return render_template('user.html', user = u, Permission = Permission, l =l, r =r,allans = allans, ques = ques, pagination = pagination)

@app.route('/user/<int:id>/<int:tag>')
def user1(id, tag):
	u = User.query.filter_by(id = id).first()
	follow = Follow.query.all()
	l = 0
	r = 0
	for f in follow:
		if f.follower_id == u.id:
			l = l+1
		elif f.followed_id == u.id:
			r = r+1
	if tag == 1:
		page = request.args.get('page', 1, type=int)
		pagination = Items.query.order_by(Items.timestamp.desc()).filter(Items.types == 1, Items.author_id == id,Items.deleted ==0).paginate(
             		page, per_page=10, error_out=False)
		art = pagination.items
		return render_template('user1.html', user = u, Permission = Permission, l =l, r =r,art = art, pagination = pagination)
	if tag == 0:
		page = request.args.get('page', 1, type=int)
		pagination = Items.query.order_by(Items.timestamp.desc()).filter(Items.types == 0, Items.author_id == id,Items.deleted ==0).paginate(
             		page, per_page=10, error_out=False)
		art = pagination.items
		return render_template('user2.html', user = u, Permission = Permission, l =l, r =r,art = art, pagination = pagination)
	if tag == 2:
		all_u = Upvote.query.filter(Upvote.upvoter == id, Upvote.descr ==2).all()
		all_p = []
		for uu in all_u:
			all_p.append(uu.answerid)
		page = request.args.get('page', 1, type=int)
		pagination = Items.query.filter(Items.id.in_(all_p), Items.deleted ==0).paginate(\
             		page, per_page=10, error_out=False)  
    		allans = pagination.items
    		allans.sort(key = lambda x: x.timestamp, reverse = True)
    		ques = Items.query.filter(Items.types == 0, Items.deleted ==0).all()
		return render_template('user3.html', user = u, Permission = Permission, l =l, r =r,allans = allans, ques = ques, pagination = pagination)

	if tag == 3:
		all_f = FocusTagQues.query.filter(FocusTagQues.personid == id).all()
		all_p = []
		for f in all_f:
			all_p.append(f.focusedid)
		page = request.args.get('page', 1, type=int)
		pagination = Items.query.filter(Items.id.in_(all_p), Items.deleted ==0).paginate(\
             		page, per_page=10, error_out=False)  
    		allans = pagination.items
    		allans.sort(key = lambda x: x.timestamp, reverse = True)
		return render_template('user4.html', user = u, Permission = Permission, l =l, r =r,allans = allans, pagination = pagination)

@app.route('/upvote/<int:quesid>/<int:id>')
def upvote( quesid, id):
    if current_user.is_anony():
    	return render_template('403.html')
    ans = Items.query.get(id)
    if ans.author_id == current_user.id:
    	return render_template('not.html',text = u'您不能对自己的回答点赞')
    u=Upvote.query.filter(Upvote.upvoter == current_user.id ).filter(Upvote.answerid == id).first()
    if u is None:
    	ans = Items.query.filter_by(id = id).first().answer
    	it = Items.query.filter_by(id = id).first()
    	ans.upvote = ans.upvote + 1
    	us = User.query.filter_by(id = it.author_id).first()    	
    	us.ups = us.ups + 1    
    	up = Upvote(upvoter = current_user.id, answerid = id, descr=2)
    	db.session.add(ans)
    	db.session.add(us)    	
    	db.session.add(up)  
	db.session.commit()
    	return redirect(url_for('question', id = quesid ))
    else:
    	ans = Items.query.filter_by(id = id).first().answer
    	it = Items.query.filter_by(id = id).first()
    	if u.descr == 2:
    		ans.upvote = ans.upvote - 1
    		us = User.query.get( it.author_id)   	
    		us.ups = us.ups - 1    
    		up = Upvote.query.filter(Upvote.upvoter == current_user.id).filter( Upvote.answerid == id).filter(Upvote.descr == 2).first()    		
    		db.session.delete(up) 
    	elif u.descr == 0:
    		ans.upvote = ans.upvote + 1
    		ans.downvote = ans.downvote - 1
    		us = User.query.filter_by(id = it.author_id).first()    	
    		us.ups = us.ups + 1    
    		up = Upvote.query.filter(Upvote.upvoter == current_user.id).filter( Upvote.answerid == id).filter(Upvote.descr == 0).first()
    		up.descr = 2
    		db.session.add(up) 
    	db.session.add(ans)
    	db.session.add(us)   	
    	db.session.commit()
    	return redirect(url_for('question', id = quesid ))
    

@app.route('/downvote/<int:quesid>/<int:id>')
def downvote(quesid, id):
	if current_user.is_anony():
    		return render_template('403.html')
    	ans = Items.query.get(id)
    	if ans.author_id == current_user.id:
    		return render_template('not.html',text = u'您不能对自己的回答点反对')
	u=Upvote.query.filter(Upvote.upvoter == current_user.id ).filter(Upvote.answerid == id).first()
	if u is None:
    		ans = Items.query.filter_by(id = id).first().answer
    		it = Items.query.filter_by(id = id).first()
    		ans.downvote = ans.downvote + 1
    		us = User.query.filter_by(id = it.author_id).first()	
		up = Upvote(upvoter = current_user.id, answerid = id, descr = 0) 
    		db.session.add(ans)    		
    		db.session.add(up)  
		db.session.commit()
    		return redirect(url_for('question', id = quesid ))
	else:
    		ans = Items.query.filter_by(id = id).first().answer
    		it = Items.query.filter_by(id = id).first()
    		if u.descr == 0:
    			ans.downvote = ans.downvote - 1    		  	
			up = Upvote.query.filter(Upvote.upvoter == current_user.id).filter( Upvote.answerid == id).filter(Upvote.descr == 0).first()    		
    			db.session.delete(up)    			
		elif u.descr == 2:
    			ans.upvote = ans.upvote - 1
    			ans.downvote = ans.downvote +1
    			us = User.query.filter_by(id = it.author_id).first()    	
    			us.ups = us.ups - 1    
    			up = Upvote.query.filter(Upvote.upvoter == current_user.id).filter( Upvote.answerid == id).filter(Upvote.descr == 2).first()
    			up.descr = 0
    			db.session.add(up)
    			db.session.add(us)    
    		db.session.add(ans)    		
    		db.session.commit()
    		return redirect(url_for('question', id = quesid ))


@app.route('/about_the_tag/<int:id>',  methods=['GET', 'POST'])
def about_the_tag(id):
	if current_user.is_anony():
		return render_template('403.html')
	pt = PostTag.query.filter(PostTag.tagid == id).all()
	ques_ = []
	for p in pt:
		ques_.append(p.postid)
	ques = Items.query.filter(Items.id.in_(ques_),Items.deleted ==0).all()
	tag = Items.query.filter_by(id = id).first()
    	return render_template('topic.html',ques=ques, tag=tag)

@app.route('/article/<int:id>',  methods=['GET', 'POST'])
def article(id):	
    art = Items.query.filter_by(id = id).first()
    return render_template('article.html', art = art)

@app.route('/question_for_anonymous/<int:id>',  methods=['GET', 'POST'])
def question_for_anonymous(id):
     ques = Items.query.filter_by(id = id).first()
     ansform = AnswerForm()
     ans_ = Answer.query.filter(Answer.belongtoques == id).all()
     ans_id_ = []
     for a in ans_:
        ans_id_.append(a.id)
     ans = Items.query.filter(Items.types == 2).filter(Items.ans_id.in_( ans_id_ )).all() 	
     pt  = PostTag.query.filter_by(postid = id).all()
     the_ques_tags_id = []
     related = []
     for p in pt:
         the_ques_tags_id.append( p.tagid )
     the_ques_tags = Items.query.filter(Items.id.in_( the_ques_tags_id )).all()
     rposts_rcds = PostTag.query.filter(PostTag.tagid.in_( the_ques_tags_id )).all()
     ansnum = Answer.query.filter(Answer.belongtoques == id).count()
     for r in rposts_rcds:
    	related.append(r.postid)
     related = list(set(related))
     if len(related) != 0:
    	related.remove(id)
    	rposts = Items.query.filter(Items.id.in_( related )).all()
     else:
    	rposts = []
     
     return render_template('questions.html', ques = ques, form = ansform, Permission = Permission, \
    	ans = ans,  tags= the_ques_tags, ansnum = ansnum, rposts = rposts)  

@app.route('/question/<int:id>',  methods=['GET', 'POST'])
def question(id):
    if current_user.is_anony():
        return redirect(url_for('question_for_anonymous', id = id))	
    ques = Items.query.filter(Items.id == id, Items.deleted ==0).first()
    ansform = AnswerForm()
    if ansform.validate_on_submit():
    	allans = Answer.query.filter_by(belongtoques = id).all()
    	for a in allans:
    		p = Items.query.filter_by(ans_id=a.id).first()
    		if p.author_id == current_user.id:
    			return render_template('not.html', text = u'您不能回答同一个问题两次')
    	ans = Answer(belongtoques = id)
    	db.session.add(ans)
    	db.session.commit()
    	a = Answer.query.order_by(Answer.id.desc()).filter_by(belongtoques = id).first()
	e = Items(title_or_ans = ansform.answer.data, author_id = current_user.id,  types =2, ans_id = a.id)        
	db.session.add(e)   
	db.session.add(a) 
	db.session.commit()
    ansnum = Answer.query.filter(Answer.belongtoques == id).count()
    allans = Answer.query.filter(Answer.belongtoques == id).all()
    for a in allans:
    	if Items.query.filter_by(ans_id = a.id).first().deleted == 1:
    		ansnum = ansnum -1
    ans_ = Answer.query.filter(Answer.belongtoques == id).all()
    ans_id_ = []
    ansdo = []
    for a in ans_:
    	ans_id_.append(a.id)
    ans = Items.query.filter(Items.types == 2, Items.deleted ==0).filter(Items.ans_id.in_( ans_id_ )).all()
    ans_id = []
    for a in ans:
    	ans_id.append(a.id)
    i_do_to_the_ans = Upvote.query.filter(Upvote.upvoter == current_user.id).filter(Upvote.answerid.in_( ans_id )).all()
    for i in i_do_to_the_ans:
    	if Items.query.get(i.answerid).deleted ==0:
    	 	ansdo.append((i.answerid, i.descr))
    pt = PostTag.query.filter_by(postid = id).all()
    the_ques_tags_id = []
    related = []
    for p in pt:
    	the_ques_tags_id.append( p.tagid )
    the_ques_tags = Items.query.filter(Items.id.in_( the_ques_tags_id )).all()
    rposts_rcds = PostTag.query.filter(PostTag.tagid.in_( the_ques_tags_id )).all()
    for r in rposts_rcds:
    	related.append(r.postid)
    related = list(set(related))
    if len(related) != 0:
    	related.remove(id)
    	rposts = Items.query.filter(Items.id.in_( related ), Items.deleted ==0).all()
    else:
    	rposts = []
    thank = []
    thank_ = Thank.query.filter(Thank.personid == current_user.id).filter(Thank.postid.in_( ans_id) ).all()
    for t in thank_:
    	thank.append(t.postid)
    return render_template('question.html', ques = ques, form = ansform, Permission = Permission, \
    	ans = ans, ansdo = ansdo, tags= the_ques_tags, ansnum = ansnum, rposts = rposts, thank = thank)
    	

   
filters = {  
     Items.types <2
}
filters2 = {  
     Items.types >= 1
}
filters3 = {  
     Items.types >= 1
}

@app.route('/edit_tags/<int:id>',  methods=['GET', 'POST'])
def edit_tags(id):
	if current_user.is_anony():
    		return render_template('403.html')	
	ques = Items.query.get(id)   
    	pt = PostTag.query.filter(PostTag.postid == id).all()
    	ptnum = PostTag.query.filter(PostTag.postid == id).count()
    	taglist=[]
    	for p in pt:
    		taglist.append(p.items_.title_or_ans)
    	while(  len(taglist) <3):
    		taglist.append('')
	tagval1 = taglist[0]
	tagval2 = taglist[1]
	tagval3 = taglist[2]
	if request.method == 'POST' :
		thesetags = []
		tagval1 = request.form.get('tag1', '???') 
		tagval2 = request.form.get('tag2', '???') 
		tagval3 = request.form.get('tag3', '???') 
		thesetags.append( tagval1)
		thesetags.append( tagval2 )
		thesetags.append( tagval3)
		PostTag.query.filter(PostTag.postid == id).delete()
		db.session.commit()
		for t in thesetags:
			if t != '???' and t.strip()!='' :
				existing_tag = Items.query.filter(Items.types == 3).filter(Items.title_or_ans == t).first()
				if existing_tag is None: 
					p = Items(title_or_ans = t, types = 3)
					db.session.add(p)
					db.session.add(p)
					new_tag = Items.query.filter(Items.types == 3).filter(Items.title_or_ans == t).first()
					pt = PostTag(postid = id, tagid = new_tag.id )
					db.session.add(pt)
					db.session.commit()
				else:
					old_tag = Items.query.filter(Items.types == 3).filter(Items.title_or_ans == t).first()
					pt = PostTag(postid = id, tagid = old_tag.id )
					db.session.add(pt)
					db.session.commit()
		return redirect(url_for('question', id = ques.id ))
	return render_template('edit_tags.html', tagval1 = tagval1, tagval2 = tagval2, tagval3 = tagval3, ques = ques,\
		 Permission = Permission) 
		


@app.route('/',  methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Items.query.filter( Items.types <2 ,Items.deleted ==0).order_by(Items.timestamp.desc()).paginate(
             page, per_page=10, error_out=False)
    title = pagination.items
    return render_template('index.html', title = title, pagination=pagination, data = '')


@app.route('/focus/')
def focus():
    if current_user.is_anony():
    	return render_template('403.html')    
    page = request.args.get('page', 1, type=int)
    follow = current_user.followed.all()   
    focusid = []
    for i in follow:
    	focusid.append( i.followed_id )
    all_p = Items.query.filter(Items.author_id.in_(focusid)).filter(Items.types <= 2).all()
    all_p_id = []
    for a in all_p:
    	all_p_id.append(a.id)

    ftq = FocusTagQues.query.filter(FocusTagQues.personid.in_(focusid)).all()
    upt = Upvote.query.filter(Upvote.upvoter.in_(focusid)).all()
    dic = {}
    dicvote = {}
    for f in ftq:
    	if f.focusedid not in all_p_id:
     		value = dic.get(f.focusedid, 'empty')
     		if value == 'empty':
     			tmp = []
     			tmp.append(f.personid)
     			dic[f.focusedid] = tmp

     		else:
     			tmp = dic[f.focusedid]
     			tmp.append(f.personid)
     			dic[f.focusedid] = tmp
    for u in upt:
     	if u.answerid not in all_p_id:
     		value = dicvote.get(u.answerid, 'empty')
     		if value == 'empty':
     			tmp = []
     			tmp.append(u.upvoter)
     			dicvote[u.answerid] = tmp
     		else:
     			tmp = dicvote[u.answerid]
     			tmp.append(u.upvoter)
     			dicvote[u.answerid]= tmp

    all = []
    for a in all_p:
     	all.append(a.id)
    for a in ftq:
     	all.append(a.focusedid)
    for a in upt:
     	all.append(a.answerid)
    all = list(set(all))
    all.sort()
    pagination = Items.query.filter(Items.id.in_(all), Items.deleted ==0).paginate(\
             page, per_page=10, error_out=False)  
    posts = pagination.items
    posts.sort(key = lambda x: x.timestamp, reverse = True)
    u = User.query.filter(User.id.in_(focusid)).all()
    ques = Items.query.filter(Items.types == 0, Items.deleted ==0).all()
    return render_template('focus.html', posts = posts,  pagination=pagination,  u = u, dic = dic, dicvote =dicvote, ques = ques)

@app.route('/search_results/',  methods=['GET', 'POST'])
def search_results():
    all = []
    datas = ''
    ques = Items.query.filter(Items.types == 0, Items.deleted ==0).all()
    if request.method == 'POST' and request.form.get('search', '???') is not '???':
    	data = request.form.get('search')
    	datas = data    	
	sl = jieba.lcut( data, cut_all=True )
	allposts = Items.query.order_by(Items.id.asc()).all()
	for p in allposts:
		pbody = p.title_or_ans
		if not (pbody is None or isinstance(pbody,int) or pbody.isdigit() or p.types ==3 ):
			pbodycut = jieba.lcut( pbody, cut_all=True )
			for pside in pbodycut:
				for s in sl:
					if pside == s:
						all.append(p.id)
	for p in allposts:
	    if p.types != 0:
	        continue
            pdescr = p.question.description           
            if not ( pdescr is None or isinstance(pdescr,int) or  pdescr.isdigit()  ):
                pdescr = (p.question.description)
                pdescrcut = jieba.lcut( pdescr, cut_all=True )
                for pside in pdescrcut:
                    for s in sl:
                        if pside == s:
                            all.append(p.id)
    for p in allposts:
        if p.types !=1:
            continue
        elif p.types == 1:
            pans = (p.article.content)
            if not ( pans is None or isinstance(pans,int) or  pans.isdigit() ):
                panscut = jieba.lcut( pans, cut_all=True )
                for pside in panscut:
                    for s in sl:
                        if pside == s:
                            all.append(p.id)
    ansall = []
    all = list(set(all))
    all.sort()
    page = request.args.get('page', 1, type=int)
    pagination = Items.query.filter(Items.id.in_( all ), Items.deleted ==0 ).paginate(\
             	page, per_page=10, error_out=False)
    posts = pagination.items
    posts.sort(key = lambda x: x.timestamp, reverse = True)
    tpc = Items.query.filter(Items.types == 3, Items.title_or_ans == datas).first()
    if tpc is not None:
        posts.insert(0,tpc)
    return render_template('search.html', posts = posts, pagination=pagination, ques = ques, data = data)



@app.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('index'))
    if current_user.confirm(token):
        flash(u'您已经确认了账户,感谢!')
    else:
        flash(u'确认链接无效或已经失效')
    return redirect(url_for('index'))



@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
	form = EditProfileForm()
	if form.validate_on_submit():
		current_user.name = form.name.data
		current_user.location = form.location.data
		current_user.about_me = form.about_me.data
		db.session.add(current_user)		
		return redirect(url_for('user', id =current_user.id))
	form.name.data = current_user.name
	form.location.data = current_user.location
	form.about_me.data = current_user.about_me
	return render_template('edit_profile.html', form=form)



@app.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash(u'您的邮箱已被更新.')
    else:
        flash(u'无效的请求')
    return redirect(url_for('index'))

@app.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, u'确认您的邮箱',
                       'change_email',
                       user=current_user, token=token)
            flash(u'一封带有确认链接的邮件已经发往您的新邮箱,请查阅确认.')
            return redirect(url_for('index'))
        else:
            flash(u'无效的邮箱或密码')
    return render_template("change_email0.html", form=form)




@app.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, u'重置您的密码',
                       'reset_password',
                       user=user, token=token)
        flash(u'一封带有重置密码链接的邮件已发往您的邮箱')
        return redirect(url_for('login'))
    return render_template('reset_password0.html', form=form)



@app.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('index'))
        if user.reset_password(token, form.password.data):
            flash(u'您的密码已被更新')
            return redirect(url_for('login'))
        else:
            return redirect(url_for('index'))
    return render_template('reset_password0.html', form=form)


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash(u'您的密码已被更新')
            return redirect(url_for('index'))
        else:
            flash(u'密码不正确')
    return render_template("change_password.html", form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    name=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, u'确认您的账户',
                   'confirm', user=user, token=token)
        login_user(user)
        flash(u'一封带有确认链接的邮件已经发往您的邮箱,请使用本浏览器登录邮箱查阅,确认您的账户')
        return redirect(url_for('index'))
    return render_template('register.html', form=form)

@app.route('/login/',  methods=['GET', 'POST'])
def login():
    form = LoginForm()     
    if form.validate_on_submit():        
        user = User.query.filter_by(email = form.email.data).first()        
        if user is not None and user.verify_password(form.password.data):
        	login_user(user)
        	return redirect(url_for('index'))
        flash(u'您的用户名或密码不正确')
    return render_template('login.html', form=form)
      
@app.route('/logout/',  methods=['GET', 'POST'])
def logout():
	logout_user()
	return render_template('logout.html')


@app.route('/follow/<int:id>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(id):
    user = User.query.filter_by(id = id).first()
    if user is None:       
        return redirect(url_for('index'))
    if current_user.is_following(user):        
        return redirect(url_for('user', id = id))
    current_user.follow(user)
    return redirect(url_for('user', id = id))


@app.route('/unfollow/<int:id>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(id):
    user = User.query.filter_by(id=id).first()
    if user is None:
        return redirect(url_for('index'))
    if not current_user.is_following(user):
        return redirect(url_for('user', id=id))
    current_user.unfollow(user)
    return redirect(url_for('user', id = id))

@app.route('/follow_question_or_tag/<int:id>')
@login_required
def follow_question_or_tag(id):
	if current_user.is_anony():
    		return render_template('403.html')
	p = Items.query.filter_by(id =id).first()
	f = FocusTagQues(personid = current_user.id, focusedid = id)
	db.session.add(f)
	db.session.commit()
	if p.types == 0:
		return redirect(url_for('question', id = id ))
	return redirect(url_for('about_the_tag', id = id ))


@app.route('/unfollow_question_or_tag/<int:id>')
@login_required
def unfollow_question_or_tag(id):
	if current_user.is_anony():
    		return render_template('403.html')
	p = Items.query.filter_by(id =id).first()
	f = FocusTagQues.query.filter(FocusTagQues.personid == current_user.id).filter(FocusTagQues.focusedid == id).first()
	db.session.delete(f)
	db.session.commit()
	if p.types == 0:
		return redirect(url_for('question', id = id ))
	return redirect(url_for('about_the_tag', id = id ))


if __name__ == '__main__':
    manager.run()
 
    
