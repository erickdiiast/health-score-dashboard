"""
Upload direto para o GitHub via API
"""

import requests
import base64
import os

# Configuracoes - ALTERE AQUI
TOKEN = ""  # Coloque seu token do GitHub aqui
REPO_NOME = "health-score-dashboard"  # Nome do repositorio

ARQUIVOS = [
    "app.py",
    "requirements.txt", 
    "README.md",
    "static/style.css",
    "static/app.js",
    "templates/index.html",
]

def enviar_arquivo(token, repo, arquivo):
    """Envia um arquivo para o GitHub"""
    
    # Le o arquivo
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
    except:
        with open(arquivo, 'rb') as f:
            conteudo = f.read().decode('utf-8', errors='ignore')
    
    # Codifica em base64
    conteudo_b64 = base64.b64encode(conteudo.encode('utf-8')).decode('utf-8')
    
    # URL da API
    url = f"https://api.github.com/repos/erickdiiast/{repo}/contents/{arquivo}"
    
    # Headers
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Verifica se arquivo ja existe (para pegar SHA)
    response = requests.get(url, headers=headers)
    sha = None
    if response.status_code == 200:
        sha = response.json().get('sha')
    
    # Prepara dados
    data = {
        "message": "Atualizacao do dashboard - aba Clusters e filtros VIP",
        "content": conteudo_b64,
        "branch": "main"
    }
    if sha:
        data["sha"] = sha
    
    # Envia
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"OK: {arquivo}")
        return True
    else:
        print(f"ERRO {response.status_code}: {arquivo}")
        print(response.text)
        return False

def main():
    print("="*60)
    print("Upload para GitHub")
    print("="*60)
    
    if not TOKEN:
        print("\nERRO: Voce precisa configurar o TOKEN no arquivo.")
        print("\n1. Acesse: https://github.com/settings/tokens")
        print("2. Clique em 'Generate new token (classic)'")
        print("3. Marque a opcao 'repo'")
        print("4. Copie o token e cole na variavel TOKEN deste arquivo")
        return
    
    print(f"\nRepositorio: {REPO_NOME}")
    print(f"Arquivos: {len(ARQUIVOS)}")
    print("-"*60)
    
    sucessos = 0
    for arquivo in ARQUIVOS:
        if os.path.exists(arquivo):
            if enviar_arquivo(TOKEN, REPO_NOME, arquivo):
                sucessos += 1
        else:
            print(f"NAO ENCONTRADO: {arquivo}")
    
    print("-"*60)
    print(f"Concluido: {sucessos}/{len(ARQUIVOS)} arquivos enviados")
    print("="*60)

if __name__ == "__main__":
    main()
