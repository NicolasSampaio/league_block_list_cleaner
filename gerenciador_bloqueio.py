import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
import requests
import time
import pandas as pd
from lol_client import LolClient
import urllib.parse

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

class GerenciadorBloqueios:
    """
    Classe principal para gerenciar a lista de bloqueados do League of Legends.
    
    Esta classe fornece uma interface gráfica para:
    - Conectar ao cliente do League of Legends
    - Analisar jogadores na lista de bloqueados
    - Limpar a lista automaticamente com base em critérios de elo
    
    Attributes:
        root (tk.Tk): O widget raiz da aplicação
        client (LolClient): Instância para comunicação com o cliente do LoL
        region (str): Região do servidor (br1, na1, etc.)
        riot_region (str): Região da API Riot (americas, europe, etc.)
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Lista de Bloqueados - LoL")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.client = LolClient()
        self.region = "br1"
        self.riot_region = "americas"
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do usuário."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Seção: Configuração e conexão
        self._configurar_secao_conexao(main_frame)
        
        # Seção: Status e informações
        self._configurar_secao_informacoes(main_frame)
        
        # Seção: Parâmetros de limpeza
        self._configurar_secao_parametros(main_frame)
        
        # Seção: Log e progresso
        self._configurar_secao_log(main_frame)
        
        # Desabilitar botões inicialmente
        self.analyze_button.config(state=tk.DISABLED)
        self.clean_button.config(state=tk.DISABLED)

    def _configurar_secao_conexao(self, parent_frame):
        """Configura a seção de conexão."""
        config_frame = ttk.LabelFrame(parent_frame, text="Configuração", padding=10)
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Região:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.region_combo = ttk.Combobox(config_frame, values=["br1", "na1", "euw1", "eun1", "kr", "jp1"])
        self.region_combo.current(0)
        self.region_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.connect_button = ttk.Button(config_frame, text="Conectar ao Cliente", command=self.connect_to_client)
        self.connect_button.grid(row=1, column=0, columnspan=2, pady=10)

    def _configurar_secao_informacoes(self, parent_frame):
        """Configura a seção de informações do jogador."""
        info_frame = ttk.LabelFrame(parent_frame, text="Informações", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status de conexão
        ttk.Label(info_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.status_label = ttk.Label(info_frame, text="Desconectado")
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Nome do invocador
        ttk.Label(info_frame, text="Invocador:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.summoner_label = ttk.Label(info_frame, text="-")
        self.summoner_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Elo atual
        ttk.Label(info_frame, text="Elo:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.elo_label = ttk.Label(info_frame, text="-")
        self.elo_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Total de jogadores bloqueados
        ttk.Label(info_frame, text="Total bloqueados:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.blocked_label = ttk.Label(info_frame, text="0")
        self.blocked_label.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

    def _configurar_secao_parametros(self, parent_frame):
        """Configura a seção de parâmetros de limpeza."""
        action_frame = ttk.LabelFrame(parent_frame, text="Parâmetros de Limpeza", padding=10)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Diferença de elo para remoção
        ttk.Label(action_frame, text="Diferença de elo para remover:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.elo_diff_var = tk.StringVar(value="3")
        elo_diff_options = ["1", "2", "3", "4", "5"]
        self.elo_diff_combo = ttk.Combobox(action_frame, textvariable=self.elo_diff_var, values=elo_diff_options, width=5)
        self.elo_diff_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Quantidade de usuários a analisar
        ttk.Label(action_frame, text="Quantidade de usuários a analisar:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.users_count_var = tk.StringVar(value="Todos")
        self.users_count_entry = ttk.Entry(action_frame, textvariable=self.users_count_var, width=10)
        self.users_count_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Botões de ação
        buttons_frame = ttk.Frame(action_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.analyze_button = ttk.Button(buttons_frame, text="Analisar Bloqueados", command=self.analyze_blocked)
        self.analyze_button.pack(side=tk.LEFT, padx=5)
        
        self.clean_button = ttk.Button(buttons_frame, text="Limpar Lista Automaticamente", command=self.clean_blocked_list)
        self.clean_button.pack(side=tk.LEFT, padx=5)

    def _configurar_secao_log(self, parent_frame):
        """Configura a seção de log e barra de progresso."""
        # Log de ações
        log_frame = ttk.LabelFrame(parent_frame, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Barra de progresso
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(parent_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, padx=5, pady=5)
    
    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def connect_to_client(self):
        def connect_thread():
            self.region = self.region_combo.get()
            
            self.log("Conectando ao cliente do League of Legends...")
            
            if self.client.connect():
                self.status_label.config(text="Conectado")
                
                # Obter informações do invocador
                summoner = self.client.get_current_summoner()
                if summoner:
                    self.summoner_label.config(text=f"{summoner.get('displayName', '-')}")
                    self.log(f"Conectado como: {summoner.get('displayName', '-')}")
                
                # Obter elo
                ranked_stats = self.client.get_player_elo()
                if ranked_stats:
                    for queue in ranked_stats.get("queueMap", {}).values():
                        if queue.get("queueType") == "RANKED_SOLO_5x5":
                            tier = queue.get("tier", "UNRANKED")
                            division = queue.get("division", "")
                            if tier != "UNRANKED":
                                self.elo_label.config(text=f"{tier} {division}")
                                self.log(f"Elo atual: {tier} {division}")
                            else:
                                self.elo_label.config(text="Unranked")
                                self.log("Elo atual: Unranked")
                
                # Carregar lista de bloqueados
                blocked = self.client.load_blocked_players()
                self.blocked_label.config(text=str(len(blocked)))
                self.log(f"Total de jogadores bloqueados: {len(blocked)}")
                
                # Ativar botões
                self.analyze_button.config(state=tk.NORMAL)
                self.clean_button.config(state=tk.NORMAL)
            else:
                self.status_label.config(text="Falha na conexão")
                self.log("Falha ao conectar ao cliente. Verifique se o jogo está aberto.")
                messagebox.showerror("Erro", "Não foi possível conectar ao cliente do League of Legends. Verifique se o jogo está aberto.")
        
        threading.Thread(target=connect_thread).start()
    
    def check_rate_limit(self):
        time.sleep(1.2)  # Espera básica para respeitar o rate limit da API
    
    def get_puuid(self, game_name, tagline):
        self.check_rate_limit()
        
        try:
            # Log para diagnóstico
            self.log(f"Tentando obter PUUID para {game_name}#{tagline}...")
            
            # Codificar corretamente os caracteres especiais e espaços
            encoded_game_name = urllib.parse.quote(game_name)
            encoded_tagline = urllib.parse.quote(tagline)
            
            # Tentar primeiro o endpoint v2 com LCU API - método mais direto
            summoner_data = self.client.request("GET", f"/lol-summoner/v2/summoners/by-riot-id/{encoded_game_name}/{encoded_tagline}")
            
            if summoner_data and summoner_data.status_code == 200:
                puuid = summoner_data.json().get('puuid')
                self.log(f"PUUID obtido com sucesso usando endpoint v2.")
                return puuid
            
            # Tentar obter informações via accountId
            self.log(f"Tentando via LCU API alternativa para {game_name}...")
            
            # Tentar o endpoint que busca por nome exato
            account_data = self.client.request("GET", f"/lol-summoner/v1/summoners?name={encoded_game_name}")
            
            if account_data and account_data.status_code == 200 and isinstance(account_data.json(), list):
                summoners = account_data.json()
                for summoner in summoners:
                    # Verificamos pelo nome exato (case sensitive)
                    if summoner.get('displayName', '').lower() == game_name.lower():
                        puuid = summoner.get('puuid')
                        self.log(f"PUUID obtido via nome de invocador.")
                        return puuid
            
            # Tentar buscar pelo XMPP Name (nome de chat)
            self.log("Tentando via API de chat...")
            chat_data = self.client.request("GET", "/lol-chat/v1/friends")
            
            if chat_data and chat_data.status_code == 200:
                friends = chat_data.json()
                for friend in friends:
                    if friend.get('name', '').lower() == game_name.lower() or friend.get('gameName', '').lower() == game_name.lower():
                        puuid = friend.get('puuid')
                        if puuid:
                            self.log(f"PUUID obtido via lista de amigos.")
                            return puuid
            
            # Se todas as tentativas falharam, reportar o erro
            self.log(f"Erro ao obter PUUID após múltiplas tentativas: {summoner_data.status_code if summoner_data else 'Falha na requisição'}")
            return None
        except Exception as e:
            self.log(f"Exceção ao obter PUUID: {str(e)}")
            return None
    
    def get_summoner_id(self, puuid):
        self.check_rate_limit()
        
        # Usar o cliente em vez da API da Riot
        summoner_data = self.client.request("GET", f"/lol-summoner/v1/summoners/by-puuid/{puuid}")
        
        if summoner_data and summoner_data.status_code == 200:
            return summoner_data.json().get('id')
        else:
            self.log(f"Erro ao obter Summoner ID: {summoner_data.status_code if summoner_data else 'Falha na requisição'}")
            return None
    
    def get_summoner_rank(self, summoner_id):
        self.check_rate_limit()
        
        # Usar o cliente em vez da API da Riot
        ranked_data = self.client.request("GET", f"/lol-ranked/v1/ranked-stats/{summoner_id}")
        
        if ranked_data and ranked_data.status_code == 200:
            # Converter do formato do cliente para o formato da API pública
            data = ranked_data.json()
            result = []
            
            for queue_type, queue_data in data.get('queueMap', {}).items():
                if queue_type == 'RANKED_SOLO_5x5':
                    entry = {
                        'queueType': 'RANKED_SOLO_5x5',
                        'tier': queue_data.get('tier', 'UNRANKED'),
                        'rank': queue_data.get('division', 'I'),
                        'leaguePoints': queue_data.get('leaguePoints', 0),
                        'wins': queue_data.get('wins', 0),
                        'losses': queue_data.get('losses', 0)
                    }
                    result.append(entry)
            
            return result
        else:
            self.log(f"Erro ao obter informações de rank: {ranked_data.status_code if ranked_data else 'Falha na requisição'}")
            return None
    
    def sort_by_elo(self, player_data):
        """Ordena os jogadores por elo para exibição ordenada."""
        elo = player_data.get('Elo', 'UNRANKED I')
        
        if elo.lower() == 'unranked':
            return -1  # Coloca jogadores sem rank no final
        
        parts = elo.split()
        tier = parts[0].upper()  # Normaliza para maiúsculas
        division = parts[1] if len(parts) > 1 else 'I'
        
        tier_value = TIER_ORDER.get(tier, -1)
        rank_value = RANK_ORDER.get(division, 0)
        
        return tier_value * 10 + rank_value
    
    def calculate_elo_difference(self, player_elo, my_elo):
        """Calcula a diferença de elo entre dois jogadores em tiers."""
        if player_elo.lower() == 'unranked' or my_elo == 'UNRANKED I':
            return 0  # Não podemos calcular a diferença para jogadores sem ranked
        
        # Separar tier e divisão
        player_parts = player_elo.split()
        my_parts = my_elo.split()
        
        player_tier = player_parts[0].upper()
        player_division = player_parts[1] if len(player_parts) > 1 else 'I'
        
        my_tier = my_parts[0].upper()
        my_division = my_parts[1] if len(my_parts) > 1 else 'I'
        
        # Converter para valores numéricos
        player_tier_value = TIER_ORDER.get(player_tier, 0)
        player_rank_value = RANK_ORDER.get(player_division, 0)
        
        my_tier_value = TIER_ORDER.get(my_tier, 0)
        my_rank_value = RANK_ORDER.get(my_division, 0)
        
        # Calcular diferença (em divisões)
        player_total = player_tier_value * 4 + player_rank_value
        my_total = my_tier_value * 4 + my_rank_value
        
        return abs(player_total - my_total) // 4  # Diferença em tiers
    
    def _validar_quantidade_usuarios(self, total_usuarios, proposito="analisar"):
        """Valida a quantidade de usuários a processar."""
        usuarios_a_processar = self.users_count_var.get().strip()
        
        if usuarios_a_processar.lower() == "todos":
            return total_usuarios
        
        try:
            usuarios_a_processar = int(usuarios_a_processar)
            if usuarios_a_processar > total_usuarios:
                usuarios_a_processar = total_usuarios
            elif usuarios_a_processar < 1:
                usuarios_a_processar = 1
        except ValueError:
            self.log(f"Valor inválido para quantidade de usuários. {proposito.capitalize()}ando todos.")
            usuarios_a_processar = total_usuarios
        
        return usuarios_a_processar

    def _obter_jogadores_a_processar(self, todos_jogadores, quantidade):
        """Retorna a lista limitada de jogadores a processar e o restante a manter."""
        if quantidade < len(todos_jogadores):
            return todos_jogadores[:quantidade], todos_jogadores[quantidade:]
        return todos_jogadores, []

    def _processar_jogador(self, jogador, my_elo, diff_limit):
        """Processa um jogador bloqueado e determina se deve ser mantido ou removido."""
        game_name = jogador.get('gameName', '')
        game_tag = jogador.get('gameTag', '')
        
        self.log(f"Processando {game_name}#{game_tag}...")
        
        # Tentar obter o PUUID
        puuid = self.get_puuid(game_name, game_tag)
        if not puuid:
            # Tentar método alternativo sem tagline
            self.log(f"Tentando método alternativo para {game_name}...")
            summoner = self.get_summoner_by_name(game_name)
            if summoner:
                puuid = summoner.get('puuid')
        
        # Se não conseguiu obter PUUID
        if not puuid:
            self.log(f" - Mantendo {game_name}#{game_tag} (PUUID não encontrado)")
            return None, None, "PUUID não encontrado"
        
        # Obter Summoner ID
        summoner_id = self.get_summoner_id(puuid)
        if not summoner_id:
            self.log(f" - Mantendo {game_name}#{game_tag} (Summoner ID não encontrado)")
            return None, None, "Summoner ID não encontrado"
        
        # Obter informações de ranked
        ranked_info = self.get_summoner_rank(summoner_id)
        if not ranked_info:
            self.log(f" - Mantendo {game_name}#{game_tag} (sem informações de rank)")
            return None, None, "Sem informações de rank"
        
        # Verificar filas ranqueadas
        for entry in ranked_info:
            if entry['queueType'] == 'RANKED_SOLO_5x5':
                elo = f"{entry['tier']} {entry['rank']}"
                diff = self.calculate_elo_difference(elo, my_elo)
                
                # Dados do jogador para retorno
                player_data = {
                    'Nome': f"{game_name}#{game_tag}",
                    'id': jogador.get('id'),
                    'Summoner ID': summoner_id,
                    'puuid': puuid,
                    'Fila': entry['queueType'],
                    'Elo': elo,
                    'Pontos de Liga (LP)': entry['leaguePoints'],
                    'Vitórias': entry['wins'],
                    'Derrotas': entry['losses'],
                    'Winrate': f"{(entry['wins']/(entry['wins'] + entry['losses']))*100:.2f}%",
                    'Diferença de Elo': diff
                }
                
                # Decisão se deve remover
                if diff >= diff_limit:
                    return player_data, True, f"diferença de elo: {diff}"
                else:
                    return player_data, False, f"diferença de elo: {diff}"
        
        # Se não encontrou RANKED_SOLO_5x5
        player_data = {
            'Nome': f"{game_name}#{game_tag}",
            'id': jogador.get('id'),
            'Summoner ID': summoner_id,
            'puuid': puuid,
            'Fila': "",
            'Elo': "unranked",
            'Pontos de Liga (LP)': "",
            'Vitórias': "",
            'Derrotas': "",
            'Winrate': "",
            'Diferença de Elo': 0
        }
        
        self.log(f" - Mantendo {game_name}#{game_tag} (sem ranked solo)")
        return player_data, False, "sem ranked solo"

    def analyze_blocked(self):
        """Analisa os jogadores bloqueados e exporta para Excel."""
        def analyze_thread():
            # Desativar botões durante análise
            self._desativar_botoes()
            
            # Obter elo do jogador atual
            my_elo = self.elo_label.cget("text")
            if not my_elo or my_elo == "-":
                messagebox.showerror("Erro", "Não foi possível determinar seu elo atual.")
                self._ativar_botoes()
                return
            
            # Obter lista de bloqueados
            blocked_players = self.client.load_blocked_players()
            total = len(blocked_players)
            
            if total == 0:
                self.log("Nenhum jogador bloqueado encontrado.")
                self._ativar_botoes()
                return
            
            # Determinar o número de usuários a analisar
            users_to_analyze = self._validar_quantidade_usuarios(total, "analisar")
            
            self.log(f"Iniciando análise de {users_to_analyze} jogadores bloqueados...")
            
            # Limitar a quantidade de jogadores a analisar
            blocked_to_analyze, _ = self._obter_jogadores_a_processar(blocked_players, users_to_analyze)
            
            # Lista para armazenar dados de ranked
            ranked_data = []
            
            # Diferença de elo para considerar na remoção
            diff_limit = int(self.elo_diff_var.get())
            
            for i, usuario in enumerate(blocked_to_analyze):
                # Atualizar barra de progresso
                progress = (i + 1) / users_to_analyze * 100
                self.progress_var.set(progress)
                
                game_name = usuario.get('gameName', '')
                game_tag = usuario.get('gameTag', '')
                
                self.log(f"Analisando {game_name}#{game_tag} ({i+1}/{users_to_analyze})...")
                
                player_data, should_remove, reason = self._processar_jogador(usuario, my_elo, diff_limit)
                
                if player_data:
                    ranked_data.append(player_data)
            
            # Ordenar os dados
            ranked_data_sorted = sorted(ranked_data, key=self.sort_by_elo, reverse=True)
            
            # Exportar os dados para Excel (para referência)
            if ranked_data_sorted:
                df = pd.DataFrame(ranked_data_sorted)
                df.to_excel('ranked_info_completo.xlsx', index=False)
                self.log("Dados exportados para 'ranked_info_completo.xlsx'")
                
                # Mostrar resumo
                self.log("\nResumo da análise:")
                
                to_remove = [p for p in ranked_data_sorted if p['Diferença de Elo'] >= diff_limit]
                
                self.log(f"Total de jogadores bloqueados: {total}")
                self.log(f"Jogadores com diferença de elo >= {diff_limit}: {len(to_remove)}")
                self.log(f"Jogadores a manter: {total - len(to_remove)}")
                
                messagebox.showinfo("Análise Concluída", 
                                   f"Total de jogadores bloqueados: {total}\n"
                                   f"Jogadores com diferença de elo >= {diff_limit}: {len(to_remove)}\n"
                                   f"Jogadores a manter: {total - len(to_remove)}")
            else:
                self.log("Nenhum dado para analisar.")
            
            # Reativar botões
            self._ativar_botoes()
        
        threading.Thread(target=analyze_thread).start()

    def clean_blocked_list(self):
        """Remove jogadores bloqueados com base na diferença de elo configurada."""
        def clean_thread():
            self.log("Iniciando limpeza da lista de bloqueados...")
            
            # Desativar botões durante a limpeza
            self._desativar_botoes()
            
            # Obter elo do jogador atual
            my_elo = self.elo_label.cget("text")
            if not my_elo or my_elo == "-":
                messagebox.showerror("Erro", "Não foi possível determinar seu elo atual.")
                self._ativar_botoes()
                return
            
            # Carregar lista de bloqueados
            blocked_players = self.client.load_blocked_players()
            total = len(blocked_players)
            
            if total == 0:
                self.log("Nenhum jogador bloqueado encontrado.")
                self._ativar_botoes()
                return
            
            # Determinar o número de usuários a processar
            users_to_process = self._validar_quantidade_usuarios(total, "processar")
            
            self.log(f"Processando {users_to_process} de {total} jogadores bloqueados...")
            
            # Limitar a quantidade de jogadores a processar
            blocked_to_process, blocked_to_keep = self._obter_jogadores_a_processar(blocked_players, users_to_process)
            
            # Lista para manter jogadores que não serão removidos
            players_to_keep = blocked_to_keep.copy()  # Já inclui os que não serão processados
            players_to_remove = []
            
            diff_limit = int(self.elo_diff_var.get())
            
            for i, usuario in enumerate(blocked_to_process):
                # Atualizar barra de progresso
                progress = (i + 1) / users_to_process * 100
                self.progress_var.set(progress)
                
                game_name = usuario.get('gameName', '')
                game_tag = usuario.get('gameTag', '')
                
                self.log(f"Verificando {game_name}#{game_tag} ({i+1}/{users_to_process})...")
                
                _, should_remove, reason = self._processar_jogador(usuario, my_elo, diff_limit)
                
                if should_remove:
                    self.log(f" - Removendo {game_name}#{game_tag} ({reason})")
                    players_to_remove.append(usuario)
                else:
                    self.log(f" - Mantendo {game_name}#{game_tag} ({reason})")
                    players_to_keep.append(usuario)
            
            # Remover jogadores
            removed_count = 0
            for player in players_to_remove:
                player_id = player.get('id')
                if self.client.unblock_player(player_id):
                    removed_count += 1
                    self.log(f"Removido com sucesso: {player.get('gameName')}#{player.get('gameTag')}")
                else:
                    self.log(f"Falha ao remover: {player.get('gameName')}#{player.get('gameTag')}")
                    players_to_keep.append(player)
                
                time.sleep(0.5)  # Pequena pausa para não sobrecarregar o cliente
            
            # Atualizar arquivo JSON
            if self.client.save_blocked_players(players_to_keep):
                self.log("Arquivo de bloqueados atualizado com sucesso.")
            else:
                self.log("Erro ao atualizar arquivo de bloqueados.")
            
            # Atualizar contagem de bloqueados
            self.blocked_label.config(text=str(len(players_to_keep)))
            
            self.log(f"\nLimpeza concluída:")
            self.log(f"Jogadores removidos: {removed_count}")
            self.log(f"Jogadores mantidos: {len(players_to_keep)}")
            
            messagebox.showinfo("Limpeza Concluída", 
                               f"Total de jogadores bloqueados originalmente: {total}\n"
                               f"Jogadores removidos: {removed_count}\n"
                               f"Jogadores mantidos: {len(players_to_keep)}")
            
            # Reativar botões
            self._ativar_botoes()
        
        # Confirmação antes de limpar
        result = messagebox.askyesno("Confirmar Limpeza", 
                                    f"Isso removerá automaticamente jogadores bloqueados com diferença de elo >= {self.elo_diff_var.get()}.\n\n"
                                    "Deseja continuar?")
        
        if result:
            threading.Thread(target=clean_thread).start()

    def _desativar_botoes(self):
        """Desativa os botões de ação."""
        self.analyze_button.config(state=tk.DISABLED)
        self.clean_button.config(state=tk.DISABLED)

    def _ativar_botoes(self):
        """Ativa os botões de ação."""
        self.analyze_button.config(state=tk.NORMAL)
        self.clean_button.config(state=tk.NORMAL)

    def get_summoner_by_name(self, game_name):
        """Tenta obter o invocador usando apenas o nome de exibição"""
        self.check_rate_limit()
        
        try:
            encoded_name = urllib.parse.quote(game_name)
            
            # Tentar primeiro pelo endpoint específico
            self.log(f"Buscando invocador por nome exato: {game_name}")
            response = self.client.request("GET", f"/lol-summoner/v1/summoners?name={encoded_name}")
            
            if response and response.status_code == 200:
                summoners = response.json()
                if isinstance(summoners, list) and summoners:
                    # Procurar por correspondência exata ou parcial
                    for summoner in summoners:
                        display_name = summoner.get('displayName', '')
                        if display_name.lower() == game_name.lower():
                            self.log(f"Invocador encontrado: {display_name}")
                            return summoner
                    
                    # Se não encontrou correspondência exata, use a primeira
                    self.log(f"Usando primeira correspondência: {summoners[0].get('displayName')}")
                    return summoners[0]
            
            # Tentar via a lista de bloqueados
            self.log("Tentando buscar nas informações da lista de bloqueados...")
            blocked = self.client.load_blocked_players()
            for blocked_user in blocked:
                if blocked_user.get('gameName', '').lower() == game_name.lower():
                    # Encontrado o usuário bloqueado, tentar obter seu summoner_id
                    if 'id' in blocked_user:
                        self.log(f"Encontrado na lista de bloqueados, tentando obter summonerId")
                        summoner_info = self.client.request("GET", f"/lol-chat/v1/blocked-players/{blocked_user['id']}")
                        if summoner_info and summoner_info.status_code == 200:
                            return summoner_info.json()
            
            self.log(f"Nenhum invocador encontrado com o nome: {game_name}")
            return None
        except Exception as e:
            self.log(f"Erro ao buscar invocador por nome: {str(e)}")
            return None

    def reconnect_client(self):
        self.log("Tentando reconectar ao cliente do League of Legends...")
        if self.client.connect():
            self.log("Reconexão bem-sucedida!")
            return True
        else:
            self.log("Falha na reconexão.")
            return False

    def get_blocked_player_info(self, player_id):
        """Obtém informações do jogador bloqueado diretamente pelo ID"""
        self.check_rate_limit()
        
        try:
            response = self.client.request("GET", f"/lol-chat/v1/blocked-players/{player_id}")
            
            if response and response.status_code == 200:
                player_info = response.json()
                self.log(f"Informações obtidas para jogador bloqueado ID: {player_id}")
                return player_info
            else:
                self.log(f"Erro ao obter informações do jogador bloqueado: {response.status_code if response else 'Falha na requisição'}")
                return None
        except Exception as e:
            self.log(f"Erro ao obter informações do jogador bloqueado: {str(e)}")
            return None

if __name__ == "__main__":
    root = tk.Tk()
    app = GerenciadorBloqueios(root)
    root.mainloop() 
