import requests
import time
import random
from math import exp

class WPlaceMultiAreaDefender:
    def __init__(self, coordinates_list, width, height, session_cookie, base_url="https://wplace.live"):
        """
        Inicializa o bot para múltiplas áreas
        
        :param coordinates_list: Lista de tuplas [(x1,y1), (x2,y2)] com coordenadas iniciais
        :param width: Largura da área a proteger
        :param height: Altura da área a proteger
        :param session_cookie: Cookie de sessão
        :param base_url: URL base do WPlace
        """
        self.coordinates_list = coordinates_list
        self.width = width
        self.height = height
        self.session_cookie = session_cookie
        self.base_url = base_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Cookie': f'session={session_cookie}',
            'Accept': 'application/json',
        }
        
        self.reference_colors = {coord: {} for coord in coordinates_list}
        self.request_delay = 1.0  # Delay base entre requisições (em segundos)
        self.rate_limit_multiplier = 1.0  # Multiplicador para aumentar delays quando receber 429
        
        self.map_current_colors()
    
    def get_pixel_color(self, x, y):
        try:
            time.sleep(self.request_delay * random.uniform(0.8, 1.2) * self.rate_limit_multiplier)
            
            response = requests.get(
                f"{self.base_url}/api/pixel?x={x}&y={y}",
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 429:
                print(f"Rate limit atingido! Aumentando delays...")
                self.rate_limit_multiplier *= 2  # Dobra o delay entre requisições
                return None
                
            if response.status_code == 200:
                self.rate_limit_multiplier = max(1.0, self.rate_limit_multiplier * 0.9)  # Reduz gradualmente o multiplicador
                return response.json().get('color', None)
            
            print(f"Erro ao obter pixel ({x},{y}): {response.status_code}")
            return None
            
        except Exception as e:
            print(f"Erro de conexão ao obter pixel ({x},{y}): {e}")
            return None
    
    def map_current_colors(self):
        print("Mapeando cores atuais das áreas...")
        for coord in self.coordinates_list:
            start_x, start_y = coord
            for x in range(start_x, start_x + self.width):
                for y in range(start_y, start_y + self.height):
                    color = self.get_pixel_color(x, y)
                    if color is not None:
                        self.reference_colors[coord][(x, y)] = color
                    else:
                        print(f"Falha ao mapear pixel ({x},{y}), tentando novamente...")
                        time.sleep(5)
                        color = self.get_pixel_color(x, y)
                        if color is not None:
                            self.reference_colors[coord][(x, y)] = color
            print(f"Área {coord} mapeada - {len(self.reference_colors[coord])} pixels")
        print("Mapeamento completo!")
    
    def place_pixel(self, x, y, color):
        try:
            time.sleep(self.request_delay * random.uniform(1.0, 1.5) * self.rate_limit_multiplier)
            
            response = requests.post(
                f"{self.base_url}/api/pixel",
                headers=self.headers,
                json={
                    'x': x,
                    'y': y,
                    'color': color
                },
                timeout=15
            )
            
            if response.status_code == 429:
                print(f"Rate limit atingido ao tentar colocar pixel! Aumentando delays...")
                self.rate_limit_multiplier *= 2
                return False
                
            if response.status_code == 200:
                self.rate_limit_multiplier = max(1.0, self.rate_limit_multiplier * 0.9)
                return True
                
            print(f"Erro ao enviar pixel ({x},{y}): {response.status_code}")
            return False
            
        except Exception as e:
            print(f"Erro de conexão ao enviar pixel ({x},{y}): {e}")
            return False
    
    def check_and_fix_areas(self):
        total_changed = 0
        
        for coord in self.coordinates_list:
            changed_pixels = 0
            area_pixels = list(self.reference_colors[coord].items())
            random.shuffle(area_pixels)
            
            for (x, y), target_color in area_pixels:
                current_color = self.get_pixel_color(x, y)
                
                if current_color is None:
                    continue  # Skip se não conseguiu obter a cor
                    
                if current_color != target_color:
                    print(f"Pixel ({x},{y}) na área {coord} alterado de {target_color} para {current_color}! Corrigindo...")
                    if self.place_pixel(x, y, target_color):
                        changed_pixels += 1
                        time.sleep(random.uniform(2, 5))  # Delay extra após colocar um pixel
                    else:
                        time.sleep(random.uniform(5, 10))  # Delay maior se falhou
                
                # Delay aleatório entre verificações
                time.sleep(random.uniform(0.5, 1.5) * self.rate_limit_multiplier)
            
            print(f"Área {coord}: {changed_pixels} pixels corrigidos")
            total_changed += changed_pixels
        
        return total_changed
    
    def run(self, scan_interval=600):  # Intervalo padrão aumentado para 10 minutos
        print(f"Iniciando defensor para {len(self.coordinates_list)} áreas de {self.width}x{self.height}")
        
        while True:
            start_time = time.time()
            changed = self.check_and_fix_areas()
            elapsed = time.time() - start_time
            
            print(f"Varredura completa. Total de pixels corrigidos: {changed}. Tempo: {elapsed:.2f}s")
            
            # Calcula tempo até próxima verificação baseado em quantos pixels foram alterados
            if changed > 0:
                # Se muitos pixels foram alterados, verifica novamente mais cedo
                sleep_time = max(60, scan_interval / (changed * 0.5 + 1))
            else:
                # Se nenhum pixel foi alterado, espera o intervalo completo
                sleep_time = scan_interval
                
            # Aplica variação aleatória e multiplicador de rate limit
            sleep_time *= random.uniform(0.9, 1.1) * self.rate_limit_multiplier
            sleep_time = max(60, sleep_time)  # Nunca menos que 1 minuto
            
            print(f"Próxima verificação em {sleep_time/60:.1f} minutos...\n")
            time.sleep(sleep_time)


#É AQUI EMBAIXO ONDE VC SETA AS COISAS   


if __name__ == "__main__":
    COORDINATES = [
        (3721, 3592),  
        (3534, 3592)   
    ]
    WIDTH = 60 # tamanho da area
    HEIGHT = 60 # altura da área
    SESSION_COOKIE = "" #coloca aqui o cookie do site ou da conta
    
    defender = WPlaceMultiAreaDefender(COORDINATES, WIDTH, HEIGHT, SESSION_COOKIE)
    defender.run()

