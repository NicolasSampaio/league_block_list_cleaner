import json
import requests
import random
import time
import pandas as pd

# Caminho para o arquivo JSON
json_path = "bloqueados.json"

# Ler e carregar o conteúdo do JSON
with open(json_path, "r", encoding="utf-8") as file:
    data = json.load(file)

# Exemplo: listar os nomes de usuários bloqueados
usuarios = data.get("usuariosBlock", [])
usuarios99 = random.sample(usuarios, 99)
print(f"Quantidade de elementos: {len(usuarios)}")

# Sua chave de API da Riot Games
API_KEY = 'RGAPI-885d73a7-bda1-47de-b305-ece183a6d643'

# Região do jogador (por exemplo, 'americas' para servidores das Américas)
REGION = 'americas'

# URL base da API
BASE_URL = f'https://{REGION}.api.riotgames.com'

# Variáveis para controle do rate limit
REQUEST_COUNT = 0  # Contador de requisições
LAST_REQUEST_TIME = time.time()  # Tempo da última requisição

# Lista para armazenar os dados de ranked
ranked_data = []

# Mapeamento dos tiers para ordenação
TIER_ORDER = {
    'IRON': 0,
    'BRONZE': 1,
    'SILVER': 2,
    'GOLD': 3,
    'PLATINUM': 4,
    'EMERALD': 5,
    'DIAMOND': 6,
    'MASTER': 7,
    'GRANDMASTER': 8,
    'CHALLENGER': 9
}

# Mapeamento das divisões para ordenação
RANK_ORDER = {
    'IV': 0,
    'III': 1,
    'II': 2,
    'I': 3
}

# 1. Obter o PUUID usando o Riot ID
def get_puuid(game_name, tagline):
    global REQUEST_COUNT, LAST_REQUEST_TIME

    # Verificar e aplicar o rate limit
    check_rate_limit()

    url = f'{BASE_URL}/riot/account/v1/accounts/by-riot-id/{game_name}/{tagline}'
    headers = {
        'X-Riot-Token': API_KEY
    }
    response = requests.get(url, headers=headers)
    
    REQUEST_COUNT += 1  # Incrementar o contador de requisições
    LAST_REQUEST_TIME = time.time()  # Atualizar o tempo da última requisição

    if response.status_code == 200:
        return response.json()['puuid']  # Retorna o PUUID
    else:
        print(f"Erro ao obter PUUID: {response.status_code}")
        return None

# 2. Obter o encryptedSummonerId usando o PUUID
def get_summoner_id(puuid):
    global REQUEST_COUNT, LAST_REQUEST_TIME

    # Verificar e aplicar o rate limit
    check_rate_limit()

    url = f'https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}'
    headers = {
        'X-Riot-Token': API_KEY
    }
    response = requests.get(url, headers=headers)
    
    REQUEST_COUNT += 1  # Incrementar o contador de requisições
    LAST_REQUEST_TIME = time.time()  # Atualizar o tempo da última requisição

    if response.status_code == 200:
        return response.json()['id']  # Retorna o encryptedSummonerId
    else:
        print(f"Erro ao obter summoner ID: {response.status_code}")
        return None

# 3. Obter o elo do jogador
def get_summoner_rank(summoner_id):
    global REQUEST_COUNT, LAST_REQUEST_TIME

    # Verificar e aplicar o rate limit
    check_rate_limit()

    url = f'https://br1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}'
    headers = {
        'X-Riot-Token': API_KEY
    }
    response = requests.get(url, headers=headers)
    
    REQUEST_COUNT += 1  # Incrementar o contador de requisições
    LAST_REQUEST_TIME = time.time()  # Atualizar o tempo da última requisição

    if response.status_code == 200:
        return response.json()  # Retorna a lista de entradas de ranked
    else:
        print(f"Erro ao obter informações de ranked: {response.status_code}")
        return None

# Função para verificar e aplicar o rate limit
def check_rate_limit():
    global REQUEST_COUNT, LAST_REQUEST_TIME

    # Rate limit de 20 requisições por segundo
    if REQUEST_COUNT >= 20:
        elapsed_time = time.time() - LAST_REQUEST_TIME
        if elapsed_time < 1:
            time.sleep(1 - elapsed_time)  # Pausa para garantir 1 segundo
        REQUEST_COUNT = 0  # Resetar o contador

    # Rate limit de 100 requisições a cada 2 minutos
    if REQUEST_COUNT >= 100:
        elapsed_time = time.time() - LAST_REQUEST_TIME
        if elapsed_time < 120:
            time.sleep(120 - elapsed_time)  # Pausa para garantir 2 minutos
        REQUEST_COUNT = 0  # Resetar o contador

# Função para ordenar os dados pelo elo
def sort_by_elo(entry):
    if entry['Elo'] == 'unranked':
        return (0, 0)
    tier = entry['Elo'].split()[0]  # Extrai o tier (ex: 'GOLD')
    rank = entry['Elo'].split()[1]  # Extrai a divisão (ex: 'IV')
    return (TIER_ORDER.get(tier, 0), RANK_ORDER.get(rank, 0))

# Execução do código
if __name__ == '__main__':
    for usuario in usuarios99:
        puuid = get_puuid(usuario.get('gameName'), usuario.get('gameTag'))
        if puuid:
            summoner_id = get_summoner_id(puuid)
            if summoner_id:
                print(f"Summoner ID encontrado: {summoner_id}")
                ranked_info = get_summoner_rank(summoner_id)
                
                if ranked_info:
                    for entry in ranked_info:
                        # Adicionar os dados à lista
                        ranked_data.append({
                            'Nome': usuario.get('gameName') + '#' + usuario.get('gameTag'),
                            'id': usuario.get('id'),
                            'Summoner ID': summoner_id,
                            'puuid': puuid,
                            'Fila': entry['queueType'],
                            'Elo': f"{entry['tier']} {entry['rank']}",
                            'Pontos de Liga (LP)': entry['leaguePoints'],
                            'Vitórias': entry['wins'],
                            'Derrotas': entry['losses'],
                            'Winrate':  str((entry['wins']/(entry['wins'] + entry['losses']))*100) + "%"
                        })
                else:
                    ranked_data.append({
                            'Nome': usuario.get('gameName') + '#' + usuario.get('gameTag'),
                            'id': usuario.get('id'),
                            'Summoner ID': summoner_id,
                            'puuid': puuid,
                            'Fila': "",
                            'Elo': "unranked",
                            'Pontos de Liga (LP)': "",
                            'Vitórias': "",
                            'Derrotas': ""
                        })
            else:
                print("Summoner ID não encontrado.")

    ranked_data_sorted = sorted(ranked_data, key=sort_by_elo, reverse=True)

    # Exportar os dados ordenados para um arquivo Excel
    if ranked_data_sorted:
        df = pd.DataFrame(ranked_data_sorted)
        df.to_excel('ranked_info_ordenado.xlsx', index=False)
        print("Dados ordenados exportados para 'ranked_info_ordenado.xlsx'.")
    else:
        print("Nenhum dado para exportar.")