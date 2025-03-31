import requests
import base64
import urllib3
import psutil
import time
import json
from pathlib import Path

# Desabilitar avisos de SSL - o cliente do LoL usa um certificado autoassinado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LolClient:
    """
    Classe para comunicação com o cliente do League of Legends.
    
    Permite interagir com as APIs internas do cliente para obter informações
    sobre o jogador atual, gerenciar lista de bloqueados e outras operações.
    
    Attributes:
        process: Processo do cliente do LoL
        auth: Token de autenticação codificado em base64
        port: Porta em que o cliente está operando
        base_url: URL base para as requisições
        connected: Status da conexão com o cliente
        blocklist_file: Caminho para o arquivo de bloqueados
    """
    def __init__(self):
        self.process = None
        self.auth = None
        self.port = None
        self.base_url = None
        self.connected = False
        self.blocklist_file = Path("bloqueados.json")

    def connect(self):
        """Conecta ao cliente do LoL procurando o processo em execução"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.name() == "LeagueClientUx.exe":
                self.process = proc
                break
        
        if not self.process:
            print("Cliente do League of Legends não está em execução.")
            return False
        
        # Extrair porta e token de autenticação dos argumentos de linha de comando
        cmdline = self.process.cmdline()
        port = None
        password = None
        
        for arg in cmdline:
            if "--app-port" in arg:
                port = arg.split("=")[1]
            if "--remoting-auth-token" in arg:
                password = arg.split("=")[1]
        
        if not port or not password:
            print("Não foi possível encontrar a porta ou o token de autenticação.")
            return False
        
        self.port = port
        auth_string = f"riot:{password}"
        self.auth = base64.b64encode(auth_string.encode()).decode()
        self.base_url = f"https://127.0.0.1:{port}"
        self.connected = True
        return True

    def request(self, method, endpoint, data=None):
        """Faz uma requisição para a API do cliente"""
        if not self.connected:
            if not self.connect():
                return None
        
        headers = {
            "Accept": "application/json",
            "Authorization": f"Basic {self.auth}"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, verify=False)
            elif method.upper() == "POST":
                headers["Content-Type"] = "application/json"
                response = requests.post(url, headers=headers, json=data, verify=False)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, verify=False)
            else:
                print(f"Método não suportado: {method}")
                return None
            
            return response
        except Exception as e:
            print(f"Erro na requisição: {e}")
            return None
    
    def get_current_summoner(self):
        """Obter informações do invocador atual"""
        response = self.request("GET", "/lol-summoner/v1/current-summoner")
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def get_player_elo(self):
        """Obter o elo do jogador atual"""
        response = self.request("GET", "/lol-ranked/v1/current-ranked-stats")
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def unblock_player(self, player_id):
        """Desbloquear um jogador pelo ID"""
        endpoint = f"/lol-chat/v1/blocked-players/{player_id}"
        response = self.request("DELETE", endpoint)
        return response and response.status_code == 204
    
    def load_blocked_players(self):
        """Carrega a lista de jogadores bloqueados."""
        # Primeiro tenta obter a lista do cliente
        response = self.request("GET", "/lol-chat/v1/blocked-players")
        
        if response and response.status_code == 200:
            blocked_list = response.json()
            
            # Salva a lista atualizada para uso futuro
            if blocked_list:
                with open(self.blocklist_file, 'w', encoding='utf-8') as f:
                    json.dump({"usuariosBlock": blocked_list}, f, ensure_ascii=False, indent=2)
            
            return blocked_list
        
        # Se falhar, tenta carregar do arquivo local
        if self.blocklist_file.exists():
            try:
                with open(self.blocklist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("usuariosBlock", [])
            except Exception as e:
                print(f"Erro ao carregar arquivo de bloqueados: {e}")
        
        return []
    
    def save_blocked_players(self, blocked_list):
        """Salva a lista de jogadores bloqueados no arquivo JSON."""
        try:
            with open(self.blocklist_file, 'w', encoding='utf-8') as f:
                json.dump({"usuariosBlock": blocked_list}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erro ao salvar arquivo de bloqueados: {e}")
            return False
    
    def get_summoner_by_puuid(self, puuid):
        """Obtém informações de um invocador pelo PUUID"""
        response = self.request("GET", f"/lol-summoner/v1/summoners/by-puuid/{puuid}")
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def get_ranked_stats_by_summonerId(self, summoner_id):
        """Obtém estatísticas de ranked de um jogador pelo summoner ID"""
        response = self.request("GET", f"/lol-ranked/v1/ranked-stats/{summoner_id}")
        if response and response.status_code == 200:
            return response.json()
        return None 
