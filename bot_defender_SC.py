import requests
import time
import random

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
            'User-Agent': 'Mozilla/5.0',
            'Cookie': f'session={session_cookie}'
        }
        
        self.reference_colors = {coord: {} for coord in coordinates_list}
        
        self.map_current_colors()
    
    def get_pixel_color(self, x, y):
        try:
            response = requests.get(
                f"{self.base_url}/api/pixel?x={x}&y={y}",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
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
                    time.sleep(0.1)
            print(f"Área {coord} mapeada - {len(self.reference_colors[coord])} pixels")
        print("Mapeamento completo!")
    
    def place_pixel(self, x, y, color):
        try:
            response = requests.post(
                f"{self.base_url}/api/pixel",
                headers=self.headers,
                json={
                    'x': x,
                    'y': y,
                    'color': color
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao enviar pixel ({x},{y}): {e}")
            return False
    
    def check_and_fix_areas(self):
        total_changed = 0
        
        for coord in self.coordinates_list:
            changed_pixels = 0
            area_pixels = list(self.reference_colors[coord].items())
            random.shuffle(area_pixels)
            
            for (x, y), target_color in area_pixels:
                current_color = self.get_pixel_color(x, y)
                
                if current_color != target_color:
                    print(f"Pixel ({x},{y}) na área {coord} alterado! Corrigindo...")
                    if self.place_pixel(x, y, target_color):
                        changed_pixels += 1
                    time.sleep(random.uniform(1, 3))
                
                if random.random() < 0.1:
                    time.sleep(random.uniform(0.5, 1.5))
            
            print(f"Área {coord}: {changed_pixels} pixels corrigidos")
            total_changed += changed_pixels
        
        return total_changed
    
    def run(self, scan_interval=300):
        print(f"Iniciando defensor para {len(self.coordinates_list)} áreas de {self.width}x{self.height}")
        
        while True:
            start_time = time.time()
            changed = self.check_and_fix_areas()
            elapsed = time.time() - start_time
            
            print(f"Varredura completa. Total de pixels corrigidos: {changed}. Tempo: {elapsed:.2f}s")
            
            sleep_time = max(60, scan_interval / (changed + 1)) if changed else scan_interval
            sleep_time *= random.uniform(0.8, 1.2)
            sleep_time = max(30, sleep_time)
            
            print(f"Próxima verificação em {sleep_time:.1f} segundos...\n")
            time.sleep(sleep_time)



#É AQUI EMBAIXO ONDE VC SETA AS COISAS   


if __name__ == "__main__":
    COORDINATES = [
        (3721, 3592),  
        (3534, 3592)   
    ]
    WIDTH = 60 # tamanho da area
    HEIGHT = 60 # altura da área
    SESSION_COOKIE = #coloca aqui o cookie do site ou da conta
    
    defender = WPlaceMultiAreaDefender(COORDINATES, WIDTH, HEIGHT, SESSION_COOKIE)
    defender.run()

