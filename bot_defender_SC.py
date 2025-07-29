import requests
import time
import random
from math import exp
import json

class WPlaceMultiAreaDefender:
    def __init__(self, coordinates_list, width, height, session_cookie, base_url="https://wplace.live"):
        self.coordinates_list = coordinates_list
        self.width = width
        self.height = height
        self.session_cookie = session_cookie
        self.base_url = base_url
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': base_url,
            'Origin': base_url,
        }
        
        if session_cookie:
            self.headers['Cookie'] = f'session={session_cookie}'
        
        self.reference_colors = {coord: {} for coord in coordinates_list}
        self.request_delay = 2.0
        self.rate_limit_multiplier = 1.0
        
        if self.test_connection():
            self.map_current_colors()
        else:
            print("ERRO: Não foi possível estabelecer conexão com o WPlace!")
    
    def test_connection(self):
        try:
            print("Testando conexão com WPlace...")
            response = requests.get(
                f"{self.base_url}/api/pixel?x=0&y=0",
                headers=self.headers,
                timeout=10
            )
            
            print(f"Status da conexão: {response.status_code}")
            print(f"Headers da resposta: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✓ Conexão estabelecida com sucesso!")
                return True
            elif response.status_code == 401:
                print("❌ ERRO: Cookie de sessão inválido ou expirado!")
                return False
            elif response.status_code == 403:
                print("❌ ERRO: Acesso negado - verifique suas credenciais!")
                return False
            else:
                print(f"❌ ERRO: Status inesperado {response.status_code}")
                print(f"Resposta: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ ERRO: Timeout na conexão - WPlace pode estar offline")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ ERRO: Falha na conexão - verifique sua internet ou URL")
            return False
        except Exception as e:
            print(f"❌ ERRO: Exceção inesperada: {e}")
            return False
    
    def get_pixel_color(self, x, y, retries=3):
        for attempt in range(retries):
            try:
                delay = self.request_delay * random.uniform(0.8, 1.2) * self.rate_limit_multiplier
                time.sleep(delay)
                
                response = requests.get(
                    f"{self.base_url}/api/pixel?x={x}&y={y}",
                    headers=self.headers,
                    timeout=15
                )
                
                if response.status_code == 429:
                    print(f"Rate limit atingido! Aumentando delays... (tentativa {attempt + 1})")
                    self.rate_limit_multiplier *= 1.5
                    time.sleep(10 * (attempt + 1))
                    continue
                    
                if response.status_code == 200:
                    self.rate_limit_multiplier = max(1.0, self.rate_limit_multiplier * 0.95)
                    
                    try:
                        data = response.json()
                        return data.get('color', None)
                    except json.JSONDecodeError:
                        print(f"Resposta inválida para pixel ({x},{y}): {response.text}")
                        continue
                
                if response.status_code == 401:
                    print("❌ ERRO: Cookie de sessão expirou!")
                    return None
                    
                print(f"Erro ao obter pixel ({x},{y}): Status {response.status_code}")
                print(f"Resposta: {response.text}")
                
                if attempt < retries - 1:
                    time.sleep(5 * (attempt + 1))
                
            except requests.exceptions.Timeout:
                print(f"Timeout ao obter pixel ({x},{y}) - tentativa {attempt + 1}")
                if attempt < retries - 1:
                    time.sleep(5)
            except Exception as e:
                print(f"Erro de conexão ao obter pixel ({x},{y}): {e}")
                if attempt < retries - 1:
                    time.sleep(5)
        
        return None
    
    def map_current_colors(self):
        print("Mapeando cores atuais das áreas...")
        
        for i, coord in enumerate(self.coordinates_list):
            start_x, start_y = coord
            print(f"Mapeando área {i+1}/{len(self.coordinates_list)}: ({start_x}, {start_y})")
            
            total_pixels = self.width * self.height
            mapped_pixels = 0
            failed_pixels = []
            
            for x in range(start_x, start_x + self.width):
                for y in range(start_y, start_y + self.height):
                    color = self.get_pixel_color(x, y)
                    
                    if color is not None:
                        self.reference_colors[coord][(x, y)] = color
                        mapped_pixels += 1
                        
                        progress = (mapped_pixels / total_pixels) * 100
                        if mapped_pixels % max(1, total_pixels // 10) == 0:
                            print(f"  Progresso: {progress:.1f}% ({mapped_pixels}/{total_pixels})")
                    else:
                        failed_pixels.append((x, y))
                        print(f"  ❌ Falha ao mapear pixel ({x},{y})")
            
            if failed_pixels:
                print(f"Tentando remapear {len(failed_pixels)} pixels que falharam...")
                time.sleep(10)
                
                for x, y in failed_pixels:
                    color = self.get_pixel_color(x, y)
                    if color is not None:
                        self.reference_colors[coord][(x, y)] = color
                        mapped_pixels += 1
            
            success_rate = (mapped_pixels / total_pixels) * 100
            print(f"✓ Área {coord} mapeada: {mapped_pixels}/{total_pixels} pixels ({success_rate:.1f}%)")
            
            if success_rate < 90:
                print(f"⚠️  AVISO: Taxa de sucesso baixa ({success_rate:.1f}%) - verifique conexão!")
        
        print("Mapeamento completo!")
    
    def place_pixel(self, x, y, color, retries=2):
        for attempt in range(retries):
            try:
                delay = self.request_delay * random.uniform(1.0, 1.5) * self.rate_limit_multiplier
                time.sleep(delay)
                
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
                    print(f"Rate limit ao colocar pixel! Aumentando delays... (tentativa {attempt + 1})")
                    self.rate_limit_multiplier *= 2
                    time.sleep(30 * (attempt + 1))
                    continue
                    
                if response.status_code == 200:
                    self.rate_limit_multiplier = max(1.0, self.rate_limit_multiplier * 0.9)
                    return True
                
                if response.status_code == 401:
                    print("❌ ERRO: Cookie de sessão expirou!")
                    return False
                    
                print(f"Erro ao enviar pixel ({x},{y}): Status {response.status_code}")
                print(f"Resposta: {response.text}")
                
                if attempt < retries - 1:
                    time.sleep(10)
                
            except Exception as e:
                print(f"Erro de conexão ao enviar pixel ({x},{y}): {e}")
                if attempt < retries - 1:
                    time.sleep(10)
        
        return False
    
    def check_and_fix_areas(self):
        total_changed = 0
        
        for coord in self.coordinates_list:
            changed_pixels = 0
            area_pixels = list(self.reference_colors[coord].items())
            random.shuffle(area_pixels)
            
            print(f"Verificando área {coord}...")
            
            for (x, y), target_color in area_pixels:
                current_color = self.get_pixel_color(x, y)
                
                if current_color is None:
                    print(f"  ⚠️  Não foi possível verificar pixel ({x},{y})")
                    continue
                    
                if current_color != target_color:
                    print(f"  🔧 Pixel ({x},{y}) alterado: {target_color} → {current_color}. Corrigindo...")
                    if self.place_pixel(x, y, target_color):
                        changed_pixels += 1
                        print(f"  ✓ Pixel ({x},{y}) corrigido!")
                        time.sleep(random.uniform(3, 6))
                    else:
                        print(f"  ❌ Falha ao corrigir pixel ({x},{y})")
                        time.sleep(random.uniform(10, 15))
                
                time.sleep(random.uniform(0.5, 1.5) * self.rate_limit_multiplier)
            
            print(f"✓ Área {coord}: {changed_pixels} pixels corrigidos")
            total_changed += changed_pixels
        
        return total_changed
    
    def run(self, scan_interval=600):
        print(f"🚀 Iniciando defensor para {len(self.coordinates_list)} áreas de {self.width}x{self.height}")
        
        cycle = 0
        while True:
            cycle += 1
            start_time = time.time()
            
            print(f"\n🔍 Iniciando ciclo {cycle}...")
            changed = self.check_and_fix_areas()
            elapsed = time.time() - start_time
            
            print(f"✓ Ciclo {cycle} completo. Pixels corrigidos: {changed}. Tempo: {elapsed:.2f}s")
            
            if changed > 0:
                sleep_time = max(120, scan_interval / (changed * 0.3 + 1))
            else:
                sleep_time = scan_interval
                
            sleep_time *= random.uniform(0.9, 1.1) * self.rate_limit_multiplier
            sleep_time = max(120, sleep_time)
            
            print(f"⏰ Próxima verificação em {sleep_time/60:.1f} minutos...\n")
            time.sleep(sleep_time)


if __name__ == "__main__":
    COORDINATES = [
        (3721, 3533),
    ]
    
    WIDTH = 60
    HEIGHT = 60
    SESSION_COOKIE = ""
    
    if not SESSION_COOKIE:
        print("❌ ERRO: SESSION_COOKIE não foi definido!")
        print("Por favor, cole seu cookie de sessão do WPlace na variável SESSION_COOKIE")
        exit(1)
    
    try:
        defender = WPlaceMultiAreaDefender(COORDINATES, WIDTH, HEIGHT, SESSION_COOKIE)
        defender.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot interrompido pelo usuário")
    except Exception as e:
        print(f"❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
