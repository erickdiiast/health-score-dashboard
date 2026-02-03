"""
Upload direto para o GitHub sem precisar do Git instalado
Usa a API do GitHub para criar o repositório e enviar os arquivos
"""

import requests
import base64
import json
import os
from pathlib import Path

# Arquivos a serem enviados
ARQUIVOS = {
    "app.py": "app.py",
    "requirements.txt": "requirements.txt", 
    "README.md": "README.md",
    "static/style.css": "static/style.css",
    "static/app.js": "static/app.js",
    "templates/index.html": "templates/index.html",
}


def ler_arquivo(caminho):
    """Lê o conteúdo de um arquivo"""
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        with open(caminho, 'rb') as f:
            return f.read().decode('utf-8', errors='ignore')


def criar_repo(token, nome_repo, descricao=""):
    """Cria um novo repositório no GitHub"""
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": nome_repo,
        "description": descricao,
        "private": False,
        "auto_init": False
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"✅ Repositório '{nome_repo}' criado com sucesso!")
        return response.json()["clone_url"]
    elif response.status_code == 422:
        print(f"ℹ️ Repositório '{nome_repo}' já existe. Usando ele...")
        return f"https://github.com/{requests.get('https://api.github.com/user', headers=headers).json()['login']}/{nome_repo}"
    else:
        print(f"❌ Erro ao criar repositório: {response.status_code}")
        print(response.json())
        return None


def criar_arquivo(token, dono, repo, caminho, conteudo, mensagem="Add file"):
    """Cria ou atualiza um arquivo no repositório"""
    url = f"https://api.github.com/repos/{dono}/{repo}/contents/{caminho}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Codifica o conteúdo em base64
    conteudo_b64 = base64.b64encode(conteudo.encode('utf-8')).decode('utf-8')
    
    # Verifica se o arquivo já existe
    response = requests.get(url, headers=headers)
    sha = None
    if response.status_code == 200:
        sha = response.json()["sha"]
    
    data = {
        "message": mensagem,
        "content": conteudo_b64
    }
    if sha:
        data["sha"] = sha
    
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"  ✅ {caminho}")
        return True
    else:
        print(f"  ❌ Erro em {caminho}: {response.status_code}")
        return False


def main():
    print("=" * 60)
    print("  Health Score Dashboard - Upload para GitHub")
    print("=" * 60)
    print()
    
    # Coleta informações
    print("📝 Informações necessárias:")
    print()
    
    token = input("1. Personal Access Token do GitHub:\n   (crie em: github.com/settings/tokens)\n   > ").strip()
    
    if not token:
        print("❌ Token é obrigatório!")
        return
    
    # Verifica o token
    headers = {"Authorization": f"token {token}"}
    response = requests.get("https://api.github.com/user", headers=headers)
    
    if response.status_code != 200:
        print("❌ Token inválido!")
        return
    
    usuario = response.json()["login"]
    print(f"   ✅ Logado como: {usuario}")
    print()
    
    nome_repo = input("2. Nome do repositório (ex: health-score-dashboard):\n   > ").strip()
    if not nome_repo:
        nome_repo = "health-score-dashboard"
    
    descricao = input("3. Descrição (opcional):\n   > ").strip()
    print()
    
    # Cria o repositório
    print("📦 Criando repositório...")
    repo_url = criar_repo(token, nome_repo, descricao)
    
    if not repo_url:
        return
    
    print()
    print("📤 Enviando arquivos...")
    
    # Envia cada arquivo
    base_path = Path(__file__).parent
    sucessos = 0
    falhas = 0
    
    for destino, origem in ARQUIVOS.items():
        caminho_completo = base_path / origem
        if caminho_completo.exists():
            conteudo = ler_arquivo(caminho_completo)
            if criar_arquivo(token, usuario, nome_repo, destino, conteudo, 
                           f"Adicionando {destino}"):
                sucessos += 1
            else:
                falhas += 1
        else:
            print(f"  ⚠️ Arquivo não encontrado: {origem}")
            falhas += 1
    
    print()
    print("=" * 60)
    if falhas == 0:
        print("✅ SUCESSO! Todos os arquivos enviados!")
    else:
        print(f"⚠️ Concluído: {sucessos} arquivos OK, {falhas} falhas")
    print()
    print(f"🔗 Seu repositório:")
    print(f"   https://github.com/{usuario}/{nome_repo}")
    print("=" * 60)
    print()
    input("Pressione Enter para sair...")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        input("\nPressione Enter para sair...")
