# encoding=utf-8
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from wtforms.widgets import TextArea
from wtforms import StringField, SubmitField, TextAreaField, PasswordField
from .models import User


class AnswerForm(FlaskForm):
    answer = PageDownField(u'您的答案是:', validators=[Required()])  
    submit = SubmitField(u'提交')

class LoginForm(FlaskForm):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64),
        Email()])
    password = PasswordField(u'密码', validators=[Required()])  
    submit = SubmitField(u'确认')
    
class CommentForm(FlaskForm):
    body = StringField(u'在此输入你的评论:', validators=[Required()])  
    submit = SubmitField(u'提交')
	

class PostForm(FlaskForm):
    title = StringField(u'标题', widget=TextArea(), validators=[Required()])
    body = StringField(u'正文', widget=TextArea())

class QuestionForm(FlaskForm):
    title = StringField(u'问题名称', widget=TextArea(), validators=[Required()])
    body = StringField(u'问题描述', widget=TextArea())



class RegistrationForm(FlaskForm):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64),
                                           Email()])
    username = StringField(u'用户名', validators=[
        Required(), Length(1, 64)])
    password = PasswordField(u'密码', validators=[
        Required(), EqualTo('password2', message=u'两次密码输入必须相同.')])
    password2 = PasswordField(u'确认密码', validators=[Required()])
    submit = SubmitField(u'注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'邮箱已被注册')

    def validate_username(self, field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError(u'用户名已被使用')

class EditProfileForm(FlaskForm):
	name = StringField(u'名字', validators=[Length(0, 64)])
	location = StringField(u'来自', validators=[Length(0, 64)])
	about_me = TextAreaField(u'关于我')
	submit = SubmitField(u'提交')

class ChangeEmailForm(FlaskForm):
    email = StringField(u'新邮箱', validators=[Required(), Length(1, 64),
                                                 Email()])
    password = PasswordField(u'密码', validators=[Required()])
    submit = SubmitField(u'更新邮箱')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'邮箱已被使用')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(u'旧密码', validators=[Required()])
    password = PasswordField(u'新密码', validators=[
        Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField(u'确认密码', validators=[Required()])
    submit = SubmitField(u'更新密码')

class PasswordResetRequestForm(FlaskForm):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64),
                                             Email()])
    submit = SubmitField(u'重置密码')

class PasswordResetForm(FlaskForm):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField(u'新密码', validators=[
        Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField(u'确认密码', validators=[Required()])
    submit = SubmitField(u'重置密码')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(u'邮箱无效')

