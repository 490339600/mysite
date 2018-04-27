from django.shortcuts import render
from django.shortcuts import redirect
from . import models, forms
import hashlib
import datetime
from django.conf import settings
# Create your views here.


def hash_code(s, salt='mysite'):
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())
    return h.hexdigest()


def index(request):
    pass
    return render(request, 'login/index.html')


def login(request):
    if request.method == 'POST':
        login_form = forms.loginForm(request.POST)
        message = '请确认输入的信息是否正确!'
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            try:
                user = models.User.objects.get(name=username)
                if hash_code(password) != user.password:
                    message = '请输入正确的密码！'
                    return render(request, 'login/login.html', locals())
                if not user.is_confirm:
                    message = '该用户还未通过邮箱确认！'
                    return render(request, 'login/login.html', locals())
                request.session['user_name'] = username
                return redirect('/index/')
            except:
                message = '当前用户不存在！'
        return render(request, 'login/login.html', locals())
    login_form = forms.loginForm
    return render(request, 'login/login.html', locals())


def register(request):
    if request.method == "POST":
        register_form = forms.registerForm(request.POST)
        message = "请确认您输入的内容是否正确"
        if register_form.is_valid():
            username = register_form.cleaned_data['username']
            password = register_form.cleaned_data['password']
            password2 = register_form.cleaned_data['password2']
            email = register_form.cleaned_data['email']
            sex = register_form.cleaned_data['sex']
            if password != password2:
                message = "两次密码输入不一致！"
                return render(request, 'login/register.html', locals())
            else:
                same_username = models.User.objects.filter(name=username)
                same_email = models.User.objects.filter(email=email)
                if same_username:
                    message = '当前用户名已存在！'
                    return render(request, 'login/register.html', locals())
                if same_email :
                    message = "当前邮箱已注册！"
                    return render(request, 'login/register.html', locals())
                new_user = models.User.objects.create(name=username, password=hash_code(password), sex=sex, email=email)
                new_confirm = make_confirm(new_user)
                send_mail(email, new_confirm.code)
                return redirect('/login/')
        return render(request, 'login/register.html', locals())
    register_form = forms.registerForm
    return render(request, 'login/register.html', locals())


def logout(request):
    if request.session.get('user_name', None):
        request.session.flush()
    return redirect('/index/')


def send_mail(email, code):

    from django.core.mail import EmailMultiAlternatives

    subject = '来自wangyili的注册确认邮件'
    text_content = "感谢您的注册，如果您看到这条消息，说明您的邮箱服务器不提供HTML链接，请联系管理员！"
    html_content = '''<p>感谢您的注册<a href="http://{}/confirm/?code={}" target=blank>请点击此处</a></p>
                    <p>请点击站点链接完成注册确认</p>
                    <p>此链接有效期为{}天</p>'''.format('127.0.0.1:8000', code, settings.CONFIRM_DAYS)
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def make_confirm(user):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    code = hash_code(user.name, now)
    new_confirm = models.ConfirmString.objects.create(code=code, user=user,)
    return new_confirm


def confirm(request):
    code = request.GET.get('code', None)
    try:
        confirm = models.ConfirmString.objects.get(code=code)
    except:
        message = '无效的请求'
        return render(request, 'login/register.html', locals())

    now = datetime.datetime.now()
    c_time = confirm.c_time.replace(tzinfo=None)
    if now > c_time +datetime.timedelta(days=settings.CONFIRM_DAYS):
        confirm.user.delete()
        message = '您的邮件已过期，请重新注册!'
        return render(request, 'login/register.html', locals())
    else:
        confirm.user.is_confirm = True
        confirm.user.save()
        confirm.delete()
        message = '感谢确认，请使用账户登陆！'
        return render(request, 'login/login.html', locals())
