from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from db_config import Cursor
from functools import wraps
import os

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para acessar esta página.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_autenticado'):
            flash('Acesso restrito ao administrador.')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('cadastro'))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.get_json()
        senha = data.get('senha')

        senha_correta = os.getenv("ADMIN_PASSWORD")

        if senha == senha_correta:
            session['admin_autenticado'] = True
            return jsonify({'autenticado': True})
        else:
            return jsonify({'autenticado': False})

    return render_template('admin_login.html')

@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/produtos')
@admin_required
def admin_produtos():
    with Cursor() as cursor:
        cursor.execute('''
            SELECT produto_id, produto_nome, produto_preco, produto_desc, produto_tipo, produto_avaliacao
            FROM produtos
        ''')
        result = cursor.fetchall()

    produtos = []
    for row in result:
        produtos.append({
            'id': row[0],
            'nome': row[1],
            'preco': row[2],
            'descricao': row[3],
            'tipo': row[4],
            'avaliacao': row[5]
        })
    return render_template('admin_produtos.html', produtos=produtos)

@app.route('/admin/produtos/novo', methods=['GET', 'POST'])
@admin_required
def admin_novo_produto():
    with Cursor() as cursor:
        cursor.execute('SELECT tipo_id, tipo_nome FROM tipos')
        tipos = [{'id': row[0], 'nome': row[1]} for row in cursor.fetchall()]

    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco']
        descricao = request.form['descricao']
        tipo = request.form['tipo']
        avaliacao = request.form['avaliacao']

        with Cursor() as cursor:
            cursor.execute('''
                INSERT INTO produtos (produto_nome, produto_preco, produto_desc, produto_tipo, produto_avaliacao)
                VALUES (%s, %s, %s, %s, %s)
            ''', (nome, preco, descricao, tipo, avaliacao))

        flash('Produto adicionado com sucesso!')
        return redirect(url_for('admin_produtos'))
    return render_template('admin_novo_produto.html', tipos=tipos)

@app.route('/admin/produtos/editar/<int:produto_id>', methods=['GET', 'POST'])
@admin_required
def admin_editar_produto(produto_id):
    with Cursor() as cursor:
        cursor.execute('SELECT tipo_id, tipo_nome FROM tipos')
        tipos = [{'id': row[0], 'nome': row[1]} for row in cursor.fetchall()]

        cursor.execute('''
            SELECT produto_nome, produto_preco, produto_desc, produto_tipo, produto_avaliacao
            FROM produtos WHERE produto_id = %s
        ''', (produto_id,))
        row = cursor.fetchone()

    if not row:
        flash('Produto não encontrado.')
        return redirect(url_for('admin_produtos'))

    produto = {
        'id': produto_id,
        'nome': row[0],
        'preco': row[1],
        'descricao': row[2],
        'tipo': row[3],
        'avaliacao': row[4]
    }

    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco']
        descricao = request.form['descricao']
        tipo = request.form['tipo']
        avaliacao = request.form['avaliacao']

        with Cursor() as cursor:
            cursor.execute('''
                UPDATE produtos
                SET produto_nome = %s, produto_preco = %s, produto_desc = %s,
                    produto_tipo = %s, produto_avaliacao = %s
                WHERE produto_id = %s
            ''', (nome, preco, descricao, tipo, avaliacao, produto_id))

        flash('Produto atualizado com sucesso!')
        return redirect(url_for('admin_produtos'))

    return render_template('admin_editar_produto.html', produto=produto, tipos=tipos)

@app.route('/admin/produtos/remover/<int:produto_id>')
@admin_required
def admin_remover_produto(produto_id):
    with Cursor() as cursor:
        cursor.execute('DELETE FROM produtos WHERE produto_id = %s', (produto_id,))
    flash('Produto removido com sucesso!')
    return redirect(url_for('admin_produtos'))

@app.route('/admin/tipos')
@admin_required
def admin_tipos():
    with Cursor() as cursor:
        cursor.execute('SELECT tipo_id, tipo_nome FROM tipos')
        result = cursor.fetchall()

    tipos = [{'id': row[0], 'nome': row[1]} for row in result]
    return render_template('admin_tipos.html', tipos=tipos)

@app.route('/admin/tipos/novo', methods=['POST'])
@admin_required
def admin_novo_tipo():
    tipo_nome = request.form['tipo_nome']
    with Cursor() as cursor:
        cursor.execute('INSERT INTO tipos (tipo_nome) VALUES (%s)', (tipo_nome,))
    flash('Tipo adicionado com sucesso!')
    return redirect(url_for('admin_tipos'))

@app.route('/admin/tipos/remover/<int:tipo_id>')
@admin_required
def admin_remover_tipo(tipo_id):
    with Cursor() as cursor:
        cursor.execute('DELETE FROM tipos WHERE tipo_id = %s', (tipo_id,))
    flash('Tipo removido com sucesso!')
    return redirect(url_for('admin_tipos'))

@app.route('/cardapio')
def cardapio():
    with Cursor() as cursor:
        cursor.execute('''
            SELECT * FROM produtos
        ''')
        result = cursor.fetchall()
    produtos = []
    for row in result:
        produtos.append({
            'id': row[0],
            'nome': row[1],
            'preco': row[2],
            'descricao': row[3],
            'tipo': row[4],
            'avaliacao': row[5]
        })
    return render_template('cardapio.html', produtos=produtos)


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        endereco = request.form['endereco']
        senha_hash = generate_password_hash(senha)

        with Cursor() as cursor:
            cursor.execute('SELECT * FROM usuarios WHERE usuario_email = %s', (email,))
            if cursor.fetchone():
                error = "E-mail já cadastrado."
                return render_template('cadastro.html', error=error)

            cursor.execute('''
                INSERT INTO usuarios (usuario_nome, usuario_email, usuario_senha, usuario_endereco)
                VALUES (%s, %s, %s, %s)
            ''', (nome, email, senha_hash, endereco))

        flash('Cadastro realizado com sucesso!')
        return redirect(url_for('login'))

    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        with Cursor() as cursor:
            cursor.execute('''
                SELECT usuario_id, usuario_nome, usuario_senha FROM usuarios
                WHERE usuario_email = %s
            ''', (email,))
            usuario = cursor.fetchone()

        if usuario and check_password_hash(usuario[2], senha):
            session['usuario_id'] = usuario[0]
            session['usuario_nome'] = usuario[1]
            flash('Login realizado com sucesso!')
            return redirect(url_for('cardapio'))
        else:
            flash('Email ou senha inválidos.')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)