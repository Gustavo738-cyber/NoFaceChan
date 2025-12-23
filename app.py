from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configura o banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nofacechan.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELO DO BANCO DE DADOS ---
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, default=0) # 0 se for tópico, ID do pai se for resposta
    nome = db.Column(db.String(50), default="Anônimo")
    titulo = db.Column(db.String(100))
    conteudo = db.Column(db.Text, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)

    def contar_respostas(self):
        return Post.query.filter_by(parent_id=self.id).count()

    def numero_na_thread(self):
        if self.parent_id == 0:
            return "OP"
        posicao = Post.query.filter(
            Post.parent_id == self.parent_id, 
            Post.id <= self.id
        ).count()
        return posicao

# Cria o banco de dados
with app.app_context():
    db.create_all()

# --- ROTAS ---

@app.route('/')
def index():
    topicos = Post.query.filter_by(parent_id=0).order_by(Post.data.desc()).all()
    total_mensagens = Post.query.count()
    return render_template('index.html', posts=topicos, total=total_mensagens)

@app.route('/thread/<int:post_id>')
def ver_thread(post_id):
    principal = Post.query.get_or_404(post_id)
    respostas = Post.query.filter_by(parent_id=post_id).order_by(Post.data.asc()).all()
    return render_template('thread.html', principal=principal, respostas=respostas)

@app.route('/comentario', methods=['POST'])
@app.route('/comentario/<int:parent_id>', methods=['POST'])
def criar_post(parent_id=0):
    nome_form = request.form.get('nome') or "Anônimo"
    titulo_form = request.form.get('titulo')
    conteudo_form = request.form.get('mensagem')

    # Sistema de Moderação (Sufixo Secreto)
    if "##admin123" in nome_form:
        nome_form = "Administrador"

    if conteudo_form:
        novo_post = Post(
            nome=nome_form, 
            titulo=titulo_form, 
            conteudo=conteudo_form,
            parent_id=parent_id
        )
        db.session.add(novo_post)
        db.session.commit()
    
    if parent_id == 0:
        return redirect(url_for('index'))
    else:
        return redirect(url_for('ver_thread', post_id=parent_id))

@app.route('/deletar/<int:post_id>')
def deletar_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Se deletar o post principal, deleta todas as respostas dele também
    if post.parent_id == 0:
        Post.query.filter_by(parent_id=post.id).delete()
    
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':

    app.run(debug=True)
    if __name__ == '__main__':
    # O Render precisa que o app aceite conexões de qualquer IP (0.0.0.0)
    app.run(host='0.0.0.0', port=5000)
