from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from functools import wraps
import socket
import os
from werkzeug.utils import secure_filename
from PIL import Image 
from groq import Groq
# Инициализация приложения
# Initialize application
app = Flask(__name__)

# Секретный ключ для сессии (замените на свой сложный ключ)
# Secret key for session (replace with your own complex key)
app.secret_key = 'secret_key'  

# Данные администратора (храните в безопасном месте, например, в переменных окружения)
# Admin credentials (store in a secure place, like environment variables)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'

# API ключ непосредственно в коде
client = Groq(api_key="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")


@app.route('/botai')
def botai():
    return render_template('botai.html')


@app.route('/pokupka')
def pokupka():
    return render_template('pokupka.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    data = request.json
    user_text = data.get('text', '')
    print(f"Received text: {user_text}")  # Отладочный вывод
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Ты - русскоязычный ассистент. Всегда отвечай на русском языке."},
                {"role": "user", "content": user_text}
            ],
            model="llama3-8b-8192",
        )
        
        response = chat_completion.choices[0].message.content
        print(f"Groq response: {response}")  # Отладочный вывод
        return jsonify({"response": response})
    except Exception as e:
        print(f"Error in process_audio: {str(e)}")  # Отладочный вывод
        return jsonify({"response": f"Произошла ошибка: {str(e)}"}), 500



# Функция-декоратор для проверки авторизации
# Decorator function to check authorization
def admin_required(f):
    # Декоратор, который принимает функцию f (например, обработчик маршрута)
    @wraps(f)  # Сохраняем информацию о функции f
    def decorated_function(*args, **kwargs):
        # Вложенная функция, которая будет вызываться вместо функции f
        # *args и **kwargs позволяют передавать любые аргументы функции f
        # Проверяем, есть ли у пользователя права администратора
        if not session.get('is_admin'):
            # Если прав нет, отображаем сообщение об ошибке
            flash('Требуется авторизация администратора', 'error')
            # Перенаправляем пользователя на страницу входа
            return redirect(url_for('login'))
        # Если у пользователя есть права администратора, вызываем оригинальную функцию f
        return f(*args, **kwargs)
    # Возвращаем новую функцию с добавленной логикой проверки
    return decorated_function

# Конфигурация базы данных
# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Добавляем миграции

# Конфигурация для загрузки файлов
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Создаем папку для загрузок, если её нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Функция для проверки допустимого расширения файла
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Модель для хранения постов блога
# Model for storing blog posts
class Post(db.Model):
    # Уникальный идентификатор поста
    # Unique post identifier
    id = db.Column(db.Integer, primary_key=True)
    
    # Заголовок поста (максимум 100 символов)
    # Post title (maximum 100 characters)
    title = db.Column(db.String(100), nullable=False)
    
    image = db.Column(db.String(255), nullable=True)
    # Содержание поста
    # Post content
    content = db.Column(db.Text, nullable=False)

    # Цена товара
    price = db.Column(db.String(50), nullable=True)
    
    # Дата создания поста
    # Post creation date
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Post {self.title}>'

# Модель для хранения данных клиентов
# Model for storing client data
class Clients(db.Model):
    __tablename__ = 'clients'  # Указываем имя таблицы (необязательно, но рекомендовано)
    
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор клиента
    name = db.Column(db.String(100), nullable=False)  # Имя клиента
    phone = db.Column(db.String(20), nullable=False)  # Номер телефона клиента
    ip = db.Column(db.String(45), nullable=False, default='0')  # IP по умолчанию '0'
    order = db.Column(db.String(255), nullable=False)  # Заказ клиента
    date = db.Column(db.DateTime, default=datetime.utcnow)  # Дата заказа

    def __repr__(self):
        return f'<Client {self.name}>'


    def __repr__(self):
        return f'<Client {self.name}>'

# Маршруты / Routes
# Route for the home page
@app.route('/')
def home():
    # Получаем все посты, отсортированные по дате (новые сверху)
    # Get all posts sorted by date (newest first)
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

# Маршрут для страницы поста
# Route for the post page
@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)

# Маршрут для удаления поста
# Route for deleting a post
@app.route('/delete/<int:post_id>')
@admin_required
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Пост успешно удален', 'success')
    return redirect(url_for('home'))

# Маршрут для логина
# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('Вы успешно вошли в систему', 'success')
            return redirect(url_for('home'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('login.html')

# Маршрут для логаута
# Route for logout
@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('home'))

def resize_image(image_path):
    with Image.open(image_path) as img:
        # Максимальные размеры для превью
        MAX_WIDTH = 800
        MAX_HEIGHT = 600
        
        # Получаем размеры
        width, height = img.size
        
        # Вычисляем новые размеры, сохраняя пропорции
        if width > MAX_WIDTH or height > MAX_HEIGHT:
            ratio = min(MAX_WIDTH/width, MAX_HEIGHT/height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            # Изменяем размер
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Сохраняем с новым размером
            resized_img.save(image_path, quality=95, optimize=True)

# Маршрут для создания нового поста
# Route for creating a new post
@app.route('/create', methods=['GET', 'POST'])
@admin_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        price = request.form.get('price', type=str)  # type=int автоматически преобразует строку в число
        
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                file.save(file_path)
                resize_image(file_path)
                
                image_path = f"uploads/{unique_filename}"
        
        post = Post(title=title, content=content, image=image_path, price=price)
        db.session.add(post)
        db.session.commit()
        
        return redirect(url_for('home'))
    
    return render_template('create.html')


@app.route('/add_client', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name')  # Получаем имя из формы
        phone = request.form.get('phone')  # Получаем телефон из формы
        order = request.form.get('order')  # Получаем заказ из формы
        ip = request.remote_addr  # Получаем IP адрес клиента

        # Проверяем, что все обязательные поля заполнены
        if not name or not phone or not order:
            flash('Все поля обязательны для заполнения!', 'error')
            return redirect(url_for('add_client'))

        # Создаем объект клиента с данными из формы
        client = Clients(name=name, phone=phone, order=order, ip=ip)

        # Сохраняем клиента в базе данных
        db.session.add(client)
        db.session.commit()

        flash('Ваш запрос успешно отправлен! Мы свяжемся с вами в ближайшее время.', 'success')
        return redirect(url_for('home'))

    # Если метод GET, просто отображаем форму
    return render_template('add_client.html')  # Убедитесь, что у вас есть файл add_client.html


@app.route('/clients')
@admin_required
def clients():
    clients = Clients.query.order_by(Clients.date.desc()).all()
    return render_template('clients.html', clients=clients)


@app.route('/delete_client/<int:client_id>', methods=['POST'])
@admin_required
def delete_client(client_id):
    client = Clients.query.get(client_id)  # Получаем клиента по ID
    if client:
        db.session.delete(client)  # Удаляем клиента
        db.session.commit()  # Сохраняем изменения в базе данных
        flash('Клиент успешно удален!', 'success')
    else:
        flash('Клиент не найден!', 'error')
    return redirect(url_for('clients'))  # Перенаправляем обратно на страницу клиентов



# Запуск приложения
# Run the application
if __name__ == '__main__':
    # Создаем таблицы в базе данных
    # Create database tables
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
