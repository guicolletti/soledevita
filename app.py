from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime
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
    return render_template('index.html')

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
                           INSERT INTO produtos (produto_nome, produto_preco, produto_desc, produto_tipo,
                                                 produto_avaliacao)
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
                       FROM produtos
                       WHERE produto_id = %s
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
                           SET produto_nome      = %s,
                               produto_preco     = %s,
                               produto_desc      = %s,
                               produto_tipo      = %s,
                               produto_avaliacao = %s
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

@app.route('/admin/produtos_deliv')
@admin_required
def admin_produtosdeliv():
    with Cursor() as cursor:
        cursor.execute('''
                       SELECT deliv_id, deliv_nome, deliv_desc, deliv_preco, deliv_tipo, deliv_avaliacao
                       FROM produtos_delivery
                       ''')
        result = cursor.fetchall()

    produtos_deliv = []
    for row in result:
        produtos_deliv.append({
            'id': row[0],
            'nome': row[1],
            'preco': row[3],
            'descricao': row[2],
            'tipo': row[4],
            'avaliacao': row[5]
        })
    return render_template('admin_delivprodutos.html', produtos_deliv=produtos_deliv)

@app.route('/admin/produtos_deliv/novo', methods=['GET', 'POST'])
@admin_required
def admin_novo_deliv_produto():
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
                           INSERT INTO produtos_delivery (deliv_nome, deliv_desc, deliv_preco, deliv_tipo, deliv_avaliacao)
                           VALUES (%s, %s, %s, %s, %s)
                           ''', (nome, descricao, preco, tipo, avaliacao))

        flash('Produto do delivery adicionado com sucesso!')
        return redirect(url_for('admin_produtosdeliv'))

    return render_template('admin_novo_delivproduto.html', tipos=tipos)

@app.route('/admin/produtos_deliv/editar/<int:produto_id>', methods=['GET', 'POST'])
@admin_required
def admin_editar_produto_deliv(produto_id):
    with Cursor() as cursor:
        cursor.execute('''
                       SELECT deliv_id, deliv_nome, deliv_desc, deliv_preco, deliv_tipo, deliv_avaliacao
                       FROM produtos_delivery
                       WHERE deliv_id = %s
                       ''', (produto_id,))
        row = cursor.fetchone()
        cursor.execute('SELECT tipo_id, tipo_nome FROM tipos')
        tipos = [{'id': row[0], 'nome': row[1]} for row in cursor.fetchall()]

    if not row:
        flash('Produto não encontrado.')
        return redirect(url_for('admin_produtosdeliv'))

    produto_deliv = {
        'id': row[0],
        'nome': row[1],
        'descricao': row[2],
        'preco': row[3],
        'tipo': row[4],
        'avaliacao': row[5]
    }

    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco']
        descricao = request.form['descricao']
        tipo = request.form['tipo']
        avaliacao = request.form['avaliacao']

        with Cursor() as cursor:
            cursor.execute('''
                           UPDATE produtos_delivery
                           SET deliv_nome=%s,
                               deliv_desc=%s,
                               deliv_preco=%s,
                               deliv_tipo=%s,
                               deliv_avaliacao=%s
                           WHERE deliv_id = %s
                           ''', (nome, descricao, preco, tipo, avaliacao, produto_id))

        flash('Produto atualizado com sucesso!')
        return redirect(url_for('admin_produtosdeliv'))

    return render_template('admin_editar_delivproduto.html', produto_deliv=produto_deliv, tipos=tipos)

@app.route('/admin/produtos_deliv/remover/<int:produto_id>')
@admin_required
def admin_remover_produto_deliv(produto_id):
    with Cursor() as cursor:
        cursor.execute('DELETE FROM produtos_delivery WHERE deliv_id = %s', (produto_id,))
    flash('Produto removido com sucesso!')
    return redirect(url_for('admin_produtosdeliv'))

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

@app.route('/admin/tipos/editar/<int:tipo_id>', methods=['GET', 'POST'])
@admin_required
def admin_editar_tipo(tipo_id):
    with Cursor() as cursor:
        cursor.execute('SELECT tipo_id, tipo_nome FROM tipos WHERE tipo_id = %s', (tipo_id,))
        row = cursor.fetchone()

    if not row:
        flash('Tipo não encontrado.')
        return redirect(url_for('admin_tipos'))

    tipo = {'id': row[0], 'nome': row[1]}

    if request.method == 'POST':
        novo_nome = request.form['tipo_nome']
        with Cursor() as cursor:
            cursor.execute('UPDATE tipos SET tipo_nome = %s WHERE tipo_id = %s', (novo_nome, tipo_id))
        flash('Tipo atualizado com sucesso!')
        return redirect(url_for('admin_tipos'))

    return render_template('admin_editar_tipo.html', tipo=tipo)

@app.route('/delivery')
@login_required
def delivery():
    return redirect(url_for('escolher_massa'))

@app.route('/delivery/massa', methods=['GET', 'POST'])
@login_required
def escolher_massa():
    with Cursor() as cursor:
        cursor.execute(
            "SELECT deliv_id, deliv_nome, deliv_desc, deliv_preco FROM produtos_delivery WHERE deliv_tipo = 1")
        massas = [{'id': r[0], 'nome': r[1], 'desc': r[2], 'preco': r[3]} for r in cursor.fetchall()]

    if request.method == 'POST':
        session['delivery_massa'] = request.form['massa_id']
        return redirect(url_for('escolher_molho'))

    return render_template('delivery_massa.html', massas=massas)

@app.route('/delivery/molho', methods=['GET', 'POST'])
@login_required
def escolher_molho():
    with Cursor() as cursor:
        cursor.execute(
            "SELECT deliv_id, deliv_nome, deliv_desc, deliv_preco FROM produtos_delivery WHERE deliv_tipo = 5")
        molhos = [{'id': r[0], 'nome': r[1], 'desc': r[2], 'preco': r[3]} for r in cursor.fetchall()]

    if request.method == 'POST':
        session['delivery_molho'] = request.form['molho_id']
        return redirect(url_for('escolher_bebida'))

    return render_template('delivery_molho.html', molhos=molhos)

@app.route('/delivery/bebida', methods=['GET', 'POST'])
@login_required
def escolher_bebida():
    with Cursor() as cursor:
        cursor.execute(
            "SELECT deliv_id, deliv_nome, deliv_desc, deliv_preco FROM produtos_delivery WHERE deliv_tipo = 4")
        bebidas = [{'id': r[0], 'nome': r[1], 'desc': r[2], 'preco': r[3]} for r in cursor.fetchall()]

    if request.method == 'POST':
        session['delivery_bebida'] = request.form['bebida_id']
        return redirect(url_for('confirmar_delivery'))

    return render_template('delivery_bebida.html', bebidas=bebidas)

@app.route('/delivery/confirmar', methods=['GET', 'POST'])
@login_required
def confirmar_delivery():
    massa_id = session.get('delivery_massa')
    molho_id = session.get('delivery_molho')
    bebida_id = session.get('delivery_bebida')

    if not (massa_id and molho_id and bebida_id):
        flash("Você precisa escolher massa, molho e bebida.")
        return redirect(url_for('escolher_massa'))

    with Cursor() as cursor:
        cursor.execute("SELECT deliv_id, deliv_nome, deliv_preco FROM produtos_delivery WHERE deliv_id IN (%s, %s, %s)",
                       (massa_id, molho_id, bebida_id))
        itens = cursor.fetchall()

    total = sum([i[2] for i in itens])

    if request.method == 'POST':
        carrinho = session.get('carrinho', [])
        carrinho.append({
            'tipo': 'delivery',
            'massa_id': massa_id,
            'molho_id': molho_id,
            'bebida_id': bebida_id,
            'nome': f"Prato Delivery ({itens[0][1]}, {itens[1][1]}, {itens[2][1]})",
            'preco': total,
            'quantidade': 1
        })
        session['carrinho'] = carrinho
        flash("Prato adicionado ao carrinho!")
        return redirect(url_for('carrinho'))

    return render_template('delivery_confirmar.html', itens=itens, total=total)

@app.route('/admin/tipos/remover/<int:tipo_id>')
@admin_required
def admin_remover_tipo(tipo_id):
    with Cursor() as cursor:
        cursor.execute('DELETE FROM tipos WHERE tipo_id = %s', (tipo_id,))
    flash('Tipo removido com sucesso!')
    return redirect(url_for('admin_tipos'))

@app.route('/admin/pedidos')
@admin_required
def admin_pedidos():
    with Cursor() as cursor:
        cursor.execute('''
            SELECT p.pedido_id, u.usuario_nome, p.pedido_status, 
                   p.pedido_prectotal, p.pedido_endentrega, p.pedido_data
            FROM pedidos p
            JOIN usuarios u ON p.usuario_id = u.usuario_id
            ORDER BY p.pedido_data DESC
        ''')
        pedidos = [
            {
                'id': row[0],
                'cliente': row[1],
                'status': row[2],
                'total': row[3],
                'endereco': row[4],
                'data': row[5]
            }
            for row in cursor.fetchall()
        ]

    return render_template('admin_pedidos.html', pedidos=pedidos)

@app.route('/admin/pedidos/finalizar/<int:pedido_id>')
@admin_required
def admin_finalizar_pedido(pedido_id):
    with Cursor() as cursor:
        cursor.execute('UPDATE pedidos SET pedido_status = %s WHERE pedido_id = %s',
                       ('Finalizado', pedido_id))
    flash('Pedido marcado como Finalizado!')
    return redirect(url_for('admin_pedidos'))

@app.route('/cardapio')
def cardapio():
    with Cursor() as cursor:
        cursor.execute('''
                       SELECT *
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
                           SELECT usuario_id, usuario_nome, usuario_senha
                           FROM usuarios
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

@app.route('/carrinho/adicionar/<int:produto_id>')
@login_required
def adicionar_carrinho(produto_id):
    with Cursor() as cursor:
        cursor.execute('SELECT produto_id, produto_nome, produto_preco FROM produtos WHERE produto_id = %s',
                       (produto_id,))
        produto = cursor.fetchone()

    if not produto:
        flash('Produto não encontrado.')
        return redirect(url_for('cardapio'))

    item = {
        'id': produto[0],
        'nome': produto[1],
        'preco': float(produto[2]),
        'quantidade': 1
    }

    carrinho = session.get('carrinho', [])

    for p in carrinho:
        if p.get('id') == item['id']:
            p['quantidade'] += 1
            break
    else:
        carrinho.append(item)

    session['carrinho'] = carrinho
    flash(f"{produto[1]} adicionado ao carrinho!")
    return redirect(url_for('cardapio'))

@app.route('/carrinho')
@login_required
def carrinho():
    carrinho = session.get('carrinho', [])
    total = sum(item['preco'] * item['quantidade'] for item in carrinho)
    return render_template('carrinho.html', carrinho=carrinho, total=total)

@app.route('/carrinho/remover/<int:index>')
@login_required
def remover_carrinho(index):
    carrinho = session.get('carrinho', [])
    if 0 <= index < len(carrinho):
        carrinho.pop(index)
    session['carrinho'] = carrinho
    flash('Item removido do carrinho.')

    return redirect(url_for('carrinho'))

@app.route('/finalizar-pedido')
@login_required
def finalizar_pedido():
    carrinho = session.get('carrinho', [])

    if not carrinho:
        flash("Seu carrinho está vazio.")
        return redirect(url_for('cardapio'))

    with Cursor() as cursor:
        cursor.execute("SELECT usuario_endereco FROM usuarios WHERE usuario_id = %s", (session['usuario_id'],))
        endereco = cursor.fetchone()[0]

        cursor.execute('''
            INSERT INTO pedidos (usuario_id, pedido_status, pedido_prectotal, pedido_endentrega)
            VALUES (%s, %s, %s, %s)
            RETURNING pedido_id
        ''', (
            session['usuario_id'],
            'Em andamento',
            sum(item['preco'] * item['quantidade'] for item in carrinho),
            endereco
        ))
        pedido_id = cursor.fetchone()[0]

        for item in carrinho:
            if item.get('tipo') == 'delivery':
                for pid in (item['massa_id'], item['molho_id'], item['bebida_id']):
                    cursor.execute('''
                        INSERT INTO itens_pedido (pedido_id, produto_id, itpedidos_qtde, itpedidos_precouni)
                        VALUES (%s, %s, %s, (
                            SELECT deliv_preco FROM produtos_delivery WHERE deliv_id = %s
                        ))
                    ''', (pedido_id, pid, 1, pid))
            else:
                cursor.execute('''
                    INSERT INTO itens_pedido (pedido_id, produto_id, itpedidos_qtde, itpedidos_precouni)
                    VALUES (%s, %s, %s, %s)
                ''', (pedido_id, item['id'], item['quantidade'], item['preco']))

    session['carrinho'] = []
    flash("Pedido finalizado com sucesso! Acesse seu perfil para ver os pedidos")

    return redirect(url_for('perfil_pedidos'))

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    with Cursor() as cursor:
        cursor.execute("SELECT usuario_nome, usuario_email, usuario_endereco FROM usuarios WHERE usuario_id = %s",
                       (session['usuario_id'],))
        usuario = cursor.fetchone()

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        endereco = request.form['endereco']
        senha = request.form.get('senha')

        with Cursor() as cursor:
            if senha:  # só atualiza senha se o usuário digitou
                cursor.execute('''
                    UPDATE usuarios
                    SET usuario_nome = %s, usuario_email = %s, usuario_endereco = %s, usuario_senha = crypt(%s, gen_salt('bf'))
                    WHERE usuario_id = %s
                ''', (nome, email, endereco, senha, session['usuario_id']))
            else:
                cursor.execute('''
                    UPDATE usuarios
                    SET usuario_nome = %s, usuario_email = %s, usuario_endereco = %s
                    WHERE usuario_id = %s
                ''', (nome, email, endereco, session['usuario_id']))

        flash("Perfil atualizado com sucesso!")
        return redirect(url_for('perfil'))

    return render_template('perfil.html', usuario=usuario)

@app.route('/perfil/pedidos')
@login_required
def perfil_pedidos():
    with Cursor() as cursor:
        cursor.execute('''
            SELECT pedido_id, pedido_status, pedido_prectotal, pedido_endentrega, pedido_data
            FROM pedidos
            WHERE usuario_id = %s
            ORDER BY pedido_data DESC
        ''', (session['usuario_id'],))
        pedidos = [
            {
                'id': row[0],
                'status': row[1],
                'total': row[2] or 0,
                'endereco': row[3],
                'data': row[4]
            }
            for row in cursor.fetchall()
        ]

    return render_template('perfil_pedidos.html', pedidos=pedidos)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)